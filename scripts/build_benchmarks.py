#!/usr/bin/env python3
"""Build benchmark.json and benchmark.md for each workspace, and fix grading.json format."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, stdev

ROOT = Path("/Users/dejanwho/Projects/Code/mudblazor-skills/skills")


def fix_grading_json(run_dir: Path, eval_name: str, condition: str):
    """Wrap existing grading.json data under 'summary' key as the schema expects."""
    p = run_dir / "grading.json"
    if not p.exists():
        return None
    data = json.loads(p.read_text())
    # If already has 'summary', leave it alone
    if "summary" not in data:
        fixed = {
            "summary": {
                "passed": data["passed"],
                "failed": data["total"] - data["passed"],
                "total": data["total"],
                "pass_rate": data["pass_rate"],
            },
            "expectations": data["expectations"],
        }
        p.write_text(json.dumps(fixed, indent=2))
        data = fixed
    return data


def load_timing(run_dir: Path) -> dict:
    p = run_dir / "timing.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def calc_stats(values):
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}
    m = mean(values)
    s = stdev(values) if len(values) > 1 else 0.0
    return {
        "mean": round(m, 4),
        "stddev": round(s, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


def build_benchmark(workspace_name: str, skill_name: str, eval_specs: list):
    """eval_specs = [(eval_id, eval_name), ...]"""
    iteration_dir = ROOT / workspace_name / "iteration-1"
    runs = []

    for eval_id, eval_name in eval_specs:
        for condition in ["with_skill", "without_skill"]:
            run_dir = iteration_dir / eval_name / condition
            grading = fix_grading_json(run_dir, eval_name, condition)
            if grading is None:
                continue
            timing = load_timing(run_dir)
            summary = grading["summary"]
            run = {
                "eval_id": eval_id,
                "eval_name": eval_name,
                "configuration": condition,
                "run_number": 1,
                "result": {
                    "pass_rate": summary["pass_rate"],
                    "passed": summary["passed"],
                    "failed": summary["failed"],
                    "total": summary["total"],
                    "time_seconds": timing.get("total_duration_seconds", 0),
                    "tokens": timing.get("total_tokens", 0),
                    "tool_calls": timing.get("tool_uses", 0),
                    "errors": 0,
                },
                "expectations": grading["expectations"],
                "notes": [],
            }
            runs.append(run)

    # Aggregate by configuration
    run_summary = {}
    for condition in ["with_skill", "without_skill"]:
        relevant = [r for r in runs if r["configuration"] == condition]
        if not relevant:
            continue
        run_summary[condition] = {
            "pass_rate": calc_stats([r["result"]["pass_rate"] for r in relevant]),
            "time_seconds": calc_stats([r["result"]["time_seconds"] for r in relevant]),
            "tokens": calc_stats([r["result"]["tokens"] for r in relevant]),
        }

    # Delta (with_skill - without_skill)
    if "with_skill" in run_summary and "without_skill" in run_summary:
        d_pr = run_summary["with_skill"]["pass_rate"]["mean"] - run_summary["without_skill"]["pass_rate"]["mean"]
        d_t = run_summary["with_skill"]["time_seconds"]["mean"] - run_summary["without_skill"]["time_seconds"]["mean"]
        d_tok = run_summary["with_skill"]["tokens"]["mean"] - run_summary["without_skill"]["tokens"]["mean"]
        run_summary["delta"] = {
            "pass_rate": f"{d_pr:+.2f}",
            "time_seconds": f"{d_t:+.1f}",
            "tokens": f"{d_tok:+.0f}",
        }

    benchmark = {
        "metadata": {
            "skill_name": skill_name,
            "skill_path": str(ROOT / skill_name),
            "executor_model": "claude-opus-4-6",
            "analyzer_model": "claude-opus-4-6",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": [spec[0] for spec in eval_specs],
            "runs_per_configuration": 1,
        },
        "runs": runs,
        "run_summary": run_summary,
        "notes": [],
    }

    return benchmark


def generate_markdown(benchmark: dict) -> str:
    m = benchmark["metadata"]
    s = benchmark["run_summary"]
    lines = [
        f"# Skill Benchmark: {m['skill_name']}",
        "",
        f"**Model**: {m['executor_model']}",
        f"**Date**: {m['timestamp']}",
        f"**Evals**: {', '.join(map(str, m['evals_run']))} ({m['runs_per_configuration']} runs each per configuration)",
        "",
        "## Summary",
        "",
        "| Metric | With Skill | Without Skill | Delta |",
        "|--------|------------|---------------|-------|",
    ]
    ws = s.get("with_skill", {})
    wos = s.get("without_skill", {})
    d = s.get("delta", {})

    def fmt_pct(x):
        return f"{x.get('mean', 0)*100:.0f}% ± {x.get('stddev', 0)*100:.0f}%"

    def fmt_s(x):
        return f"{x.get('mean', 0):.1f}s ± {x.get('stddev', 0):.1f}s"

    def fmt_tok(x):
        return f"{x.get('mean', 0):.0f} ± {x.get('stddev', 0):.0f}"

    lines.append(f"| Pass Rate | {fmt_pct(ws.get('pass_rate', {}))} | {fmt_pct(wos.get('pass_rate', {}))} | {d.get('pass_rate', '—')} |")
    lines.append(f"| Time | {fmt_s(ws.get('time_seconds', {}))} | {fmt_s(wos.get('time_seconds', {}))} | {d.get('time_seconds', '—')}s |")
    lines.append(f"| Tokens | {fmt_tok(ws.get('tokens', {}))} | {fmt_tok(wos.get('tokens', {}))} | {d.get('tokens', '—')} |")
    lines.append("")
    lines.append("## Per-eval breakdown")
    lines.append("")
    lines.append("| Eval | With Skill | Without Skill |")
    lines.append("|------|------------|---------------|")
    eval_groups = {}
    for r in benchmark["runs"]:
        eval_groups.setdefault(r["eval_name"], {})[r["configuration"]] = r["result"]
    for ename, configs in eval_groups.items():
        ws_res = configs.get("with_skill", {})
        wos_res = configs.get("without_skill", {})
        ws_str = f"{ws_res.get('passed', 0)}/{ws_res.get('total', 0)} ({ws_res.get('pass_rate', 0)*100:.0f}%)"
        wos_str = f"{wos_res.get('passed', 0)}/{wos_res.get('total', 0)} ({wos_res.get('pass_rate', 0)*100:.0f}%)"
        lines.append(f"| {ename} | {ws_str} | {wos_str} |")
    return "\n".join(lines)


def main():
    workspaces = [
        ("mudblazor-migration-8-to-9-workspace", "mudblazor-migration-8-to-9", [
            (1, "eval-1-mudchart-v9-migration"),
            (2, "eval-2-dialog-async-and-menu-context"),
            (3, "eval-3-custom-form-component-converter"),
        ]),
        ("mudblazor-9-workspace", "mudblazor-9", [
            (1, "eval-1-orders-page-with-server-datagrid"),
            (2, "eval-2-create-product-form-with-validation"),
            (3, "eval-3-custom-theme-with-dark-mode-toggle"),
        ]),
    ]

    for workspace, skill_name, specs in workspaces:
        benchmark = build_benchmark(workspace, skill_name, specs)
        iteration_dir = ROOT / workspace / "iteration-1"
        (iteration_dir / "benchmark.json").write_text(json.dumps(benchmark, indent=2))
        (iteration_dir / "benchmark.md").write_text(generate_markdown(benchmark))
        print(f"Generated {iteration_dir / 'benchmark.json'}")

        # Print summary
        s = benchmark["run_summary"]
        ws_pr = s.get("with_skill", {}).get("pass_rate", {}).get("mean", 0) * 100
        wos_pr = s.get("without_skill", {}).get("pass_rate", {}).get("mean", 0) * 100
        print(f"  with_skill:    {ws_pr:.1f}% pass rate")
        print(f"  without_skill: {wos_pr:.1f}% pass rate")
        print(f"  delta:         {s.get('delta', {}).get('pass_rate', '?')}")
        print()


if __name__ == "__main__":
    main()
