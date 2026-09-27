
"""
retrobio_synbiocad.py
A compact helper library to drive Galaxy-SynBioCAD tools and enumerate/rank retrobiosynthetic
paths from RetroPath2.0 outputs. Designed for use in Colab/Jupyter.

Public entry points:
- set_galaxy(url, api_key)
- check_tools(url=None, api_key=None)
- create_history(name)
- upload_text(hid, name, text, ext="txt")
- upload_file(hid, path, ext=None)
- wait_history(hid, timeout=1200, poll=4)
- resolve_tool_id(candidates)
- ensure_sink_ok(hid, sbml_id, compartments=("MNXC3","MNXC4"))
- ensure_rrules(hid)  -> rules dataset id (csv)
- run_rp2_pipe(hid, rules_id, sink_id, inchi, name, max_steps=4, dmin=1, dmax=8, topx=200, timeout=240, version="v9")
- enumerate_and_rank(hid, net_id, enum_max_steps=6, enum_max_branch=10, drop_currency=True)
- resolve_name_to_inchi(name)
- save_cfg_patch(d, path="./retro_config.json")
- run_end_to_end(sbml_path, target_name, history_name="RetroBio run", **kwargs)
"""

import io
import json
import os
import time
import re
from typing import Dict, List, Tuple, Optional

import requests
import pandas as pd

# --------- Global Galaxy session ---------
BASE = None
KEY  = None
_session = requests.Session()

def set_galaxy(url: str, api_key: str):
    """Configure the Galaxy endpoint to use for subsequent calls."""
    global BASE, KEY, _session
    BASE = url.rstrip("/")
    KEY  = api_key
    _session = requests.Session()
    # convenience: default key param for GETs
    _session.params = {"key": KEY}
    return {"base": BASE, "key_set": bool(KEY)}

# --------- Low-level HTTP helpers ---------
def gget(path: str, **params) -> requests.Response:
    assert BASE and KEY, "Call set_galaxy(url, api_key) first."
    url = BASE + path
    p = dict(_session.params) if getattr(_session, "params", None) else {}
    p.update(params)
    r = _session.get(url, params=p, timeout=params.pop("timeout", 120))
    r.raise_for_status()
    return r

def gpost_tools(payload: dict, timeout: int = 1200) -> requests.Response:
    """POST to /api/tools with a JSON payload."""
    assert BASE and KEY, "Call set_galaxy(url, api_key) first."
    url = f"{BASE}/api/tools"
    p = dict(_session.params) if getattr(_session, "params", None) else {}
    r = _session.post(url, params=p, json=payload, timeout=timeout)
    r.raise_for_status()
    return r

def wait_history(hid: str, timeout: int = 1200, poll: int = 4) -> str:
    """Poll the history until it is ok/error/failed; return final state."""
    start = time.time()
    while True:
        r = gget(f"/api/histories/{hid}")
        st = r.json().get("state", "")
        if st in {"ok", "error", "failed"}:
            return st
        if time.time() - start > timeout:
            raise TimeoutError(f"History {hid} timed out (>{timeout}s)")
        time.sleep(poll)

# alias
wait_hist = wait_history

# --------- Basic Galaxy helpers ---------
def create_history(name: str) -> str:
    r = _session.post(f"{BASE}/api/histories", params={"key": KEY},
                      json={"name": name}, timeout=60)
    r.raise_for_status()
    return r.json()["id"]

def upload_text(hid: str, name: str, text: str, ext: str = "txt") -> str:
    payload = {
        "tool_id": "upload1",
        "history_id": hid,
        "inputs": {
            "file_type": ext,
            "dbkey": "?",
            "files_0|type": "upload_dataset",
            "files_0|NAME": name,
            "files_0|url_paste": text
        }
    }
    gpost_tools(payload, timeout=300)
    wait_hist(hid)
    # find newest OK with this name
    items = list_ok(hid)
    for d in reversed(items):
        if (d.get("name") or "").lower() == name.lower():
            return d["id"]
    # fallback: newest OK dataset
    return items[-1]["id"] if items else ""

def upload_file(hid: str, path: str, ext: Optional[str] = None) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    if ext is None:
        ext = os.path.splitext(path)[1].lstrip(".") or "data"
    with open(path, "rb") as fh:
        r = requests.post(f"{BASE}/api/tools", params={"key": KEY}, files={"files_0|file_data": fh},
                          data={"tool_id": "upload1", "history_id": hid,
                                "inputs": json.dumps({"dbkey": "?", "file_type": ext})},
                          timeout=600)
        r.raise_for_status()
    wait_hist(hid)
    items = list_ok(hid)
    return items[-1]["id"] if items else ""

def list_ok(hid: str) -> List[dict]:
    r = gget(f"/api/histories/{hid}/contents", types="dataset", details="all")
    items = r.json()
    ok = [d for d in items if d.get("state") == "ok"]
    ok.sort(key=lambda d: d.get("update_time", ""), reverse=False)
    return ok

def get_hda_meta(hid: str, cid: str) -> dict:
    return gget(f"/api/histories/{hid}/contents/{cid}", view="detailed").json()

def dataset_text(hid: str, cid: str) -> str:
    meta = get_hda_meta(hid, cid)
    dl = meta.get("download_url")
    if not dl:
        # fallback legacy field
        dl = f"/api/datasets/{cid}/display"
    r = requests.get(f"{BASE}{dl}", params={"key": KEY}, timeout=300)
    r.raise_for_status()
    return r.text

def resolve_tool_id(candidates: List[str]) -> str:
    """Return the first tool id that matches any substring in candidates."""
    r = gget("/api/tools", in_panel="false")
    items = r.json()
    texts = []
    for e in items:
        if isinstance(e, dict):
            texts.append((e.get("id","") + " " + e.get("name","")).lower())
        else:
            texts.append(str(e).lower())
    for cand in candidates:
        c = cand.lower()
        for e in items:
            t = (e.get("id","") + " " + e.get("name","")).lower() if isinstance(e, dict) else str(e).lower()
            if c in t:
                return e["id"] if isinstance(e, dict) else e
    # fallback: first item name-contains
    for e in items:
        if isinstance(e, dict) and any(c in e.get("id","").lower() for c in candidates):
            return e["id"]
    raise RuntimeError(f"No matching tool id for {candidates}")

def check_tools(url: Optional[str]=None, api_key: Optional[str]=None) -> Dict[str, bool]:
    """Lightweight check that core tools exist."""
    base = url.rstrip("/") if url else BASE
    key  = api_key or KEY
    assert base and key, "Provide url/api_key or call set_galaxy first."
    r = requests.get(f"{base}/api/tools", params={"key": key, "in_panel":"false"}, timeout=60)
    r.raise_for_status()
    items = r.json()
    def has(subs): 
        return any(isinstance(e, dict) and any(s in (e.get("id","").lower()) for s in subs) for e in items)
    res = {
        "retropath2": has(["retropath2/retropath2","retropath2"]),
        "rp2paths":   has(["rp2paths/rp2paths","rp2paths"]),
        "rpextractsink": has(["rpextractsink"]),
        "rrparser":   has(["rrparser/rrparser","rrparser"]),
    }
    return res

# --------- Sink builder (SBML → sink CSV) ---------
def ensure_sink_ok(hid: str, sbml_id: str, compartments=("MNXC3","MNXC4")) -> str:
    """Run rpextractsink against an SBML HDA and return a fresh sink CSV id."""
    tool_id = resolve_tool_id(["rpextractsink","toolshed.g2.bx.psu.edu/repos/tduigou/rpextractsink"])
    attempts = []
    for comp in compartments:
        attempts.append({"sbml": {"src":"hda","id": sbml_id}, "compartment_mnx_id": comp})
        attempts.append({"input":{"src":"hda","id": sbml_id}, "compartment_mnx_id": comp})
    last_err = None
    for inp in attempts:
        try:
            gpost_tools({"tool_id": tool_id, "history_id": hid, "inputs": inp}, timeout=900)
            wait_hist(hid)
            # choose newest OK csv with "sink" in name
            ok = [d for d in list_ok(hid) if d.get("extension")=="csv" and "sink" in (d.get("name","").lower())]
            if ok:
                return ok[-1]["id"]
        except Exception as e:
            last_err = e
    raise RuntimeError(f"rpextractsink failed to produce a sink CSV. Last error: {last_err}")

# --------- RRParser (rules.csv) ---------
def _introspect_rrparser_diameters(tool_id: str) -> Optional[str]:
    """Try to read valid diameter options from the Tool definition and pick one."""
    try:
        r = gget(f"/api/tools/{tool_id}", io_details="true")
        J = r.json()
        # walk inputs to find a 'diameters' select
        def walk(node):
            if isinstance(node, dict):
                if node.get("name") == "diameters" and "options" in node:
                    opts = [str(o[0]) if isinstance(o, list) else str(o.get("value")) for o in node["options"]]
                    # choose a median reasonable value
                    if opts:
                        # prefer 8 if present, else first
                        if "8" in opts: return "8"
                        return opts[0]
                for v in node.values():
                    out = walk(v)
                    if out: return out
            elif isinstance(node, list):
                for v in node:
                    out = walk(v)
                    if out: return out
        return walk(J)
    except Exception:
        return None

def ensure_rrules(hid: str) -> str:
    """Guarantee a rules CSV exists by running RRParser with a valid single diameter."""
    tool_id = resolve_tool_id(["rrparser/rrparser","rrparser"])
    dia = _introspect_rrparser_diameters(tool_id) or "8"
    inputs = {"direction":"retro", "diameters": dia, "split": "false"}
    try:
        gpost_tools({"tool_id": tool_id, "history_id": hid, "inputs": inputs}, timeout=600)
        wait_hist(hid)
        # newest OK csv with "rules" or "RRules Parser" in name
        ok = [d for d in list_ok(hid) if d.get("extension")=="csv"]
        ok_named = [d for d in ok if "rrules" in (d.get("name","").lower()) or "parser" in (d.get("name","").lower())]
        return (ok_named[-1]["id"] if ok_named else ok[-1]["id"])
    except Exception as e:
        raise RuntimeError(f"RRParser failed: {e}")

# --------- RetroPath2.0 (pipe schema) ---------
def run_rp2_pipe(
    hid: str,
    rules_id: str,
    sink_id: str,
    inchi: str,
    name: str,
    max_steps: int = 4,
    dmin: int = 1,
    dmax: int = 8,
    topx: int = 200,
    timeout: int = 240,
    version: str = "v9",
) -> str:
    rp2_id = resolve_tool_id(["retropath2/retropath2","retropath2"])
    inputs = {
        "rulesfile": {"src":"hda","id": rules_id},
        "sinkfile":  {"src":"hda","id": sink_id},
        "source_inchi_type|inchi_type": "string",
        "source_inchi_type|source_inchi": inchi,
        "source_name": name,
        "max_steps": str(max_steps),
        "adv|version": version,
        "adv|topx": str(topx),
        "adv|dmin": str(dmin),
        "adv|dmax": str(dmax),
        "adv|mwmax_source": "1000",
        "adv|timeout": str(timeout)
    }
    gpost_tools({"tool_id": rp2_id, "history_id": hid, "inputs": inputs}, timeout=2400)
    wait_hist(hid)
    # newest OK "RetroPath" dataset with expected header
    for d in reversed(list_ok(hid)):
        nm = (d.get("name","").lower())
        if "retropath" in nm or "network" in nm:
            txt = dataset_text(hid, d["id"])
            head = (txt.splitlines()[0] if txt else "")
            if all(k in head for k in ["Initial source","Substrate InChI","Product InChI"]):
                return d["id"]
    raise RuntimeError("RetroPath2.0 finished but no valid Reaction Network was detected.")

# --------- CSV robust loader ---------
def _parse_csv_robust(text: str) -> pd.DataFrame:
    try:
        return pd.read_csv(io.StringIO(text))
    except Exception:
        # try python engine
        try:
            return pd.read_csv(io.StringIO(text), engine="python")
        except Exception:
            # fix common broken-quote lines: drop lines ending with odd quotes
            lines = text.splitlines()
            cleaned = []
            openq = False
            for ln in lines:
                # naive fix for dangling quote
                if ln.count('"') % 2 == 1:
                    # drop it
                    continue
                cleaned.append(ln)
            return pd.read_csv(io.StringIO("\n".join(cleaned)), engine="python")

# --------- Enumerate & rank (RP2paths stand-in) ---------
CURRENCY_MNX = {"MNXM1","MNXM2","MNXM11","MNXM12","MNXM14"}

def enumerate_and_rank(
    hid: str,
    net_id: str,
    enum_max_steps: int = 6,
    enum_max_branch: int = 10,
    drop_currency: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    txt = dataset_text(hid, net_id)
    df  = _parse_csv_robust(txt)
    # standardize columns
    df.columns = [c.strip().strip('"') for c in df.columns]
    if "In Sink" not in df.columns:
        raise ValueError("Network missing 'In Sink' column.")
    def _to01(v):
        s = str(v).strip().strip('"').lower()
        return 1 if s in ("1","true","t","yes","y") else 0
    df["In Sink"] = df["In Sink"].apply(_to01)

    from collections import defaultdict, deque
    adj = defaultdict(list)
    for _, r in df.iterrows():
        subs = str(r["Substrate InChI"]); prod = str(r["Product InChI"])
        rule = str(r["Rule ID"]).strip("[]")
        ec   = str(r.get("EC number","")).strip("[]")
        try: sc = float(r.get("Score", 0.0))
        except Exception: sc = 0.0
        adj[subs].append((prod, rule, ec if ec else "NOEC", sc))

    start_inchi = str(df["Substrate InChI"].iloc[0])
    sink_idx = (df["In Sink"]==1)
    sink_set = set(df.loc[sink_idx, "Product InChI"].astype(str))
    sink_name_by_inchi = {
        str(r["Product InChI"]): str(r["Sink name"]).strip("[]")
        for _, r in df.loc[sink_idx].iterrows()
    }

    # BFS
    paths=[]; q=deque(); q.append((start_inchi, [])); best_depth={start_inchi:0}
    while q:
        node, path = q.popleft()
        depth = len(path)
        if depth >= enum_max_steps:
            continue
        outs = adj.get(node, [])[:enum_max_branch]
        for (prod, rule, ec, sc) in outs:
            step = (node, prod, rule, ec, sc)
            newp = path + [step]
            if prod in sink_set:
                paths.append(newp)
            if best_depth.get(prod, 1e9) > depth+1:
                best_depth[prod] = depth+1
                q.append((prod, newp))

    def agg_score(p): return sum(s[-1] for s in p)
    paths.sort(key=lambda p: (len(p), -agg_score(p)))

    rows=[]
    for pid, p in enumerate(paths, 1):
        for step_idx, (subs, prod, rule, ec, sc) in enumerate(p, 1):
            rows.append({
                "PathID": pid,
                "Step": step_idx,
                "From (Substrate InChI)": subs,
                "To (Product InChI)": prod,
                "Rule ID": rule,
                "EC number": ec,
                "Score": sc,
                "Hit sink?": "YES" if prod in sink_set else "NO",
                "Sink name": sink_name_by_inchi.get(prod, "")
            })
    df_paths = pd.DataFrame(rows)

    # filter & summarize
    if drop_currency and not df_paths.empty:
        terminal = df_paths.groupby("PathID")["Step"].max().rename("MaxStep")
        dfp2 = df_paths.merge(terminal, on="PathID")
        terminals = dfp2[dfp2["Step"]==dfp2["MaxStep"]].copy()
        keep_ids = terminals[~terminals["Sink name"].isin(CURRENCY_MNX)]["PathID"].unique()
        df_paths = df_paths[df_paths["PathID"].isin(keep_ids)].copy()

    def split_ecs(series):
        ecs=set()
        for r in series:
            # remove brackets and split on comma/space
            toks = re.split(r"[,\s]+", str(r).replace("[","").replace("]",""))
            for t in toks:
                t = t.strip()
                if t and t != "NOEC":
                    ecs.add(t)
        return sorted(ecs)

    summ = (
        df_paths.groupby("PathID")
        .agg(
            steps=("Step","max"),
            total_score=("Score","sum"),
            terminal_inchi=("To (Product InChI)","last"),
            terminal_sink=("Sink name","last"),
            rules=("Rule ID", lambda s: sorted(set(
                x for r in s for x in re.split(r"[,\s]+", str(r).replace("[","").replace("]","")) if x
            ))),
            ecs=("EC number", split_ecs)
        )
        .reset_index()
        .sort_values(["steps","total_score"], ascending=[True,False])
    )

    return df_paths, summ

# --------- Compound resolver ---------
def resolve_name_to_inchi(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("Empty compound name.")
    # NIH Cactus InChI
    try:
        r = requests.get(f"https://cactus.nci.nih.gov/chemical/structure/{name}/stdinchi", timeout=30)
        if r.ok and r.text.strip():
            return r.text.strip()
    except Exception:
        pass
    # PubChem
    try:
        r = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/cids/TXT", timeout=30)
        if r.ok and r.text.strip():
            cid = r.text.splitlines()[0].strip()
            r2 = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/InChI/TXT", timeout=30)
            if r2.ok and r2.text.strip():
                return r2.text.strip()
    except Exception:
        pass
    raise RuntimeError("Could not resolve name to InChI via Cactus or PubChem.")

# --------- Config patch helper ---------
def save_cfg_patch(d: dict, path: str="./retro_config.json"):
    cur = {}
    if os.path.exists(path):
        try:
            with open(path,"r") as f: cur = json.load(f)
        except Exception:
            cur = {}
    cur.update(d)
    with open(path,"w") as f:
        json.dump(cur, f, indent=2)
    return os.path.abspath(path)

# --------- One-call end-to-end ---------
def run_end_to_end(
    sbml_path: str,
    target_name: str,
    history_name: str = "RetroBio run",
    rp2_version: str = "v9",
    max_steps: int = 4,
    dmin: int = 1,
    dmax: int = 8,
    topx: int = 200,
    timeout: int = 240,
    enum_max_steps: int = 6,
    enum_max_branch: int = 10
) -> dict:
    """High-level pipeline: history → sink → rules → network → enumerate+rank."""
    assert BASE and KEY, "Call set_galaxy(url, api_key) first."
    hid = create_history(history_name)

    # Upload SBML + extract sink
    sbml_id = upload_file(hid, sbml_path, ext="xml")
    sink_id = ensure_sink_ok(hid, sbml_id)

    # Resolve target
    inchi = resolve_name_to_inchi(target_name)

    # Source CSV
    src_id = upload_text(hid, "source.csv", f'Name,InChI\n{target_name},"{inchi}"\n', ext="csv")

    # Rules
    rules_id = ensure_rrules(hid)

    # RP2 network
    net_id = run_rp2_pipe(hid, rules_id, sink_id, inchi, target_name,
                          max_steps=max_steps, dmin=dmin, dmax=dmax, topx=topx,
                          timeout=timeout, version=rp2_version)

    # Enumerate + rank
    paths_df, summ_df = enumerate_and_rank(hid, net_id, enum_max_steps=enum_max_steps, enum_max_branch=enum_max_branch)

    return {
        "history_id": hid,
        "sbml_id": sbml_id,
        "sink_id": sink_id,
        "source_id": src_id,
        "rules_id": rules_id,
        "net_id": net_id,
        "paths": paths_df,
        "summary": summ_df
    }
