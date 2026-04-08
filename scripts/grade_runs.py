#!/usr/bin/env python3
"""Grade all 12 runs against their assertions by pattern-checking the output files.

Writes grading.json into each run directory with fields: expectations[{text, passed, evidence}].
"""
import json
import re
from pathlib import Path

ROOT = Path("/Users/dejanwho/Projects/Code/mudblazor-skills/skills")


def read_all(output_dir: Path) -> str:
    """Concatenate all output files so patterns can span them (e.g. dialog is in a sibling file)."""
    if not output_dir.exists():
        return ""
    parts = []
    for p in sorted(output_dir.glob("*")):
        if p.is_file():
            try:
                parts.append(p.read_text(errors="replace"))
            except Exception:
                pass
    return "\n".join(parts)


# Assertion checkers: (id, text, check_fn(text) -> (passed: bool, evidence: str))
# check_fn receives the concatenated content of the outputs/ directory.

def has(pat, flags=0):
    def check(text):
        m = re.search(pat, text, flags)
        if m:
            snippet = m.group(0)
            if len(snippet) > 120:
                snippet = snippet[:120] + "..."
            return True, snippet
        return False, f"pattern not found: {pat}"
    return check

def missing(pat, flags=0):
    """Asserts the pattern is NOT present (good thing)."""
    def check(text):
        m = re.search(pat, text, flags)
        if m:
            return False, f"unwanted pattern found: {m.group(0)[:120]}"
        return True, f"confirmed absent: {pat}"
    return check

def both(fn1, fn2):
    def check(text):
        p1, e1 = fn1(text)
        p2, e2 = fn2(text)
        return (p1 and p2), f"{e1} | {e2}"
    return check


# -------- Migration eval 1: mudchart --------

MIG_1 = [
    ("no-input-data",
     "Dashboard.razor no longer uses the v8 'InputData' parameter on MudChart",
     missing(r"InputData\s*=")),
    ("no-x-axis-labels",
     "Dashboard.razor no longer uses the v8 'XAxisLabels' parameter",
     missing(r"XAxisLabels\s*=")),
    ("no-input-labels",
     "Dashboard.razor no longer uses the v8 'InputLabels' parameter",
     missing(r"InputLabels\s*=")),
    ("no-mud-time-series-chart",
     "Dashboard.razor no longer uses the removed <MudTimeSeriesChart> component",
     missing(r"<MudTimeSeriesChart\b")),
    ("uses-chart-series-typed",
     "Dashboard.razor uses the typed ChartSeries<T> generic for chart data",
     has(r"ChartSeries<\w+>")),
    ("uses-bar-chart-options",
     "Dashboard.razor uses BarChartOptions (or similar type-specific options class)",
     has(r"BarChartOptions|LineChartOptions|DonutChartOptions|PieChartOptions")),
    ("uses-as-chart-data-set",
     "Dashboard.razor wraps chart data with .AsChartDataSet()",
     has(r"\.AsChartDataSet\(\)")),
    ("preserves-page-directive",
     "Dashboard.razor preserves the @page \"/dashboard\" route",
     has(r'@page\s+"/dashboard"')),
]

# -------- Migration eval 2: dialog/menu --------

MIG_2 = [
    ("no-sync-show",
     "UserList.razor no longer calls DialogService.Show<...>(...) (synchronous v8 method)",
     missing(r"DialogService\.Show<[^>]+>\(")),  # allows ShowAsync to pass
    ("uses-show-async",
     "UserList.razor uses await DialogService.ShowAsync<...>(...)",
     has(r"DialogService\.ShowAsync<")),
    ("uses-show-message-box-async",
     "UserList.razor uses ShowMessageBoxAsync",
     has(r"ShowMessageBoxAsync")),
    ("server-data-takes-cancellation-token",
     "LoadServerDataAsync accepts CancellationToken as second parameter",
     has(r"LoadServerDataAsync\s*\(\s*GridState<User>\s+\w+\s*,\s*CancellationToken\s+\w+")),
    ("menu-uses-context-toggle",
     "MudMenu's ActivatorContent button wires OnClick to @context.ToggleAsync",
     has(r"context\.(?:ToggleAsync|OpenAsync)")),
    ("preserves-route",
     "UserList.razor preserves the @page \"/users\" route",
     has(r'@page\s+"/users"')),
    ("preserves-grid-columns",
     "UserList.razor preserves all four grid columns",
     both(
         has(r'Property\s*=\s*"?x\s*=>\s*x\.Id"?|Property="x\s*=>\s*x\.Id"'),
         has(r'Property\s*=\s*"?x\s*=>\s*x\.Email"?|Property="x\s*=>\s*x\.Email"'),
     )),
]

# -------- Migration eval 3: custom form component --------

MIG_3 = [
    ("overrides-get-default-converter",
     "TagsInput.razor.cs overrides GetDefaultConverter()",
     has(r"override\s+\w[\w<>,?\s]*\s+GetDefaultConverter\s*\(")),
    ("no-write-value-async",
     "No longer overrides WriteValueAsync",
     missing(r"override\s+\w[\w<>,?\s]*\s+WriteValueAsync\s*\(")),
    ("uses-set-value-core-async",
     "Overrides SetValueCoreAsync",
     has(r"override\s+\w[\w<>,?\s]*\s+SetValueCoreAsync\s*\(")),
    ("no-base-converter-call",
     "Constructor no longer passes a Converter to base()",
     missing(r":\s*base\s*\(\s*new\s+DefaultConverter")),
    ("uses-validate-async",
     "Validate() override renamed to ValidateAsync()",
     has(r"override\s+\w[\w<>,?\s]*\s+ValidateAsync\s*\(")),
    ("preserves-tags-parsing-behavior",
     "Preserves comma-split + trim tag parsing behavior",
     both(
         has(r"\.Split\("),
         has(r"\.Trim\("),
     )),
]

# -------- Usage eval 1: orders page --------

USG_1 = [
    ("has-page-directive",
     "Orders.razor declares @page \"/orders\"",
     has(r'@page\s+"/orders"')),
    ("has-render-mode",
     "Declares @rendermode InteractiveServer",
     has(r"@rendermode\s+InteractiveServer")),
    ("uses-mud-data-grid-typed",
     "Uses MudDataGrid<Order>",
     has(r"MudDataGrid<Order>|MudDataGrid\s+T=\"Order\"")),
    ("uses-server-data-with-cancellation",
     "ServerData delegate accepts CancellationToken and passes to QueryAsync",
     both(
         has(r"ServerData\s*=|Task<GridData<Order>>\s+\w+\s*\(\s*GridState<Order>"),
         has(r"CancellationToken"),
     )),
    ("has-debounced-search",
     "Has search MudTextField with DebounceInterval=\"300\"",
     has(r'DebounceInterval\s*=\s*"?300"?')),
    ("has-property-columns-formatted",
     "PropertyColumns for OrderId, CustomerName, Total (currency), CreatedAt (yyyy-MM-dd)",
     both(
         has(r'Format\s*=\s*"(?:C\d*|\{0:C[^"]*\})"'),
         has(r'Format\s*=\s*"yyyy-MM-dd"'),
     )),
    ("has-pager-with-page-sizes",
     "MudDataGridPager with page sizes 10, 25, 50, 100",
     both(
         has(r"MudDataGridPager"),
         has(r"10.*25.*50.*100|new\s*\[\s*\]\s*\{\s*10\s*,\s*25\s*,\s*50\s*,\s*100"),
     )),
    ("has-view-action-column",
     "Action column with per-row View button that opens a dialog",
     both(
         has(r"TemplateColumn"),
         has(r"MudIconButton"),
     )),
    ("uses-show-async",
     "Dialog opening uses await DialogService.ShowAsync",
     has(r"DialogService\.ShowAsync")),
    ("dialog-component-exists",
     "A dialog .razor component is created showing the order ID",
     has(r"<MudDialog>|@inherits\s+\w*Dialog|IMudDialogInstance|MudDialogInstance")),
]

# -------- Usage eval 2: product form --------

USG_2 = [
    ("has-page-directive",
     "CreateProduct.razor declares @page \"/products/new\"",
     has(r'@page\s+"/products/new"')),
    ("uses-edit-form",
     "Uses <EditForm Model=...>",
     has(r"<EditForm\b")),
    ("uses-data-annotations-validator",
     "Includes <DataAnnotationsValidator />",
     has(r"<DataAnnotationsValidator\s*/>")),
    ("model-has-required-name-with-length",
     "Model has [Required] and [StringLength(100, MinimumLength = 3)] on Name",
     both(
         has(r"\[Required[\s\S]{0,80}?Name|Name[\s\S]{0,100}?\[Required"),
         has(r"StringLength\s*\(\s*100\s*,\s*MinimumLength\s*=\s*3"),
     )),
    ("model-has-sku-regex",
     "Model has [RegularExpression] on SKU",
     has(r'RegularExpression\s*\(\s*@?"\^\[A-Z\]\{3\}-\\d\{4\}\$"')),
    ("model-has-price-range",
     "Model has [Range] on Price",
     has(r"\[Range\s*\(")),
    ("model-has-description-length",
     "Model has [StringLength(500)] on Description",
     has(r"StringLength\s*\(\s*500")),
    ("submit-button-is-submit-type",
     "Submit button uses ButtonType=\"ButtonType.Submit\"",
     has(r'ButtonType\s*=\s*"ButtonType\.Submit"')),
    ("inputs-have-for-binding",
     "Inputs use For=\"@(() => model.X)\"",
     has(r'For\s*=\s*"@\(\(\)\s*=>\s*_model\.')),
    ("calls-service-on-valid-submit",
     "OnValidSubmit handler calls ProductService.CreateAsync",
     has(r"ProductService\.CreateAsync")),
    ("shows-snackbar-on-success",
     "Calls Snackbar.Add with Severity.Success",
     has(r"Snackbar\.Add[\s\S]{0,200}Severity\.Success")),
    ("resets-form-after-submit",
     "Resets the model after submit",
     has(r"_model\s*=\s*new\s*\(")),
    ("cancel-navigates-back",
     "Cancel button navigates to /products",
     has(r'NavigateTo\s*\(\s*"/products"')),
]

# -------- Usage eval 3: theme / dark mode --------

USG_3 = [
    ("has-mud-theme-provider",
     "Includes <MudThemeProvider> with Theme bound",
     has(r"<MudThemeProvider[^>]*Theme\s*=")),
    ("has-mud-popover-provider",
     "Includes <MudPopoverProvider />",
     has(r"<MudPopoverProvider\s*/>")),
    ("has-mud-dialog-provider",
     "Includes <MudDialogProvider />",
     has(r"<MudDialogProvider\b")),
    ("has-mud-snackbar-provider",
     "Includes <MudSnackbarProvider />",
     has(r"<MudSnackbarProvider\s*/>")),
    ("popover-before-dialog",
     "MudPopoverProvider appears BEFORE MudDialogProvider",
     lambda text: (
         (text.find("MudPopoverProvider") != -1
          and text.find("MudDialogProvider") != -1
          and text.find("MudPopoverProvider") < text.find("MudDialogProvider")),
         f"Popover idx={text.find('MudPopoverProvider')}, Dialog idx={text.find('MudDialogProvider')}"
     )),
    ("theme-has-primary-color",
     "Custom theme sets Primary = \"#0EA5E9\"",
     has(r'Primary\s*=\s*"#0EA5E9"', re.IGNORECASE)),
    ("theme-has-secondary-color",
     "Custom theme sets Secondary = \"#64748B\"",
     has(r'Secondary\s*=\s*"#64748B"', re.IGNORECASE)),
    ("theme-has-border-radius",
     "Theme sets LayoutProperties.DefaultBorderRadius = \"8px\"",
     has(r'DefaultBorderRadius\s*=\s*"8px"')),
    ("theme-has-drawer-width",
     "Theme sets LayoutProperties.DrawerWidthLeft = \"280px\"",
     has(r'DrawerWidthLeft\s*=\s*"280px"')),
    ("follows-os-dark-mode",
     "Calls GetSystemDarkModeAsync() (v9 method)",
     has(r"GetSystemDarkModeAsync")),
    ("has-toggle-button",
     "AppBar has MudIconButton with sun/moon icons",
     both(
         has(r"MudIconButton"),
         has(r"LightMode|DarkMode|Brightness"),
     )),
    ("uses-localstorage-via-jsinterop",
     "Toggle handler persists to localStorage via IJSRuntime",
     has(r"localStorage\.(?:getItem|setItem)")),
    ("preserves-app-name",
     "Preserves 'Acme Dashboard' in the AppBar",
     has(r"Acme Dashboard")),
    ("preserves-nav-links",
     "Preserves Home/Users/Settings NavLinks",
     both(
         has(r'Href\s*=\s*"/users"'),
         has(r'Href\s*=\s*"/settings"'),
     )),
]


RUNS = [
    ("mudblazor-migration-8-to-9-workspace", "eval-1-mudchart-v9-migration", MIG_1),
    ("mudblazor-migration-8-to-9-workspace", "eval-2-dialog-async-and-menu-context", MIG_2),
    ("mudblazor-migration-8-to-9-workspace", "eval-3-custom-form-component-converter", MIG_3),
    ("mudblazor-9-workspace", "eval-1-orders-page-with-server-datagrid", USG_1),
    ("mudblazor-9-workspace", "eval-2-create-product-form-with-validation", USG_2),
    ("mudblazor-9-workspace", "eval-3-custom-theme-with-dark-mode-toggle", USG_3),
]


def grade_run(workspace: str, eval_name: str, assertions: list, condition: str):
    run_dir = ROOT / workspace / "iteration-1" / eval_name / condition
    outputs = run_dir / "outputs"
    text = read_all(outputs)
    expectations = []
    passed_count = 0
    for aid, atext, check in assertions:
        try:
            p, evidence = check(text)
        except Exception as e:
            p, evidence = False, f"grader error: {e}"
        expectations.append({
            "id": aid,
            "text": atext,
            "passed": bool(p),
            "evidence": str(evidence)[:500],
        })
        if p:
            passed_count += 1
    result = {
        "eval_name": eval_name,
        "condition": condition,
        "passed": passed_count,
        "total": len(assertions),
        "pass_rate": passed_count / len(assertions) if assertions else 0,
        "expectations": expectations,
    }
    grading_path = run_dir / "grading.json"
    grading_path.write_text(json.dumps(result, indent=2))
    return result


def main():
    summary = []
    for workspace, eval_name, assertions in RUNS:
        for condition in ["with_skill", "without_skill"]:
            result = grade_run(workspace, eval_name, assertions, condition)
            summary.append(result)
            status = "✓" if result["pass_rate"] == 1.0 else ("~" if result["pass_rate"] >= 0.5 else "✗")
            print(f"{status} {workspace:45s} {eval_name:50s} {condition:15s} {result['passed']:2d}/{result['total']:2d}")
    return summary


if __name__ == "__main__":
    main()
