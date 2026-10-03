"""SynBioCrow 2.4.32 high-tail out-of-fold ranking audit.

Development-only diagnostic. Converts corrected internal-anchor similarity into a
within-target high-similarity tail label (default top decile) and evaluates
out-of-fold nonlinear classifiers/rankers. No production ranking change,
generation, or validation/evaluation truth access.
"""
from __future__ import annotations
import math

FEATURES=(
"rhea_connectivity_fraction","ec_context_fraction","reviewed_ec_context_fraction",
"step_feasibility_mean","step_feasibility_min","filter_score_mean","filter_score_min",
"precedent_step_fraction","rule_coverage_fraction","template_metadata_fraction",
"reaction_domain_fraction","reaction_type_fraction","route_length"
)

def num(x):
    try:
        x=float(x)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def matrix(rows):
    X=[]; y=[]; ids=[]
    for r in rows:
        yy=num(r.get("similarity"))
        if yy is None:
            continue
        X.append([0.0 if num(r.get(f)) is None else num(r.get(f)) for f in FEATURES])
        y.append(yy)
        ids.append(r.get("route_id"))
    return X,y,ids

def tail_labels(y,quantile=0.90):
    import numpy as np
    y=np.asarray(y,float)
    threshold=float(np.quantile(y,quantile))
    labels=(y>=threshold).astype(int)
    return labels.tolist(),threshold
