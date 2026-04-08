using System.Globalization;
using Microsoft.AspNetCore.Components;
using MudBlazor;

namespace MyApp.Components;

/// <summary>
/// A multi-tag input that takes a List&lt;string&gt; and renders comma-separated tags
/// in a single MudTextField. This is a custom MudFormComponent built for v8.
/// </summary>
public partial class TagsInput : MudFormComponent<List<string>, string>
{
    public TagsInput() : base(new DefaultConverter<List<string>>())
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

    protected override Task WriteValueAsync(List<string>? value)
    {
        Value = value;
        return ValueChanged.InvokeAsync(value);
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
