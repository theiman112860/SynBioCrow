from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import matplotlib.pyplot as plt

ARMS=("doranet","retrobiocat2","retropath_standalone","ensemble")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scored",required=True)
    ap.add_argument("--errors",required=True)
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()
    scored=json.loads(Path(args.scored).read_text())
    errors=json.loads(Path(args.errors).read_text())
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)

    rows=[]
    for arm in ARMS:
        s=scored["summary"]["connectivity"][arm]
        rows.append({
            "arm":arm,
            "partial_recovery_targets":s["partial_recovery_targets"],
            "exact_top10":s["exact_top10"],
            "exact_top50":s["exact_top50"],
            "mean_best_reaction_recall":s["mean_best_reaction_recall"],
            "exact_mrr":s["exact_mrr"],
        })
    with (out/"table_benchmark_summary.csv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    labels=[r["arm"] for r in rows]
    vals=[r["partial_recovery_targets"] for r in rows]
    fig=plt.figure(figsize=(8,5))
    plt.bar(labels,vals)
    plt.ylabel("Targets with partial reaction recovery (of 65)")
    plt.title("Held-out Galaxy benchmark: connectivity-level recovery")
    plt.tight_layout()
    fig.savefig(out/"figure_benchmark_partial_recovery.png",dpi=200)
    plt.close(fig)

    ec=errors["counts"]
    fig=plt.figure(figsize=(10,5))
    plt.bar(list(ec),list(ec.values()))
    plt.xticks(rotation=45,ha="right")
    plt.ylabel("Targets")
    plt.title("Held-out benchmark failure-mode classification")
    plt.tight_layout()
    fig.savefig(out/"figure_benchmark_failure_modes.png",dpi=200)
    plt.close(fig)

    md=["# SynBioCrow 2.3 manuscript-ready benchmark summary","",
        "| Arm | Partial recovery | Exact Top-10 | Exact Top-50 | Mean best recall | Exact MRR |",
        "|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        md.append(f"| {r['arm']} | {r['partial_recovery_targets']}/65 | {r['exact_top10']}/65 | {r['exact_top50']}/65 | {r['mean_best_reaction_recall']:.3f} | {(r['exact_mrr'] or 0):.3f} |")
    md+=["","## Failure modes",""]
    for k,v in sorted(ec.items(),key=lambda kv:(-kv[1],kv[0])):
        md.append(f"- {k}: {v}/65")
    (out/"MANUSCRIPT_BENCHMARK_TABLES.md").write_text("\n".join(md)+"\n")
    print("\n".join(md))
    return 0
if __name__=="__main__": raise SystemExit(main())
