from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
ALPHA90_MODULE = ROOT / "releases" / "alpha90_1_2_3" / "src" / "alpha90_1_2_3.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def alpha90():
    return load_module(ALPHA90_MODULE, "synbiocrow_alpha90_1_2_3_tested")
