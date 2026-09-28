import io
import tempfile
import unittest
import zipfile
from pathlib import Path
import importlib.util


BOOTSTRAP = Path(__file__).resolve().parents[1] / "scripts" / "bootstrap_retropath2.py"
SPEC = importlib.util.spec_from_file_location("bootstrap_retropath2", BOOTSTRAP)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)


def content_xml(*ids: str) -> bytes:
    units = "".join(f'<unit id="{x}" version="1.0.0"/>' for x in ids)
    return f'<?xml version="1.0" encoding="UTF-8"?><repository><units>{units}</units></repository>'.encode()


class P2RepositoryProbeTests(unittest.TestCase):
    def test_reads_content_xml_repository(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "repo.zip"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("content.xml", content_xml("org.knime.chem.base", "org.rdkit.knime.feature.feature.group"))
            self.assertEqual(
                MOD.p2_units(p),
                {"org.knime.chem.base", "org.rdkit.knime.feature.feature.group"},
            )

    def test_reads_content_jar_repository(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "repo.zip"
            inner = io.BytesIO()
            with zipfile.ZipFile(inner, "w") as z:
                z.writestr("content.xml", content_xml("org.knime.chem.base"))
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("content.jar", inner.getvalue())
            self.assertEqual(MOD.p2_units(p), {"org.knime.chem.base"})

    def test_non_p2_zip_is_empty(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "repo.zip"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("README.txt", "not a p2 repository")
            self.assertEqual(MOD.p2_units(p), set())


if __name__ == "__main__":
    unittest.main()
