import unittest
from pathlib import Path


class FrontendGenerationControlsStaticTests(unittest.TestCase):
    REPO_ROOT = Path(__file__).resolve().parents[1]

    def test_frontend_exposes_generation_controls_and_payload_fields(self):
        frontend_html = (self.REPO_ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        frontend_js = (self.REPO_ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
        frontend_css = (self.REPO_ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("Parametros de generacion", frontend_html)
        self.assertIn('class="generation-controls-grid"', frontend_html)
        self.assertIn('id="temperatureSelect"', frontend_html)
        self.assertIn('id="topPInput"', frontend_html)
        self.assertIn('id="topPInput"\n                    type="range"', frontend_html)
        self.assertIn('id="topPValue"', frontend_html)
        self.assertIn('id="topKInput"', frontend_html)
        self.assertIn('id="topKInput"\n                    type="range"', frontend_html)
        self.assertIn('id="topKValue"', frontend_html)
        self.assertIn("Temperature", frontend_html)
        self.assertIn("Top P", frontend_html)
        self.assertIn("Top K generacion", frontend_html)
        self.assertIn("Aleatoriedad de la respuesta.", frontend_html)
        self.assertIn("Probabilidad acumulada considerada.", frontend_html)
        self.assertIn("Candidatos del modelo. No afecta al RAG.", frontend_html)
        self.assertIn('id="responseTopP"', frontend_html)
        self.assertIn('id="responseTopK"', frontend_html)
        self.assertIn('id="runDetailTopP"', frontend_html)
        self.assertIn('id="runDetailTopK"', frontend_html)

        self.assertIn(".generation-controls-grid {", frontend_css)
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr));", frontend_css)
        self.assertIn("align-items: end;", frontend_css)
        self.assertIn(".generation-control {", frontend_css)
        self.assertIn(".generation-control-label {", frontend_css)
        self.assertIn(".range-value {", frontend_css)
        self.assertIn("@media (max-width: 760px)", frontend_css)

        self.assertIn("const DEFAULT_TOP_P = 0.9;", frontend_js)
        self.assertIn("const DEFAULT_TOP_K = 40;", frontend_js)
        self.assertIn("const fallbackGenerationOptions = {", frontend_js)
        self.assertIn("data?.generation", frontend_js)
        self.assertIn("locales.chatTopP", frontend_js)
        self.assertIn("locales.chatTopK", frontend_js)
        self.assertIn("top_p: selectedTopP", frontend_js)
        self.assertIn("top_k: selectedTopK", frontend_js)
        self.assertIn("applyTopPOptions(fallbackGenerationOptions.top_p)", frontend_js)
        self.assertIn("applyTopKOptions(fallbackGenerationOptions.top_k)", frontend_js)
        self.assertIn('topPValue: document.querySelector("#topPValue")', frontend_js)
        self.assertIn('topKValue: document.querySelector("#topKValue")', frontend_js)
        self.assertIn('elements.topPInput.addEventListener("input"', frontend_js)
        self.assertIn('elements.topKInput.addEventListener("input"', frontend_js)
        self.assertIn("function renderGenerationControlValues()", frontend_js)
        self.assertIn('responseTopP: document.querySelector("#responseTopP")', frontend_js)
        self.assertIn('responseTopK: document.querySelector("#responseTopK")', frontend_js)
        self.assertIn('runDetailTopP: document.querySelector("#runDetailTopP")', frontend_js)
        self.assertIn('runDetailTopK: document.querySelector("#runDetailTopK")', frontend_js)
        self.assertIn("renderGenerationControlValues();", frontend_js)
        self.assertIn("elements.responseTopP.textContent = formatFloat(data?.top_p, 2);", frontend_js)
        self.assertIn("elements.responseTopK.textContent = metricOrNA(data?.top_k, (value) => Number(value).toFixed(0));", frontend_js)


if __name__ == "__main__":
    unittest.main()
