# MudBlazor Custom Agents for GitHub Copilot

Two self-contained Copilot custom agents for VS Code:

| File | Purpose |
|---|---|
| `mudblazor-migrate-v8-to-v9.agent.md` | Walk a Blazor Server project through the MudBlazor 8 → 9 migration. Bumps the package, applies every breaking change, verifies the build, surfaces runtime caveats. |
| `mudblazor-9.agent.md` | Build new pages, forms, dialogs, data grids, and theming with MudBlazor 9. Knows the v9 API surface and the common pitfalls. |

Both files are **self-contained** — no external skill files required. Drop them into any project and they work.

## Install

### Option A — drop into your project

Copy the two `.agent.md` files into your project's `.github/agents/` directory:

```
your-project/
└── .github/
    └── agents/
        ├── mudblazor-migrate-v8-to-v9.agent.md
        └── mudblazor-9.agent.md
```

That's it. Reload VS Code (or run **Developer: Reload Window**) and the agents show up in the Copilot Chat agents dropdown.

### Option B — install globally for all projects

Copy the files into your user profile so every project has them available:

**macOS / Linux:** `~/.copilot/agents/`
**Windows:** `%USERPROFILE%\.copilot\agents\`

```bash
mkdir -p ~/.copilot/agents
cp mudblazor-migrate-v8-to-v9.agent.md ~/.copilot/agents/
cp mudblazor-9.agent.md ~/.copilot/agents/
```

## Using the agents

1. Open Copilot Chat in VS Code (`⌃⌘I` on macOS / `Ctrl+Alt+I` on Windows).
2. Click the agent dropdown above the chat input.
3. Pick **MudBlazor v8 → v9 Migrator** or **MudBlazor 9 (Blazor Server)**.
4. Ask your question. The agent's persona and instructions are applied automatically.

Examples:

**Migration agent:**
> "I just bumped MudBlazor in my .csproj from 8.11.0 to 9.3.0 and the build is broken. Fix it."
>
> "Check whether my project is ready to upgrade to MudBlazor 9 and apply the migration."
>
> "I'm getting a compile error: `'MyTagsInput' does not implement inherited abstract member 'GetDefaultConverter()'`. Help."

**Usage agent:**
> "Add a /orders page with a server-side MudDataGrid showing OrderId, CustomerName, Total, CreatedAt with sorting, paging, and a search box."
>
> "Create a Create-Product form with EditForm + DataAnnotations validation."
>
> "Set up a dark mode toggle in MainLayout that follows the OS preference and persists to localStorage."

## Format note

These files use the **`.agent.md`** format (the current VS Code Copilot custom agent format, previously called "custom chat modes" with the `.chatmode.md` extension). If your VS Code is on a version that still uses the old format, rename the files from `.agent.md` to `.chatmode.md` and put them in `.github/chatmodes/` instead — the file content is identical.

## What's inside each agent

Each `.agent.md` file is a YAML frontmatter (name, description, tools, model preferences) followed by a Markdown body. The body contains:

- A workflow the agent follows (preflight → apply → verify → report for migration; understand → write idiomatic code → wire interactivity → verify for usage)
- The key v9 API surface and breaking changes inline
- Common pitfalls and their fixes
- Code examples for typical patterns

The agents request these tools:
- `search/codebase` — find files using MudBlazor
- `search/usages` — find references to specific APIs
- `edit` — apply changes
- `web/fetch` — optionally pull MudBlazor docs

If a tool isn't available in your Copilot install, it's silently ignored.

## Source

Built from research against the [MudBlazor v9.0.0 Migration Guide](https://github.com/MudBlazor/MudBlazor/issues/12666) and [MudBlazor docs](https://mudblazor.com).
