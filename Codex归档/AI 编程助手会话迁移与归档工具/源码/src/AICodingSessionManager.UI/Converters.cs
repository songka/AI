using System.Globalization;
using System.Windows.Data;
using AICodingSessionManager.Domain;
using AICodingSessionManager.Migration;

namespace AICodingSessionManager.UI;

public sealed class FileSizeConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        var bytes = value is long size ? size : 0;
        return bytes switch
        {
            >= 1024 * 1024 => $"{bytes / 1024d / 1024d:0.0} MB",
            >= 1024 => $"{bytes / 1024d:0.0} KB",
            _ => $"{bytes} B"
        };
    }
    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) => throw new NotSupportedException();
}

public sealed class RoleLabelConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture) => value switch
    {
        MessageRole.User => "USER",
        MessageRole.Assistant => "ASSISTANT",
        MessageRole.Tool => "TOOL",
        MessageRole.System => "SYSTEM",
        _ => value?.ToString()?.ToUpperInvariant() ?? "MESSAGE"
    };
    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) => throw new NotSupportedException();
}

public sealed class ContentKindConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture) => value switch
    {
        ContentPartKind.Text => "TEXT",
        ContentPartKind.Reasoning => "REASONING",
        ContentPartKind.ToolCall => "TOOL CALL",
        ContentPartKind.ToolResult => "TOOL RESULT",
        ContentPartKind.Command => "COMMAND",
        ContentPartKind.CommandResult => "COMMAND RESULT",
        ContentPartKind.Patch => "PATCH",
        ContentPartKind.Diff => "DIFF",
        _ => value?.ToString()?.ToUpperInvariant() ?? "CONTENT"
    };
    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) => throw new NotSupportedException();
}

public sealed class EnumLabelConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture) => value switch
    {
        SessionDateFilter.All => "全部时间",
        SessionDateFilter.Today => "今天",
        SessionDateFilter.Last7Days => "最近 7 天",
        SessionDateFilter.Last30Days => "最近 30 天",
        SessionDateFilter.LastYear => "最近一年",
        MigrationTarget.Codex => "Codex",
        MigrationTarget.ClaudeCode => "Claude Code",
        MigrationTarget.OpenCode => "OpenCode",
        _ => value?.ToString() ?? ""
    };

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) =>
        throw new NotSupportedException();
}
