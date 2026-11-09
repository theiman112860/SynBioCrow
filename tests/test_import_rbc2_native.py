"""Structural-only tests: invented fixtures never count as native evidence."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from import_rbc2_native import convert, SOURCE_COMMIT


def fixture():
    return {'engine': 'RetroBioCat2', 'source_commit': SOURCE_COMMIT, 'status': 'COMPLETED',
            'targets': [{'smiles': 'CCCC=O', 'status': 'NATIVE_EXECUTED', 'count': 1,
                         'reactions': [{'target_smiles': 'CCCC=O', 'engine': 'RetroBioCat2',
                                        'source_commit': SOURCE_COMMIT,
                                        'reaction_smiles': 'CCC=O>>CCCC=O',
                                        'candidate_only': True,
                                        'reaction_smiles_parseable': True}]}]}


class ImportTests(unittest.TestCase):
    def test_import_candidate_not_certified(self):
        result = convert(fixture())
        self.assertEqual(len(result['reactions']), 1)
        self.assertFalse(result['reactions'][0]['reaction_graph_certified'])
        self.assertEqual(result['pathways'], [])

    def test_zero_reactions_not_invented(self):
        data = fixture()
        data['targets'][0].update(count=0, reactions=[])
        result = convert(data)
        self.assertEqual(result['reactions'], [])
        self.assertEqual(result['diagnostics'][0]['issue'], 'zero_native_reactions')

    def test_wrong_commit_rejected(self):
        data = fixture()
        data['source_commit'] = 'other'
        with self.assertRaises(ValueError):
            convert(data)

    def test_wrong_target_rejected(self):
        data = fixture()
        data['targets'][0]['reactions'][0]['target_smiles'] = 'wrong'
        with self.assertRaises(ValueError):
            convert(data)

    def test_failed_native_target_does_not_import(self):
        data = fixture()
        data['targets'][0].update(status='TARGET_FAILED', reactions=[], count=0)
        result = convert(data)
        self.assertEqual(result['reactions'], [])
        self.assertEqual(result['diagnostics'][0]['issue'], 'native_target_not_executed')

    def test_failed_target_with_reactions_rejected(self):
        data = fixture()
        data['targets'][0]['status'] = 'TARGET_FAILED'
        with self.assertRaises(ValueError):
            convert(data)

    def test_unparseable_candidate_flagged_not_certified(self):
        data = fixture()
        data['targets'][0]['reactions'][0]['reaction_smiles_parseable'] = False
        result = convert(data)
        self.assertEqual(result['diagnostics'][0]['issue'], 'native_parser_did_not_validate_smiles')


if __name__ == '__main__':
    unittest.main()
