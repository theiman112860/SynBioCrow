"""M1.20.6 RSPlanner worker, executed only inside the native environment."""
import json
import sys
import traceback
from pathlib import Path

from rdkit import Chem
from retro_planner.api import RSPlanner


def canonical(smiles):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError("Invalid SMILES: " + smiles)
    return Chem.MolToSmiles(molecule)


def main():
    config_path, stock, model, targets_path, output = map(str, sys.argv[1:])
    config = json.loads(Path(config_path).read_text())
    planner = RSPlanner(config)
    planner.select_stock(stock)
    planner.select_one_step_model(model)
    planner.prepare_plan(
        prepare_easifa=False,
        prepare_condition_predictor=False,
        prepare_enzyme_recommander=False,
    )
    results = []
    for target in json.loads(Path(targets_path).read_text()):
        try:
            expected = canonical(target)
            result = planner.plan(expected)
            if result is not None and (not isinstance(result, dict) or not result.get("succ")):
                raise RuntimeError("Unexpected RSPlanner result for " + target)
            routes = ([route.route_to_dict() for route in result["all_succ_routes"]]
                      if result else [])
            for route in routes:
                if canonical(route["smiles"]) != expected or not route.get("children"):
                    raise ValueError("Route root is not a target-specific reaction for " + target)
            results.append({"target": target, "canonical_target": expected, "routes": routes})
        except Exception as exc:
            results.append({"target": target, "routes": [], "error": str(exc)})
            traceback.print_exc()
        Path(output).write_text(json.dumps(results, default=str, indent=2) + "\n")



if __name__ == "__main__":
    main()
