using System.Globalization;
using System.Text;
using System.Text.Json;
using AICodingSessionManager.Domain;

namespace AICodingSessionManager.Export;

/// <summary>Renders a session as a readable, provider-neutral Markdown document.</summary>
public sealed class MarkdownSessionRenderer : ISessionRenderer
{
    /// <inheritdoc />
    public string FileExtension => "md";

    /// <inheritdoc />
    public string MediaType => "text/markdown";

    /// <inheritdoc />
    public string Render(UniversalSession session)
    {
        ArgumentNullException.ThrowIfNull(session);

        var output = new StringBuilder();
        output.Append("# ").AppendLine(session.Session.Title);
        output.AppendLine();
        AppendField(output, "Session ID", session.Session.Id);
        AppendField(output, "Source", DisplayName(session.Session.Source));
        AppendField(output, "Source session ID", session.Session.SourceSessionId);
        AppendField(output, "Created", FormatTimestamp(session.Session.CreatedAt));
        AppendField(output, "Updated", FormatTimestamp(session.Session.UpdatedAt));
        AppendField(output, "Project", session.Session.Project.Name);
        AppendField(output, "Working directory", session.Session.Cwd);
        AppendField(output, "Model", session.Session.Model);
        AppendField(output, "Provider", session.Session.Provider);

        foreach (var message in session.Messages)
        {
            output.AppendLine();
            output.Append("## ").AppendLine(DisplayName(message.Role));
            output.AppendLine();
            if (message.Timestamp is not null)
            {
                output.Append("_").Append(FormatTimestamp(message.Timestamp)).AppendLine("_");
                output.AppendLine();
            }

            foreach (var part in message.Content)
            {
                AppendPart(output, part);
            }
        }

        if (session.UnsupportedRecords.Count > 0)
        {
            output.AppendLine();
            output.AppendLine("## Unsupported source records");
            output.AppendLine();
            output.Append(session.UnsupportedRecords.Count.ToString(CultureInfo.InvariantCulture))
                .AppendLine(" record(s) were preserved in the Universal Session JSON and raw archive.");
        }

        return output.ToString();
    }

    private static void AppendField(StringBuilder output, string label, string? value)
    {
        if (!string.IsNullOrWhiteSpace(value))
        {
            output.Append("**").Append(label).Append(":** ").AppendLine(value);
        }
    }

    private static void AppendPart(StringBuilder output, ContentPart part)
    {
        switch (part.Type)
        {
            case ContentPartKind.Text:
                output.AppendLine(part.Text ?? string.Empty);
                break;
            case ContentPartKind.ToolCall:
                output.Append("**Tool call: `").Append(part.ToolName ?? "unknown").AppendLine("`**");
                AppendCodeBlock(output, part.Arguments?.GetRawText() ?? part.Text);
                break;
            case ContentPartKind.ToolResult:
                output.AppendLine("**Tool result**");
                AppendCodeBlock(output, part.Text);
                break;
            default:
                output.Append("**").Append(DisplayName(part.Type)).AppendLine("**");
                AppendCodeBlock(output, part.Text ?? part.Arguments?.GetRawText());
                break;
        }

        output.AppendLine();
    }

    private static void AppendCodeBlock(StringBuilder output, string? value)
    {
        if (string.IsNullOrEmpty(value))
        {
            return;
        }

        var fence = value.Contains("```", StringComparison.Ordinal) ? "````" : "```";
        output.AppendLine(fence).AppendLine(value).AppendLine(fence);
    }

    private static string FormatTimestamp(DateTimeOffset? timestamp) =>
        timestamp?.ToUniversalTime().ToString("O", CultureInfo.InvariantCulture) ?? string.Empty;

    private static string DisplayName(AgentKind agent) => agent switch
    {
        AgentKind.ClaudeCode => "Claude Code",
        AgentKind.ClaudeDesktop => "Claude Desktop",
        AgentKind.OpenCode => "OpenCode",
        _ => agent.ToString(),
    };

    private static string DisplayName(MessageRole role) => role.ToString();

    private static string DisplayName(ContentPartKind kind) => kind switch
    {
        ContentPartKind.ToolCall => "Tool call",
        ContentPartKind.ToolResult => "Tool result",
        ContentPartKind.CommandResult => "Command result",
        _ => kind.ToString(),
    };
}
