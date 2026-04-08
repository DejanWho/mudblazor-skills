# MudBlazor 9 — Theming

Customize colors, typography, spacing, and shadows via the `MudTheme` object. Dark mode is built in; toggling is straightforward but doesn't persist by default.

## The MudTheme object

`MudTheme` is a plain C# object with four main sub-objects:

- **`PaletteLight`** — colors for light mode
- **`PaletteDark`** — colors for dark mode
- **`Typography`** — font families and sizes
- **`LayoutProperties`** — border radius, drawer width, app bar height, etc.
- **`Shadows`** — the elevation ladder (elevation 0 through 25)
- **`ZIndex`** — z-index values for overlays

You pass a `MudTheme` instance to `MudThemeProvider`:

```razor
<MudThemeProvider Theme="_theme" @bind-IsDarkMode="_isDarkMode" />
```

## Custom theme

```csharp
private MudTheme _theme = new()
{
    PaletteLight = new PaletteLight
    {
        Primary = "#594AE2",
        Secondary = "#FF5722",
        AppbarBackground = "#594AE2",
        Background = "#F5F5F5",
        DrawerBackground = "#FFFFFF",
        DrawerText = "rgba(0, 0, 0, 0.7)",
        Surface = "#FFFFFF",
        TextPrimary = "rgba(0, 0, 0, 0.87)",
        TextSecondary = "rgba(0, 0, 0, 0.54)",
        ActionDefault = "rgba(0, 0, 0, 0.54)",
        ActionDisabled = "rgba(0, 0, 0, 0.26)",
        Divider = "rgba(0, 0, 0, 0.12)"
    },
    PaletteDark = new PaletteDark
    {
        Primary = "#7E6FFF",
        Secondary = "#FF7043",
        AppbarBackground = "#1E1E2E",
        Background = "#1A1A2E",
        DrawerBackground = "#1E1E2E",
        DrawerText = "rgba(255, 255, 255, 0.7)",
        Surface = "#27273C",
        TextPrimary = "rgba(255, 255, 255, 0.87)",
        TextSecondary = "rgba(255, 255, 255, 0.54)",
        ActionDefault = "rgba(255, 255, 255, 0.54)",
        ActionDisabled = "rgba(255, 255, 255, 0.26)",
        Divider = "rgba(255, 255, 255, 0.12)"
    },
    LayoutProperties = new LayoutProperties
    {
        DefaultBorderRadius = "6px",
        DrawerWidthLeft = "260px",
        AppbarHeight = "64px"
    },
    Typography = new Typography
    {
        Default = new DefaultTypography
        {
            FontFamily = new[] { "Inter", "Helvetica", "Arial", "sans-serif" },
            FontSize = "0.875rem",
            FontWeight = "400",
            LineHeight = "1.43",
            LetterSpacing = "0.01071em"
        },
        H1 = new H1Typography
        {
            FontSize = "6rem",
            FontWeight = "300",
            LineHeight = "1.167",
            LetterSpacing = "-0.01562em"
        },
        H4 = new H4Typography
        {
            FontSize = "2.125rem",
            FontWeight = "500",
            LineHeight = "1.235",
            LetterSpacing = "0.00735em"
        }
    }
};
```

> **v9 note:** `PaletteLight` / `PaletteDark` now use `Palette` as the base type (they still exist as distinct classes, but the property type on `MudTheme` is `Palette`). This is usually invisible to consumers.

## Important palette properties

These are the palette fields you'll touch most often:

```
Primary              Main brand color
PrimaryContrastText  Text color on top of Primary
Secondary            Secondary brand color
Tertiary
Info
Success
Warning
Error
Dark

AppbarBackground     Top bar bg
AppbarText

DrawerBackground     Sidebar bg
DrawerText
DrawerIcon

Background           Page bg
BackgroundGray       Slightly off-background (cards)
Surface              Cards, papers
TextPrimary          Main text color
TextSecondary        Muted text
TextDisabled         Disabled text

ActionDefault        Icon buttons, nav icons
ActionDisabled
ActionDisabledBackground

Divider              Borders between sections
DividerLight
TableLines           Between table rows
TableStriped         Stripe color
TableHover           Row hover

Skeleton             Skeleton placeholder color

LinesDefault         Input borders
LinesInputs
```

Each color supports lighten/darken variants (e.g., `PrimaryLighten`, `PrimaryDarken`) automatically computed from the base, but you can override them.

## Dark mode toggle (the minimum)

`MudThemeProvider` has an `IsDarkMode` parameter. Bind to it from a state field:

```razor
@* MainLayout.razor *@
<MudThemeProvider Theme="_theme" @bind-IsDarkMode="_isDarkMode" />
<MudPopoverProvider />
<MudDialogProvider />
<MudSnackbarProvider />

<MudLayout>
    <MudAppBar Elevation="1">
        <MudText Typo="Typo.h6">My App</MudText>
        <MudSpacer />
        <MudIconButton Icon="@(_isDarkMode ? Icons.Material.Filled.LightMode : Icons.Material.Filled.DarkMode)"
                       Color="Color.Inherit"
                       OnClick="ToggleDarkMode" />
    </MudAppBar>
    <MudMainContent Class="pa-4">
        @Body
    </MudMainContent>
</MudLayout>

@code {
    private MudTheme _theme = new();  // default theme
    private bool _isDarkMode;

    private void ToggleDarkMode() => _isDarkMode = !_isDarkMode;
}
```

## Following the OS preference

To start in whatever mode the user's OS prefers, use `MudThemeProvider`'s system dark-mode detection:

```razor
<MudThemeProvider @ref="_mudThemeProvider"
                  Theme="_theme"
                  @bind-IsDarkMode="_isDarkMode" />

@code {
    private MudThemeProvider _mudThemeProvider = default!;
    private MudTheme _theme = new();
    private bool _isDarkMode;

    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        if (firstRender)
        {
            _isDarkMode = await _mudThemeProvider.GetSystemDarkModeAsync();

            // Optionally listen for OS-level changes
            await _mudThemeProvider.WatchSystemDarkModeAsync(
                async isDark =>
                {
                    _isDarkMode = isDark;
                    await InvokeAsync(StateHasChanged);
                });

            StateHasChanged();
        }
    }
}
```

> **v9 note:** The method was renamed from `GetSystemPreference` / `WatchSystemPreference` / `SystemPreferenceChanged` to `GetSystemDarkModeAsync` / `WatchSystemDarkModeAsync` / `SystemDarkModeChangedAsync`.

## Persisting the user's choice

MudBlazor doesn't persist the dark-mode choice for you. Options:

### Option 1: Cookies (Blazor Server, simplest)

Read/write a cookie via an injected `IHttpContextAccessor` in a SignalR-free path (server-rendered initial load), or via JS interop in an interactive circuit.

### Option 2: localStorage via JS interop

```csharp
@inject IJSRuntime JS

protected override async Task OnAfterRenderAsync(bool firstRender)
{
    if (firstRender)
    {
        try
        {
            var saved = await JS.InvokeAsync<string?>("localStorage.getItem", "darkMode");
            if (saved is not null)
                _isDarkMode = saved == "true";
        }
        catch { /* prerender, ignore */ }

        StateHasChanged();
    }
}

private async Task ToggleDarkMode()
{
    _isDarkMode = !_isDarkMode;
    await JS.InvokeVoidAsync("localStorage.setItem", "darkMode", _isDarkMode.ToString().ToLower());
}
```

On a prerendering Blazor Server app, you'll see a brief flash of light mode before the JS call completes. There's no elegant fix without moving dark-mode state to a cookie the server reads at prerender time.

### Option 3: User profile / database

If the user has an account, store the preference server-side and load it in `OnInitializedAsync`.

## Using theme colors from code

The palette is exposed as CSS variables. If you need a theme color in your own CSS:

```css
.my-custom-element {
    background: var(--mud-palette-primary);
    color: var(--mud-palette-primary-text);
    border: 1px solid var(--mud-palette-divider);
}
```

Every palette property has a corresponding CSS variable: `--mud-palette-<property>` in kebab-case.

## Layout properties

```csharp
LayoutProperties = new LayoutProperties
{
    DefaultBorderRadius = "4px",    // MudPaper, buttons, inputs
    DrawerMiniWidthLeft = "56px",
    DrawerMiniWidthRight = "56px",
    DrawerWidthLeft = "240px",
    DrawerWidthRight = "240px",
    AppbarHeight = "64px"
}
```

These drive the CSS variables `--mud-default-borderradius`, `--mud-drawer-width-left`, etc.

## Shadows

The elevation ladder. Index 0 is no shadow; higher numbers are more lift. You usually don't override these, but you can:

```csharp
Shadows = new Shadow
{
    Elevation = new string[]
    {
        "none",
        "0 1px 3px 0 rgba(0,0,0,0.12)",
        "0 3px 6px 0 rgba(0,0,0,0.16)",
        // ... up to 25
    }
}
```

## Pre-built palettes (starter points)

MudBlazor's default theme is pleasant but distinctive. If you want a cleaner, more neutral look, start from one of these:

```csharp
// Neutral / professional
PaletteLight = new PaletteLight
{
    Primary = "#2563EB",       // blue
    Secondary = "#64748B",
    Background = "#F8FAFC",
    Surface = "#FFFFFF",
    AppbarBackground = "#FFFFFF",
    AppbarText = "#0F172A",
    DrawerBackground = "#FFFFFF",
    TextPrimary = "#0F172A",
    TextSecondary = "#64748B",
    Divider = "#E2E8F0"
}

// Warm / friendly
PaletteLight = new PaletteLight
{
    Primary = "#D97706",       // amber
    Secondary = "#7C2D12",
    Background = "#FFFBEB",
    Surface = "#FFFFFF",
    TextPrimary = "#1C1917",
    TextSecondary = "#78716C"
}
```

## Common mistakes

- **Forgetting to pass `Theme` to the provider.** Just `<MudThemeProvider />` uses defaults. You need `<MudThemeProvider Theme="_theme" />`.
- **Mutating the theme after render.** Palette properties are on the theme object; if you mutate them, you won't see the change until something triggers a re-render. Safer: swap the whole `_theme` instance.
- **Using hex codes in components.** `Style="color: #594AE2"` defeats theming. Use `Color="Color.Primary"`.
- **Assuming dark mode is persisted.** It's not. Persist it yourself if you care.

## Sources

- [MudBlazor Theming Overview](https://mudblazor.com/customization/overview)
- [MudTheme source](https://github.com/MudBlazor/MudBlazor/blob/dev/src/MudBlazor/Themes/MudTheme.cs)
- [MudBlazor ThemeManager example repo](https://github.com/MudBlazor/ThemeManager)
