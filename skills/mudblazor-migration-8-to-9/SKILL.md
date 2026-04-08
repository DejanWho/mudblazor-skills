---
name: mudblazor-migration-8-to-9
description: Migrate a Blazor Server project from MudBlazor 8.x to MudBlazor 9.x — bump the package, apply every breaking change (converters, async dialog/menu APIs, MudChart/MudChat/MudFileUpload/MudTreeView rewrites, removed MudGlobal theming properties, popover/dialog service changes, ServerData cancellation token, etc.), and verify the build compiles and runs. Use this skill whenever the user mentions upgrading MudBlazor, bumping to MudBlazor 9, a v9 migration, breaking changes after updating the MudBlazor NuGet, build errors after upgrading MudBlazor, "CS0246 The type or namespace Converter could not be found", `Show` vs `ShowAsync` deprecation, `SetValueAsync` vs `SetValueCoreAsync`, missing `GetDefaultConverter`, removed `MudChat`, `ChartSeries` vs `InputData`, or any compile/runtime error that appeared after changing the MudBlazor version.
---

# MudBlazor 8 → 9 Migration

Your job is to migrate a Blazor Server project from MudBlazor 8.x to MudBlazor 9.x so that it **builds, runs, and behaves the same** as before. You are not just listing changes — you are applying them, verifying the build, and fixing the fallout.

MudBlazor 9's theme for breaking changes is "async everywhere + remove everything that was marked obsolete in v8." There's no single find-and-replace that gets you there; you'll work through the codebase methodically, component by component.

## Why this is harder than most upgrades

Two things make this migration unusually tricky:

1. **The compiler won't catch everything.** Some changes — Popover modal default flipping from `true` to `false`, dialog focus behavior moving from `MudGlobal` to `MudDialogProvider`, snackbar auto-dismiss behavior changing when action buttons are present — compile fine but behave differently at runtime. After the build passes, you still need a smoke test pass.

2. **The converter rewrite cascades.** Any custom component deriving from `MudFormComponent<T, U>` will fail to compile until you implement `GetDefaultConverter()`, because the old `Converter = new DefaultConverter<T>()` assignment in the constructor no longer works. You must find these.

Keep the "why" in mind as you work: the v9 changes exist to support `INumber<T>` in charts, cancellation tokens in server data, proper async semantics, and a cleaner theming story. When you hit an ambiguous situation, let that intent guide you.

## Workflow

Execute these phases in order. Don't skip the pre-flight check — it catches half the problems before they happen.

### Phase 1: Pre-flight check

Before touching anything, gather facts. This protects you from blindly applying changes that don't apply.

1. **Find the .csproj** that references MudBlazor. Read it. Note:
   - Current MudBlazor version
   - Current `TargetFramework` (must be `net8.0` or newer — MudBlazor 9 supports .NET 8, 9, and 10)
   - Any related packages: `MudBlazor.ThemeManager`, `MudBlazor.Extensions`, `MudBlazor.FluentValidation`, `MudBlazor.Markdown`
2. **Confirm it's actually v8.x** via `grep`/Grep on the .csproj. If it's already 9.x, stop and tell the user. If it's v7 or lower, stop and tell the user they need to go through the v8 migration first (a separate guide exists at [github.com/MudBlazor/MudBlazor/issues/9953](https://github.com/MudBlazor/MudBlazor/issues/9953)).
3. **Locate MudBlazor entry points** so you know the blast radius:
   - `Program.cs` — `AddMudServices()` call and any `MudGlobal.*` / `config.PopoverOptions.*` configuration
   - `MainLayout.razor` / `App.razor` — the provider tags (`MudThemeProvider`, `MudPopoverProvider`, `MudDialogProvider`, `MudSnackbarProvider`)
   - Any `*.razor` / `*.razor.cs` files importing `MudBlazor` or using `Mud*` components
4. **Read `references/breaking-changes.md`** now, before you start editing. It's the authoritative checklist; treat this SKILL.md as workflow and `breaking-changes.md` as the reference.
5. **Make sure you can run the build.** Try `dotnet build` once on the v8 codebase so you have a baseline — if it's already broken, you need to know that before you blame v9.

### Phase 2: Bump the package

1. Update the MudBlazor package version in the .csproj to `9.3.0` (or the latest stable 9.x). The package name is unchanged: `MudBlazor`.
2. If `MudBlazor.ThemeManager`, `MudBlazor.Extensions`, or other satellite packages are referenced, check whether they have 9.x-compatible versions and bump them too. Tell the user if you find one that hasn't shipped a v9 build yet — they'll need to decide whether to drop it or wait.
3. Run `dotnet restore`. If this fails, surface the error to the user — it's usually a transitive dependency conflict, not a migration issue.

**Don't build yet.** Apply the source changes first, or you'll drown in compile errors that obscure the real issues.

### Phase 3: Apply breaking changes systematically

Work through `references/breaking-changes.md` section by section. For each section:

1. Use `Grep` to find all call sites of the old API in the codebase
2. Apply the transformation for each match
3. Don't fix only the first hit — grep for the pattern repo-wide

Do these in this order, because later phases depend on earlier ones being done:

1. **MudGlobal theming properties** (removed) — `Program.cs` usually. Move to provider parameters or wrapper components.
2. **Popover configuration** — moved from `MudGlobal.PopoverDefaults` to `AddMudServices(config => config.PopoverOptions...)`. **Modal default flipped from `true` to `false`** — if the user's app relied on popovers blocking click-through, they need to set `Modal="true"` explicitly now.
3. **Converter system rewrite** — the largest change. Search for `Converter<`, `DefaultConverter`, `BoolConverter`, `DateConverter`, and `MudFormComponent<`. Custom form components need `GetDefaultConverter()` implemented. `Converter` is now nullable; access the active converter via `GetConverter()` (method, not property).
4. **Async method renames** — sweep for `.Show(`, `.ShowMessageBox(`, `.Close(`, `.ClearAsync`, `.Clear(`, `ExpandAllGroups(`, `CollapseAllGroups(`, `ActivatePanel(`. Most just gain `Async` suffix, but **you must `await` them** — they return `Task` now, and forgetting the await is a silent runtime bug.
5. **MudFormComponent / MudBaseInput method renames** — `WriteValueAsync` → `SetValueCoreAsync`, `Reset` → `ResetAsync`, `Validate` → `ValidateAsync`, `SetValueAsync` → `SetValueAndUpdateTextAsync`, `SetTextAsync` → `SetTextCoreAsync`. Hit custom input components.
6. **MudSelect** — `SelectedValues` type changed to `IReadOnlyCollection<T>`. `SelectOption(object?)` → `SelectOption(T?)`. Check for places that cast or mutate `SelectedValues`.
7. **MudMenu** — if using `<ActivatorContent>` with a button, you now need `@context.ToggleAsync` to open it (old implicit-activation magic is gone). Also `Stylename` parameter removed.
8. **MudFileUpload** — `<ActivationContent>` is gone, replaced with `<CustomContent Context="fileUpload">` + explicit `OpenFilePickerAsync` call. Auto-open on render is gone.
9. **MudChart** — big one. `InputData` → `ChartSeries`, `XAxisLabels`/`InputLabels` → `ChartLabels`, `AxisChartOptions` → type-specific `BarChartOptions`/`LineChartOptions`/etc. Data shape changed from `double[]` to `List<ChartSeries<T>>` with `.AsChartDataSet()`. `MudTimeSeriesChart` component is gone — use `MudChart` with `ChartType.TimeSeries`. See breaking-changes.md for the full data-shape migration.
10. **MudChat** — entirely removed. If any `<MudChat>`, `<MudChatBubble>`, `<MudChatHeader>`, `<MudChatFooter>` exist, tell the user they need to either install the community `MudX.MudBlazor.Extension` package or build their own chat UI. Don't invent a replacement silently.
11. **MudTreeView** — `Items` now `IReadOnlyCollection<ITreeItemData<T>>` (interface, not concrete class). `TreeItemData<T>.Children` is read-only; assign the whole collection once instead of `.Add()`.
12. **MudDataGrid.ServerData** — signature changed to accept `CancellationToken` as the second parameter. Update every server-side grid handler. Pass the token through to your data access layer if possible.
13. **MudStepper** — `Steps` and `ActiveStep` are now `IStepContext` instead of `MudStep`. Templates receive `IStepContext`. Drop any `.GetState(...)` calls — access properties directly.
14. **MudTabs** — `TabPanelClass` → `TabButtonsClass`, `PanelClass` → `TabPanelsClass`. `MudTabPanel.Class` now only styles the button; use new `PanelClass` for panel content styling.
15. **MudLink** — `Typo` default changed from `Typo.body1` to `Typo.inherit`. If links looked smaller/larger after upgrade, that's why.
16. **MudSnackbar** — snackbars with an action button don't auto-dismiss anymore. If you want the old behavior, set `RequireInteraction = false` explicitly.
17. **MudThemeProvider** — `ObserveSystemThemeChange` → `ObserveSystemDarkModeChange`. `GetSystemPreference()` → `GetSystemDarkModeAsync()`. Update any dark-mode-following code.
18. **Range<T> / DateRange** — setters removed, properties are init-only. Construct new instances instead of mutating.
19. **CssBuilder / StyleBuilder** — now `readonly struct`. `default(CssBuilder)` will NPE. Use `new CssBuilder()` or `CssBuilder.Default()`.
20. **MudDialog focus & options** — `MudGlobal.DialogDefaults.DefaultFocus` moved to `<MudDialogProvider DefaultFocus="..." />` or per-dialog `DialogOptions`.

After each section, briefly tell the user what changed and how many files were touched. This makes the diff reviewable and catches over-eager edits early.

### Phase 4: Verify the build

1. Run `dotnet build` and capture the output.
2. **Read the errors carefully.** Most v9-related errors fall into a few categories:
   - `CS1061: 'IDialogService' does not contain a definition for 'Show'` — missed an async rename
   - `CS0535: '...' does not implement 'GetDefaultConverter()'` — missed a custom form component
   - `CS0266: Cannot implicitly convert type 'ICollection<T>' to 'IReadOnlyCollection<T>'` — `MudSelect.SelectedValues` type change
   - `CS1061: 'MudChart' does not contain a definition for 'InputData'` — missed the MudChart migration
   - `CS0246: The type or namespace 'MudChat' could not be found` — removed component, surface to user
   - `CS0103: The name 'Converter' does not exist` — converter system rewrite
3. Fix the errors. After each round of fixes, rebuild. Repeat until clean.
4. **Warnings matter too** — `[Obsolete]` warnings in v9 often point to things that will be removed in v10. Mention them to the user so they can plan ahead, but don't fix them unless asked.

If you hit an error you don't understand, go back to `references/breaking-changes.md` and search for the symbol. Don't guess.

### Phase 5: Verify runtime behavior

A green build is necessary but not sufficient. These things compile fine but behave differently in v9:

- **Popover modal default flipped to `false`.** Previously popovers blocked click-through on the page behind them. Now they don't. Mention this to the user and suggest they test any UI that relied on popover modality (filter dropdowns, autocomplete panels over forms).
- **Snackbars with action buttons stay open.** If your app shows snackbars with a "Retry" or "Undo" button, they no longer auto-dismiss. Users may be confused.
- **Dialog default focus location.** If you relied on `MudGlobal.DialogDefaults.DefaultFocus`, the default behavior may differ until you move the setting to the provider.
- **MudLink inherits typography.** Links inside a `Typo.h2` are now big instead of `body1`-sized. Check headers with links.
- **MudMenu activator no longer opens on click implicitly.** If menus stopped opening, verify the `ActivatorContent` wires up `@context.ToggleAsync`.
- **ServerData cancellation.** Rapid filter changes now cancel in-flight requests. This is almost always what you want, but if your backend logs cancelled-request warnings, that's why.

Run the app (if you can — ask the user) and spot-check: open a dialog, open a menu, filter a data grid, toggle dark mode. If anything looks off, it's almost certainly one of the above.

### Phase 6: Report

When you're done, give the user:
1. **The package version** you landed on (`9.x.y`)
2. **A list of files changed** (count is fine; names if fewer than ~20)
3. **Any breaking changes you couldn't auto-apply** — typically MudChat removal or custom chart code with unusual shapes
4. **The runtime caveats from Phase 5** they should verify manually
5. **Any `[Obsolete]` warnings** worth knowing about

Don't declare success until the build is clean and you've surfaced the runtime caveats.

## Principles

- **Don't rewrite working code that isn't affected.** The goal is minimal delta. Leave unchanged files alone.
- **Use `Grep` to find call sites.** Don't try to hold the whole codebase in your head. Search for the old symbol, fix the matches.
- **Apply changes in categories, not files.** Doing "all the `Show` → `ShowAsync` fixes" at once is faster and less error-prone than walking file-by-file.
- **When an error is ambiguous, read `breaking-changes.md` again.** The answer is almost always there.
- **Surface judgment calls to the user.** MudChat removal, satellite package compatibility, and popover-modal-default behavior are things the user should decide — don't invent workarounds.
- **Don't mix this with other refactors.** If you notice opportunities to clean up the codebase, resist them. A clean migration diff is easier to review than one tangled with unrelated changes.

## When things go wrong

- **Package restore fails after bump** — usually a transitive dependency conflict, often from a satellite package (`MudBlazor.ThemeManager`, etc.) that hasn't shipped a v9 build. Tell the user; let them decide.
- **Build has hundreds of errors** — this is normal for the first pass if the codebase is large. Fix in categories. The count should drop by 80%+ after the first batch.
- **Runtime error: `Object reference not set` inside MudBlazor** — often a missing provider or `default(CssBuilder)` somewhere. Check Phase 3 step 19 and the provider ordering in MainLayout.
- **Runtime error: menus don't close in dialogs** — provider ordering. `MudPopoverProvider` must come **before** `MudDialogProvider` in MainLayout.razor. (This is a v8 bug too but gets exposed during v9 migrations when people touch the providers.)

## Reference

`references/breaking-changes.md` — full list of every breaking change with before/after code snippets. Read this when you're unsure about a specific API.

Sources used to build this skill:
- [v9.0.0 Migration Guide · Issue #12666](https://github.com/MudBlazor/MudBlazor/issues/12666)
- [MudBlazor Migration Guides · Discussion #12086](https://github.com/MudBlazor/MudBlazor/discussions/12086)
- [NuGet Gallery | MudBlazor](https://www.nuget.org/packages/MudBlazor)
