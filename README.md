# mudblazor-skills

A collection of Claude agent skills — plus matching GitHub Copilot custom agents where applicable — for common developer workflows. The repo originally shipped a pair of MudBlazor 9 skills, hence the name; it now covers other workflows too (AWS CDK → Terraform conversion). The build + benchmark tooling under `scripts/` is shared across all of them.

## Skills in this repo

| Skill | What it does | Copilot agent? |
|---|---|---|
| **`mudblazor-migration-8-to-9`** | Migrate a Blazor Server project from MudBlazor 8.x to 9.x. Bumps the package, applies every breaking change (converters, async dialog/menu APIs, MudChart/MudChat/MudFileUpload/MudTreeView rewrites, removed `MudGlobal` properties, popover modal default flip, `ServerData` cancellation token, dark-mode API rename, and more), verifies the build, and surfaces runtime caveats. | Yes |
| **`mudblazor-9`** | Build new Blazor Server UI with MudBlazor 9.x. Knows installation, layout, forms (`EditForm` + DataAnnotations and `MudForm` + FluentValidation), dialogs, snackbars, `MudDataGrid` (including server-side data with cancellation), and theming with dark mode. | Yes |
| **`cdk-dotnet-to-terraform`** | Convert AWS CDK projects written in C# / .NET 8 into Terraform that fits a host repo's existing modules and conventions. Self-bootstrapping: a first-run "init" step walks the host repo to learn where modules live, how they're shaped, and what conventions the team follows, persisting that into its own reference files so later conversions stay consistent. Handles greenfield conversion and `import` blocks for already-deployed resources (Terraform ≥ 1.5). Pipeline-agnostic: produces `.tf` that `terraform fmt` accepts locally; `init` / `validate` / `plan` happen in the user's CI. | No — Claude Code / Agent SDK only |

The Copilot agent files (`.github/agents/*.agent.md`) are self-contained and inline everything needed. The Claude Code skills live under `skills/` with a `SKILL.md` entry point plus deeper reference files under `references/`.

---

## Repository layout

```
mudblazor-skills/
├── README.md                                         ← you are here
├── .github/
│   └── agents/                                       ← GitHub Copilot custom agents
│       ├── README.md                                 ←   install + usage for Copilot
│       ├── mudblazor-migrate-v8-to-v9.agent.md
│       └── mudblazor-9.agent.md
├── skills/                                           ← Agent SDK / Claude Code skills
│   ├── mudblazor-migration-8-to-9/
│   │   ├── SKILL.md
│   │   ├── references/breaking-changes.md
│   │   └── evals/
│   │       ├── evals.json
│   │       └── fixtures/
│   ├── mudblazor-migration-8-to-9-workspace/
│   │   └── iteration-1/                              ← eval results, benchmark, review viewer
│   ├── mudblazor-9/
│   │   ├── SKILL.md
│   │   ├── references/{setup,components,forms,data-grid,theming}.md
│   │   └── evals/evals.json
│   ├── mudblazor-9-workspace/
│   │   └── iteration-1/
│   ├── cdk-dotnet-to-terraform/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── init-walkthrough.md                   ← how the init phase learns a repo's conventions
│   │   │   ├── construct-mapping.md                  ← CDK → Terraform resource cheat sheet
│   │   │   ├── bedrock-patterns.md                   ← Bedrock / Anthropic-on-AWS specifics
│   │   │   ├── cdk-synth-harness.md                  ← running & parsing `cdk synth` for .NET CDK
│   │   │   ├── import-blocks.md                      ← Terraform 1.5 `import` syntax + drift handling
│   │   │   ├── repo-conventions.md.template          ← populated per host repo during init
│   │   │   └── module-inventory.md.template          ← populated per host repo during init
│   │   └── evals/
│   │       ├── evals.json
│   │       └── fixtures/fixture-alb-fargate-bedrock/ ← mock host TF repo + CDK .NET 8 project + pre-computed `cdk.out/`
│   └── cdk-dotnet-to-terraform-workspace/
│       └── iteration-1/
└── scripts/                                          ← grading + benchmarking utilities
    ├── grade_runs.py
    └── build_benchmarks.py
```

---

## Using the skills

### With GitHub Copilot (VS Code)

Self-contained `.agent.md` files under `.github/agents/` (MudBlazor skills only). Drop them into any project's `.github/agents/` directory (or `~/.copilot/agents/` for global install), reload VS Code, and pick the agent from Copilot Chat's agents dropdown.

See [`.github/agents/README.md`](.github/agents/README.md) for install steps, example prompts, and compatibility notes.

The Copilot agents are **self-contained** — they don't need the `skills/` directory to be present in the workspace. All essential knowledge is inlined.

### With Claude Code / Agent SDK

Each skill under `skills/` has:

- `SKILL.md` — the entry point with YAML frontmatter (name + description) and a workflow body
- `references/*.md` — deeper reference files the skill instructs the agent to read on demand
- `evals/evals.json` — realistic test prompts with assertions
- `evals/fixtures/` (where applicable) — input files the evals run against

Point Claude Code at the skill directory:

```bash
claude -p "Convert our CDK app to Terraform" \
  --skill ./skills/cdk-dotnet-to-terraform
```

Or install it into your project's `.claude/skills/` directory.

To package a skill as a distributable `.skill` file:

```bash
python3 -m scripts.package_skill ./skills/<skill-name>
```

(Uses the packaging script from the [`anthropic-skills/skill-creator`](https://github.com/anthropics/skills) plugin.)

---

## Skill overviews

### `mudblazor-migration-8-to-9`

Source → target: Blazor Server with MudBlazor **8.x → 9.x**.

Two things make this migration unusually tricky: the compiler misses some changes (popover modal default flip, dialog focus behaviour, snackbar auto-dismiss), and the converter system rewrite cascades through any custom component deriving from `MudFormComponent<T, U>`. The skill walks the breaking changes in order, uses `Grep` to find all call sites per category, and flags runtime caveats after the build goes green.

Breaking-change categories covered: converter rewrite, async API renames (`Show` → `ShowAsync`, etc.), `MudFormComponent` method renames, `MudSelect` / `MudMenu` / `MudFileUpload` / `MudChart` / `MudChat` / `MudTreeView` / `MudDataGrid.ServerData` / `MudStepper` / `MudTabs` / `MudSnackbar` / `MudThemeProvider` changes, `Range<T>` / `DateRange` init-only, `CssBuilder` / `StyleBuilder` readonly struct, dialog focus options. Full list in [`skills/mudblazor-migration-8-to-9/references/breaking-changes.md`](skills/mudblazor-migration-8-to-9/references/breaking-changes.md).

### `mudblazor-9`

Build new MudBlazor 9 UI from scratch. Covers: setup (NuGet + `Program.cs` + provider ordering), layout (`MudAppBar`, `MudDrawer`, typography, icons), forms (both `EditForm` + DataAnnotations and `MudForm` + FluentValidation patterns), dialogs and snackbars with the v9 async APIs, `MudDataGrid` with server-side data and cancellation tokens, and theming with OS-follow dark mode.

### `cdk-dotnet-to-terraform`

Convert AWS CDK C# / .NET 8 projects into Terraform that fits a host repo's existing style, modules, and conventions. The skill has two modes:

- **Init** — walks the host Terraform repo on first use (or on-demand) to learn where modules live, how they're shaped, and what conventions the team follows. Persists findings into its own reference files (`repo-conventions.md`, `module-inventory.md`) so later conversions stay consistent. Re-runnable when the repo's style changes.
- **Convert** — given a CDK .NET 8 project, translates it into Terraform that honors the learned conventions. Reuses existing repo modules where they fit; authors new modules in the same style when a construct has no match; falls back to raw resources for one-offs. Handles both greenfield deployment and `import` blocks (Terraform ≥ 1.5) for resources already deployed.

Designed around common real-world constraints: pipeline-agnostic (local environment only runs `terraform fmt`; `init` / `validate` / `plan` happen in CI), doesn't require live `cdk synth` access (reads a pre-existing `cdk.out/` as a fallback), surfaces judgment calls (CDK Pipelines, `AwsCustomResource`, cross-region patterns) as explicit `TODO:` markers rather than faking them.

The skill ships "template" conventions/inventory files; the init phase writes real per-host versions of each alongside. Commit those generated files so future Claude sessions and team reviewers share the same understanding of your repo.

Includes reference material for: generic CDK → Terraform construct mapping, AWS Bedrock / Anthropic-on-AWS patterns (IAM for `bedrock:InvokeModel`, VPC endpoints, agents / knowledge bases / guardrails), `cdk synth` harness (how to run it for .NET CDK, parse the output, map CFN logical IDs back to construct paths), and `import` block syntax + drift handling.

---

## How the skills were built and tested

All skills were built with the `skill-creator` workflow:

1. Researched the source-of-truth docs for the target area (MudBlazor migration guides, AWS CDK API reference, Terraform AWS provider docs).
2. Drafted `SKILL.md` + reference files organized by topic.
3. Wrote 2–3 realistic test cases per skill (`skills/<skill>/evals/evals.json`) covering the hardest scenarios, with input fixtures where needed.
4. Ran each test case twice — once with the skill loaded, once as a baseline with no skill — using independent subagents.
5. Graded each run against per-assertion checks and aggregated into `benchmark.json` + `benchmark.md` per skill.

### Benchmark results (iteration 1)

| Skill | With skill | Baseline | Delta |
|---|---|---|---|
| `mudblazor-migration-8-to-9` | **100% (21/21)** | 58.5% (12/21) | **+41.5 pts** |
| `mudblazor-9` | **100% (37/37)** | 91.0% (34/37) | **+9.0 pts** |
| `cdk-dotnet-to-terraform` | **97.9% (43/44)** | 92.4% (41/44) | **+5.6 pts** |

Why the deltas vary:

- **`mudblazor-migration-8-to-9` — largest delta.** MudBlazor 9 changed enough API surface that LLMs commonly "remember" the v8 API and confidently write code that no longer compiles (kept `XAxisLabels`, `MudTimeSeriesChart`, synchronous `ShowMessageBox`, `GetSystemPreference`, `SetValueAsync`). The skill catches all of these.
- **`mudblazor-9` — moderate delta.** General patterns like `EditForm` + DataAnnotations are stable across MudBlazor versions; the skill's wins concentrate where v9 differs subtly from prior knowledge (`ServerData` cancellation token, `GetSystemDarkModeAsync`, `IMudDialogInstance`, provider ordering).
- **`cdk-dotnet-to-terraform` — smaller aggregate delta, but concentrated on the hard case.** On the straightforward greenfield convert, raw Opus 4.7 is already competent (both runs hit 100%). The skill's lead shows up on the harder VPC-import scenario (+17 pts), where the baseline produced a duplicate `network` module to route the import, while the skill imported directly into `module.network.aws_vpc.this` — cleaner state, no drift.

### Review the eval results

Each workspace has per-run output files, a graded `benchmark.json`, and a standalone `review.html` you can open in a browser:

```bash
open skills/mudblazor-migration-8-to-9-workspace/iteration-1/review.html
open skills/mudblazor-9-workspace/iteration-1/review.html
open skills/cdk-dotnet-to-terraform-workspace/iteration-1/review.html
```

Or start a live server with feedback save (skill-creator's `generate_review.py`):

```bash
python3 <path-to-skill-creator>/eval-viewer/generate_review.py \
  skills/cdk-dotnet-to-terraform-workspace/iteration-1 \
  --skill-name cdk-dotnet-to-terraform \
  --benchmark skills/cdk-dotnet-to-terraform-workspace/iteration-1/benchmark.json \
  --port 3117
```

---

## Rebuilding benchmarks

If you re-run evals (or fix a skill and want to measure again):

```bash
# MudBlazor skills use the shared shell scripts at scripts/
python3 scripts/grade_runs.py
python3 scripts/build_benchmarks.py

# cdk-dotnet-to-terraform has its own graders in its workspace
python3 skills/cdk-dotnet-to-terraform-workspace/grade_runs.py
python3 skills/cdk-dotnet-to-terraform-workspace/build_benchmark.py
```

The shared scripts under `scripts/` reference the skills directory via an absolute path at the top — edit `ROOT` if you move the repo.

---

## Per-skill notes

### MudBlazor

- Target: **MudBlazor 9.3.0** (latest stable at build time)
- Supports **.NET 8, 9, and 10**
- Project type assumed: **Blazor Server** (the skills call this out in their frontmatter)

The MudBlazor skills reference v9.3.0 specifically but should work for any 9.x version — the breaking changes listed are from 9.0.0 and haven't been reverted since.

### CDK → Terraform

- CDK language: **C# / .NET 8** (Amazon.CDK.Lib 2.x). Other CDK languages (TypeScript, Python, Java, Go) are not in scope — their idioms differ enough that the skill's heuristics wouldn't generalize.
- Terraform version floor: **1.5+** (needed for `import` blocks).
- AWS provider floor: **~> 5.70** (for Bedrock resource coverage).
- Local env: the skill assumes `terraform init` / `validate` / `plan` may not run locally (common in air-gapped dev environments) and stops at `terraform fmt`. Full validation is expected to happen in the team's CI pipeline (the skill is pipeline-agnostic).
- Out of scope (surfaced as explicit `TODO:` markers rather than silently faked): CDK Pipelines, CDK Aspects, `AwsCustomResource` / Lambda-backed custom resources, `CfnInclude`, cross-region replication patterns, L3 constructs that do work at deploy time (e.g. `BucketDeployment`).

## Sources

**MudBlazor skills:**
- [MudBlazor v9.0.0 Migration Guide · Issue #12666](https://github.com/MudBlazor/MudBlazor/issues/12666)
- [MudBlazor docs](https://mudblazor.com)
- [MudBlazor GitHub](https://github.com/MudBlazor/MudBlazor)
- [MudBlazor NuGet](https://www.nuget.org/packages/MudBlazor)

**CDK → Terraform skill:**
- [AWS CDK v2 API reference (.NET)](https://docs.aws.amazon.com/cdk/api/v2/dotnet/api/index.html)
- [Terraform AWS Provider docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform `import` blocks (v1.5)](https://developer.hashicorp.com/terraform/language/import)
- [Amazon Bedrock user guide](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)
