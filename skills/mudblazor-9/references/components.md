# MudBlazor 9 — Components & layout

The components you'll reach for 80% of the time when building pages. This is not an exhaustive catalog — it's the practical toolkit.

## The core enums

Keep these in mind; they appear on nearly every component.

```csharp
// Color enum
Color.Default, Color.Primary, Color.Secondary, Color.Tertiary,
Color.Info, Color.Success, Color.Warning, Color.Error,
Color.Dark, Color.Inherit, Color.Transparent, Color.Surface

// Variant enum
Variant.Filled, Variant.Outlined, Variant.Text

// Size enum
Size.Small, Size.Medium, Size.Large

// Typo enum (for MudText)
Typo.h1, Typo.h2, Typo.h3, Typo.h4, Typo.h5, Typo.h6,
Typo.subtitle1, Typo.subtitle2,
Typo.body1, Typo.body2,
Typo.button, Typo.caption, Typo.overline,
Typo.inherit

// Elevation: 0..25 (0 = no shadow, higher = more lift)

// Breakpoint (for MudHidden, MudGrid)
Breakpoint.Xs, Sm, Md, Lg, Xl, Xxl, None, Always
SmAndDown, MdAndDown, LgAndDown, SmAndUp, MdAndUp, LgAndUp
```

## Spacing & utility classes

MudBlazor ships with Tailwind-ish utility classes. Use `Class="..."` on any component.

```
ma-N        margin: N (all sides; N = 0..16)
mt-N, mb-N  margin-top, margin-bottom
ml-N, mr-N  margin-left, margin-right
mx-N, my-N  margin horizontal/vertical
pa-N        padding (same pattern as ma)
pt-N, pb-N, px-N, py-N ...

gap-N       flex/grid gap

d-flex              display: flex
d-inline-flex       display: inline-flex
d-block             display: block
d-none              display: none
flex-row            flex-direction: row
flex-column         flex-direction: column
align-center        align-items: center
align-start         align-items: flex-start
align-end           align-items: flex-end
justify-center      justify-content: center
justify-start       justify-content: flex-start
justify-end         justify-content: flex-end
justify-space-between
justify-space-around
flex-grow-1         flex-grow: 1
flex-shrink-0       flex-shrink: 0

text-center, text-left, text-right
text-wrap, text-nowrap, text-truncate

w-100, h-100                  width/height: 100%
```

Responsive variants: `mt-md-4` = `margin-top: 16px` starting at `md` breakpoint.

## Layout shell

The canonical Blazor Server app layout with MudBlazor.

```razor
@inherits LayoutComponentBase

<MudLayout>
    <MudAppBar Elevation="1">
        <MudIconButton Icon="@Icons.Material.Filled.Menu"
                       Color="Color.Inherit"
                       Edge="Edge.Start"
                       OnClick="@(() => _drawerOpen = !_drawerOpen)" />
        <MudText Typo="Typo.h6" Class="ml-3">Dashboard</MudText>
        <MudSpacer />
        <MudIconButton Icon="@Icons.Material.Filled.Notifications" Color="Color.Inherit" />
        <MudMenu Icon="@Icons.Material.Filled.AccountCircle" Color="Color.Inherit">
            <MudMenuItem>Profile</MudMenuItem>
            <MudMenuItem>Sign out</MudMenuItem>
        </MudMenu>
    </MudAppBar>

    <MudDrawer @bind-Open="_drawerOpen"
               Elevation="1"
               Variant="DrawerVariant.Responsive"
               ClipMode="DrawerClipMode.Always">
        <MudDrawerHeader>
            <MudText Typo="Typo.h6">Menu</MudText>
        </MudDrawerHeader>
        <MudNavMenu>
            <MudNavLink Href="/" Match="NavLinkMatch.All"
                        Icon="@Icons.Material.Filled.Dashboard">
                Home
            </MudNavLink>
            <MudNavLink Href="/users" Icon="@Icons.Material.Filled.People">
                Users
            </MudNavLink>
            <MudNavGroup Title="Reports" Icon="@Icons.Material.Filled.Assessment">
                <MudNavLink Href="/reports/sales">Sales</MudNavLink>
                <MudNavLink Href="/reports/inventory">Inventory</MudNavLink>
            </MudNavGroup>
        </MudNavMenu>
    </MudDrawer>

    <MudMainContent Class="pa-4">
        <MudContainer MaxWidth="MaxWidth.Large">
            @Body
        </MudContainer>
    </MudMainContent>
</MudLayout>

@code {
    private bool _drawerOpen = true;
}
```

`MudLayout` + `MudAppBar` + `MudDrawer` + `MudMainContent` is the Material-app-shell shape. `MudContainer` inside `MudMainContent` gives you max-width constraints for comfortable reading on wide screens.

### Drawer variants

- `DrawerVariant.Responsive` — drawer collapses on small screens, visible on large
- `DrawerVariant.Temporary` — modal drawer that opens over content
- `DrawerVariant.Persistent` — drawer pushes content when open
- `DrawerVariant.Mini` — narrow drawer showing only icons

## Grid layout

MudBlazor's 12-column responsive grid. Use for two-column, three-column, dashboard layouts — anything that needs to reflow on small screens.

```razor
<MudGrid Spacing="4">
    <MudItem xs="12" sm="6" md="4">
        <MudCard>
            <MudCardContent>
                <MudText Typo="Typo.h6">Card 1</MudText>
                <MudText Typo="Typo.body2">Description</MudText>
            </MudCardContent>
        </MudCard>
    </MudItem>
    <MudItem xs="12" sm="6" md="4">
        <MudCard>...</MudCard>
    </MudItem>
    <MudItem xs="12" sm="12" md="4">
        <MudCard>...</MudCard>
    </MudItem>
</MudGrid>
```

`xs="12"` means "full width on extra-small screens," `md="4"` means "one third on medium+." Breakpoint params: `xs`, `sm`, `md`, `lg`, `xl`, `xxl`.

## Stacks (flex shortcuts)

`MudStack` is a shortcut for flex containers. Prefer it over manual `d-flex` classes when you just want things laid out in a row or column with gaps.

```razor
<MudStack Row="true" Spacing="2" AlignItems="AlignItems.Center">
    <MudIcon Icon="@Icons.Material.Filled.Person" />
    <MudText Typo="Typo.body1">John Doe</MudText>
    <MudSpacer />
    <MudButton Variant="Variant.Outlined" Color="Color.Primary">Edit</MudButton>
</MudStack>

<MudStack Spacing="2">  @* column by default *@
    <MudTextField Label="Name" @bind-Value="_name" />
    <MudTextField Label="Email" @bind-Value="_email" />
</MudStack>
```

`MudSpacer` is a zero-size element with `flex-grow: 1` — pushes following items to the right (or bottom).

## Typography

Use `MudText`, not raw `<p>` / `<h1>` / `<span>`. Typography inherits from the theme.

```razor
<MudText Typo="Typo.h4" GutterBottom="true">Page title</MudText>
<MudText Typo="Typo.subtitle1" Color="Color.Secondary">Page subtitle</MudText>
<MudText Typo="Typo.body1">Body paragraph.</MudText>
<MudText Typo="Typo.body2" Color="Color.Error">Error inline text.</MudText>
<MudText Typo="Typo.caption">12px caption.</MudText>
```

`Align="Align.Center"`, `Align.Left`, `Align.Right`, `Align.Justify` for alignment.

## Buttons

```razor
@* Primary action *@
<MudButton Variant="Variant.Filled" Color="Color.Primary" OnClick="Save">
    Save
</MudButton>

@* Secondary action *@
<MudButton Variant="Variant.Outlined" Color="Color.Primary">Cancel</MudButton>

@* Tertiary / low-emphasis *@
<MudButton Variant="Variant.Text">Learn more</MudButton>

@* Icon + text *@
<MudButton Variant="Variant.Filled"
           Color="Color.Primary"
           StartIcon="@Icons.Material.Filled.Save">
    Save
</MudButton>

@* Icon only *@
<MudIconButton Icon="@Icons.Material.Filled.Delete"
               Color="Color.Error"
               Size="Size.Small"
               OnClick="Delete" />

@* Floating action button *@
<MudFab Color="Color.Primary"
        StartIcon="@Icons.Material.Filled.Add"
        Label="Add" />

@* Toggle button *@
<MudToggleIconButton @bind-Toggled="_starred"
                     Icon="@Icons.Material.Filled.StarBorder"
                     ToggledIcon="@Icons.Material.Filled.Star"
                     ToggledColor="Color.Warning" />

@* Disabled state *@
<MudButton Variant="Variant.Filled" Disabled="@_isSaving">
    @(_isSaving ? "Saving..." : "Save")
</MudButton>
```

## Cards & surfaces

```razor
<MudCard>
    <MudCardHeader>
        <CardHeaderContent>
            <MudText Typo="Typo.h6">User Details</MudText>
            <MudText Typo="Typo.caption">Last updated 2 hours ago</MudText>
        </CardHeaderContent>
        <CardHeaderActions>
            <MudIconButton Icon="@Icons.Material.Filled.MoreVert" />
        </CardHeaderActions>
    </MudCardHeader>
    <MudCardContent>
        <MudText>John Doe</MudText>
        <MudText Typo="Typo.body2">john@example.com</MudText>
    </MudCardContent>
    <MudCardActions>
        <MudButton Variant="Variant.Text" Color="Color.Primary">Edit</MudButton>
        <MudButton Variant="Variant.Text" Color="Color.Error">Delete</MudButton>
    </MudCardActions>
</MudCard>
```

`MudPaper` is the primitive surface — use it for generic container panels that don't need the card's header/content/actions structure:

```razor
<MudPaper Elevation="2" Class="pa-4">
    <MudText Typo="Typo.h6">Settings</MudText>
    <MudText>...</MudText>
</MudPaper>

@* Outlined (no shadow) *@
<MudPaper Outlined="true" Class="pa-4">...</MudPaper>
```

## Lists

```razor
<MudList T="string" Clickable="true" @bind-SelectedValue="_selected">
    <MudListItem T="string" Value="@("inbox")" Icon="@Icons.Material.Filled.Inbox">
        Inbox
        <MudBadge Content="12" Color="Color.Primary" Class="ml-auto" />
    </MudListItem>
    <MudListItem T="string" Value="@("sent")" Icon="@Icons.Material.Filled.Send">
        Sent
    </MudListItem>
    <MudListItem T="string" Value="@("drafts")" Icon="@Icons.Material.Filled.Drafts">
        Drafts
    </MudListItem>
</MudList>
```

`MudList` is strongly-typed via `T=`. `Value` sets the item's selection key. `@bind-SelectedValue` gives you two-way binding on the selection.

## Chips

```razor
<MudChip T="string" Color="Color.Primary">Primary</MudChip>
<MudChip T="string" Color="Color.Success" Variant="Variant.Outlined">Active</MudChip>
<MudChip T="string" Icon="@Icons.Material.Filled.Star" Color="Color.Warning">Featured</MudChip>
<MudChip T="string" OnClose="@(() => RemoveTag())">Removable</MudChip>
```

## Alerts

```razor
<MudAlert Severity="Severity.Info">This is informational.</MudAlert>
<MudAlert Severity="Severity.Success" Variant="Variant.Filled">Saved successfully.</MudAlert>
<MudAlert Severity="Severity.Warning" Variant="Variant.Outlined">Heads up.</MudAlert>
<MudAlert Severity="Severity.Error"
          ShowCloseIcon="true"
          CloseIconClicked="@(() => _errorVisible = false)">
    Something went wrong.
</MudAlert>
```

## Tabs

```razor
<MudTabs Elevation="1" Rounded="true" ApplyEffectsToContainer="true" PanelClass="pa-4">
    <MudTabPanel Text="Overview" Icon="@Icons.Material.Filled.Info">
        <MudText>Overview content</MudText>
    </MudTabPanel>
    <MudTabPanel Text="Details" Icon="@Icons.Material.Filled.Description">
        <MudText>Details content</MudText>
    </MudTabPanel>
    <MudTabPanel Text="History" BadgeData="3" BadgeColor="Color.Error">
        <MudText>History content</MudText>
    </MudTabPanel>
</MudTabs>
```

> **v9 note:** The `PanelClass` on `MudTabs` styles the panel wrapper; use `TabButtonsClass` for the tab buttons. On `MudTabPanel`, `Class` only styles the button — use the new `PanelClass` for the panel content.

## Breakpoints & responsive hiding

```razor
<MudHidden Breakpoint="Breakpoint.SmAndDown">
    <MudText>Only visible on md and up</MudText>
</MudHidden>

<MudHidden Breakpoint="Breakpoint.MdAndUp" Invert="true">
    <MudText>Only visible on md and up (inverted)</MudText>
</MudHidden>
```

For dynamic responsive behavior, inject `IBreakpointService`:

```csharp
@inject IBreakpointService BreakpointService

@code {
    protected override async Task OnInitializedAsync()
    {
        var current = await BreakpointService.GetBreakpointAsync();
        // ...
        await BreakpointService.SubscribeAsync(async b =>
        {
            // react to changes
            await InvokeAsync(StateHasChanged);
        });
    }
}
```

## Icons

Icons are SVG string constants. Four families: `Filled`, `Outlined`, `Rounded`, `Sharp`, `TwoTone`.

```razor
<MudIcon Icon="@Icons.Material.Filled.Home" />
<MudIcon Icon="@Icons.Material.Outlined.Settings" Color="Color.Primary" Size="Size.Large" />
<MudIcon Icon="@Icons.Custom.Brands.GitHub" />  @* Brand icons *@
```

Custom brand icons live in `Icons.Custom.Brands.*`. There are also `Icons.Custom.FileFormats.*` and `Icons.Custom.Uncategorized.*`.

## Progress

```razor
<MudProgressCircular Color="Color.Primary" Indeterminate="true" />
<MudProgressCircular Color="Color.Success" Value="75" />

<MudProgressLinear Color="Color.Primary" Indeterminate="true" Class="my-4" />
<MudProgressLinear Color="Color.Info" Value="60" Buffer="true" BufferValue="80" />
```

## Skeletons (loading placeholders)

```razor
@if (_loading)
{
    <MudSkeleton SkeletonType="SkeletonType.Text" Width="60%" />
    <MudSkeleton SkeletonType="SkeletonType.Rectangle" Height="100px" />
    <MudSkeleton SkeletonType="SkeletonType.Circle" Width="40px" Height="40px" />
}
else
{
    @* real content *@
}
```

## Tooltips

```razor
<MudTooltip Text="Save changes" Placement="Placement.Top">
    <MudIconButton Icon="@Icons.Material.Filled.Save" OnClick="Save" />
</MudTooltip>
```

## Breadcrumbs

```razor
<MudBreadcrumbs Items="_breadcrumbs"></MudBreadcrumbs>

@code {
    private List<BreadcrumbItem> _breadcrumbs = new()
    {
        new BreadcrumbItem("Home", href: "/"),
        new BreadcrumbItem("Users", href: "/users"),
        new BreadcrumbItem("John Doe", href: null, disabled: true)
    };
}
```

## Full page example

A realistic "list of users" page tying several components together:

```razor
@page "/users"
@rendermode InteractiveServer

<PageTitle>Users</PageTitle>

<MudStack Row="true" AlignItems="AlignItems.Center" Class="mb-4">
    <MudText Typo="Typo.h4">Users</MudText>
    <MudSpacer />
    <MudButton Variant="Variant.Filled"
               Color="Color.Primary"
               StartIcon="@Icons.Material.Filled.Add"
               OnClick="OpenCreateDialog">
        New User
    </MudButton>
</MudStack>

<MudBreadcrumbs Items="@_breadcrumbs" Class="mb-4" />

<MudGrid>
    <MudItem xs="12" md="3">
        <MudPaper Class="pa-4" Elevation="1">
            <MudText Typo="Typo.h6">Filters</MudText>
            <MudTextField @bind-Value="_search"
                          Label="Search"
                          Variant="Variant.Outlined"
                          Adornment="Adornment.Start"
                          AdornmentIcon="@Icons.Material.Filled.Search"
                          Class="mt-3" />
            <MudSelect T="string" @bind-Value="_role" Label="Role" Variant="Variant.Outlined" Class="mt-3">
                <MudSelectItem Value="@("")">All</MudSelectItem>
                <MudSelectItem Value="@("admin")">Admin</MudSelectItem>
                <MudSelectItem Value="@("user")">User</MudSelectItem>
            </MudSelect>
        </MudPaper>
    </MudItem>
    <MudItem xs="12" md="9">
        @* Data grid would go here - see data-grid.md *@
    </MudItem>
</MudGrid>

@code {
    private string _search = "";
    private string _role = "";

    private List<BreadcrumbItem> _breadcrumbs = new()
    {
        new BreadcrumbItem("Home", href: "/"),
        new BreadcrumbItem("Users", href: null, disabled: true)
    };

    private Task OpenCreateDialog() => Task.CompletedTask;
}
```
