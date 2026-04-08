using System.Globalization;
using Microsoft.AspNetCore.Components;
using MudBlazor;

namespace MyApp.Components;

/// <summary>
/// A multi-tag input that takes a List&lt;string&gt; and renders comma-separated tags
/// in a single MudTextField. Migrated to MudBlazor 9.
/// </summary>
public partial class TagsInput : MudFormComponent<List<string>, string>
{
    public TagsInput()
    {
        Converter = new DefaultConverter<List<string>>
        {
            SetFunc = list => list is null ? string.Empty : string.Join(", ", list),
            GetFunc = str => string.IsNullOrWhiteSpace(str)
                ? new List<string>()
                : str.Split(',').Select(s => s.Trim()).Where(s => s.Length > 0).ToList(),
            Culture = CultureInfo.InvariantCulture
        };
    }

    /// <summary>
    /// In MudBlazor 9 <see cref="MudFormComponent{T, U}"/> declares an abstract
    /// <c>GetDefaultConverter()</c> that derived components must implement.
    /// It returns the converter used when no custom one is supplied. We return a
    /// <see cref="DefaultConverter{T}"/> configured to round-trip a comma separated
    /// list of tags, matching the behavior of the v8 constructor-based setup.
    /// </summary>
    protected override Converter<List<string>, string> GetDefaultConverter()
        => new DefaultConverter<List<string>>
        {
            SetFunc = list => list is null ? string.Empty : string.Join(", ", list),
            GetFunc = str => string.IsNullOrWhiteSpace(str)
                ? new List<string>()
                : str.Split(',').Select(s => s.Trim()).Where(s => s.Length > 0).ToList(),
            Culture = CultureInfo.InvariantCulture
        };

    [Parameter]
    public string Label { get; set; } = "Tags";

    [Parameter]
    public string HelperText { get; set; } = "Comma-separated";

    [Parameter]
    public List<string>? Value { get; set; }

    [Parameter]
    public EventCallback<List<string>?> ValueChanged { get; set; }

    private string? _text;

    protected override async Task OnParametersSetAsync()
    {
        await base.OnParametersSetAsync();
        _text = Converter.Set(Value);
    }

    private async Task OnTextChanged(string newText)
    {
        _text = newText;
        var newValue = Converter.Get(newText);
        await SetValueAsync(newValue);
    }

    /// <summary>
    /// In MudBlazor 9 the protected override for propagating a new value to
    /// consumers is <c>SetValueAsync</c> (the v8 <c>WriteValueAsync</c> hook
    /// no longer exists on the base class). Override it to update the two-way
    /// <see cref="Value"/>/<see cref="ValueChanged"/> binding while still
    /// calling the base implementation so the internal form-component state
    /// (dirty/touched/validation) is kept in sync.
    /// </summary>
    protected override async Task SetValueAsync(List<string>? value, bool updateText = true)
    {
        if (!EqualityComparer<List<string>?>.Default.Equals(Value, value))
        {
            Value = value;
            await ValueChanged.InvokeAsync(value);
        }

        await base.SetValueAsync(value, updateText);
    }

    public override async Task Validate()
    {
        await base.Validate();
        // Custom: every tag must be non-empty after trimming
        if (Value is not null && Value.Any(t => string.IsNullOrWhiteSpace(t)))
        {
            ValidationErrors.Add("Empty tags are not allowed");
        }
    }
}
