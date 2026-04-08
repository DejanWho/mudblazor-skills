# MudBlazor 9 — MudDataGrid

The most feature-rich (and most complex) component in MudBlazor. Read this file whenever you need to build a data grid — even a "simple" one — because a lot of the footguns are in defaults.

## What it does

`MudDataGrid<T>` renders a table of `T` with optional sorting, filtering, paging, grouping, selection, editing, virtualization, and server-side data. It's typed, so columns have strongly-typed access to `T`'s properties.

## The minimum viable grid

```razor
<MudDataGrid T="User" Items="@_users">
    <Columns>
        <PropertyColumn Property="x => x.Id" Title="ID" />
        <PropertyColumn Property="x => x.Name" Title="Name" />
        <PropertyColumn Property="x => x.Email" Title="Email" />
    </Columns>
</MudDataGrid>

@code {
    private List<User> _users = new();

    protected override async Task OnInitializedAsync()
    {
        _users = await _userService.GetAllAsync();
    }

    public record User(int Id, string Name, string Email);
}
```

That's enough to render a sortable, no-filter, no-pagination grid. Everything else is opt-in.

**Type inference:** `T="User"` is technically optional when `Items` is typed, but setting it explicitly prevents annoying "the type cannot be inferred" errors in more complex scenarios.

## Column types

### PropertyColumn (most common)

Binds to a property of `T` via an expression. Automatically gets sort, filter, and header name from the property.

```razor
<PropertyColumn Property="x => x.Name" Title="Full name" />
<PropertyColumn Property="x => x.CreatedAt" Title="Created" Format="yyyy-MM-dd" />
<PropertyColumn Property="x => x.Price" Title="Price" Format="C" />
<PropertyColumn Property="x => x.IsActive" Title="Active" />
```

**Useful parameters:**
- `Title` — header text (defaults to property name)
- `Format` — standard .NET format string (`"yyyy-MM-dd"`, `"N2"`, `"C"`, `"P1"`)
- `Culture` — specific culture for formatting
- `Sortable="false"` / `Filterable="false"` — disable per-column
- `Hideable="false"` — prevent user from hiding
- `Editable="true"` — enable inline editing for this column
- `CellClass` / `CellStyle` — apply to every cell
- `HeaderClass` / `HeaderStyle` — apply to the header cell

### TemplateColumn (custom rendering)

When you need custom markup in the cell (badges, links, action buttons, conditional rendering), use `TemplateColumn`.

```razor
<TemplateColumn Title="Status" Sortable="false">
    <CellTemplate>
        @{
            var color = context.Item.IsActive ? Color.Success : Color.Default;
            var text = context.Item.IsActive ? "Active" : "Inactive";
        }
        <MudChip T="string" Color="@color" Size="Size.Small">@text</MudChip>
    </CellTemplate>
</TemplateColumn>

<TemplateColumn Title="Actions" Sortable="false" Filterable="false">
    <CellTemplate>
        <MudStack Row="true" Spacing="1">
            <MudIconButton Icon="@Icons.Material.Filled.Edit"
                           Size="Size.Small"
                           OnClick="@(() => EditUser(context.Item))" />
            <MudIconButton Icon="@Icons.Material.Filled.Delete"
                           Size="Size.Small"
                           Color="Color.Error"
                           OnClick="@(() => DeleteUser(context.Item))" />
        </MudStack>
    </CellTemplate>
</TemplateColumn>
```

`context.Item` is the row's `T`. `context.Value` only works if the column has a `Property` expression.

### ⚠️ TemplateColumn sorting/filtering gotcha

`TemplateColumn` by default has no `Property` expression, so:
- Sorting doesn't know which property to sort by
- Filtering has nothing to filter against
- In a `ServerData` scenario, the `GridState` reports the column by a GUID, not a property name

**Three ways to fix this:**

1. **Disable sort/filter** on the column (simplest if it's an action column):
```razor
<TemplateColumn Title="Actions" Sortable="false" Filterable="false">
```

2. **Give it a `SortBy` function** (for client-side sort):
```razor
<TemplateColumn Title="Full name"
                SortBy="@(x => $"{x.FirstName} {x.LastName}")">
    <CellTemplate>@context.Item.FirstName @context.Item.LastName</CellTemplate>
</TemplateColumn>
```

3. **Tag the column with the server sort key** (for `ServerData`):
```razor
<TemplateColumn Title="Name" Tag="@("name")">
    <CellTemplate>
        <MudLink Href="@($"/users/{context.Item.Id}")">@context.Item.Name</MudLink>
    </CellTemplate>
</TemplateColumn>
```

Then in your `ServerData` handler, read `state.SortDefinitions` and for any definition whose `SortBy` is a GUID, look up the column via `.Tag` to get the intended sort key.

### SelectColumn (row selection checkbox)

```razor
<SelectColumn T="User" />
```

Pairs with `MultiSelection="true"` on the grid.

### HierarchyColumn (master/detail rows)

```razor
<HierarchyColumn T="User" />
```

Pairs with a `<ChildRowContent>` template for the expanded content.

## Sorting

Sorting is on by default. Click a column header to sort; click again to reverse; click a third time to clear (`SortMode="SortMode.Multiple"` to allow multi-column sort).

```razor
<MudDataGrid T="User" Items="@_users" SortMode="SortMode.Multiple">
    <Columns>
        <PropertyColumn Property="x => x.Name" InitialDirection="SortDirection.Ascending" />
        <PropertyColumn Property="x => x.Email" />
    </Columns>
</MudDataGrid>
```

- `SortMode.Multiple` — shift-click headers to add secondary sort
- `SortMode.Single` — only one sort at a time (default)
- `SortMode.None` — no sorting

Use `InitialDirection` on a column to set the default sort.

## Filtering

There are two filter UIs:

```razor
<MudDataGrid T="User" Items="@_users" FilterMode="DataGridFilterMode.Simple">
```

- `DataGridFilterMode.Simple` — a single filter button in the toolbar that opens a dropdown
- `DataGridFilterMode.ColumnFilterMenu` — filter icons on each column header
- `DataGridFilterMode.ColumnFilterRow` — an inline row of filter inputs above the data

### Quick filter (free-text search across all columns)

```razor
<MudDataGrid T="User" Items="@_users" QuickFilter="@_quickFilter">
    <ToolBarContent>
        <MudTextField @bind-Value="_searchString"
                      Placeholder="Search..."
                      Adornment="Adornment.Start"
                      AdornmentIcon="@Icons.Material.Filled.Search"
                      IconSize="Size.Medium"
                      Class="mt-0" />
    </ToolBarContent>
    <Columns>
        <PropertyColumn Property="x => x.Name" />
        <PropertyColumn Property="x => x.Email" />
    </Columns>
</MudDataGrid>

@code {
    private string _searchString = "";

    private Func<User, bool> _quickFilter => user =>
    {
        if (string.IsNullOrWhiteSpace(_searchString))
            return true;
        if (user.Name.Contains(_searchString, StringComparison.OrdinalIgnoreCase))
            return true;
        if (user.Email.Contains(_searchString, StringComparison.OrdinalIgnoreCase))
            return true;
        return false;
    };
}
```

### Custom filter for a TemplateColumn

```razor
<TemplateColumn Title="Status">
    <CellTemplate>@context.Item.Status</CellTemplate>
    <FilterTemplate>
        <MudSelect T="string" @bind-Value="_statusFilter" Clearable="true">
            <MudSelectItem Value="@("active")">Active</MudSelectItem>
            <MudSelectItem Value="@("inactive")">Inactive</MudSelectItem>
        </MudSelect>
    </FilterTemplate>
</TemplateColumn>
```

## Paging

```razor
<MudDataGrid T="User" Items="@_users" RowsPerPage="20">
    <Columns>
        <PropertyColumn Property="x => x.Name" />
    </Columns>
    <PagerContent>
        <MudDataGridPager T="User"
                          PageSizeOptions="new[] { 10, 20, 50, 100 }"
                          InfoFormat="{first_item}-{last_item} of {all_items}" />
    </PagerContent>
</MudDataGrid>
```

`<MudDataGridPager T="User" />` inside `<PagerContent>` renders the pager bar at the bottom. `PageSizeOptions` controls the dropdown. `RowsPerPage` sets the initial page size.

## Server-side data

For tables bigger than a few thousand rows, you don't want to ship them all to the client. Use `ServerData` to paginate, sort, and filter server-side.

```razor
<MudDataGrid T="User" ServerData="LoadServerDataAsync" @ref="_grid">
    <ToolBarContent>
        <MudText Typo="Typo.h6">Users</MudText>
        <MudSpacer />
        <MudTextField @bind-Value="_searchString"
                      Placeholder="Search..."
                      Immediate="true"
                      DebounceInterval="300"
                      OnDebounceIntervalElapsed="@(() => _grid.ReloadServerData())" />
    </ToolBarContent>
    <Columns>
        <PropertyColumn Property="x => x.Id" Title="ID" />
        <PropertyColumn Property="x => x.Name" Title="Name" />
        <PropertyColumn Property="x => x.Email" Title="Email" />
        <PropertyColumn Property="x => x.CreatedAt" Title="Created" Format="yyyy-MM-dd" />
    </Columns>
    <PagerContent>
        <MudDataGridPager T="User" PageSizeOptions="new[] { 10, 25, 50, 100 }" />
    </PagerContent>
</MudDataGrid>

@code {
    private MudDataGrid<User> _grid = default!;
    private string _searchString = "";

    private async Task<GridData<User>> LoadServerDataAsync(
        GridState<User> state,
        CancellationToken cancellationToken)
    {
        // Build a query from the state
        var query = new UserQuery
        {
            Skip = state.Page * state.PageSize,
            Take = state.PageSize,
            Search = _searchString,
            SortBy = state.SortDefinitions.FirstOrDefault()?.SortBy,
            Descending = state.SortDefinitions.FirstOrDefault()?.Descending ?? false,
            Filters = state.FilterDefinitions.Select(MapFilter).ToList()
        };

        var result = await _userService.QueryAsync(query, cancellationToken);

        return new GridData<User>
        {
            Items = result.Items,
            TotalItems = result.TotalCount
        };
    }

    private UserFilter MapFilter(IFilterDefinition<User> filter)
    {
        return new UserFilter
        {
            Field = filter.Column?.PropertyName ?? "",
            Operator = filter.Operator ?? "contains",
            Value = filter.Value?.ToString() ?? ""
        };
    }
}
```

> **v9 change:** `ServerData` now takes a `CancellationToken`. **Pass it through to your data access layer** (EF Core's `ToListAsync(ct)`, HttpClient's `SendAsync(req, ct)`, etc.) so rapid filter changes actually cancel in-flight requests. Forgetting to forward the token means the grid cancels the await, but the database query keeps running.

### Reload server data after a mutation

```csharp
await _userService.CreateAsync(newUser);
await _grid.ReloadServerData();
```

## Selection

### Single row selection

```razor
<MudDataGrid T="User" Items="@_users"
             @bind-SelectedItem="_selectedUser">
    ...
</MudDataGrid>

@code {
    private User? _selectedUser;
}
```

### Multi-row selection

```razor
<MudDataGrid T="User" Items="@_users"
             MultiSelection="true"
             @bind-SelectedItems="_selectedUsers">
    <Columns>
        <SelectColumn T="User" />
        <PropertyColumn Property="x => x.Name" />
    </Columns>
</MudDataGrid>

@code {
    private HashSet<User> _selectedUsers = new();
}
```

`SelectOnRowClick="false"` if you want users to have to use the checkbox (instead of clicking anywhere on the row to select).

## Editing

Two modes: `Cell` (click a cell to edit) and `Form` (click a row to open an edit form).

```razor
<MudDataGrid T="User" Items="@_users"
             ReadOnly="false"
             EditMode="DataGridEditMode.Form"
             EditTrigger="DataGridEditTrigger.Manual"
             CommittedItemChanges="OnItemCommitted">
    <Columns>
        <PropertyColumn Property="x => x.Name" Editable="true" />
        <PropertyColumn Property="x => x.Email" Editable="true" />
        <PropertyColumn Property="x => x.CreatedAt" Editable="false" />
    </Columns>
</MudDataGrid>

@code {
    private async Task OnItemCommitted(User user)
    {
        await _userService.UpdateAsync(user);
        Snackbar.Add("Updated", Severity.Success);
    }
}
```

`EditMode`:
- `DataGridEditMode.Cell` — each cell becomes an input on click
- `DataGridEditMode.Form` — a form appears for the selected row

`EditTrigger`:
- `DataGridEditTrigger.Manual` — you start editing via code
- `DataGridEditTrigger.OnRowClick` — click a row to start editing

## Grouping

```razor
<MudDataGrid T="Order" Items="@_orders" Groupable="true" GroupBy="@_groupDefinition">
    <Columns>
        <PropertyColumn Property="x => x.CustomerName" Title="Customer" Grouping="true" />
        <PropertyColumn Property="x => x.Product" Title="Product" />
        <PropertyColumn Property="x => x.Quantity" Title="Quantity" />
        <PropertyColumn Property="x => x.Total" Title="Total" Format="C"
                        AggregateDefinition="_totalAggregate" />
    </Columns>
</MudDataGrid>

@code {
    private GridGroupDefinition<Order> _groupDefinition = new()
    {
        Grouping = true,
        Expandable = true,
        IsInitiallyExpanded = false
    };

    private AggregateDefinition<Order> _totalAggregate = new()
    {
        Type = AggregateType.Sum,
        DisplayFormat = "Total: {value:C}"
    };
}
```

`AggregateDefinition` supports `Count`, `Sum`, `Avg`, `Min`, `Max`, or `Custom` with a function.

## Virtualization

For very large datasets that you DO want to send client-side (say, 10k rows), virtualization prevents the grid from rendering all of them at once.

```razor
<MudDataGrid T="User" Items="@_users" Virtualize="true" FixedHeader="true" Height="600px">
    ...
</MudDataGrid>
```

`Virtualize="true"` renders only visible rows. Requires `FixedHeader="true"` and a set `Height` for the scroll container.

## Toolbar & custom headers

```razor
<MudDataGrid T="User" Items="@_users">
    <ToolBarContent>
        <MudText Typo="Typo.h6">Users</MudText>
        <MudSpacer />
        <MudButton Variant="Variant.Filled" Color="Color.Primary"
                   StartIcon="@Icons.Material.Filled.Add"
                   OnClick="OpenCreateDialog">
            New
        </MudButton>
    </ToolBarContent>
    <Columns>...</Columns>
    <NoRecordsContent>
        <MudStack AlignItems="AlignItems.Center" Class="pa-4">
            <MudIcon Icon="@Icons.Material.Filled.SearchOff" Size="Size.Large" />
            <MudText>No users found</MudText>
        </MudStack>
    </NoRecordsContent>
    <LoadingContent>
        <MudStack AlignItems="AlignItems.Center" Class="pa-4">
            <MudProgressCircular Indeterminate="true" />
            <MudText>Loading...</MudText>
        </MudStack>
    </LoadingContent>
</MudDataGrid>
```

Slots: `ToolBarContent`, `NoRecordsContent`, `LoadingContent`, `PagerContent`, `ChildRowContent` (for hierarchy), `FooterContent`.

## Styling rows conditionally

```razor
<MudDataGrid T="User" Items="@_users" RowClassFunc="@RowClassFunc">
    ...
</MudDataGrid>

@code {
    private string RowClassFunc(User user, int rowIndex)
    {
        if (!user.IsActive) return "inactive-row";
        if (user.Role == "admin") return "admin-row";
        return "";
    }
}

<style>
    ::deep .inactive-row { opacity: 0.6; }
    ::deep .admin-row { background: var(--mud-palette-primary-lighten); }
</style>
```

`RowStyleFunc` is the inline-style equivalent if you prefer.

## Column resize & reorder

```razor
<MudDataGrid T="User" Items="@_users"
             ColumnResizeMode="ResizeMode.Column"
             DragDropColumnReordering="true">
    ...
</MudDataGrid>
```

## MudTable vs MudDataGrid

Use `MudTable<T>` for simple displays without filter/sort UI. Use `MudDataGrid<T>` when you want real data-table features. For anything a user will interact with (filter, sort, paginate, select, edit), `MudDataGrid` is the right choice — don't build those features on top of `MudTable`.

## Checklist when building a grid

- [ ] Set `T="YourType"` explicitly
- [ ] Decide: client-side `Items` or server-side `ServerData`?
- [ ] For server-side: forward the `CancellationToken` through to the data layer
- [ ] Add a `<MudDataGridPager T="YourType" />` inside `<PagerContent>` if the grid can have more than one page
- [ ] Set `Sortable="false"` / `Filterable="false"` on action columns
- [ ] Set `InitialDirection` on the column you want sorted by default
- [ ] Provide `<NoRecordsContent>` and `<LoadingContent>` for empty/loading states
- [ ] If using `TemplateColumn` with server sort, tag the column or provide a `SortBy`/`Tag`
- [ ] For very large client datasets, set `Virtualize="true" FixedHeader="true" Height="Npx"`

## Sources

- [MudDataGrid docs](https://mudblazor.com/components/datagrid)
- [ServerData + TemplateColumn sorting discussion](https://github.com/MudBlazor/MudBlazor/discussions/7701)
- [PropertyColumn source](https://github.com/MudBlazor/MudBlazor/blob/dev/src/MudBlazor/Components/DataGrid/PropertyColumn.cs)
