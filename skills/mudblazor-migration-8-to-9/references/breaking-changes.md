# MudBlazor v9 Breaking Changes — Full Reference

This is the authoritative list of breaking changes between MudBlazor 8.x and 9.x. Use this alongside the workflow in `SKILL.md`. Entries are ordered roughly by how often you'll encounter them; the first few are the big ones.

## Table of contents

1. [Converters: complete rewrite](#1-converters-complete-rewrite)
2. [Async method renames (DialogService, DataGrid, Select, Tabs)](#2-async-method-renames)
3. [MudFormComponent / MudBaseInput API changes](#3-mudformcomponent--mudbaseinput-api-changes)
4. [MudGlobal theming properties removed](#4-mudglobal-theming-properties-removed)
5. [Popover configuration moved; Modal default flipped](#5-popover-configuration-moved-modal-default-flipped)
6. [MudDialog: DefaultFocus moved to provider](#6-muddialog-defaultfocus-moved-to-provider)
7. [MudSelect changes](#7-mudselect-changes)
8. [MudMenu: MenuContext replaces IActivatable](#8-mudmenu-menucontext-replaces-iactivatable)
9. [MudFileUpload: ActivationContent → CustomContent](#9-mudfileupload-activationcontent--customcontent)
10. [MudChart: complete refactor + INumber support](#10-mudchart-complete-refactor--inumber-support)
11. [MudChat: entirely removed](#11-mudchat-entirely-removed)
12. [MudTreeView: ITreeItemData interface](#12-mudtreeview-itreeitemdata-interface)
13. [MudDataGrid: ServerData CancellationToken](#13-muddatagrid-serverdata-cancellationtoken)
14. [MudStepper: IStepContext interface](#14-mudstepper-istepcontext-interface)
15. [MudTabs: class parameter renames](#15-mudtabs-class-parameter-renames)
16. [MudLink: Typo default changed](#16-mudlink-typo-default-changed)
17. [MudSnackbar: require-interaction for action buttons](#17-mudsnackbar-require-interaction-for-action-buttons)
18. [MudThemeProvider: dark-mode API rename](#18-mudthemeprovider-dark-mode-api-rename)
19. [Range<T> / DateRange: setters removed](#19-ranget--daterange-setters-removed)
20. [CssBuilder / StyleBuilder: readonly struct](#20-cssbuilder--stylebuilder-readonly-struct)
21. [EventListener / EventManager: removed](#21-eventlistener--eventmanager-removed)
22. [Masking API changes](#22-masking-api-changes)
23. [IScrollListener: IAsyncDisposable](#23-iscrolllistener-iasyncdisposable)
24. [New Roslyn analyzers (MUD0010-0012)](#24-new-roslyn-analyzers)
25. [Misc component tweaks](#25-misc-component-tweaks)

---

## 1. Converters: complete rewrite

The entire converter system was redesigned for type safety and performance. The old concrete classes are gone; the new system uses interfaces.

**Removed (no longer compile):**
- `Converter<T, U>`, `Converter<T>` (base classes)
- `DefaultConverter` (non-generic), `BoolConverter` (non-generic), `DateConverter`
- `NumericConverter.AreEqual` method
- `Converters` static class (the old one)

**Replacements:**
- `IConverter<TInput, TOutput>` — the new base interface
- `ICultureAwareConverter<TInput, TOutput>`
- `IReversibleConverter<TInput, TOutput>`
- `DefaultConverter<T>`, `BoolConverter<T>`, `RangeConverter<T>` (generic)
- `ConversionResult<T>` for error handling
- `ConverterExtensions` and the new `Conversions` static class

### Custom converter migration

```csharp
// Before (v8)
public class MyConverter : Converter<MyType>
{
    public MyConverter()
    {
        SetFunc = value => value?.ToString() ?? string.Empty;
        GetFunc = str => MyType.Parse(str);
    }
}

// After (v9)
public class MyConverter : IReversibleConverter<MyType, string>
{
    public string Convert(MyType input) { /* ... */ }
    public MyType ConvertBack(string input) { /* ... */ }
}
```

### Custom MudFormComponent must implement GetDefaultConverter

This is the biggest source of compile errors when migrating custom form components. You can no longer assign `Converter` in the constructor.

```csharp
// Before (v8)
public class MyInput : MudFormComponent<MyType, string>
{
    public MyInput()
    {
        Converter = new DefaultConverter<MyType>
        {
            Culture = GetCulture,
            Format = GetFormat
        };
    }
}

// After (v9)
public class MyInput : MudFormComponent<MyType, string>
{
    protected override IConverter<MyType?, string?> GetDefaultConverter()
    {
        return new DefaultConverter<MyType>
        {
            Culture = GetCulture,
            Format = GetFormat
        };
    }
}
```

**Key points:**
- `Converter` property is now nullable (`IConverter<T, U>?`)
- Access the active converter via `GetConverter()` (method, not property)
- Forgetting to override `GetDefaultConverter()` produces a compile error
- `DefaultConverter<T>` still exists — it's the assignment location that changed

### How to find affected code

```bash
# Find all custom MudFormComponent subclasses
grep -rn "MudFormComponent<" --include="*.cs"

# Find old converter constructors
grep -rn "Converter = new" --include="*.cs"
grep -rn ": Converter<" --include="*.cs"
```

---

## 2. Async method renames

Many methods marked `[Obsolete]` in v8 have been removed in v9. Their async replacements already existed in v8, so the fix is mechanical: rename + `await`.

### IDialogService

| v8                             | v9                                  |
| ------------------------------ | ----------------------------------- |
| `Show(Type)`                   | `ShowAsync(Type)`                   |
| `Show<T>()`                    | `ShowAsync<T>()`                    |
| `ShowMessageBox(...)`          | `ShowMessageBoxAsync(...)`          |
| `ShowForm<T>(...)`             | `ShowFormAsync<T>(...)`             |
| `Close()` (on IDialogReference) | `CloseAsync()`                     |

All of these return `Task<IDialogReference>` or `Task` now. You **must** `await` them — not awaiting is a silent runtime bug.

```csharp
// Before (v8)
var dialog = DialogService.Show<MyDialog>("Title");
var result = await dialog.Result;

// After (v9)
var dialog = await DialogService.ShowAsync<MyDialog>("Title");
var result = await dialog.Result;
```

### MudDataGrid

| v8                      | v9                           |
| ----------------------- | ---------------------------- |
| `ExpandAllGroups()`     | `ExpandAllGroupsAsync()`     |
| `CollapseAllGroups()`   | `CollapseAllGroupsAsync()`   |

### MudSelect

| v8        | v9            |
| --------- | ------------- |
| `Clear()` | `ClearAsync()` |

### MudTabs

| v8                   | v9                        |
| -------------------- | ------------------------- |
| `ActivatePanel(...)` | `ActivatePanelAsync(...)` |

### Removed from various places

- `MudMenu.Stylename` parameter — removed. Use `Style` instead.
- `ElementReferenceExtensions.MudDetachBlurEventWithJS` — removed.

---

## 3. MudFormComponent / MudBaseInput API changes

Custom form components that override value-setting or text-setting logic need updates.

### Method renames

| v8                              | v9                                          |
| ------------------------------- | ------------------------------------------- |
| `WriteValueAsync(T? value)`     | `SetValueCoreAsync(T? value)`               |
| `SetValueAsync(T?, bool, bool)` | `SetValueAndUpdateTextAsync(T?, bool, bool)` |
| `SetTextAsync(string?)`         | `SetTextCoreAsync(string?)`                 |
| `Reset()`                       | `ResetAsync()`                              |
| `Validate()`                    | `ValidateAsync()`                           |
| `ReadValue()` (method)          | `ReadValue` (property)                      |
| `ReadText()` (method)           | `ReadText` (property)                       |

```csharp
// Before (v8)
protected override Task WriteValueAsync(MyType? value)
{
    _value = value;
    return Task.CompletedTask;
}

// After (v9)
protected override Task SetValueCoreAsync(MyType? value)
{
    _value = value;
    return Task.CompletedTask;
}
```

### Error / ErrorId now two-way bindable

```razor
<MudTextField @bind-Error="myError" @bind-ErrorId="myErrorId" />
```

### MudBaseInput parameters removed

- `TextUpdateSuppression` — removed. The framework handles this automatically now.
- `ForceUpdate()` method — removed.

### MudSelect.WaitForRender() removed

If you were using this for test synchronization, use `WaitForAssertion` from bUnit instead, or migrate to explicit rendering waits.

---

## 4. MudGlobal theming properties removed

A bunch of `MudGlobal` static properties that let you set default theming across all components were removed. The philosophy: theming should live in the theme (per-component via parameters, or via wrapper components), not in global mutable state.

**Removed:**
- `MudGlobal.Rounded`
- `MudGlobal.ButtonDefaults.Color`, `MudGlobal.ButtonDefaults.Variant`
- `MudGlobal.InputDefaults.ShrinkLabel`, `Variant`, `Margin`
- `MudGlobal.LinkDefaults.Color`, `Typo`, `Underline`
- `MudGlobal.GridDefaults.Spacing`
- `MudGlobal.StackDefaults.Spacing`
- `MudGlobal.PopoverDefaults.Elevation`

**Still present (behavior, not style):**
- `MudGlobal.DialogDefaults.DefaultFocus` — but moved to `MudDialogProvider`, see section 6
- `MudGlobal.MenuDefaults.HoverDelay`
- `MudGlobal.PopoverDefaults.ModalOverlay`
- `MudGlobal.TooltipDefaults.Delay` / `Duration`
- `MudGlobal.TransitionDefaults.Delay` / `Duration`

### Migration strategy

```csharp
// Before (v8) - Program.cs
MudGlobal.ButtonDefaults.Variant = Variant.Filled;
MudGlobal.InputDefaults.Variant = Variant.Outlined;
MudGlobal.InputDefaults.Margin = Margin.Dense;
```

**Option A — make each call site explicit** (fastest for small codebases):

```razor
<MudButton Variant="Variant.Filled">Click Me</MudButton>
<MudTextField Variant="Variant.Outlined" Margin="Margin.Dense" />
```

**Option B — create wrapper components** (better for large codebases):

```razor
@* AppButton.razor *@
<MudButton Variant="Variant.Filled" Class="@Class" @attributes="AdditionalAttributes">
    @ChildContent
</MudButton>

@code {
    [Parameter] public string? Class { get; set; }
    [Parameter] public RenderFragment? ChildContent { get; set; }
    [Parameter(CaptureUnmatchedValues = true)]
    public IDictionary<string, object>? AdditionalAttributes { get; set; }
}
```

Then search-and-replace `<MudButton` → `<AppButton` across the codebase.

---

## 5. Popover configuration moved, Modal default flipped

Popover options used to live on `MudGlobal.PopoverDefaults`. Now they go into `AddMudServices`.

```csharp
// Before (v8)
MudGlobal.PopoverDefaults.TransitionDuration = 300;

// After (v9)
services.AddMudServices(config =>
{
    config.PopoverOptions.TransitionDuration = 300;
});
```

### ⚠️ Modal default flipped from `true` to `false`

Popovers no longer block interaction with content behind them by default. If your app relied on popovers being modal (e.g., clicking outside a filter dropdown shouldn't interact with the page behind it), you must set `Modal="true"` explicitly:

```razor
<MudPopover Modal="true" Open="_open">
    ...
</MudPopover>
```

Or globally:

```csharp
services.AddMudServices(config =>
{
    config.PopoverOptions.ModalOverlay = true;
});
```

### Flipping behavior

- `PopoverOptions.Mode` — **removed**. Flipping is always `FlipAlways` now and controlled via `PopoverOptions`.

---

## 6. MudDialog: DefaultFocus moved to provider

```csharp
// Before (v8)
MudGlobal.DialogDefaults.DefaultFocus = DefaultFocus.FirstChild;
```

```razor
@* After (v9) - option A: globally via provider *@
<MudDialogProvider DefaultFocus="DefaultFocus.FirstChild" />
```

```csharp
// After (v9) - option B: per-dialog via options
var options = new DialogOptions { DefaultFocus = DefaultFocus.FirstChild };
var dialog = await DialogService.ShowAsync<MyDialog>("Title", options);
```

---

## 7. MudSelect changes

### SelectedValues type changed

```csharp
// Before (v8)
ICollection<T> SelectedValues { get; set; }

// After (v9)
IReadOnlyCollection<T> SelectedValues { get; set; }
```

Any code that did `_select.SelectedValues.Add(x)` or cast to `List<T>` needs to assign a new collection instead.

### SelectOption generic

```csharp
// Before (v8)
SelectOption(object?)

// After (v9)
SelectOption(T?)
```

### Comparer requirement

Requires proper `GetHashCode` implementation. `EqualityComparer<T>.Create()` must include the `getHashCode` parameter:

```csharp
// Before (v8)
var comparer = EqualityComparer<MyItem>.Create((a, b) => a?.Id == b?.Id);

// After (v9)
var comparer = EqualityComparer<MyItem>.Create(
    (a, b) => a?.Id == b?.Id,
    item => item?.Id.GetHashCode() ?? 0
);
```

### Open parameter now two-way bindable

```razor
<MudSelect @bind-Open="_isOpen" />
```

---

## 8. MudMenu: MenuContext replaces IActivatable

`ActivatorContent` no longer receives an `IActivatable` via cascading. Instead, a `MenuContext` is provided via the `context` variable in the `ActivatorContent` template.

### MenuContext API

```csharp
public sealed class MenuContext
{
    public Task OpenAsync(EventArgs? args = null);
    public Task CloseAsync();
    public Task ToggleAsync(EventArgs? args = null);
    public Task CloseAllAsync();
}
```

### Before (v8)

```razor
<MudMenu>
    <ActivatorContent>
        <MudButton Variant="Variant.Filled">Open Menu</MudButton>
    </ActivatorContent>
    <ChildContent>
        <MudMenuItem>Item 1</MudMenuItem>
    </ChildContent>
</MudMenu>
```

### After (v9) — explicit activation

```razor
<MudMenu>
    <ActivatorContent>
        <MudButton Variant="Variant.Filled" OnClick="@context.ToggleAsync">Open Menu</MudButton>
    </ActivatorContent>
    <ChildContent>
        <MudMenuItem>Item 1</MudMenuItem>
    </ChildContent>
</MudMenu>
```

### Right click

```razor
<MudMenu ActivationEvent="MouseEvent.RightClick">
    <ActivatorContent>
        <div @oncontextmenu="@context.ToggleAsync" @oncontextmenu:preventDefault="true">
            <MudChip>Right Click Me</MudChip>
        </div>
    </ActivatorContent>
</MudMenu>
```

### Hover

```razor
<MudMenu ActivationEvent="MouseEvent.MouseOver">
    <ActivatorContent>
        <div @onpointerenter="@context.OpenAsync" @onpointerleave="@context.CloseAsync">
            <MudChip>Hover Over Me</MudChip>
        </div>
    </ActivatorContent>
</MudMenu>
```

---

## 9. MudFileUpload: ActivationContent → CustomContent

Auto-open on render removed. You now call `OpenFilePickerAsync()` explicitly.

### Before (v8)

```razor
<MudFileUpload T="IBrowserFile" @bind-Files="_files">
    <ActivationContent>
        <MudButton Variant="Variant.Filled" Color="Color.Primary">
            <MudIcon Icon="@Icons.Material.Filled.Upload" Class="mr-2" />
            Upload File
        </MudButton>
    </ActivationContent>
</MudFileUpload>
```

### After (v9)

```razor
<MudFileUpload T="IBrowserFile" @bind-Files="_files">
    <CustomContent Context="fileUpload">
        <MudButton Variant="Variant.Filled" Color="Color.Primary"
                   OnClick="@fileUpload.OpenFilePickerAsync">
            <MudIcon Icon="@Icons.Material.Filled.Upload" Class="mr-2" />
            Upload File
        </MudButton>
    </CustomContent>
</MudFileUpload>
```

### New features in v9

- Default file list rendering if `SelectedTemplate` isn't provided
- Built-in drag-and-drop with `DragAndDrop="true"`
- `Dragging` parameter for drag state tracking
- `GetFilenames()`, `RemoveFile()` methods

```razor
<MudFileUpload T="IReadOnlyList<IBrowserFile>"
               @bind-Files="_files"
               DragAndDrop="true"
               Dragging="@_isDragging"
               MaximumFileCount="5">
    <CustomContent Context="fileUpload">
        <MudPaper Outlined="true"
                  Class="@(_isDragging ? "mud-primary-text" : "")">
            <MudStack AlignItems="AlignItems.Center">
                <MudIcon Icon="@Icons.Material.Filled.CloudUpload" Size="Size.Large" />
                <MudText>Drag files here or
                    <MudLink OnClick="@fileUpload.OpenFilePickerAsync">click to browse</MudLink>
                </MudText>
            </MudStack>
        </MudPaper>
    </CustomContent>
</MudFileUpload>
```

---

## 10. MudChart: complete refactor + INumber support

One of the largest v9 breaking changes. Charts now support any numeric type (`int`, `decimal`, `float`, etc.) via `INumber<T>`, not just `double`. Two new chart types (`Radar`, `Rose`), combination charts, and a unified data model.

### Removed classes

- `AxisChartOptions`, `ChartOptions` → replaced by type-specific options
- `MudTimeSeriesChart` → use `MudChart` with `ChartType.TimeSeries`
- `MudCategoryChartBase`, `MudCategoryAxisChartBase`
- `TimeSeriesChartSeries`
- `NodeChartOptions` → `SankeyChartOptions`

### Parameter renames

| v8                       | v9                    |
| ------------------------ | --------------------- |
| `XAxisLabels`            | `ChartLabels`         |
| `InputData`              | `ChartSeries`         |
| `InputLabels`            | `ChartLabels`         |
| `CircleDonutRatio`       | `DonutRingRatio`      |
| `StackedBarWidthRatio`   | `BarWidthRatio`       |

### New type-specific options classes

- `BarChartOptions`
- `LineChartOptions`
- `DonutChartOptions`
- `PieChartOptions`
- `RadarChartOptions`
- `RoseChartOptions`
- `TimeSeriesChartOptions`
- `SankeyChartOptions`

### Data model migration

```razor
@* Before (v8) *@
<MudChart ChartType="ChartType.Pie"
          InputData="@data"
          InputLabels="@labels" />

@code {
    private double[] data = { 25, 50, 25 };
    private string[] labels = { "A", "B", "C" };
}
```

```razor
@* After (v9) *@
<MudChart ChartType="ChartType.Pie"
          ChartSeries="@series"
          ChartLabels="@labels" />

@code {
    private List<ChartSeries<double>> series = new()
    {
        new ChartSeries<double>
        {
            Data = new double[] { 25, 50, 25 }.AsChartDataSet()
        }
    };
    private string[] labels = { "A", "B", "C" };
}
```

### INumber support — use any numeric type

```razor
<MudChart ChartType="ChartType.Bar" ChartSeries="@series" />

@code {
    private List<ChartSeries<int>> series = new()
    {
        new ChartSeries<int>
        {
            Name = "Sales",
            Data = new int[] { 100, 200, 150, 300 }.AsChartDataSet()
        }
    };
}
```

### Options migration

```razor
@* Before (v8) *@
<MudChart ChartType="ChartType.Bar"
          XAxisChartOptions="@chartOptions" />

@code {
    private AxisChartOptions chartOptions = new()
    {
        YAxisTicks = 10,
        YAxisFormat = "N0"
    };
}
```

```razor
@* After (v9) *@
<MudChart ChartType="ChartType.Bar"
          ChartOptions="@barOptions" />

@code {
    private BarChartOptions barOptions = new()
    {
        YAxisTicks = 10,
        YAxisFormat = "N0",
        BarWidthRatio = 0.8
    };
}
```

### Combination charts (new)

```razor
<MudChart ChartType="ChartType.Bar" ChartSeries="@mixedSeries" />

@code {
    private List<ChartSeries<double>> mixedSeries = new()
    {
        new ChartSeries<double>
        {
            Name = "Revenue",
            ChartType = ChartType.Bar,
            Data = new double[] { 100, 150, 120 }.AsChartDataSet()
        },
        new ChartSeries<double>
        {
            Name = "Target",
            ChartType = ChartType.Line,
            Data = new double[] { 110, 140, 130 }.AsChartDataSet()
        }
    };
}
```

---

## 11. MudChat: entirely removed

Removed components (no longer exist):
- `<MudChat />`
- `<MudChatBubble />`
- `<MudChatHeader />`
- `<MudChatFooter />`

Removed types:
- `ChatBubblePosition`
- `ChatArrowPosition`

**Migration:** The community `MudX.MudBlazor.Extension` package from [MudXtra/MudX](https://github.com/MudXtra/MudX/) provides drop-in chat components. Alternatively, build chat UI from `MudPaper`/`MudCard` primitives.

**Do not invent a chat replacement silently during migration.** If you find `<MudChat>` usage, surface it to the user and let them decide.

---

## 12. MudTreeView: ITreeItemData interface

`Items` is now typed as `IReadOnlyCollection<ITreeItemData<T>>` (interface). `Children` on each item is now read-only — assign a complete collection once instead of calling `.Add()`.

### Before (v8)

```csharp
public IReadOnlyCollection<TreeItemData<T>>? Items { get; set; }
public RenderFragment<TreeItemData<T>>? ItemTemplate { get; set; }
public Func<TreeItemData<T>, Task<bool>>? FilterFunc { get; set; }

// Mutating children:
var item = new TreeItemData<string> { Text = "Parent" };
item.Children = new List<TreeItemData<string>>();
item.Children.Add(new TreeItemData<string> { Text = "Child" });
```

### After (v9)

```csharp
public IReadOnlyCollection<ITreeItemData<T>>? Items { get; set; }
public RenderFragment<ITreeItemData<T>>? ItemTemplate { get; set; }
public Func<ITreeItemData<T>, Task<bool>>? FilterFunc { get; set; }

// Assign children in one go:
var children = new List<TreeItemData<string>>
{
    new TreeItemData<string> { Text = "Child" }
};
item.Children = children;
```

---

## 13. MudDataGrid: ServerData CancellationToken

The `ServerData` delegate signature changed to accept a `CancellationToken`. This enables automatic cancellation of in-flight data loads when filters/sort/page change rapidly.

```csharp
// Before (v8)
public Func<GridState<T>, Task<GridData<T>>> ServerData { get; set; }

// After (v9)
public Func<GridState<T>, CancellationToken, Task<GridData<T>>> ServerData { get; set; }
```

### Example migration

```razor
@* Before (v8) *@
<MudDataGrid T="Item" ServerData="LoadDataAsync">...</MudDataGrid>

@code {
    private async Task<GridData<Item>> LoadDataAsync(GridState<Item> state)
    {
        var items = await _repo.QueryAsync(state);
        return new GridData<Item> { Items = items, TotalItems = items.Count };
    }
}
```

```razor
@* After (v9) *@
<MudDataGrid T="Item" ServerData="LoadDataAsync">...</MudDataGrid>

@code {
    private async Task<GridData<Item>> LoadDataAsync(
        GridState<Item> state,
        CancellationToken ct)
    {
        var items = await _repo.QueryAsync(state, ct);
        return new GridData<Item> { Items = items, TotalItems = items.Count };
    }
}
```

Pass the `CancellationToken` through to your data access layer (EF Core's `ToListAsync(ct)`, HTTP clients, etc.) so the cancellation actually takes effect.

---

## 14. MudStepper: IStepContext interface

Templates previously received `MudStep`; they now receive `IStepContext`. The `Steps` and `ActiveStep` properties are also typed as `IStepContext` now.

### IStepContext contract

```csharp
public interface IStepContext
{
    string? Title { get; }
    bool Completed { get; }
    bool Disabled { get; }
    bool HasError { get; }
    bool Skipped { get; }
    bool Skippable { get; }
    bool IsActive { get; }

    Task SetHasErrorAsync(bool value, bool refreshParent = true);
    Task SetCompletedAsync(bool value, bool refreshParent = true);
    Task SetDisabledAsync(bool value, bool refreshParent = true);
    Task SetSkippedAsync(bool value, bool refreshParent = true);
}
```

### No more .GetState()

```razor
@* Before (v8) *@
<MudChip Color="@GetColor(step.GetState(s => s.Completed))">
    @step.Title
</MudChip>

@* After (v9) *@
<MudChip Color="@GetColor(step.Completed)">
    @step.Title
</MudChip>
```

---

## 15. MudTabs: class parameter renames

`MudTabs`:

| v8               | v9                 |
| ---------------- | ------------------ |
| `TabPanelClass`  | `TabButtonsClass`  |
| `PanelClass`     | `TabPanelsClass`   |

`MudTabPanel`: `Class` used to style both the button and the panel. In v9 it only styles the button; use the new `PanelClass` property for panel styling.

---

## 16. MudLink: Typo default changed

Default `Typo` went from `Typo.body1` to `Typo.inherit`. Links inside a `Typo.h2` or similar now match the surrounding typography instead of forcing body1.

If you want the old behavior, set `Typo="Typo.body1"` explicitly.

---

## 17. MudSnackbar: require-interaction for action buttons

Snackbars with an action button now require user interaction by default — they won't auto-dismiss. If you want the old auto-dismiss behavior, set `RequireInteraction = false` explicitly:

```csharp
Snackbar.Add("Saved!", Severity.Success, config =>
{
    config.Action = "Undo";
    config.ActionColor = Color.Primary;
    config.RequireInteraction = false; // explicit opt-out
    config.OnClick = snackbar => UndoAsync();
});
```

---

## 18. MudThemeProvider: dark-mode API rename

System theme listening was renamed for clarity.

| v8                              | v9                                   |
| ------------------------------- | ------------------------------------ |
| `ObserveSystemThemeChange`      | `ObserveSystemDarkModeChange`        |
| `GetSystemPreference()`         | `GetSystemDarkModeAsync()`           |
| `WatchSystemPreference()`       | `WatchSystemDarkModeAsync()`         |
| `SystemPreferenceChanged()`     | `SystemDarkModeChangedAsync()`       |

---

## 19. Range<T> / DateRange: setters removed

`Range<T>` and `DateRange` are now immutable (init-only properties). Construct new instances to update.

```csharp
// Before (v8)
var range = new DateRange();
range.Start = DateTime.Today;
range.End = DateTime.Today.AddDays(7);

// After (v9) - constructor
var range = new DateRange(DateTime.Today, DateTime.Today.AddDays(7));

// After (v9) - replace instance when updating
_dateRange = new DateRange(newStart, newEnd);
```

---

## 20. CssBuilder / StyleBuilder: readonly struct

Both are now `readonly struct`. `default(CssBuilder)` will throw `NullReferenceException` at runtime — use a real constructor.

```csharp
// Before (v8) - works
var cssBuilder = default(CssBuilder);
cssBuilder.AddClass("my-class");

// After (v9) - NPE at runtime
// Fix options:
var cssBuilder = new CssBuilder();
cssBuilder.AddClass("my-class");

// Or the factory:
var cssBuilder = CssBuilder.Default().AddClass("my-class");

// Or chain (recommended):
var classes = new CssBuilder("base-class")
    .AddClass("additional-class", when: someCondition)
    .Build();
```

---

## 21. EventListener / EventManager: removed

Entirely removed:
- `IEventListener` / `EventListener`
- `IEventListenerFactory` / `EventListenerFactory`
- `IEventManager`
- `WebEventJsonContext`

If you were using these directly, you'll need to wire up JS interop or `@on...` handlers yourself. Most apps don't touch these.

---

## 22. Masking API changes

- `MaskChar` is now a `readonly struct` — use the constructor, not object initializer
- `RegexMask.Delimiters` → `DelimiterCharacters`
- `IMask.Mask` and `IMask.Text` are now non-nullable
- `BaseMask`: protected fields became private; use the protected properties/methods instead

---

## 23. IScrollListener: IAsyncDisposable

Changed from `IDisposable` to `IAsyncDisposable` — use `await DisposeAsync()`.

New members:
- `ReportRateMs` property (default: 10ms)
- `GetCurrentScrollDataAsync()` method
- `ScrollEventArgs.ClientHeight` and `ClientWidth`
- `IScrollListenerFactory.Create()` overload taking `reportRateMs`

---

## 24. New Roslyn analyzers

Three new code analyzers enforce `ParameterState` best practices. They may emit warnings/errors on code that compiled cleanly under v8:

- **MUD0010** — Warning: reading `ParameterState` property outside constructors
- **MUD0011** — Error: writing to `ParameterState` property
- **MUD0012** — Warning: accessing `ParameterState` from outside the component

Most apps won't touch `ParameterState` directly. If you see these, follow the analyzer's guidance — they exist because the v8 patterns could cause parameter-tearing bugs.

---

## 25. Misc component tweaks

- **MudCollapse** — content now rendered inside a `<span>` element (was `<div>` or nothing). Check CSS selectors.
- **MudColorPicker** — now supports `null` color values correctly; improved throttling.
- **MudDialogContainer** — `OnMouseUp` → `OnMouseUpAsync`; now `private`.
- **MudBaseInput.TextUpdateSuppression** parameter — removed.
- **MudBaseInput.ForceUpdate()** method — removed.
- **MudSelect.WaitForRender()** — removed (test helper).

---

## Source

- [MudBlazor v9.0.0 Migration Guide · Issue #12666](https://github.com/MudBlazor/MudBlazor/issues/12666) — authoritative upstream source
- [v9: Remove all code marked obsolete/deprecated · Issue #12048](https://github.com/MudBlazor/MudBlazor/issues/12048)
- [MudBlazor Migration Guides · Discussion #12086](https://github.com/MudBlazor/MudBlazor/discussions/12086)
