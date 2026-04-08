# MudBlazor 9 — Forms, validation, dialogs & snackbars

This covers the pieces you'll use to collect and validate user input: form inputs, the two validation strategies, dialogs, and toast notifications.

## Input components

All MudBlazor inputs use `@bind-Value` for two-way binding. They expose `Value` + `ValueChanged` so `@bind-Value` wires both.

```razor
@* Text *@
<MudTextField @bind-Value="_name" Label="Name" Variant="Variant.Outlined" />
<MudTextField @bind-Value="_bio" Label="Bio" Lines="4" Variant="Variant.Outlined" />
<MudTextField @bind-Value="_password" Label="Password" InputType="InputType.Password"
              Adornment="Adornment.End"
              AdornmentIcon="@Icons.Material.Filled.Visibility"
              OnAdornmentClick="TogglePasswordVisibility" />

@* Number *@
<MudNumericField @bind-Value="_age" Label="Age" Min="0" Max="150" Step="1" />
<MudNumericField @bind-Value="_price" Label="Price" Format="N2" HideSpinButtons="true" />

@* Select (single) *@
<MudSelect T="string" @bind-Value="_country" Label="Country" Variant="Variant.Outlined">
    <MudSelectItem Value="@("US")">United States</MudSelectItem>
    <MudSelectItem Value="@("CA")">Canada</MudSelectItem>
    <MudSelectItem Value="@("MX")">Mexico</MudSelectItem>
</MudSelect>

@* Select (multi) *@
<MudSelect T="string" Label="Tags" MultiSelection="true"
           @bind-SelectedValues="_tags"
           Variant="Variant.Outlined">
    <MudSelectItem Value="@("urgent")">Urgent</MudSelectItem>
    <MudSelectItem Value="@("internal")">Internal</MudSelectItem>
    <MudSelectItem Value="@("customer")">Customer-facing</MudSelectItem>
</MudSelect>

@* Autocomplete *@
<MudAutocomplete T="string" Label="Search users"
                 SearchFunc="SearchUsersAsync"
                 @bind-Value="_selectedUser"
                 Variant="Variant.Outlined"
                 ResetValueOnEmptyText="true"
                 CoerceText="true"
                 CoerceValue="true" />

@* Checkbox *@
<MudCheckBox T="bool" @bind-Value="_agreeToTerms" Label="I agree to the terms" />

@* Switch *@
<MudSwitch T="bool" @bind-Value="_notifications" Label="Enable notifications" Color="Color.Primary" />

@* Radio *@
<MudRadioGroup T="string" @bind-Value="_priority">
    <MudRadio Value="@("low")" Color="Color.Info">Low</MudRadio>
    <MudRadio Value="@("medium")" Color="Color.Warning">Medium</MudRadio>
    <MudRadio Value="@("high")" Color="Color.Error">High</MudRadio>
</MudRadioGroup>

@* Date picker *@
<MudDatePicker @bind-Date="_startDate" Label="Start date"
               Variant="Variant.Outlined"
               DateFormat="yyyy-MM-dd" />

@* Date range picker *@
<MudDateRangePicker @bind-DateRange="_dateRange" Label="Date range" />

@* Time picker *@
<MudTimePicker @bind-Time="_appointmentTime" Label="Appointment time" />

@* Slider *@
<MudSlider T="int" @bind-Value="_volume" Min="0" Max="100" Step="5" Color="Color.Primary">
    Volume: @_volume
</MudSlider>

@* Color picker *@
<MudColorPicker @bind-Text="_brandColor" Label="Brand color" />

@* File upload *@
<MudFileUpload T="IReadOnlyList<IBrowserFile>"
               @bind-Files="_files"
               MaximumFileCount="5"
               DragAndDrop="true"
               Dragging="@_isDragging">
    <CustomContent Context="fileUpload">
        <MudPaper Outlined="true" Class="pa-4">
            <MudStack AlignItems="AlignItems.Center">
                <MudIcon Icon="@Icons.Material.Filled.CloudUpload" Size="Size.Large" />
                <MudText>Drag files here or
                    <MudLink OnClick="@fileUpload.OpenFilePickerAsync">browse</MudLink>
                </MudText>
            </MudStack>
        </MudPaper>
    </CustomContent>
</MudFileUpload>
```

> **v9 note:** `MudFileUpload` uses `<CustomContent Context="...">` (not `<ActivationContent>`) and requires an explicit `OpenFilePickerAsync()` call to open the picker. Auto-open is gone.

### Autocomplete with async search

```razor
@code {
    private async Task<IEnumerable<string>> SearchUsersAsync(string value, CancellationToken ct)
    {
        if (string.IsNullOrWhiteSpace(value))
            return Array.Empty<string>();

        var results = await _userService.SearchAsync(value, ct);
        return results.Select(u => u.Name);
    }
}
```

Note the `CancellationToken` — the autocomplete cancels in-flight searches when the user types again, so pass the token through to your data source.

## Validation: two strategies

MudBlazor supports two validation approaches. **Pick one, not both**, and use it consistently across a form.

### Option A: EditForm + DataAnnotations (recommended for simple forms)

Use this if your model already has `[Required]`, `[EmailAddress]`, `[StringLength]` etc. attributes. Blazor's built-in validation handles everything.

```razor
@page "/users/new"
@rendermode InteractiveServer

<MudText Typo="Typo.h4" GutterBottom="true">Create user</MudText>

<EditForm Model="@_model" OnValidSubmit="HandleValidSubmit">
    <DataAnnotationsValidator />

    <MudGrid>
        <MudItem xs="12">
            <MudTextField @bind-Value="_model.Name"
                          For="@(() => _model.Name)"
                          Label="Name"
                          Variant="Variant.Outlined"
                          Required="true"
                          RequiredError="Name is required" />
        </MudItem>
        <MudItem xs="12">
            <MudTextField @bind-Value="_model.Email"
                          For="@(() => _model.Email)"
                          Label="Email"
                          Variant="Variant.Outlined"
                          Required="true" />
        </MudItem>
        <MudItem xs="12" sm="6">
            <MudSelect T="string" @bind-Value="_model.Role"
                       For="@(() => _model.Role)"
                       Label="Role"
                       Variant="Variant.Outlined">
                <MudSelectItem Value="@("admin")">Admin</MudSelectItem>
                <MudSelectItem Value="@("user")">User</MudSelectItem>
            </MudSelect>
        </MudItem>
        <MudItem xs="12">
            <MudButton ButtonType="ButtonType.Submit"
                       Variant="Variant.Filled"
                       Color="Color.Primary">
                Save
            </MudButton>
        </MudItem>
    </MudGrid>
</EditForm>

@code {
    private CreateUserModel _model = new();

    private async Task HandleValidSubmit()
    {
        await _userService.CreateAsync(_model);
        Snackbar.Add("User created", Severity.Success);
        _model = new();
    }

    public class CreateUserModel
    {
        [Required(ErrorMessage = "Name is required")]
        [StringLength(100, MinimumLength = 2)]
        public string Name { get; set; } = "";

        [Required]
        [EmailAddress]
        public string Email { get; set; } = "";

        [Required]
        public string Role { get; set; } = "user";
    }
}
```

**Key points:**
- Wrap inputs in `<EditForm Model="...">`.
- Add `<DataAnnotationsValidator />` as the first child.
- Every input needs `For="@(() => _model.Property)"` so the validator knows which field it's validating.
- Submit buttons need `ButtonType="ButtonType.Submit"` — don't call `OnClick`.
- `OnValidSubmit` fires only when validation passes; `OnInvalidSubmit` fires otherwise.
- **Don't wrap `EditForm` in `MudForm`.** They're two different validation systems.

### Option B: MudForm + FluentValidation (for complex cross-field rules)

Use this if you have rules that DataAnnotations can't express cleanly — cross-field validation ("confirm password must match password"), database uniqueness checks, or conditional validation.

First install the helper package:
```bash
dotnet add package Blazored.FluentValidation
```

Write the validator:

```csharp
public class CreateUserValidator : AbstractValidator<CreateUserModel>
{
    public CreateUserValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Name is required")
            .MaximumLength(100);

        RuleFor(x => x.Email)
            .NotEmpty().EmailAddress();

        RuleFor(x => x.Password)
            .NotEmpty().MinimumLength(8)
            .Matches("[A-Z]").WithMessage("Must contain an uppercase letter")
            .Matches("[0-9]").WithMessage("Must contain a digit");

        RuleFor(x => x.ConfirmPassword)
            .Equal(x => x.Password).WithMessage("Passwords must match");
    }

    // MudForm uses this signature
    public Func<object, string, Task<IEnumerable<string>>> ValidateValue => async (model, propertyName) =>
    {
        var result = await ValidateAsync(
            ValidationContext<CreateUserModel>.CreateWithOptions((CreateUserModel)model,
                x => x.IncludeProperties(propertyName)));

        if (result.IsValid)
            return Array.Empty<string>();
        return result.Errors.Select(e => e.ErrorMessage);
    };
}
```

Use it in a `MudForm`:

```razor
<MudForm @ref="_form" Model="@_model" @bind-IsValid="_isValid" @bind-Errors="_errors">
    <MudTextField @bind-Value="_model.Name"
                  Label="Name"
                  For="@(() => _model.Name)"
                  Validation="@(_validator.ValidateValue)" />

    <MudTextField @bind-Value="_model.Email"
                  Label="Email"
                  For="@(() => _model.Email)"
                  Validation="@(_validator.ValidateValue)" />

    <MudTextField @bind-Value="_model.Password"
                  Label="Password"
                  InputType="InputType.Password"
                  For="@(() => _model.Password)"
                  Validation="@(_validator.ValidateValue)" />

    <MudTextField @bind-Value="_model.ConfirmPassword"
                  Label="Confirm password"
                  InputType="InputType.Password"
                  For="@(() => _model.ConfirmPassword)"
                  Validation="@(_validator.ValidateValue)" />

    <MudButton Variant="Variant.Filled" Color="Color.Primary" OnClick="SubmitAsync" Disabled="!_isValid">
        Save
    </MudButton>
</MudForm>

@code {
    private MudForm _form = default!;
    private CreateUserModel _model = new();
    private CreateUserValidator _validator = new();
    private bool _isValid;
    private string[] _errors = Array.Empty<string>();

    private async Task SubmitAsync()
    {
        await _form.Validate();
        if (!_isValid) return;

        await _userService.CreateAsync(_model);
        Snackbar.Add("User created", Severity.Success);
    }
}
```

**Key points:**
- `MudForm` doesn't have a submit event. You call `.Validate()` from a button click and check `IsValid`.
- Each field's `Validation` parameter points at your validator function.
- `@bind-IsValid` gives you a reactive flag for disabling the submit button.
- Works fine without FluentValidation too — `Validation` accepts any `Func<T, Task<IEnumerable<string>>>` or sync equivalents.

### Quick pattern comparison

| | EditForm + DataAnnotations | MudForm + FluentValidation |
|---|---|---|
| Best for | Simple rules on model properties | Cross-field, conditional, DB-backed rules |
| Submit trigger | `OnValidSubmit` event | Manual `.Validate()` call |
| Input parameter | `For="@(() => model.X)"` | `For=...` + `Validation=...` |
| Button type | `ButtonType.Submit` | `OnClick` (regular button) |
| Nested models | Works | Works |

## Dialogs

Dialogs are separate Razor components that inherit the dialog context from a parent, opened via `IDialogService`.

### Inject the service

```razor
@inject IDialogService DialogService
```

### Simple confirmation dialog

```razor
@code {
    private async Task DeleteUserAsync(User user)
    {
        var parameters = new DialogParameters<ConfirmDialog>
        {
            { x => x.ContentText, $"Delete user {user.Name}? This cannot be undone." },
            { x => x.ButtonText, "Delete" },
            { x => x.Color, Color.Error }
        };

        var options = new DialogOptions { CloseOnEscapeKey = true };

        var dialog = await DialogService.ShowAsync<ConfirmDialog>("Confirm delete", parameters, options);
        var result = await dialog.Result;

        if (!result.Canceled)
        {
            await _userService.DeleteAsync(user.Id);
            Snackbar.Add("User deleted", Severity.Success);
        }
    }
}
```

The `ConfirmDialog.razor`:

```razor
<MudDialog>
    <DialogContent>
        <MudText>@ContentText</MudText>
    </DialogContent>
    <DialogActions>
        <MudButton OnClick="Cancel">Cancel</MudButton>
        <MudButton Variant="Variant.Filled" Color="@Color" OnClick="Submit">@ButtonText</MudButton>
    </DialogActions>
</MudDialog>

@code {
    [CascadingParameter] private IMudDialogInstance MudDialog { get; set; } = default!;

    [Parameter] public string ContentText { get; set; } = "";
    [Parameter] public string ButtonText { get; set; } = "OK";
    [Parameter] public Color Color { get; set; } = Color.Primary;

    private void Submit() => MudDialog.Close(DialogResult.Ok(true));
    private void Cancel() => MudDialog.Cancel();
}
```

### Dialog that returns data

```razor
@* EditUserDialog.razor *@
<MudDialog>
    <DialogContent>
        <MudTextField @bind-Value="_model.Name" Label="Name" />
        <MudTextField @bind-Value="_model.Email" Label="Email" />
    </DialogContent>
    <DialogActions>
        <MudButton OnClick="Cancel">Cancel</MudButton>
        <MudButton Color="Color.Primary" Variant="Variant.Filled" OnClick="Save">Save</MudButton>
    </DialogActions>
</MudDialog>

@code {
    [CascadingParameter] private IMudDialogInstance MudDialog { get; set; } = default!;

    [Parameter] public User User { get; set; } = default!;

    private EditUserModel _model = new();

    protected override void OnInitialized()
    {
        _model = new EditUserModel { Name = User.Name, Email = User.Email };
    }

    private void Save() => MudDialog.Close(DialogResult.Ok(_model));
    private void Cancel() => MudDialog.Cancel();
}
```

Opening it from the parent page:

```csharp
var parameters = new DialogParameters<EditUserDialog>
{
    { x => x.User, user }
};

var dialog = await DialogService.ShowAsync<EditUserDialog>("Edit user", parameters);
var result = await dialog.Result;

if (!result.Canceled && result.Data is EditUserModel updated)
{
    user.Name = updated.Name;
    user.Email = updated.Email;
    await _userService.UpdateAsync(user);
    Snackbar.Add("User updated", Severity.Success);
}
```

### Dialog options

```csharp
var options = new DialogOptions
{
    CloseOnEscapeKey = true,
    CloseButton = true,
    NoHeader = false,
    Position = DialogPosition.Center, // or CenterLeft/CenterRight/TopLeft/etc.
    FullWidth = true,
    FullScreen = false,
    MaxWidth = MaxWidth.Medium,
    BackdropClick = false, // v9: prevents close on backdrop click
    DefaultFocus = DefaultFocus.FirstChild
};
```

> **v9 note:** `DialogService.Show` is gone — always use `ShowAsync`. `IMudDialogInstance` is the v9 cascading type (was `MudDialogInstance` in v8, still available but prefer the interface).

### Message boxes (shortcut for simple yes/no)

```csharp
bool? result = await DialogService.ShowMessageBoxAsync(
    "Warning",
    "Deleting this user is permanent!",
    yesText: "Delete",
    cancelText: "Cancel");

if (result == true)
{
    // user clicked Delete
}
```

## Snackbars (toast notifications)

Inject `ISnackbar`:

```razor
@inject ISnackbar Snackbar
```

### Basic usage

```csharp
Snackbar.Add("Saved!", Severity.Success);
Snackbar.Add("Something went wrong", Severity.Error);
Snackbar.Add("Heads up", Severity.Warning);
Snackbar.Add("FYI", Severity.Info);
```

### With action button

```csharp
Snackbar.Add("Item deleted", Severity.Info, config =>
{
    config.Action = "Undo";
    config.ActionColor = Color.Primary;
    config.OnClick = async snackbar =>
    {
        await RestoreAsync();
        return Task.CompletedTask;
    };
    config.RequireInteraction = false; // v9: override the default-stays-open behavior
});
```

> **v9 note:** Snackbars with an action button **require interaction by default** — they won't auto-dismiss. If you want the old auto-dismiss behavior with a button, set `config.RequireInteraction = false` explicitly.

### Persistent (won't auto-dismiss)

```csharp
Snackbar.Add("Upload in progress", Severity.Info, config =>
{
    config.RequireInteraction = true;
    config.ShowCloseIcon = true;
});
```

### Clear all

```csharp
Snackbar.Clear();
```

## Common form patterns

### Reset a form after submit

```csharp
private async Task HandleValidSubmit()
{
    await _service.SaveAsync(_model);
    Snackbar.Add("Saved", Severity.Success);
    _model = new(); // new instance; EditForm re-initializes
    StateHasChanged();
}
```

### Disable submit while saving

```razor
<MudButton ButtonType="ButtonType.Submit"
           Variant="Variant.Filled"
           Color="Color.Primary"
           Disabled="@_saving">
    @if (_saving)
    {
        <MudProgressCircular Class="ms-n1" Size="Size.Small" Indeterminate="true" />
        <MudText Class="ms-2">Saving</MudText>
    }
    else
    {
        <MudText>Save</MudText>
    }
</MudButton>

@code {
    private bool _saving;

    private async Task HandleValidSubmit()
    {
        _saving = true;
        try { await _service.SaveAsync(_model); }
        finally { _saving = false; }
    }
}
```

### Prompt before navigating away if dirty

Use Blazor's built-in `NavigationLock` combined with a dirty flag set by the form's `@bind-Value`-modified inputs.

## Sources

- [MudBlazor Form Docs](https://mudblazor.com/components/form)
- [MudBlazor Dialog Docs](https://mudblazor.com/components/dialog)
- [Blazored.FluentValidation](https://github.com/Blazored/FluentValidation)
