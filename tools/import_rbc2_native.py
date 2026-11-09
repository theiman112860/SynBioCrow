"""Import Canonical V2 RetroBioCat2 native output into an uncertified exchange.

No engine is executed here. This never labels pathways certified.
Usage: python tools/import_rbc2_native.py results.json exchange.json
"""
import argparse
import json
from pathlib import Path

ENGINE = 'RetroBioCat2'
SOURCE_COMMIT = 'c5f32561b1ed99d0701a6dbb472dc448d6c082e8'


def convert(report):
    """Return a lossless, conservative exchange or raise ValueError."""
    if not isinstance(report, dict) or report.get('engine') != ENGINE:
        raise ValueError('Unexpected native engine')
    if report.get('source_commit') != SOURCE_COMMIT:
        raise ValueError('Unexpected or missing native source commit')
    targets = report.get('targets')
    if not isinstance(targets, list):
        raise ValueError('Missing native targets')
    records, diagnostics, seen = [], [], set()
    for target in targets:
        if not isinstance(target, dict) or not isinstance(target.get('smiles'), str):
            raise ValueError('Malformed target record')
        smiles = target['smiles']
        if smiles in seen:
            raise ValueError('Duplicate native target: ' + smiles)
        seen.add(smiles)
        status = target.get('status')
        reactions = target.get('reactions')
        if not isinstance(reactions, list):
            raise ValueError('Missing reaction array for ' + smiles)
        if status != 'NATIVE_EXECUTED':
            diagnostics.append({'target_smiles': smiles, 'issue': 'native_target_not_executed', 'native_status': status})
            if reactions:
                raise ValueError('Failed native target contains reactions: ' + smiles)
            continue
        if target.get('count') != len(reactions):
            raise ValueError('Native reaction count mismatch for ' + smiles)
        if not reactions:
            diagnostics.append({'target_smiles': smiles, 'issue': 'zero_native_reactions'})
        for index, rec in enumerate(reactions):
            if not isinstance(rec, dict):
                raise ValueError('Malformed native reaction')
            if rec.get('target_smiles') != smiles or rec.get('engine') != ENGINE or rec.get('source_commit') != SOURCE_COMMIT:
                raise ValueError('Reaction provenance mismatch for ' + smiles)
            reaction_smiles = rec.get('reaction_smiles')
            if not isinstance(reaction_smiles, str) or reaction_smiles.count('>>') != 1 or not all(reaction_smiles.split('>>')):
                raise ValueError('Missing reaction SMILES for ' + smiles)
            if rec.get('candidate_only') is not True:
                raise ValueError('Native candidate status missing for ' + smiles)
            if rec.get('reaction_smiles_parseable') is not True:
                diagnostics.append({'target_smiles': smiles, 'reaction_index': index, 'issue': 'native_parser_did_not_validate_smiles'})
            records.append({
                'id': f'retrobiocat2-{len(records):06d}',
                'engine': 'retrobiocat2',
                'target_smiles': smiles,
                'reaction_smiles': reaction_smiles,
                'reaction_name': rec.get('reaction_name'),
                'native_score': rec.get('native_score'),
                'source_commit': SOURCE_COMMIT,
                'reaction_smiles_parseable_native': rec.get('reaction_smiles_parseable') is True,
                'status': 'CANDIDATE_UNCERTIFIED',
                'reaction_graph_certified': False,
                'native_record': rec,
            })
    return {
        'schema_version': 'synbiocrow.engine-exchange.v3',
        'source_format': 'SynBioCrow_Seven_Engine_Canonical_V2/results/results.json',
        'native_run_status': report.get('status'),
        'reactions': records,
        'pathways': [],
        'diagnostics': diagnostics,
        'scientific_status': 'CANDIDATE_UNCERTIFIED',
        'note': 'Imported native candidate reactions only; no pathway closure or scientific certification.'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('native_results', type=Path)
    parser.add_argument('exchange_output', type=Path)
    args = parser.parse_args()
    exchange = convert(json.loads(args.native_results.read_text(encoding='utf-8')))
    args.exchange_output.parent.mkdir(parents=True, exist_ok=True)
    args.exchange_output.write_text(json.dumps(exchange, indent=2), encoding='utf-8')
    print('Imported', len(exchange['reactions']), 'uncertified RBC2 candidates; diagnostics:', len(exchange['diagnostics']))


if __name__ == '__main__':
    main()
