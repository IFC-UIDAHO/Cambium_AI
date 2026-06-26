"""Cambium framework tests — deterministic checks for the core tools.
Run: pytest -q   (from the repo root)
"""
import os, sys, subprocess, json, tempfile, csv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import task_router, toolsmith, model_router

def run(rel, *args):
    return subprocess.run([sys.executable, rel, *args], cwd=ROOT, capture_output=True, text=True)

# ---- Task Router: auto-selects councils per task type ----
def test_router_software():
    r = task_router.route("build a deployable web app with a backend")
    assert r["type"] == "software"
    assert {"lab","exec","verify"} <= set(r["councils"])
    assert any(p["id"] == "provision" for p in r["phases"])   # toolsmith provisioning gate

def test_router_grant():
    assert task_router.route("write an NSF AFRI grant proposal")["type"] == "grant"

def test_router_review_includes_governance():
    r = task_router.route("review and harden the app")
    assert r["type"] == "review" and "gov" in r["councils"]

def test_router_always_returns_phases():
    for t in ["analyze a dataset","make a progress report","study a new estimator","random words"]:
        r = task_router.route(t); assert r["phases"] and r["type"]

# ---- Toolsmith: recommends a stack ----
def test_toolsmith_software_stack():
    m = toolsmith.manifest("build a 3d web app")
    assert m["type"] == "software" and len(m["recommended"]) >= 3
    assert all("install" in x for x in m["recommended"])

# ---- Model Router: tier mapping is correct ----
def test_model_router_tiers():
    assert model_router.TIER_OF["opus"] == "strong"
    assert model_router.TIER_OF["haiku"] == "light"

def test_model_router_resolve_opus_to_strong():
    cards = model_router.load_cards(); cfg,_ = model_router.load_config()
    _, tiers = model_router.active_tiers(cfg)
    rt, model = model_router.resolve("lab-theory", cards, tiers)   # lab-theory is opus
    assert rt == "strong" and model == tiers["strong"]

# ---- CLI tools exit cleanly on a healthy repo ----
def test_check_agents_ok():    assert run("tools/check_agents.py").returncode == 0
def test_consistency_ok():     assert run("tools/consistency_check.py").returncode == 0
def test_doctor_ok():          assert run("tools/doctor.py").returncode == 0
def test_doctor_grade_ok():    assert run("tools/doctor.py","--grade").returncode == 0

# ---- gen_agent_cards: count matches the live roster ----
def test_agent_cards_in_sync():
    assert run("tools/gen_agent_cards.py").returncode == 0
    import glob
    nf = len([p for p in glob.glob(os.path.join(ROOT,".claude","agents","*.md")) if os.path.basename(p).upper()!="README.MD"])
    n = json.load(open(os.path.join(ROOT,"agent_cards.json")))["count"]
    assert n == nf

# ---- validate.py: blocks fake claims, passes clean ones ----
def _ledger(rows):
    fd, path = tempfile.mkstemp(suffix=".csv"); os.close(fd)
    with open(path,"w",newline="") as f:
        w=csv.writer(f); w.writerow(["id","issue","agents","severity","claim_tier","evidence","status","citation_status","repro"]); 
        for r in rows: w.writerow(r)
    return path

def test_validate_blocks_uncited_code_verified():
    p=_ledger([["F1","x","a","P2","Code-verified","we just ran it","closed","resolved","done"]])
    assert run("governance/validate.py", p).returncode == 1; os.remove(p)

def test_validate_passes_clean():
    p=_ledger([["F1","x","a","P2","Code-verified","$ python check.py -> ok","closed","resolved","done"]])
    assert run("governance/validate.py", p).returncode == 0; os.remove(p)

def test_validate_blocks_unresolved_citation():
    p=_ledger([["F1","x","a","P2","Asserted","see Smith 2024","closed","unresolved","na"]])
    assert run("governance/validate.py", p).returncode == 1; os.remove(p)
