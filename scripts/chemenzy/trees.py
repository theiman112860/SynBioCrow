"""Extract explicit forward-side precursor/product records from native route trees."""


def reaction_records(results):
    def walk(molecule, path):
        if molecule["type"] != "mol" or not molecule["smiles"]:
            raise ValueError(f"Expected a molecule at {path}")
        for index, reaction in enumerate(molecule.get("children", [])):
            pointer = f"{path}/children/{index}"
            precursors = reaction["children"]
            if reaction["type"] != "reaction" or not precursors:
                raise ValueError(f"Expected a reaction with substrates at {pointer}")
            if any(child["type"] != "mol" or not child["smiles"] for child in precursors):
                raise ValueError(f"Invalid substrate node at {pointer}")
            reactants = ".".join(child["smiles"] for child in precursors)
            product = molecule["smiles"]
            yield {
                "reactants": reactants,
                "products": product,
                "reaction_smiles": f"{reactants}>>{product}",
                "native_pointer": pointer,
                "native_template": reaction.get("template"),
                "direction": "precursors_to_target",
            }
            for child_index, child in enumerate(precursors):
                yield from walk(child, f"{pointer}/children/{child_index}")

    for target_index, result in enumerate(results):
        for route_index, route in enumerate(result["routes"]):
            for record in walk(route, f"/{target_index}/routes/{route_index}"):
                yield {"target_smiles": result["canonical_target"], **record}
