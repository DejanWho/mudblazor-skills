#!/usr/bin/env python3
"""Grade all 6 runs of cdk-dotnet-to-terraform iteration-1 against assertions.

Writes grading.json into each run directory with fields:
  { "eval_name", "condition", "passed", "total", "pass_rate", "expectations": [{text, passed, evidence}] }
"""
import json
import re
from pathlib import Path

ROOT = Path("/Users/dejanwho/Projects/Code/mudblazor-skills/skills/cdk-dotnet-to-terraform-workspace/iteration-1")


def read_skill_references(outputs: Path) -> str:
    """Read any .md files under skill-references/ (init-mode artefacts)."""
    parts = []
    refs = outputs / "skill-references"
    if refs.exists():
        for p in sorted(refs.rglob("*")):
            if p.is_file():
                try:
                    parts.append(f"# FILE: {p.relative_to(outputs)}\n{p.read_text(errors='replace')}")
                except Exception:
                    pass
    summary = outputs / "SUMMARY.md"
    if summary.exists():
        try:
            parts.append(f"# FILE: SUMMARY.md\n{summary.read_text(errors='replace')}")
        except Exception:
            pass
    return "\n\n".join(parts)


FIXTURE_MODULES = {"network", "alb", "ecs-service", "iam-role"}
FIXTURE_LIVE = {"reference-service"}


def _read_new_files(outputs: Path, suffixes: set[str]) -> str:
    """Read only *new* files produced under terraform-host — skip fixture modules and reference-service."""
    parts = []
    th = outputs / "terraform-host"
    if not th.exists():
        return ""

    # New modules under modules/
    modules_dir = th / "modules"
    if modules_dir.exists():
        for mod_dir in sorted(modules_dir.iterdir()):
            if mod_dir.is_dir() and mod_dir.name not in FIXTURE_MODULES:
                for p in sorted(mod_dir.rglob("*")):
                    if p.is_file() and p.suffix in suffixes:
                        try:
                            parts.append(f"# FILE: {p.relative_to(outputs)}\n{p.read_text(errors='replace')}")
                        except Exception:
                            pass

    # New live configs under live/<env>/
    live_dir = th / "live"
    if live_dir.exists():
        for env_dir in sorted(live_dir.iterdir()):
            if env_dir.is_dir():
                for app_dir in sorted(env_dir.iterdir()):
                    if app_dir.is_dir() and app_dir.name not in FIXTURE_LIVE:
                        for p in sorted(app_dir.rglob("*")):
                            if p.is_file() and p.suffix in suffixes:
                                try:
                                    parts.append(f"# FILE: {p.relative_to(outputs)}\n{p.read_text(errors='replace')}")
                                except Exception:
                                    pass
    return "\n\n".join(parts)


def read_new_terraform(outputs: Path) -> str:
    """All new .tf + .md files (used for most assertions)."""
    return _read_new_files(outputs, {".tf", ".md"})


def read_new_tf_only(outputs: Path) -> str:
    """Only .tf files — for assertions that must not trip on docs/comments mentioning CDK terms."""
    return _read_new_files(outputs, {".tf"})


def read_conventions_file(outputs: Path) -> str:
    """Just the conventions file, for placeholder-scoped assertions."""
    p = outputs / "skill-references" / "repo-conventions.md"
    if not p.exists():
        return ""
    try:
        return p.read_text(errors="replace")
    except Exception:
        return ""


def read_inventory_file(outputs: Path) -> str:
    p = outputs / "skill-references" / "module-inventory.md"
    if not p.exists():
        return ""
    try:
        return p.read_text(errors="replace")
    except Exception:
        return ""


def read_all_outputs(outputs: Path) -> str:
    """All relevant outputs for grading, concatenated."""
    return "\n\n".join([
        read_skill_references(outputs),
        read_new_terraform(outputs),
    ])


# ----- assertion combinators -----

def has(pattern, flags=0, name=None, scope=None):
    def check(text):
        m = re.search(pattern, text, flags)
        if m:
            ev = m.group(0)
            if len(ev) > 120:
                ev = ev[:120] + "..."
            return True, ev
        return False, f"pattern not found: {pattern[:80]}"
    if scope:
        check._scope = scope
    return check


def missing(pattern, flags=0, scope=None):
    def check(text):
        m = re.search(pattern, text, flags)
        if m:
            return False, f"unwanted pattern found: {m.group(0)[:120]}"
        return True, f"confirmed absent: {pattern[:80]}"
    if scope:
        check._scope = scope
    return check


def all_of(*fns, scope=None):
    def check(text):
        evidences = []
        for fn in fns:
            p, e = fn(text)
            if not p:
                return False, e
            evidences.append(e)
        return True, " | ".join(evidences)[:500]
    if scope:
        check._scope = scope
    return check


def any_of(*fns):
    def check(text):
        evidences = []
        for fn in fns:
            p, e = fn(text)
            if p:
                return True, e
            evidences.append(e)
        return False, "none matched: " + " / ".join(evidences)[:400]
    return check


def min_bytes(n, path_rel):
    """Scoped to files under outputs, check a named file exceeds n bytes."""
    def check_with_outputs(outputs: Path):
        p = outputs / path_rel
        if not p.exists():
            return False, f"file missing: {path_rel}"
        sz = p.stat().st_size
        if sz < n:
            return False, f"{path_rel} is only {sz} bytes (<{n})"
        return True, f"{path_rel} is {sz} bytes"
    check_with_outputs._needs_outputs = True
    return check_with_outputs


def file_exists(path_glob):
    """Check that at least one file matches the glob under outputs."""
    def check_with_outputs(outputs: Path):
        matches = list(outputs.glob(path_glob))
        if matches:
            return True, ", ".join(str(p.relative_to(outputs)) for p in matches[:5])
        return False, f"no match for: {path_glob}"
    check_with_outputs._needs_outputs = True
    return check_with_outputs


# ===== Eval 1: init-mode-learn-conventions =====

EVAL_1 = [
    ("conventions-file-exists",
     "repo-conventions.md file is produced and non-trivial (>800 bytes)",
     min_bytes(800, "skill-references/repo-conventions.md")),
    ("conventions-no-fill-in-placeholders",
     "repo-conventions.md has no unfilled <FILL IN> placeholders remaining",
     missing(r"<\s*FILL\s*IN\s*>", re.IGNORECASE, scope="conventions")),
    ("conventions-documents-module-file-layout",
     "repo-conventions.md mentions the module file layout (main.tf, variables.tf, outputs.tf, versions.tf)",
     all_of(has(r"main\.tf"), has(r"variables\.tf"), has(r"outputs\.tf"), has(r"versions\.tf"))),
    ("conventions-documents-snake-case-variables",
     "repo-conventions.md identifies the snake_case variable convention",
     has(r"snake[_\s-]case", re.IGNORECASE)),
    ("conventions-documents-tagging-pattern",
     "repo-conventions.md documents the tagging pattern (common_tags / default_tags / tags variable)",
     any_of(has(r"common_tags"), has(r"default_tags"), has(r"merge\(.*tags"))),
    ("conventions-documents-backend",
     "repo-conventions.md mentions the S3 backend",
     all_of(has(r"backend", re.IGNORECASE), has(r"s3", re.IGNORECASE))),
    ("conventions-documents-provider-version",
     "repo-conventions.md documents the AWS provider version floor (~> 5.70)",
     has(r"5\.70")),
    ("conventions-documents-region",
     "repo-conventions.md mentions the default region (eu-central-1)",
     has(r"eu-central-1")),
    ("conventions-documents-resource-label-convention",
     "repo-conventions.md identifies the resource label convention (`this`)",
     has(r'"this"|\bthis\b.*resource|resource.*\bthis\b', re.IGNORECASE)),
    ("conventions-documents-per-rule-sg-style",
     "repo-conventions.md mentions the per-resource security group rule style (aws_vpc_security_group_*_rule)",
     has(r"aws_vpc_security_group_(ingress|egress)_rule")),
    ("inventory-file-exists",
     "module-inventory.md file is produced and non-trivial (>400 bytes)",
     min_bytes(400, "skill-references/module-inventory.md")),
    ("inventory-lists-network",
     "module-inventory.md lists the network module",
     has(r"\bnetwork\b")),
    ("inventory-lists-alb",
     "module-inventory.md lists the alb module",
     has(r"\balb\b", re.IGNORECASE)),
    ("inventory-lists-ecs-service",
     "module-inventory.md lists the ecs-service module",
     has(r"ecs-service|ecs_service")),
    ("inventory-lists-iam-role",
     "module-inventory.md lists the iam-role module",
     has(r"iam-role|iam_role")),
    ("inventory-documents-inputs-outputs",
     "module-inventory.md documents Inputs and Outputs (or equivalent) for modules",
     all_of(has(r"[Ii]nputs?:"), has(r"[Oo]utputs?:"))),
]


# ===== Eval 2: convert-greenfield-bedrock-stack =====

EVAL_2 = [
    ("has-new-live-config-dir",
     "A new live config directory was created under terraform-host/live/dev/ (not reference-service)",
     file_exists("terraform-host/live/dev/*/main.tf")),
    ("has-variables-tf",
     "New live config has a variables.tf",
     file_exists("terraform-host/live/dev/*/variables.tf")),
    ("has-versions-tf",
     "New live config has a versions.tf",
     file_exists("terraform-host/live/dev/*/versions.tf")),
    ("calls-network-module",
     "main.tf calls the existing `network` module",
     has(r'module\s+"[^"]*"\s*\{[^}]*source\s*=\s*"[^"]*modules/network"', re.DOTALL)),
    ("calls-alb-module",
     "main.tf calls the existing `alb` module",
     has(r'module\s+"[^"]*"\s*\{[^}]*source\s*=\s*"[^"]*modules/alb"', re.DOTALL)),
    ("calls-ecs-service-module",
     "main.tf calls the existing `ecs-service` module",
     has(r'module\s+"[^"]*"\s*\{[^}]*source\s*=\s*"[^"]*modules/ecs-service"', re.DOTALL)),
    ("has-bedrock-invoke-model",
     "Generated Terraform grants bedrock:InvokeModel",
     has(r'bedrock:InvokeModel(?!With)')),
    ("has-bedrock-invoke-stream",
     "Generated Terraform grants bedrock:InvokeModelWithResponseStream",
     has(r'bedrock:InvokeModelWithResponseStream')),
    ("has-claude-sonnet-arn",
     "Generated Terraform references claude-3-5-sonnet foundation model",
     has(r'anthropic\.claude-3-5-sonnet', re.IGNORECASE)),
    ("has-claude-haiku-arn",
     "Generated Terraform references claude-3-haiku foundation model",
     has(r'anthropic\.claude-3-haiku', re.IGNORECASE)),
    ("has-bedrock-vpc-endpoint",
     "Generated Terraform creates a VPC interface endpoint for bedrock-runtime",
     has(r'com\.amazonaws\.[^"]*bedrock-runtime')),
    ("no-cdk-csharp-syntax-in-tf",
     "No C# / CDK syntax leaked into .tf files (e.g. 'new Vpc(', 'Construct', 'PolicyStatement')",
     all_of(missing(r"\bnew\s+Vpc\s*\("),
            missing(r"\bConstruct\b(?!\w)"),
            missing(r"\bPolicyStatement\b"),
            missing(r"\bAmazon\.CDK"),
            scope="tf_only")),
    ("backend-s3-in-versions-tf",
     "versions.tf includes a backend \"s3\" block matching repo convention",
     has(r'backend\s+"s3"')),
    ("provider-eu-central-1",
     "AWS provider region is eu-central-1 (literal or via variable/locals with the value defined)",
     any_of(has(r'region\s*=\s*"eu-central-1"'),
            all_of(has(r'region\s*=\s*var\.[A-Za-z_]+'),
                   has(r'"eu-central-1"')))),
    ("no-cdk-token-references-left",
     "No CFN Fn:: / Ref:: tokens or raw synth placeholders remain in the generated .tf",
     all_of(missing(r'"Fn::[A-Z][a-zA-Z]+"'),
            missing(r'\{\s*"Ref"\s*:'))),
    ("uses-for-each-or-matches-style",
     "Generated Terraform uses conventions similar to reference service (default_tags or local.common_tags pattern)",
     any_of(has(r"default_tags"), has(r"local\.common_tags"), has(r"locals\s*\{"))),
]


# ===== Eval 3: convert-with-vpc-import =====

EVAL_3 = [
    # Subset of Eval 2 assertions — same output structure still expected
    ("has-new-live-config-dir",
     "A new live config directory was created under terraform-host/live/dev/",
     file_exists("terraform-host/live/dev/*/main.tf")),
    ("calls-network-module",
     "main.tf calls the existing `network` module (not raw VPC resources)",
     has(r'module\s+"[^"]*"\s*\{[^}]*source\s*=\s*"[^"]*modules/network"', re.DOTALL)),
    ("calls-alb-module",
     "main.tf calls the existing `alb` module",
     has(r'module\s+"[^"]*"\s*\{[^}]*source\s*=\s*"[^"]*modules/alb"', re.DOTALL)),
    ("calls-ecs-service-module",
     "main.tf calls the existing `ecs-service` module",
     has(r'module\s+"[^"]*"\s*\{[^}]*source\s*=\s*"[^"]*modules/ecs-service"', re.DOTALL)),
    ("has-bedrock-invoke-model",
     "Generated Terraform grants bedrock:InvokeModel",
     has(r'bedrock:InvokeModel(?!With)')),
    ("has-bedrock-invoke-stream",
     "Generated Terraform grants bedrock:InvokeModelWithResponseStream",
     has(r'bedrock:InvokeModelWithResponseStream')),
    ("has-bedrock-vpc-endpoint",
     "Generated Terraform creates a VPC interface endpoint for bedrock-runtime",
     has(r'com\.amazonaws\.[^"]*bedrock-runtime')),
    # Import-specific
    ("has-imports-tf",
     "An imports.tf file was created in the new live config directory",
     file_exists("terraform-host/live/dev/*/imports.tf")),
    ("has-vpc-import-block",
     "imports.tf contains an import block adopting the deployed VPC",
     all_of(has(r"^\s*import\s*\{", re.MULTILINE),
            has(r'vpc-0a1b2c3d4e5f6a7b8'))),
    ("import-to-addresses-vpc",
     "The VPC import block's `to` address references a VPC resource (module or raw)",
     has(r'to\s*=\s*(?:module\.[^\s,]+aws_vpc\.[^\s]+|aws_vpc\.[^\s]+)', re.DOTALL)),
    ("no-duplicate-vpc-resource",
     "No raw `resource \"aws_vpc\" \"...\"` in the live config alongside the module (would conflict with import into module)",
     missing(r'^\s*resource\s+"aws_vpc"\s+"', re.MULTILINE)),
    ("no-cdk-csharp-syntax-in-tf",
     "No C# / CDK syntax leaked into .tf files",
     all_of(missing(r"\bnew\s+Vpc\s*\("),
            missing(r"\bConstruct\b(?!\w)"),
            missing(r"\bPolicyStatement\b"),
            missing(r"\bAmazon\.CDK"),
            scope="tf_only")),
]


RUNS = [
    ("eval-1-init-mode-learn-conventions", EVAL_1),
    ("eval-2-convert-greenfield-bedrock-stack", EVAL_2),
    ("eval-3-convert-with-vpc-import", EVAL_3),
]


def grade(eval_name: str, condition: str, assertions: list):
    run_dir = ROOT / eval_name / condition
    outputs = run_dir / "outputs"
    default_text = read_all_outputs(outputs)
    scoped_texts = {
        "tf_only": read_new_tf_only(outputs),
        "conventions": read_conventions_file(outputs),
        "inventory": read_inventory_file(outputs),
    }
    expectations = []
    passed_count = 0
    for aid, atext, check in assertions:
        try:
            if getattr(check, "_needs_outputs", False):
                p, evidence = check(outputs)
            else:
                scope = getattr(check, "_scope", None)
                text = scoped_texts.get(scope, default_text) if scope else default_text
                p, evidence = check(text)
        except Exception as e:
            p, evidence = False, f"grader error: {e}"
        expectations.append({
            "id": aid,
            "text": atext,
            "passed": bool(p),
            "evidence": str(evidence)[:500],
        })
        if p:
            passed_count += 1
    result = {
        "eval_name": eval_name,
        "condition": condition,
        "passed": passed_count,
        "total": len(assertions),
        "pass_rate": passed_count / len(assertions) if assertions else 0,
        "expectations": expectations,
    }
    grading_path = run_dir / "grading.json"
    grading_path.write_text(json.dumps(result, indent=2))
    return result


def main():
    summary = []
    for eval_name, assertions in RUNS:
        for condition in ["with_skill", "without_skill"]:
            run_dir = ROOT / eval_name / condition
            outputs = run_dir / "outputs"
            if not outputs.exists():
                print(f"  [skip] {eval_name}/{condition} — outputs/ missing (subagent may not be done yet)")
                continue
            r = grade(eval_name, condition, assertions)
            print(f"  {eval_name}/{condition}: {r['passed']}/{r['total']} ({r['pass_rate']*100:.0f}%)")
            summary.append(r)
    # Quick side-by-side
    print("\n=== Summary ===")
    print(f"{'eval':<45} {'with_skill':>12} {'baseline':>12}  delta")
    by_eval = {}
    for r in summary:
        by_eval.setdefault(r['eval_name'], {})[r['condition']] = r
    for name, cases in sorted(by_eval.items()):
        ws = cases.get('with_skill')
        wo = cases.get('without_skill')
        if ws and wo:
            delta = (ws['pass_rate'] - wo['pass_rate']) * 100
            print(f"{name:<45} {ws['passed']:>3}/{ws['total']:<8} {wo['passed']:>3}/{wo['total']:<8}  {delta:+.0f} pts")


if __name__ == "__main__":
    main()
