# mudblazor-skills

A pair of agent skills and matching GitHub Copilot custom agents for working with **MudBlazor 9** in Blazor Server projects.

| Skill | What it does |
|---|---|
| **`mudblazor-migration-8-to-9`** | Migrate a Blazor Server project from MudBlazor 8.x to 9.x. Bumps the package, applies every breaking change (converters, async dialog/menu APIs, MudChart/MudChat/MudFileUpload/MudTreeView rewrites, removed `MudGlobal` properties, popover modal default flip, `ServerData` cancellation token, dark-mode API rename, and more), verifies the build, and surfaces runtime caveats. |
| **`mudblazor-9`** | Build new Blazor Server UI with MudBlazor 9.x. Knows installation, layout, forms (`EditForm` + DataAnnotations and `MudForm` + FluentValidation), dialogs, snackbars, `MudDataGrid` (including server-side data with cancellation), and theming with dark mode. |

Both are available in two forms so you can use them with either Claude Code (as Agent SDK skills) or GitHub Copilot in VS Code (as custom agents).

---

## Repository layout

```
mudblazor-skills/
├── README.md                          ← you are here
├── .github/
│   └── agents/                        ← GitHub Copilot custom agents
│       ├── README.md                  ←   install + usage for Copilot
│       ├── mudblazor-migrate-v8-to-v9.agent.md
│       └── mudblazor-9.agent.md
├── skills/                            ← Agent SDK skills
│   ├── mudblazor-migration-8-to-9/
│   │   ├── SKILL.md                   ← the skill workflow
│   │   ├── references/
│   │   │   └── breaking-changes.md    ← full v8→v9 breaking change reference
│   │   └── evals/                     ← test cases + input fixtures
│   │       ├── evals.json
│   │       └── fixtures/
│   │           ├── eval-1-chart/Dashboard.razor
│   │           ├── eval-2-dialog-and-async/UserList.razor
│   │           └── eval-3-custom-form-component/TagsInput.razor.cs
│   ├── mudblazor-migration-8-to-9-workspace/
│   │   └── iteration-1/               ← eval results, benchmark, review viewer
│   ├── mudblazor-9/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── setup.md               ← install, Program.cs, providers
│   │   │   ├── components.md          ← layout, buttons, cards, typography, icons
│   │   │   ├── forms.md               ← forms, validation, dialogs, snackbars
│   │   │   ├── data-grid.md           ← MudDataGrid deep dive
│   │   │   └── theming.md             ← MudTheme, palette, dark mode
│   │   └── evals/evals.json
│   └── mudblazor-9-workspace/
│       └── iteration-1/
└── scripts/                           ← utilities for grading + benchmarking
    ├── grade_runs.py
    └── build_benchmarks.py
```

---

## Using the skills

### With GitHub Copilot (VS Code)

Two self-contained `.agent.md` files under `.github/agents/`. Drop them into any project's `.github/agents/` directory (or `~/.copilot/agents/` for global install), reload VS Code, and pick the agent from Copilot Chat's agents dropdown.

See [`.github/agents/README.md`](.github/agents/README.md) for install steps, example prompts, and compatibility notes (including the `.chatmode.md` fallback for older VS Code versions).

The Copilot agents are **self-contained** — they don't need the `skills/` directory to be present in the workspace. All essential knowledge is inlined.

### With Claude Code / Agent SDK

The canonical skill format lives under `skills/`. Each skill has:

- `SKILL.md` — the entry point with YAML frontmatter (name + description) and a workflow body
- `references/*.md` — deeper reference files the skill instructs the agent to read on demand
- `evals/evals.json` — realistic test prompts with assertions

Point your agent at the skill directory:

```bash
# Example: using the migration skill with Claude Code
claude -p "Migrate my project to MudBlazor 9" \
  --skill ./skills/mudblazor-migration-8-to-9
```

Or install it into your project's `.claude/skills/` directory.

To package a skill as a distributable `.skill` file:

```bash
python -m scripts.package_skill ./skills/mudblazor-9
```

(This uses the packaging script from the [`anthropic-skills/skill-creator`](https://github.com/anthropics/skills) plugin.)

---

## How the skills were built and tested

Both skills were built with the `skill-creator` workflow:

1. Researched the MudBlazor 9 breaking changes and API surface from the upstream [v9.0.0 Migration Guide](https://github.com/MudBlazor/MudBlazor/issues/12666) and [MudBlazor docs](https://mudblazor.com).
2. Drafted `SKILL.md` + reference files organized by topic.
3. Wrote three realistic test cases per skill (`skills/<skill>/evals/evals.json`) covering the hardest scenarios.
4. Ran each test case twice — once with the skill loaded, once as a baseline with no skill — using independent subagents.
5. Graded each run against per-assertion regex checks (`scripts/grade_runs.py`) and aggregated into `benchmark.json` + `benchmark.md` per skill.

### Benchmark results (iteration 1)

| Skill | With skill | Baseline | Delta |
|---|---|---|---|
| `mudblazor-migration-8-to-9` | **100% (21/21)** | 58.5% (12/21) | **+41.5 pts** |
| `mudblazor-9` | **100% (37/37)** | 91.0% (34/37) | **+9.0 pts** |

The migration skill shows the largest delta because v9 changed enough that LLMs commonly "remember" the v8 API and confidently write code that no longer compiles (kept `XAxisLabels`, `MudTimeSeriesChart`, synchronous `ShowMessageBox`, `GetSystemPreference`, `SetValueAsync`). The skill catches all of these.

The usage skill shows a smaller delta because general patterns like `EditForm` + DataAnnotations are stable across MudBlazor versions. Its wins are concentrated where v9 differs subtly from prior knowledge: the `ServerData` cancellation token, `GetSystemDarkModeAsync`, `IMudDialogInstance`, and the provider ordering rule.

### Review the eval results

Each workspace has per-run output files, a graded `benchmark.json`, and a standalone `review.html` you can open in a browser:

```bash
open skills/mudblazor-migration-8-to-9-workspace/iteration-1/review.html
open skills/mudblazor-9-workspace/iteration-1/review.html
```

Or start a live server with feedback save:

```bash
python3 <path-to-skill-creator>/eval-viewer/generate_review.py \
  skills/mudblazor-migration-8-to-9-workspace/iteration-1 \
  --skill-name mudblazor-migration-8-to-9 \
  --benchmark skills/mudblazor-migration-8-to-9-workspace/iteration-1/benchmark.json \
  --port 3117
```

---

## Rebuilding benchmarks

If you re-run the evals (or fix the skills and want to measure again):

```bash
# Re-grade all output files against the assertions in each workspace
python3 scripts/grade_runs.py

# Aggregate grading into benchmark.json + benchmark.md per skill
python3 scripts/build_benchmarks.py
```

The scripts live in `scripts/` and reference the skills directory via an absolute path at the top — edit `ROOT` if you move the repo.

---

## MudBlazor versions

- Target: **MudBlazor 9.3.0** (latest stable at build time)
- Supports **.NET 8, 9, and 10**
- Project type assumed: **Blazor Server** (the skills call this out in their frontmatter)

The skills reference v9.3.0 specifically but should work for any 9.x version — the breaking changes listed are from 9.0.0 and haven't been reverted since.

## Sources

- [MudBlazor v9.0.0 Migration Guide · Issue #12666](https://github.com/MudBlazor/MudBlazor/issues/12666)
- [MudBlazor docs](https://mudblazor.com)
- [MudBlazor GitHub](https://github.com/MudBlazor/MudBlazor)
- [MudBlazor NuGet](https://www.nuget.org/packages/MudBlazor)
