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

    def test_installed_ius_reads_plugins_and_features(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "plugins").mkdir()
            (root / "features").mkdir()
            (root / "plugins" / "org.knime.chem.base_4.6.4.v20221201.jar").write_bytes(b"x")
            (root / "features" / "org.knime.features.chem.types_4.6.4.v20221201").mkdir()
            got = MOD.installed_ius(root)
            self.assertIn("org.knime.chem.base", got)
            self.assertIn("org.knime.features.chem.types.feature.group", got)

    def test_required_runtime_lock_hashes_plugin_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "plugins").mkdir()
            (root / "features").mkdir()
            p = root / "plugins" / "org.knime.chem.base_4.6.4.v20221201.jar"
            p.write_bytes(b"abc")
            lock = MOD.required_runtime_lock(root, {"org.knime.chem.base"})
            self.assertEqual(len(lock["org.knime.chem.base"]), 1)
            row = lock["org.knime.chem.base"][0]
            self.assertEqual(row["bytes"], 3)
            self.assertEqual(
                row["sha256"],
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )

    def test_default_does_not_enable_full_archive_fallback(self):
        src = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn("--allow-full-update-archive", src)
        self.assertIn("Targeted KNIME 4.6 p2 install failed", src)

    def test_bootstrap_installs_required_ius_not_merely_unavailable_ius(self):
        src = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn("to_install=sorted(required-base_advertised)", src)
        self.assertIn("unavailable=sorted(required-(base_advertised|repo_advertised))", src)
        self.assertIn('"-i",",".join(to_install)', src)
        self.assertNotIn('"-i",",".join(missing)', src)

    def test_normal_selection_excludes_giant_analytics_archive(self):
        src = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn('"org.knime.update.analytics-platform" not in low', src)


if __name__ == "__main__":
    unittest.main()
