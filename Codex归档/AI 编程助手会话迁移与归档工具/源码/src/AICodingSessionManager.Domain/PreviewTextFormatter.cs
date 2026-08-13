using System.Text;
using System.Text.RegularExpressions;

namespace AICodingSessionManager.Domain;

/// <summary>Compacts known synthetic stress-test lines for display without changing archived data.</summary>
public static partial class PreviewTextFormatter
{
    private const int MinimumRunToCompact = 3;

    public static string CompactRepeatedFiller(string text)
    {
        if (!text.Contains("FILLER-", StringComparison.Ordinal)) return text;

        var normalized = text.Replace("\r\n", "\n", StringComparison.Ordinal).Replace('\r', '\n');
        var lines = normalized.Split('\n');
        var output = new StringBuilder(Math.Min(text.Length, 16_384));
        var index = 0;

        while (index < lines.Length)
        {
            if (!FillerLinePattern().IsMatch(lines[index]))
            {
                AppendLine(output, lines[index]);
                index++;
                continue;
            }

            var start = index;
            while (index < lines.Length && FillerLinePattern().IsMatch(lines[index])) index++;
            var count = index - start;

            if (count < MinimumRunToCompact)
            {
                for (var line = start; line < index; line++) AppendLine(output, lines[line]);
                continue;
            }

            var firstNumber = ExtractFillerNumber(lines[start]);
            var lastNumber = ExtractFillerNumber(lines[index - 1]);
            AppendLine(output, $"[已隐藏 {count:N0} 行测试占位数据：FILLER-{firstNumber} ～ FILLER-{lastNumber}；以下为真实正文]", output.Length > 0);
            output.AppendLine("── 真实正文 ──");
        }

        return output.ToString().TrimEnd('\n');
    }

    private static void AppendLine(StringBuilder output, string line, bool addLeadingBreak = false)
    {
        if (addLeadingBreak && output.Length > 0 && output[^1] != '\n') output.AppendLine();
        output.AppendLine(line);
    }

    private static string ExtractFillerNumber(string line)
    {
        var match = FillerLinePattern().Match(line);
        return match.Success ? match.Groups[1].Value : "?";
    }

    [GeneratedRegex(@"^FILLER-(\d+)\s+The quick brown fox jumps over the lazy dog 0123456789 repeat\s+filler\s+line\.?\s*$", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant)]
    private static partial Regex FillerLinePattern();
}
