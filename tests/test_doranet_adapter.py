import unittest
from unittest.mock import patch
import synbiocrow.generators.doranet as doranet_module

from synbiocrow.core.errors import ContractViolation
from synbiocrow.core.models import LifecycleState
from synbiocrow.generators.doranet import (
    DORAnetBackend,
    _network_to_candidates,
)


class FakeMol:
    def __init__(self, uid):
        self.uid = uid


class FakeRxn:
    def __init__(self, operator, reactants, products):
        self.operator = operator
        self.reactants = reactants
        self.products = products


class FakeOps:
    def meta(self, index, keys=None):
        data = {
            "name": "rule_demo",
            "SMARTS": "[C:1]>>[C:1]O",
            "Reaction_direction": "retro",
        }
        if keys is None:
            return data
        if isinstance(keys, str):
            return {keys: data[keys]} if keys in data else {}
        return {k: data[k] for k in keys if k in data}


class FakeNetwork:
    def __init__(self):
        self.mols = [FakeMol("CCO"), FakeMol("CC=O"), FakeMol("O")]
        self.rxns = [FakeRxn(0, (0,), (1, 2))]
        self.ops = FakeOps()


class DORAnetAdapterTests(unittest.TestCase):
    def test_normalizes_reaction_and_provenance(self):
        out = _network_to_candidates(
            FakeNetwork(),
            target_smiles="CCO",
            doranet_version="0.5.7a1",
            ruleset="JN3604IMT",
            direction="retro",
        )
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].steps[0].reaction, "CCO = CC=O + O")
        self.assertEqual(out[0].steps[0].rule_id, "rule_demo")
        self.assertEqual(out[0].source_backends, ("doranet",))
        self.assertEqual(out[0].lifecycle, LifecycleState.CANDIDATE)
        self.assertEqual(
            out[0].provenance["mode"],
            "one_generation_direct_rule_probe",
        )

    def test_candidate_id_is_deterministic(self):
        a = _network_to_candidates(
            FakeNetwork(),
            target_smiles="CCO",
            doranet_version="0.5.7a1",
            ruleset="JN3604IMT",
            direction="retro",
        )
        b = _network_to_candidates(
            FakeNetwork(),
            target_smiles="CCO",
            doranet_version="0.5.7a1",
            ruleset="JN3604IMT",
            direction="retro",
        )
        self.assertEqual(a[0].candidate_id, b[0].candidate_id)

    def test_multigeneration_fails_closed_before_runtime(self):
        with self.assertRaises(ContractViolation):
            DORAnetBackend().generate("CCO", options={"generations": 2})

    def test_generate_calls_live_api_contract(self):
        backend = DORAnetBackend()

        class FakeModule:
            @staticmethod
            def generate_network(**kwargs):
                self.assertEqual(kwargs["starters"], ["CCO"])
                self.assertEqual(kwargs["gen"], 1)
                self.assertEqual(kwargs["direction"], "retro")
                return FakeNetwork()

        with patch.object(backend, "available", return_value=True),              patch.object(doranet_module.importlib, "import_module", return_value=FakeModule),              patch.object(doranet_module.importlib_metadata, "version", return_value="0.5.7a1"):
            out = backend.generate("CCO")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].provenance["doranet_version"], "0.5.7a1")


if __name__ == "__main__":
    unittest.main()
