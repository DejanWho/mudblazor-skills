---
name: mudblazor-9
description: Build Blazor Server UI with MudBlazor 9 — install and wire up the providers, create pages and components, style with the MudTheme palette and dark mode, build forms with EditForm+DataAnnotations or MudForm, and construct data grids with sorting/filtering/paging/server data. Use this skill whenever the user asks for help creating Blazor UI that uses MudBlazor, references Mud-prefixed components (MudButton, MudCard, MudDataGrid, MudDialog, MudTheme, MudForm, MudLayout, MudAppBar, MudDrawer, etc.), wants to add a page, form, dialog, data table, navigation, or theming to a Blazor app built with MudBlazor 9, asks about AddMudServices, MudThemeProvider, IDialogService, ISnackbar, PropertyColumn, ServerData, PaletteLight/PaletteDark, or any time they mention building UI in Blazor Server and MudBlazor is (or should be) the UI library.
---

# MudBlazor 9 for Blazor Server

Your job is to help build Blazor Server UI with MudBlazor 9.x, writing idiomatic code that compiles on the first try and behaves correctly at runtime. This skill covers setup, page/component authoring, theming, forms, and data grids — the four things you'll do most often.

MudBlazor is a Material-Design component library. It's opinionated — there's usually "the MudBlazor way" to do something — so resist the urge to hand-roll CSS or reach for raw HTML when a MudBlazor component already exists.

## Quick reference — the shape of everything

Before you write anything, know that:

- The NuGet package is `MudBlazor`. Latest 9.x is `9.3.0`. Supports **.NET 8, 9, and 10**.
- Everything begins with `AddMudServices()` in `Program.cs` and four providers mounted in `MainLayout.razor`.
- Components are prefixed `Mud*`. Never import from `MudBlazor.Services` in .razor files — that's for `Program.cs` only.
- Colors use the `Color` enum (`Color.Primary`, `Color.Secondary`, `Color.Tertiary`, `Color.Info`, `Color.Success`, `Color.Warning`, `Color.Error`, `Color.Dark`). Variants: `Variant.Filled`, `Variant.Outlined`, `Variant.Text`.
- Icons live in `Icons.Material.Filled.*`, `Icons.Material.Outlined.*`, `Icons.Material.Rounded.*`, `Icons.Material.Sharp.*`, `Icons.Material.TwoTone.*`. Pass them as strings (they're SVG string constants).
- Spacing helpers: `mt-*`, `mb-*`, `mx-*`, `pa-*`, `gap-*` (0–16). `d-flex`, `flex-column`, `align-center`, `justify-space-between`. These are Tailwind-ish utility classes baked into MudBlazor.
- Most interactive things are two-way bindable via `@bind-Value` (or `@bind-Open`, `@bind-SelectedValues`, etc.).

## When to read the reference files

This skill has a workflow section plus four deep-dive references. **Read them when you need them**, not upfront — pulling in everything wastes context:

| Reference | Read when |
|---|---|
| `references/setup.md` | Creating a new project, wiring up `Program.cs`/providers, fixing "missing provider" errors, or configuring popover/snackbar options |
| `references/components.md` | Building any page or component — layout shell, buttons, cards, navigation, typography, spacing |
| `references/forms.md` | Building forms, validation (DataAnnotations or FluentValidation), dialogs, snackbars |
| `references/data-grid.md` | Anything involving `MudDataGrid` — always read this, it's the most complex component and has the most footguns |
| `references/theming.md` | Customizing colors, light/dark mode, layout properties, or theme switching |

## Workflow

### Step 1: Understand what the user is building

Ask yourself:

- **Is this a new project or an existing one?** New projects need the setup steps in `references/setup.md`. Existing projects probably already have providers mounted — check `MainLayout.razor` before assuming.
- **What's the scope?** A single page/component, a whole feature, or a layout overhaul? Match your response to the scope — don't rebuild the layout shell just to add a button.
- **Is MudBlazor 9 actually installed?** Open the .csproj and check. If it's 8.x, the user probably wants the migration skill first. If it's not installed at all, proceed with setup.

If you're unsure about a structural question (add a new page vs. modify an existing one? Use MudDataGrid vs. MudTable?), ask the user before writing code.

### Step 2: Read the relevant reference(s)

Pick the smallest set of references that covers your task. Don't preemptively read all five. Examples:

- "Add a user list page with sorting and filtering" → `data-grid.md`
- "Build a create-user dialog with validation" → `forms.md`
- "Make the app support dark mode" → `theming.md`, and `setup.md` if the ThemeProvider isn't wired up yet
- "Add a new page with a form and a table" → `components.md` for layout, `forms.md`, `data-grid.md`

### Step 3: Write idiomatic MudBlazor code

Some things to internalize:

- **Favor MudBlazor components over raw HTML.** If the task is "add a button," the answer is `<MudButton>`, not `<button>`. Same for text (`<MudText>` over `<p>`), containers (`<MudPaper>`/`<MudCard>` over `<div>`), grids (`<MudGrid>`/`<MudItem>` over CSS grid).
- **Favor MudBlazor spacing utilities over inline styles.** `Class="mt-4 pa-2"` is better than `Style="margin-top: 16px; padding: 8px;"`. They compose well with the theme's spacing unit.
- **Use `Color` enum values, not hex codes.** `Color="Color.Primary"` lets the theme drive colors. Hex codes defeat theming.
- **Two-way binding uses `@bind-Value`** (not `@bind`). MudBlazor inputs expose `Value` + `ValueChanged`; `@bind-Value` wires both.
- **Async all the things.** Dialog service, snackbar (synchronous OK), grid ServerData, form validation — all async. Forgetting to `await` is the most common mistake.
- **Icons are string constants, not enums.** `Icon="@Icons.Material.Filled.Save"` — the `@` prefix is important because `Icons.Material...` is evaluated as a C# expression.
- **Never use `MudGlobal.*` for styling defaults.** Those were removed in v9 (see the migration skill). Put defaults in wrapper components or use them explicitly.

### Step 4: Wire interactivity correctly

Blazor Server has a specific rendering model. For MudBlazor, this matters in two places:

- **Render mode.** If the project uses per-page interactivity (`@rendermode InteractiveServer` on individual pages), the MudBlazor providers must be on each interactive page, not just `MainLayout.razor`. If it uses global interactive mode, providers in `MainLayout.razor` are enough.
- **Provider ordering.** `MudPopoverProvider` must come **before** `MudDialogProvider` in the markup. If it's the other way around, menus inside dialogs won't close. This is a well-known gotcha.

If something "should work" but the menu won't open, the autocomplete dropdown isn't positioned, or the dialog appears behind other content — it's almost always a provider issue. See `references/setup.md`.

### Step 5: Verify

Build the project. If the user has a running dev server, ask whether you should check runtime behavior too. Common sanity checks:

- Typography looks consistent (no raw `<p>` tags in MudBlazor-styled pages)
- Colors use enum values, not hex
- Dialogs open and close; the close handler receives the right data
- Forms reset and validate correctly
- Data grid shows data, filter/sort/page work, server data doesn't throw on rapid changes

## Principles

- **Be surgical.** Don't rewrite working code. If the task is "add a delete button to the grid," do that — don't restructure the grid or reformat the page.
- **Respect existing patterns.** Look at how other pages in the codebase use MudBlazor before inventing your own style. If they use `MudPaper` wrappers, you use `MudPaper` wrappers.
- **Explain tradeoffs, don't hide them.** `MudDataGrid` vs `MudTable`, `@bind-Value` vs `ValueChanged`, `EditForm` vs `MudForm` — these are real choices. Tell the user what you picked and why if it's non-obvious.
- **Don't memorize the docs; look them up.** If you're unsure whether a parameter is `Title` or `Caption`, read the reference file or ask. Getting a parameter wrong costs a build cycle.
- **Keep it idiomatic.** If you find yourself fighting MudBlazor — writing custom CSS to override component styles, wiring events manually that MudBlazor already exposes, reaching into internal state — stop and re-read the reference. There's probably a built-in way.

## Common traps

- **Forgetting `@rendermode`** — on a per-page interactive project, a page without `@rendermode InteractiveServer` at the top won't react to input. Buttons won't click, inputs won't bind.
- **Wrong provider order** — `MudPopoverProvider` before `MudDialogProvider`, always.
- **Using `@bind` instead of `@bind-Value`** — compile error on MudBlazor inputs.
- **Forgetting to await `DialogService.ShowAsync`** — in v9, `Show` is gone; `ShowAsync` returns a `Task<IDialogReference>`. Not awaiting = null reference.
- **Type inference failing on MudDataGrid** — set `T="YourType"` explicitly if the grid can't infer it from the `Items` expression.
- **Server data ignoring filter state** — the `ServerData` delegate receives a `GridState<T>` with `FilterDefinitions`, `SortDefinitions`, `Page`, `PageSize`. Use them; don't ignore them.
- **Snackbar action buttons making snackbars stay forever** — in v9, snackbars with `Action` don't auto-dismiss. If that's not what you want, set `RequireInteraction = false`.
- **Popovers letting background clicks through** — in v9, `Modal` defaults to `false`. Set `Modal="true"` if you want the old behavior.
- **Theme toggle not persisting** — `MudThemeProvider.IsDarkMode` needs to be bound (`@bind-IsDarkMode`) or set from code; there's no auto-persistence, you wire that yourself (localStorage via JS interop or a cookie).

## Reference files

- `references/setup.md` — installation, Program.cs, providers, render mode
- `references/components.md` — layout, buttons, cards, typography, navigation, spacing
- `references/forms.md` — MudForm vs EditForm, validation, dialogs, snackbars
- `references/data-grid.md` — columns, filtering, sorting, paging, server data, selection, editing
- `references/theming.md` — MudTheme, palette, dark mode, layout properties

## Sources

- [MudBlazor NuGet](https://www.nuget.org/packages/MudBlazor)
- [MudBlazor GitHub](https://github.com/MudBlazor/MudBlazor)
- [MudBlazor docs](https://mudblazor.com)
