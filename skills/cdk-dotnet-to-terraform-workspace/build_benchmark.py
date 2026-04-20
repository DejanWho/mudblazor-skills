#!/usr/bin/env python3
"""Build benchmark.json in the format the skill-creator eval viewer expects."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/dejanwho/Projects/Code/mudblazor-skills/skills/cdk-dotnet-to-terraform-workspace/iteration-1")

EVALS = [
    (1, "init-mode-learn-conventions", "eval-1-init-mode-learn-conventions"),
    (2, "convert-greenfield-bedrock-stack", "eval-2-convert-greenfield-bedrock-stack"),
    (3, "convert-with-vpc-import", "eval-3-convert-with-vpc-import"),
]


def _stats(values):
    if not values:
        return {"mean": 0, "stddev": 0, "min": 0, "max": 0}
    n = len(values)
    mean = sum(values) / n
    stddev = math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1)) if n > 1 else 0.0
    return {"mean": round(mean, 4), "stddev": round(stddev, 4), "min": round(min(values), 4), "max": round(max(values), 4)}


def main():
    runs = []
    for eval_id, eval_name, dir_name in EVALS:
        eval_dir = ROOT / dir_name
        for config in ["with_skill", "without_skill"]:
            grading_path = eval_dir / config / "grading.json"
            timing_path = eval_dir / config / "timing.json"
            if not grading_path.exists():
                continue
            g = json.loads(grading_path.read_text())
            t = {}
            if timing_path.exists():
                t = json.loads(timing_path.read_text())
            runs.append({
                "eval_id": eval_id,
                "eval_name": eval_name,
                "configuration": config,
                "run_number": 1,
                "result": {
                    "pass_rate": g["pass_rate"],
                    "passed": g["passed"],
                    "failed": g["total"] - g["passed"],
                    "total": g["total"],
                    "time_seconds": t.get("total_duration_seconds", 0.0),
                    "tokens": t.get("total_tokens", 0),
                    "tool_calls": 0,
                    "errors": 0,
                },
                "expectations": g["expectations"],
                "notes": [],
            })

    # Sort so with_skill appears before without_skill per eval (viewer pairs them visually)
    def _key(r):
        return (r["eval_id"], 0 if r["configuration"] == "with_skill" else 1)
    runs.sort(key=_key)

    # Per-config aggregates
    by_config = {}
    for r in runs:
        by_config.setdefault(r["configuration"], []).append(r)

    def _agg(rs):
        return {
            "pass_rate": _stats([x["result"]["pass_rate"] for x in rs]),
            "time_seconds": _stats([x["result"]["time_seconds"] for x in rs]),
            "tokens": _stats([x["result"]["tokens"] for x in rs]),
        }

    summary = {}
    if "with_skill" in by_config:
        summary["with_skill"] = _agg(by_config["with_skill"])
    if "without_skill" in by_config:
        summary["without_skill"] = _agg(by_config["without_skill"])

    if "with_skill" in summary and "without_skill" in summary:
        ws = summary["with_skill"]
        wo = summary["without_skill"]
        summary["delta"] = {
            "pass_rate": f"{(ws['pass_rate']['mean'] - wo['pass_rate']['mean']):+.4f}",
            "time_seconds": f"{(ws['time_seconds']['mean'] - wo['time_seconds']['mean']):+.1f}",
            "tokens": f"{int(ws['tokens']['mean'] - wo['tokens']['mean']):+d}",
        }

    # Analyst notes
    notes = []
    # Non-differentiating assertions (pass in both configs everywhere)
    ws_runs = by_config.get("with_skill", [])
    wo_runs = by_config.get("without_skill", [])
    by_eval = {}
    for r in ws_runs + wo_runs:
        by_eval.setdefault(r["eval_id"], {})[r["configuration"]] = r
    for eid, configs in by_eval.items():
        ws = configs.get("with_skill")
        wo = configs.get("without_skill")
        if not (ws and wo):
            continue
        both_pass_always = []
        for ws_exp, wo_exp in zip(ws["expectations"], wo["expectations"]):
            if ws_exp["passed"] and wo_exp["passed"]:
                both_pass_always.append(ws_exp["text"][:80])
        only_ws_wins = []
        only_wo_wins = []
        for ws_exp, wo_exp in zip(ws["expectations"], wo["expectations"]):
            if ws_exp["passed"] and not wo_exp["passed"]:
                only_ws_wins.append(ws_exp["text"][:80])
            elif wo_exp["passed"] and not ws_exp["passed"]:
                only_wo_wins.append(ws_exp["text"][:80])
        if only_ws_wins:
            notes.append(f"Eval {eid}: with_skill wins on {len(only_ws_wins)} assertion(s): {', '.join(only_ws_wins[:3])}")
        if only_wo_wins:
            notes.append(f"Eval {eid}: baseline wins on {len(only_wo_wins)} assertion(s) — worth investigating: {', '.join(only_wo_wins[:3])}")

    # Time/token comparison
    if "delta" in summary:
        ws_t = summary["with_skill"]["time_seconds"]["mean"]
        wo_t = summary["without_skill"]["time_seconds"]["mean"]
        notes.append(f"Time: with_skill avg {ws_t:.1f}s vs baseline avg {wo_t:.1f}s (Δ {ws_t - wo_t:+.1f}s).")
        ws_k = summary["with_skill"]["tokens"]["mean"]
        wo_k = summary["without_skill"]["tokens"]["mean"]
        notes.append(f"Tokens: with_skill avg {ws_k:.0f} vs baseline avg {wo_k:.0f} (Δ {int(ws_k - wo_k):+d}).")

    benchmark = {
        "metadata": {
            "skill_name": "cdk-dotnet-to-terraform",
            "skill_path": "/Users/dejanwho/Projects/Code/mudblazor-skills/skills/cdk-dotnet-to-terraform",
            "executor_model": "claude-opus-4-7",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "evals_run": [eid for eid, *_ in EVALS],
            "runs_per_configuration": 1,
        },
        "runs": runs,
        "run_summary": summary,
        "notes": notes,
    }

    out = ROOT / "benchmark.json"
    out.write_text(json.dumps(benchmark, indent=2))
    print(f"Wrote {out}")

    # Also a short markdown summary
    md_lines = [
        "# Benchmark: cdk-dotnet-to-terraform (iteration 1)",
        "",
        f"Generated: {benchmark['metadata']['timestamp']}",
        "",
        "## Per-eval pass rates",
        "",
        "| Eval | with_skill | baseline | Δ |",
        "|---|---|---|---|",
    ]
    for eid, ename, _ in EVALS:
        ws = by_eval[eid].get("with_skill", {}).get("result", {})
        wo = by_eval[eid].get("without_skill", {}).get("result", {})
        delta_pts = (ws.get("pass_rate", 0) - wo.get("pass_rate", 0)) * 100
        md_lines.append(f"| {ename} | {ws.get('passed',0)}/{ws.get('total',0)} ({ws.get('pass_rate',0)*100:.0f}%) | {wo.get('passed',0)}/{wo.get('total',0)} ({wo.get('pass_rate',0)*100:.0f}%) | {delta_pts:+.0f} pts |")
    md_lines.append("")
    md_lines.append("## Aggregate")
    md_lines.append("")
    md_lines.append("| Metric | with_skill | baseline | Δ |")
    md_lines.append("|---|---|---|---|")
    if "delta" in summary:
        md_lines.append(f"| Pass rate | {summary['with_skill']['pass_rate']['mean']*100:.1f}% | {summary['without_skill']['pass_rate']['mean']*100:.1f}% | {summary['delta']['pass_rate']} |")
        md_lines.append(f"| Time (s) | {summary['with_skill']['time_seconds']['mean']:.0f} | {summary['without_skill']['time_seconds']['mean']:.0f} | {summary['delta']['time_seconds']} |")
        md_lines.append(f"| Tokens | {summary['with_skill']['tokens']['mean']:.0f} | {summary['without_skill']['tokens']['mean']:.0f} | {summary['delta']['tokens']} |")
    md_lines.append("")
    md_lines.append("## Notes")
    for n in notes:
        md_lines.append(f"- {n}")
    (ROOT / "benchmark.md").write_text("\n".join(md_lines))
    print(f"Wrote {ROOT / 'benchmark.md'}")


if __name__ == "__main__":
    main()
