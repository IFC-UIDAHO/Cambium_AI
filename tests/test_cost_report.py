"""Tests for tools/cost_report.py: usage roll-up priced only by user-supplied rates."""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOG_HEADER = "run,phase,agent,model,input_tokens,output_tokens,wall_s,est_usd\n"
RATES = ("model-a:\n  input_per_mtok: 3.0\n  output_per_mtok: 15.0\n"
         "model-b:\n  input_per_mtok: 1.0\n  output_per_mtok: 5.0\n")


def run(*args):
    return subprocess.run([sys.executable, os.path.join(ROOT, "tools", "cost_report.py"), *args],
                          capture_output=True, text=True)


def make_root(tmp_path):
    root = tmp_path / "repo"
    (root / "agent_outputs").mkdir(parents=True)
    (root / "agent_outputs" / "cost_log.csv").write_text(
        LOG_HEADER + "r1,produce,deck-builder,model-a,1000000,500000,1.2,0.5\n", encoding="utf-8")
    return root


def _rates(tmp_path):
    p = tmp_path / "rates.yml"
    p.write_text(RATES, encoding="utf-8")
    return str(p)


def _usage(tmp_path, body):
    p = tmp_path / "usage.csv"
    p.write_text("model,input_tokens,output_tokens,run,date\n" + body, encoding="utf-8")
    return str(p)


def test_help_exits_0():
    assert run("--help").returncode == 0


def test_refuses_without_rates(tmp_path):
    root = make_root(tmp_path)
    r = run("--root", str(root))
    assert r.returncode == 1 and "REFUSING" in r.stdout and "rates" in r.stdout.lower()


def test_refuses_unknown_model(tmp_path):
    root = make_root(tmp_path)
    usage = _usage(tmp_path, "model-z,1000,1000,r9,2026-01-01\n")
    r = run("--root", str(root), "--usage", usage, "--rates", _rates(tmp_path))
    assert r.returncode == 1 and "model-z" in r.stdout and "never invented" in r.stdout


def test_happy_path_math_and_tables(tmp_path):
    root = make_root(tmp_path)  # model-a: 1M in @3 + 0.5M out @15 = 10.50
    usage = _usage(tmp_path, "model-b,2000000,200000,r2,2026-01-15\n")  # 2.0 + 1.0 = 3.00
    r = run("--root", str(root), "--usage", usage, "--rates", _rates(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "GRAND TOTAL: 13.50 USD" in r.stdout
    assert "| model-a | 1 | 1000000 | 500000 | 10.50 |" in r.stdout
    assert "| r2 | 1 | 3.00 |" in r.stdout
    assert "user-supplied" in r.stdout.lower()


def test_monthly_rollup_buckets(tmp_path):
    root = make_root(tmp_path)  # log rows are undated
    usage = _usage(tmp_path, "model-b,1000000,0,r2,2026-01-15\nmodel-b,1000000,0,r3,2026-02-02\n")
    r = run("--root", str(root), "--usage", usage, "--rates", _rates(tmp_path))
    assert r.returncode == 0
    assert "| 2026-01 | 1 | 1.00 |" in r.stdout
    assert "| 2026-02 | 1 | 1.00 |" in r.stdout
    assert "| undated | 1 | 10.50 |" in r.stdout


def test_logged_est_usd_reported_separately(tmp_path):
    root = make_root(tmp_path)
    r = run("--root", str(root), "--rates", _rates(tmp_path))
    assert r.returncode == 0
    assert "0.5000" in r.stdout and "NOT computed by this tool" in r.stdout


def test_malformed_usage_warns_then_strict_fails(tmp_path):
    root = make_root(tmp_path)
    usage = _usage(tmp_path, "model-b,not_a_number,5,r2,2026-01-01\nmodel-b,10,5,r2,2026-01-01\n")
    r = run("--root", str(root), "--usage", usage, "--rates", _rates(tmp_path))
    assert r.returncode == 0 and "malformed" in r.stdout
    r2 = run("--root", str(root), "--usage", usage, "--rates", _rates(tmp_path), "--strict")
    assert r2.returncode == 1


def test_empty_root_no_usage_exits_0(tmp_path):
    (tmp_path / "empty").mkdir()
    r = run("--root", str(tmp_path / "empty"))
    assert r.returncode == 0 and "no usage found" in r.stdout
