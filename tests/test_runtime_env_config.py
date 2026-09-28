import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from synbiocrow.generators.registry import default_registry

class RuntimeEnvConfigTests(unittest.TestCase):
    def test_retropath_and_biopks_environment_discovery(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            rules=root/"rules.csv"; rules.write_text("x\n")
            sink=root/"sink.csv"; sink.write_text("x\n")
            knime_dir=root/"knime"; knime_dir.mkdir()
            kexec=knime_dir/"knime"
            kexec.write_text("#!/bin/sh\nexit 0\n")
            kexec.chmod(kexec.stat().st_mode | stat.S_IXUSR)
            bridge=root/"bridge.py"; bridge.write_text("print('{}')\n")
            py=root/"python"; py.write_text("#!/bin/sh\nexit 0\n")
            py.chmod(py.stat().st_mode | stat.S_IXUSR)

            env={
                "SYNBIOCROW_RETROPATH_RULES":str(rules),
                "SYNBIOCROW_RETROPATH_SINK":str(sink),
                "SYNBIOCROW_RETROPATH_KNIME":str(knime_dir),
                "SYNBIOCROW_BIOPKS_RUNNER":str(bridge),
                "SYNBIOCROW_BIOPKS_PYTHON":str(py),
                "SYNBIOCROW_BIOPKS_ACK_LICENSE":"1",
            }
            with patch.dict(os.environ,env,clear=False):
                registry=default_registry()
                rp=registry.get("retropath2")
                bp=registry.get("biopks_retrotide")
                self.assertIsNotNone(rp.settings)
                self.assertEqual(rp.settings.rules_file,str(rules))
                self.assertEqual(rp.settings.sink_file,str(sink))
                self.assertEqual(rp.settings.knime_install,str(knime_dir))
                self.assertTrue(bp.available())

if __name__=="__main__":
    unittest.main()
