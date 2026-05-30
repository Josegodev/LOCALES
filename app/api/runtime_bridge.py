from importlib import import_module
from types import ModuleType


def main_module() -> ModuleType:
    return import_module("app.main")
