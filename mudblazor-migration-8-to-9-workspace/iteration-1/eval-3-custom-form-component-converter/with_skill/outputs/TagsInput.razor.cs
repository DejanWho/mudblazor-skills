using System.Globalization;
using Microsoft.AspNetCore.Components;
using MudBlazor;

namespace MyApp.Components;

/// <summary>
/// A multi-tag input that takes a List&lt;string&gt; and renders comma-separated tags
/// in a single MudTextField. This is a custom MudFormComponent migrated to MudBlazor v9.
/// </summary>
public partial class TagsInput : MudFormComponent<List<string>, string>
{
    public TagsInput() : base()
    {
    }

    protected override IConverter<List<string>?, string?> GetDefaultConverter()
    {
        return new TagsConverter();
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
        _text = GetConverter().Convert(Value);
    }

    private async Task OnTextChanged(string newText)
    {
        _text = newText;
        var reversible = (IReversibleConverter<List<string>?, string?>)GetConverter();
        var newValue = reversible.ConvertBack(newText);
        await SetValueAndUpdateTextAsync(newValue);
    }

    protected override Task SetValueCoreAsync(List<string>? value)
    {
        Value = value;
        return ValueChanged.InvokeAsync(value);
    }

    public override async Task ValidateAsync()
    {
        await base.ValidateAsync();
        // Custom: every tag must be non-empty after trimming
        if (Value is not null && Value.Any(t => string.IsNullOrWhiteSpace(t)))
        {
            ValidationErrors.Add("Empty tags are not allowed");
        }
    }

    /// <summary>
    /// Reversible converter that joins a list of tags into a comma-separated string
    /// and splits a comma-separated string back into a list of trimmed, non-empty tags.
    /// </summary>
    private sealed class TagsConverter : IReversibleConverter<List<string>?, string?>
    {
        public CultureInfo Culture { get; set; } = CultureInfo.InvariantCulture;

        public string? Convert(List<string>? input)
        {
            return input is null ? string.Empty : string.Join(", ", input);
        }

        public List<string>? ConvertBack(string? input)
        {
            if (string.IsNullOrWhiteSpace(input))
            {
                return new List<string>();
            }

            return input
                .Split(',')
                .Select(s => s.Trim())
                .Where(s => s.Length > 0)
                .ToList();
        }
    }
}
