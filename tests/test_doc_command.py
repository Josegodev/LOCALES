import io
import json
import os
import tempfile
import unittest
import uuid
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ["TELEGRAM_ALLOWED_USER_IDS"] = "123"

import scripts.run_telegram as run_telegram
from app import llm_client
from app import document_writer
from app.document_writer import DocumentWriteError, create_document
from app.main import app
from app.schemas import CreateDocumentRequest

REQUEST_ID = "12345678123456781234567812345678"
REQUEST_ID_2 = "87654321876543218765432187654321"


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict:
        return self._payload


class DocCommandTests(unittest.TestCase):
    def run_doc_command(
        self,
        text: str,
        *,
        user_id: int | None = 123,
        chat_id: int | None = 456,
    ) -> tuple[str, dict]:
        output = io.StringIO()
        with redirect_stdout(output):
            reply = run_telegram.handle_doc_command(
                text=text,
                user_id=user_id,
                chat_id=chat_id,
            )

        log_event = json.loads(output.getvalue().strip())
        return reply, log_event

    def run_doc_ai_command(
        self,
        text: str,
        *,
        user_id: int | None = 123,
        chat_id: int | None = 456,
    ) -> tuple[str, list[dict], str]:
        output = io.StringIO()
        with redirect_stdout(output):
            reply = run_telegram.handle_doc_ai_command(
                text=text,
                user_id=user_id,
                chat_id=chat_id,
            )

        raw_output = output.getvalue()
        events = [
            json.loads(line)
            for line in raw_output.splitlines()
            if line.strip().startswith("{")
        ]
        return reply, events, raw_output

    def test_doc_valid_command_posts_create_document_request(self):
        parsed = run_telegram.parse_doc_command(
            "/doc prueba.md\ncontenido valido\nsegunda linea",
            user_id=123,
            chat_id=456,
        )
        self.assertEqual(parsed.command, "doc.create")
        self.assertEqual(parsed.filename, "prueba.md")
        self.assertEqual(parsed.content, "contenido valido\nsegunda linea")
        self.assertEqual(parsed.user_id, 123)
        self.assertEqual(parsed.chat_id, 456)

        fake_response = FakeResponse(
            200,
            {"filename": "prueba.md", "chars": 31},
        )

        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            with patch.object(run_telegram.uuid, "uuid4", return_value=uuid.UUID(hex=REQUEST_ID)):
                with patch.object(run_telegram.requests, "post", return_value=fake_response) as post:
                    reply, log_event = self.run_doc_command(
                        "/doc prueba.md\ncontenido valido\nsegunda linea"
                    )

        self.assertIn("Documento creado: prueba.md", reply)
        self.assertEqual(log_event["request_id"], REQUEST_ID)
        self.assertEqual(log_event["command"], "doc.create")
        self.assertEqual(log_event["status"], "accepted")
        self.assertEqual(log_event["reason"], "created")
        self.assertEqual(log_event["filename"], "prueba.md")
        post.assert_called_once()
        self.assertEqual(
            post.call_args.kwargs["json"],
            {
                "request_id": REQUEST_ID,
                "filename": "prueba.md",
                "content": "contenido valido\nsegunda linea",
                "overwrite": False,
                "user_id": 123,
                "chat_id": 456,
            },
        )

    def test_doc_ai_generates_content_and_posts_create_document_request(self):
        fake_response = FakeResponse(
            200,
            {"filename": "ai.md", "chars": len("# Titulo\nContenido")},
        )

        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            with patch.object(run_telegram.uuid, "uuid4", return_value=uuid.UUID(hex=REQUEST_ID)):
                with patch.object(
                    run_telegram,
                    "generate_markdown",
                    return_value="# Titulo\r\nContenido",
                ) as generate:
                    with patch.object(run_telegram.requests, "post", return_value=fake_response) as post:
                        reply, events, _ = self.run_doc_ai_command(
                            "/doc_ai ai.md\nEscribe una nota\ncon dos lineas"
                        )

        self.assertIn("Documento creado: ai.md", reply)
        generate.assert_called_once_with(
            "Escribe una nota\ncon dos lineas",
            request_id=REQUEST_ID,
        )
        post.assert_called_once()
        self.assertEqual(
            post.call_args.kwargs["json"],
            {
                "request_id": REQUEST_ID,
                "filename": "ai.md",
                "content": "# Titulo\nContenido",
                "overwrite": False,
                "user_id": 123,
                "chat_id": 456,
            },
        )
        self.assertEqual(
            [event["event"] for event in events],
            [
                "telegram.doc_ai.received",
                "llm.request.started",
                "llm.request.finished",
                "telegram.doc_ai.created",
            ],
        )
        self.assertTrue(all(event["request_id"] == REQUEST_ID for event in events))
        self.assertEqual(events[-1]["output_chars"], len("# Titulo\nContenido"))

    def test_doc_ai_rejects_unauthorized_user_before_llm(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "999"}):
            with patch.object(run_telegram, "generate_markdown") as generate:
                with patch.object(run_telegram.requests, "post") as post:
                    reply, events, _ = self.run_doc_ai_command(
                        "/doc_ai privado.md\nContenido",
                    )

        self.assertIn("No autorizado para crear documentos.", reply)
        generate.assert_not_called()
        post.assert_not_called()
        self.assertEqual(events[-1]["event"], "telegram.doc_ai.rejected")
        self.assertEqual(events[-1]["reason"], "telegram_user_not_allowed")

    def test_doc_ai_rejects_invalid_filename_before_llm(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            with patch.object(run_telegram, "generate_markdown") as generate:
                with patch.object(run_telegram.requests, "post") as post:
                    reply, events, _ = self.run_doc_ai_command(
                        "/doc_ai ../../x.md\nContenido",
                    )

        self.assertIn("No se pudo crear el documento", reply)
        generate.assert_not_called()
        post.assert_not_called()
        self.assertEqual(events[-1]["reason"], "parent_directory_not_allowed")

    def test_doc_ai_does_not_call_writer_when_llm_fails(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            with patch.object(
                run_telegram,
                "generate_markdown",
                side_effect=run_telegram.LLMClientError(
                    "llm_unavailable",
                    "LM Studio no disponible",
                ),
            ) as generate:
                with patch.object(run_telegram.requests, "post") as post:
                    reply, events, _ = self.run_doc_ai_command(
                        "/doc_ai fallo.md\nContenido",
                    )

        self.assertIn("No se pudo generar el documento: llm_unavailable", reply)
        generate.assert_called_once()
        post.assert_not_called()
        self.assertIn("llm.request.failed", [event["event"] for event in events])
        self.assertEqual(events[-1]["reason"], "llm_unavailable")

    def test_doc_ai_propagates_same_request_id_and_forces_overwrite_false(self):
        fake_response = FakeResponse(200, {"filename": "rid.md", "chars": 9})

        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            with patch.object(run_telegram.uuid, "uuid4", return_value=uuid.UUID(hex=REQUEST_ID)):
                with patch.object(run_telegram, "generate_markdown", return_value="contenido"):
                    with patch.object(run_telegram.requests, "post", return_value=fake_response) as post:
                        _, events, _ = self.run_doc_ai_command(
                            "/doc_ai rid.md\nContenido",
                        )

        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["request_id"], REQUEST_ID)
        self.assertFalse(payload["overwrite"])
        self.assertTrue(all(event["request_id"] == REQUEST_ID for event in events))

    def test_doc_ai_rejects_empty_llm_output(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            with patch.object(run_telegram, "generate_markdown", return_value=" \n\t"):
                with patch.object(run_telegram.requests, "post") as post:
                    reply, events, _ = self.run_doc_ai_command(
                        "/doc_ai vacio.md\nContenido",
                    )

        self.assertIn("llm_output_empty", reply)
        post.assert_not_called()
        self.assertEqual(events[-1]["reason"], "llm_output_empty")

    def test_doc_ai_rejects_too_large_llm_output(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            with patch.object(run_telegram.settings, "llm_max_output_chars", 5):
                with patch.object(run_telegram, "generate_markdown", return_value="123456"):
                    with patch.object(run_telegram.requests, "post") as post:
                        reply, events, _ = self.run_doc_ai_command(
                            "/doc_ai grande.md\nContenido",
                        )

        self.assertIn("llm_output_too_large", reply)
        post.assert_not_called()
        self.assertEqual(events[-1]["reason"], "llm_output_too_large")

    def test_doc_ai_rejects_null_bytes_in_llm_output(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            with patch.object(run_telegram, "generate_markdown", return_value="hola\x00mundo"):
                with patch.object(run_telegram.requests, "post") as post:
                    reply, events, _ = self.run_doc_ai_command(
                        "/doc_ai nulo.md\nContenido",
                    )

        self.assertIn("llm_output_contains_null_byte", reply)
        post.assert_not_called()
        self.assertEqual(events[-1]["reason"], "llm_output_contains_null_byte")

    def test_doc_ai_does_not_use_llm_json_as_control(self):
        fake_response = FakeResponse(200, {"filename": "seguro.md", "chars": 40})
        llm_json_as_text = '{"filename":"otro.md","content":"texto"}'

        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            with patch.object(run_telegram, "generate_markdown", return_value=llm_json_as_text):
                with patch.object(run_telegram.requests, "post", return_value=fake_response) as post:
                    reply, _, _ = self.run_doc_ai_command(
                        "/doc_ai seguro.md\nDevuelve JSON",
                    )

        self.assertIn("Documento creado: seguro.md", reply)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["filename"], "seguro.md")
        self.assertEqual(payload["content"], llm_json_as_text)

    def test_doc_ai_does_not_log_prompt_or_output_content(self):
        fake_response = FakeResponse(200, {"filename": "logs.md", "chars": 17})
        prompt_secret = "PROMPT_SECRETO_NO_LOG"
        output_secret = "OUTPUT_SECRETO_NO_LOG"

        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            with patch.object(run_telegram, "generate_markdown", return_value=output_secret):
                with patch.object(run_telegram.requests, "post", return_value=fake_response):
                    _, _, raw_output = self.run_doc_ai_command(
                        f"/doc_ai logs.md\n{prompt_secret}",
                    )

        self.assertNotIn(prompt_secret, raw_output)
        self.assertNotIn(output_secret, raw_output)

    def test_llm_client_posts_non_streaming_chat_completion(self):
        fake_response = FakeResponse(
            200,
            {"choices": [{"message": {"content": "# Markdown"}}]},
        )

        with patch.object(llm_client.settings, "ollama_base_url", "http://127.0.0.1:11434"):
            with patch.object(llm_client.settings, "ollama_model", "modelo-local"):
                with patch.object(llm_client.settings, "ollama_timeout_seconds", 12):
                    with patch.object(llm_client.requests, "post", return_value=fake_response) as post:
                        result = llm_client.generate_markdown("Haz un documento", REQUEST_ID)

        self.assertEqual(result, "# Markdown")
        self.assertEqual(
            post.call_args.args[0],
            "http://127.0.0.1:11434/v1/chat/completions",
        )
        self.assertFalse(post.call_args.kwargs["json"]["stream"])
        self.assertEqual(post.call_args.kwargs["json"]["model"], "modelo-local")
        self.assertEqual(post.call_args.kwargs["timeout"], 12)

    def test_llm_client_maps_lmstudio_connection_error(self):
        with patch.object(
            llm_client.requests,
            "post",
            side_effect=llm_client.requests.exceptions.ConnectionError(),
        ):
            with self.assertRaises(llm_client.LLMClientError) as ctx:
                llm_client.generate_markdown("Haz un documento", REQUEST_ID)

        self.assertEqual(ctx.exception.code, "llm_unavailable")

    def test_llm_client_maps_lmstudio_http_error(self):
        fake_response = FakeResponse(500, {"error": "boom"})

        with patch.object(llm_client.requests, "post", return_value=fake_response):
            with self.assertRaises(llm_client.LLMClientError) as ctx:
                llm_client.generate_markdown("Haz un documento", REQUEST_ID)

        self.assertEqual(ctx.exception.code, "llm_generation_failed")

    def test_fastapi_accepts_valid_document_request(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_safe_root = document_writer.SAFE_ROOT
            document_writer.SAFE_ROOT = Path(tmpdir)
            try:
                with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
                    client = TestClient(app)
                    response = client.post(
                        "/documents",
                        json={
                            "request_id": REQUEST_ID,
                            "filename": "integracion.md",
                            "content": "contenido valido",
                            "overwrite": False,
                            "user_id": 123,
                            "chat_id": 456,
                        },
                    )
            finally:
                document_writer.SAFE_ROOT = original_safe_root

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["request_id"], REQUEST_ID)
        self.assertEqual(response.json()["filename"], "integracion.md")
        self.assertEqual(response.json()["chars"], len("contenido valido"))

    def test_fastapi_rejects_missing_request_id(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            client = TestClient(app)
            response = client.post(
                "/documents",
                json={
                    "filename": "sin_request_id.md",
                    "content": "contenido valido",
                    "overwrite": False,
                    "user_id": 123,
                    "chat_id": 456,
                },
            )

        self.assertEqual(response.status_code, 422)

    def test_fastapi_rejects_invalid_request_id(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            client = TestClient(app)
            response = client.post(
                "/documents",
                json={
                    "request_id": "no-es-un-uuid",
                    "filename": "request_id_invalido.md",
                    "content": "contenido valido",
                    "overwrite": False,
                    "user_id": 123,
                    "chat_id": 456,
                },
            )

        self.assertEqual(response.status_code, 422)

    def test_fastapi_rejects_overwrite_true(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            client = TestClient(app)
            response = client.post(
                "/documents",
                json={
                    "request_id": REQUEST_ID,
                    "filename": "overwrite_true.md",
                    "content": "contenido valido",
                    "overwrite": True,
                    "user_id": 123,
                    "chat_id": 456,
                },
            )

        self.assertEqual(response.status_code, 422)

    def test_fastapi_rejects_extra_fields(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            client = TestClient(app)
            response = client.post(
                "/documents",
                json={
                    "request_id": REQUEST_ID,
                    "filename": "extra.md",
                    "content": "contenido valido",
                    "overwrite": False,
                    "user_id": 123,
                    "chat_id": 456,
                    "unexpected": "no permitido",
                },
            )

        self.assertEqual(response.status_code, 422)

    def test_fastapi_rejects_existing_file_even_with_overwrite_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_safe_root = document_writer.SAFE_ROOT
            document_writer.SAFE_ROOT = Path(tmpdir)
            try:
                with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
                    client = TestClient(app)
                    first_response = client.post(
                        "/documents",
                        json={
                            "request_id": REQUEST_ID,
                            "filename": "existente.md",
                            "content": "primer contenido",
                            "overwrite": False,
                            "user_id": 123,
                            "chat_id": 456,
                        },
                    )
                    second_response = client.post(
                        "/documents",
                        json={
                            "request_id": REQUEST_ID_2,
                            "filename": "existente.md",
                            "content": "segundo contenido",
                            "overwrite": False,
                            "user_id": 123,
                            "chat_id": 456,
                        },
                    )
            finally:
                document_writer.SAFE_ROOT = original_safe_root

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 400)
        self.assertEqual(second_response.json()["detail"]["code"], "file_exists")

    def test_doc_rejects_parent_directory(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            with patch.object(run_telegram.requests, "post") as post:
                reply, log_event = self.run_doc_command("/doc ../../x.md\ncontenido")

        self.assertIn("No se pudo crear el documento", reply)
        self.assertEqual(log_event["status"], "rejected")
        self.assertEqual(log_event["reason"], "parent_directory_not_allowed")
        post.assert_not_called()

    def test_doc_rejects_absolute_path(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            with patch.object(run_telegram.requests, "post") as post:
                reply, log_event = self.run_doc_command("/doc /tmp/x.md\ncontenido")

        self.assertIn("No se pudo crear el documento", reply)
        self.assertEqual(log_event["status"], "rejected")
        self.assertEqual(log_event["reason"], "absolute_path_not_allowed")
        post.assert_not_called()

    def test_doc_rejects_non_markdown_extension(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            with patch.object(run_telegram.requests, "post") as post:
                reply, log_event = self.run_doc_command("/doc a.txt\ncontenido")

        self.assertIn("No se pudo crear el documento", reply)
        self.assertEqual(log_event["status"], "rejected")
        self.assertEqual(log_event["reason"], "only_markdown_extension_allowed")
        post.assert_not_called()

    def test_doc_rejects_empty_content(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            with patch.object(run_telegram.requests, "post") as post:
                reply, log_event = self.run_doc_command("/doc vacio.md\n   ")

        self.assertIn("No se pudo crear el documento", reply)
        self.assertEqual(log_event["status"], "rejected")
        self.assertEqual(log_event["reason"], "content_required")
        post.assert_not_called()

    def test_writer_rejects_overwrite_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_safe_root = document_writer.SAFE_ROOT
            document_writer.SAFE_ROOT = Path(tmpdir)
            try:
                create_document("prueba.md", "primer contenido", request_id=REQUEST_ID)
                with self.assertRaises(DocumentWriteError) as ctx:
                    create_document("prueba.md", "segundo contenido", request_id=REQUEST_ID_2)
            finally:
                document_writer.SAFE_ROOT = original_safe_root

        self.assertEqual(ctx.exception.code, "file_exists")

    def test_doc_rejects_unauthorized_user(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "999"}):
            with patch.object(run_telegram.requests, "post") as post:
                reply, log_event = self.run_doc_command("/doc prueba.md\ncontenido")

        self.assertIn("No autorizado para crear documentos.", reply)
        self.assertIn(f"request_id={log_event['request_id']}", reply)
        self.assertEqual(log_event["status"], "rejected")
        self.assertEqual(log_event["reason"], "telegram_user_not_allowed")
        post.assert_not_called()

    def test_create_document_request_rejects_too_large_content(self):
        with self.assertRaises(ValidationError):
            CreateDocumentRequest(
                request_id=REQUEST_ID,
                filename="grande.md",
                content="x" * 100_001,
                user_id=123,
                chat_id=456,
            )

    def test_fastapi_passes_same_request_id_to_writer_and_response(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
            client = TestClient(app)
            output = io.StringIO()
            with redirect_stdout(output):
                with patch(
                    "app.main.create_document",
                    return_value={
                        "request_id": REQUEST_ID,
                        "status": "created",
                        "filename": "interno.md",
                        "path": "/tmp/interno.md",
                        "chars": len("contenido valido"),
                        "created_at": "2026-05-06T00:00:00+00:00",
                    },
                ) as writer:
                    response = client.post(
                        "/documents",
                        json={
                            "request_id": REQUEST_ID,
                            "filename": "interno.md",
                            "content": "contenido valido",
                            "overwrite": False,
                            "user_id": 123,
                            "chat_id": 456,
                        },
                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["request_id"], REQUEST_ID)
        writer.assert_called_once_with(
            filename="interno.md",
            content="contenido valido",
            request_id=REQUEST_ID,
            overwrite=False,
        )
        log_event = json.loads(output.getvalue().strip())
        self.assertEqual(log_event["component"], "fastapi.documents")
        self.assertEqual(log_event["request_id"], REQUEST_ID)

    def test_writer_logs_request_id_and_does_not_use_it_in_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_safe_root = document_writer.SAFE_ROOT
            document_writer.SAFE_ROOT = Path(tmpdir)
            output = io.StringIO()
            try:
                with redirect_stdout(output):
                    result = create_document(
                        "path_check.md",
                        "contenido valido",
                        request_id=REQUEST_ID,
                    )
                expected_path_exists = (Path(tmpdir) / "path_check.md").exists()
            finally:
                document_writer.SAFE_ROOT = original_safe_root

        self.assertEqual(result["request_id"], REQUEST_ID)
        self.assertEqual(Path(result["path"]).name, "path_check.md")
        self.assertNotIn(REQUEST_ID, result["path"])
        self.assertTrue(expected_path_exists)
        log_event = json.loads(output.getvalue().strip())
        self.assertEqual(log_event["component"], "document_writer")
        self.assertEqual(log_event["request_id"], REQUEST_ID)

    def test_request_id_crosses_telegram_fastapi_writer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_safe_root = document_writer.SAFE_ROOT
            document_writer.SAFE_ROOT = Path(tmpdir)
            try:
                with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "123"}):
                    client = TestClient(app)
                    seen_payload = {}

                    def post_to_fastapi(url: str, json: dict, timeout: int) -> FakeResponse:
                        seen_payload.update(json)
                        response = client.post("/documents", json=json)
                        return FakeResponse(
                            response.status_code,
                            response.json(),
                            response.text,
                        )

                    output = io.StringIO()
                    with redirect_stdout(output):
                        with patch.object(
                            run_telegram.uuid,
                            "uuid4",
                            return_value=uuid.UUID(hex=REQUEST_ID),
                        ):
                            with patch.object(
                                run_telegram.requests,
                                "post",
                                side_effect=post_to_fastapi,
                            ):
                                reply = run_telegram.handle_doc_command(
                                    "/doc cruce.md\ncontenido valido",
                                    user_id=123,
                                    chat_id=456,
                                )
            finally:
                document_writer.SAFE_ROOT = original_safe_root

        self.assertIn("Documento creado: cruce.md", reply)
        self.assertEqual(seen_payload["request_id"], REQUEST_ID)

        events = [
            json.loads(line)
            for line in output.getvalue().splitlines()
            if line.strip().startswith("{")
        ]
        components = {event["component"] for event in events}
        self.assertEqual(
            components,
            {"telegram.doc", "fastapi.documents", "document_writer"},
        )
        self.assertTrue(all(event["request_id"] == REQUEST_ID for event in events))


if __name__ == "__main__":
    unittest.main()
