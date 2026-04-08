# MudBlazor 9 — Setup & wiring

Everything you need to get MudBlazor 9.x running in a Blazor Server app and to avoid the "providers missing" / "menu won't close" class of runtime errors.

## Package

Latest stable: **9.3.0** (the 9.x line supports .NET 8, 9, and 10).

```bash
dotnet add package MudBlazor
```

Or in the .csproj:

```xml
<ItemGroup>
  <PackageReference Include="MudBlazor" Version="9.3.0" />
</ItemGroup>
```

## Program.cs

Add `using MudBlazor.Services;` and call `AddMudServices()`.

### Minimal Blazor Server setup

```csharp
using MudBlazor.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

// MudBlazor
builder.Services.AddMudServices();

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseAntiforgery();

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
```

### AddMudServices with configuration

You can pass a configuration lambda to customize popover, snackbar, and transition defaults globally. Most apps don't need this, but here's where the knobs live:

```csharp
builder.Services.AddMudServices(config =>
{
    // Snackbar defaults
    config.SnackbarConfiguration.PositionClass = Defaults.Classes.Position.BottomRight;
    config.SnackbarConfiguration.PreventDuplicates = false;
    config.SnackbarConfiguration.NewestOnTop = false;
    config.SnackbarConfiguration.ShowCloseIcon = true;
    config.SnackbarConfiguration.VisibleStateDuration = 5000;
    config.SnackbarConfiguration.HideTransitionDuration = 200;
    config.SnackbarConfiguration.ShowTransitionDuration = 200;
    config.SnackbarConfiguration.SnackbarVariant = Variant.Filled;

    // Popover defaults (moved here in v9)
    config.PopoverOptions.TransitionDuration = 300;
    config.PopoverOptions.ModalOverlay = false; // v9 default
});
```

> **v9 note:** `MudGlobal.PopoverDefaults.*` was removed. All popover configuration now goes through `AddMudServices` or per-component parameters.

## _Imports.razor

Add MudBlazor to the usings so you don't have to fully qualify types in every .razor file:

```razor
@using MudBlazor
```

## App.razor (CSS + JS references)

Add the MudBlazor stylesheet in the `<head>` and the JS file before `</body>`.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <base href="/" />
    <link rel="stylesheet" href="app.css" />
    <link rel="stylesheet" href="YourApp.styles.css" />

    <!-- MudBlazor CSS -->
    <link href="_content/MudBlazor/MudBlazor.min.css" rel="stylesheet" />

    <!-- Optional: Material Icons font (if you want to use <i class="material-icons">...)
         MudIcon uses inline SVG so this is NOT required. -->
    <!-- <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet" /> -->

    <HeadOutlet />
</head>
<body>
    <Routes />

    <script src="_framework/blazor.web.js"></script>
    <!-- MudBlazor JS -->
    <script src="_content/MudBlazor/MudBlazor.min.js"></script>
</body>
</html>
```

The CSS file is `_content/MudBlazor/MudBlazor.min.css`. The JS file is `_content/MudBlazor/MudBlazor.min.js`. Both are served automatically by the `_content` virtual path — no build step.

> **Icon fonts are not required.** `MudIcon` renders SVG strings from `Icons.Material.Filled.*` etc. The Material Icons web font is only needed if you also want raw `<i class="material-icons">` elements.

## MainLayout.razor (the four providers)

The four providers must be present exactly once in the render tree for any interactive page. **Provider order matters**: `MudPopoverProvider` must come **before** `MudDialogProvider`, otherwise menus inside dialogs won't close.

```razor
@inherits LayoutComponentBase

<MudThemeProvider />
<MudPopoverProvider />
<MudDialogProvider />
<MudSnackbarProvider />

<MudLayout>
    <MudAppBar Elevation="1">
        <MudIconButton Icon="@Icons.Material.Filled.Menu"
                       Color="Color.Inherit"
                       Edge="Edge.Start"
                       OnClick="ToggleDrawer" />
        <MudText Typo="Typo.h6">My App</MudText>
        <MudSpacer />
        <MudIconButton Icon="@Icons.Material.Filled.Brightness4"
                       Color="Color.Inherit"
                       OnClick="ToggleDarkMode" />
    </MudAppBar>

    <MudDrawer @bind-Open="_drawerOpen" Elevation="1">
        <NavMenu />
    </MudDrawer>

    <MudMainContent Class="pa-4">
        @Body
    </MudMainContent>
</MudLayout>

@code {
    private bool _drawerOpen = true;

    private void ToggleDrawer() => _drawerOpen = !_drawerOpen;

    // Dark mode toggle — see theming.md for a full implementation
    private void ToggleDarkMode() { /* ... */ }
}
```

### Why provider order matters

`MudPopoverProvider` owns the portal that popovers (menus, autocompletes, dropdowns) render into. `MudDialogProvider` owns the portal for dialogs. When a menu appears inside a dialog, its popover needs to be rendered in a portal that exists **before** the dialog's portal, otherwise the popover's close-on-click-outside detection can't see clicks targeting the dialog chrome.

Practical rule: put `MudPopoverProvider` first. Always.

## Render modes (Blazor Web App, .NET 8+)

If the project uses the Blazor Web App template (.NET 8+), the render mode configuration determines where the providers need to live.

### Global interactive mode

```razor
@* App.razor *@
<Routes @rendermode="InteractiveServer" />
```

With global mode, providers in `MainLayout.razor` are enough.

### Per-page interactive mode

```razor
@* Each interactive page *@
@page "/users"
@rendermode InteractiveServer

<h1>Users</h1>
@* ... *@
```

With per-page mode, any interactive page needs its own `MudThemeProvider`, `MudPopoverProvider`, `MudDialogProvider`, `MudSnackbarProvider` — the static `MainLayout.razor` can't supply them because it's rendered statically and doesn't participate in the interactive render tree.

**Easiest fix:** create a `InteractiveLayout.razor` that mounts the providers, and use it as the layout on interactive pages:

```razor
@* Layout/InteractiveLayout.razor *@
@inherits LayoutComponentBase
@layout MainLayout

<MudThemeProvider />
<MudPopoverProvider />
<MudDialogProvider />
<MudSnackbarProvider />

@Body
```

```razor
@* Pages/Users.razor *@
@page "/users"
@rendermode InteractiveServer
@layout InteractiveLayout

<MudDataGrid T="User" Items="_users">...</MudDataGrid>
```

## Sanity check

After wiring everything up, drop this on a test page to verify:

```razor
@page "/mud-test"

<MudContainer>
    <MudText Typo="Typo.h4" Class="mb-4">MudBlazor works!</MudText>
    <MudButton Variant="Variant.Filled" Color="Color.Primary" OnClick="ShowSnackbar">
        Click me
    </MudButton>
</MudContainer>

@code {
    [Inject] private ISnackbar Snackbar { get; set; } = default!;

    private void ShowSnackbar()
    {
        Snackbar.Add("Hello from MudBlazor 9!", Severity.Success);
    }
}
```

If the button styles correctly and the snackbar shows, setup is good. If the button is unstyled, the CSS reference is wrong. If the snackbar doesn't appear, `MudSnackbarProvider` is missing from the render tree.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| MudBlazor components render unstyled | CSS reference missing or wrong path |
| `InvalidOperationException: Unable to find the required 'MudPopoverProvider'` | `MudPopoverProvider` not in render tree |
| `ISnackbar` injection fails | `AddMudServices()` not called |
| Menu inside dialog won't close | `MudDialogProvider` listed before `MudPopoverProvider` |
| Page doesn't respond to clicks | Missing `@rendermode InteractiveServer` on the page |
| Dropdowns appear but are mispositioned or clipped | `MudPopoverProvider` missing or rendered inside an element with `overflow: hidden` |
| Dialogs appear behind other content | Missing `MudDialogProvider` or a z-index override elsewhere in app CSS |

## Sources

- [MudBlazor NuGet](https://www.nuget.org/packages/MudBlazor)
- [MudBlazor Installation Docs](https://mudblazor.com/getting-started/installation)
- [Missing MudPopoverProvider discussion](https://github.com/MudBlazor/MudBlazor/discussions/9757)
