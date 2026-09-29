import unittest
from pathlib import Path
import importlib.util

class M9ReleaseTests(unittest.TestCase):
    def test_required_rc_files_exist(self):
        root=Path(__file__).resolve().parents[1]
        required=[
            "README.md",
            "RELEASE_NOTES_2_2_RC1.md",
            "notebooks/SynBioCrow_2_2_RC1_ALL_GENERATORS.ipynb",
            "docs/M9_RELEASE_CANDIDATE.md",
            "paper/2.2/METHODS.md",
            "paper/2.2/RESULTS.md",
            "scripts/build_m9_release.py",
        ]
        for rel in required:
            self.assertTrue((root/rel).is_file(),rel)

    def test_package_version_is_rc1(self):
        import synbiocrow
        self.assertEqual(synbiocrow.__version__,"2.2.0rc1")

if __name__=="__main__":
    unittest.main()
