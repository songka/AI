using System.Text.Json;
using AICodingSessionManager.Domain;

namespace AICodingSessionManager.Adapters.ClaudeDesktop;

internal static class ClaudeDesktopConversationParser
{
    public static UniversalSession Parse(string json)
    {
        using var document = JsonDocument.Parse(json);
        var root = document.RootElement;
        if (root.ValueKind != JsonValueKind.Object) throw new InvalidDataException("Claude conversation must be a JSON object.");
        var id = String(root, "uuid") ?? String(root, "id") ?? throw new InvalidDataException("Claude conversation is missing uuid.");
        var session = new UniversalSession
        {
            Session = new SessionDescriptor
            {
                Id = id,
                SourceSessionId = id,
                Source = AgentKind.ClaudeDesktop,
                Title = String(root, "name") ?? String(root, "title") ?? "Claude Desktop 会话",
                CreatedAt = Date(root, "created_at"),
                UpdatedAt = Date(root, "updated_at"),
                Project = new ProjectReference { Name = "Claude Desktop" }
            }
        };
        CopyMetadata(root, session.Metadata, ["account", "summary", "settings"]);
        if (!root.TryGetProperty("chat_messages", out var messages) || messages.ValueKind != JsonValueKind.Array)
            throw new InvalidDataException("Claude conversation is missing chat_messages.");

        var index = 0;
        foreach (var item in messages.EnumerateArray())
        {
            index++;
            var sender = String(item, "sender") ?? String(item, "role");
            var role = sender switch
            {
                "human" or "user" => MessageRole.User,
                "assistant" => MessageRole.Assistant,
                "system" => MessageRole.System,
                _ => (MessageRole?)null
            };
            if (role is null)
            {
                session.UnsupportedRecords.Add(new UnsupportedRecord { LineNumber = index, Reason = $"Unsupported Claude Desktop sender: {sender ?? "(missing)"}", RawJson = item.GetRawText() });
                continue;
            }
            var message = new UniversalMessage
            {
                Id = String(item, "uuid") ?? String(item, "id") ?? $"claude-desktop-{index}",
                Role = role.Value,
                Timestamp = Date(item, "created_at")
            };
            CopyMetadata(item, message.Metadata, ["updated_at", "index", "attachments", "files"]);
            if (item.TryGetProperty("content", out var content) && content.ValueKind == JsonValueKind.Array)
            {
                foreach (var part in content.EnumerateArray()) ParsePart(part, message, session, index);
            }
            else
            {
                var text = String(item, "text");
                if (!string.IsNullOrWhiteSpace(text)) message.Content.Add(new ContentPart { Type = ContentPartKind.Text, Text = text });
            }
            AddAttachments(item, session);
            if (message.Content.Count > 0) session.Messages.Add(message);
        }
        return session;
    }

    private static void ParsePart(JsonElement part, UniversalMessage message, UniversalSession session, int index)
    {
        var type = String(part, "type");
        switch (type)
        {
            case "text":
            case "thinking":
                var text = String(part, "text") ?? String(part, "thinking");
                if (text is not null) message.Content.Add(new ContentPart { Type = type == "thinking" ? ContentPartKind.Reasoning : ContentPartKind.Text, Text = text });
                break;
            case "tool_use":
                message.Content.Add(new ContentPart
                {
                    Type = ContentPartKind.ToolCall,
                    ToolCallId = String(part, "id"),
                    ToolName = String(part, "name"),
                    Arguments = part.TryGetProperty("input", out var input) ? input.Clone() : null
                });
                break;
            case "tool_result":
                message.Content.Add(new ContentPart
                {
                    Type = ContentPartKind.ToolResult,
                    ToolCallId = String(part, "tool_use_id"),
                    Text = Display(part.TryGetProperty("content", out var output) ? output : default)
                });
                break;
            default:
                session.UnsupportedRecords.Add(new UnsupportedRecord { LineNumber = index, Reason = $"Unsupported Claude Desktop content type: {type ?? "(missing)"}", RawJson = part.GetRawText() });
                break;
        }
    }

    private static void AddAttachments(JsonElement message, UniversalSession session)
    {
        foreach (var propertyName in new[] { "attachments", "files" })
        {
            if (!message.TryGetProperty(propertyName, out var items) || items.ValueKind != JsonValueKind.Array) continue;
            foreach (var item in items.EnumerateArray())
            {
                var name = String(item, "file_name") ?? String(item, "name") ?? String(item, "filename");
                if (string.IsNullOrWhiteSpace(name)) continue;
                session.Attachments.Add(new Attachment
                {
                    Name = name,
                    MediaType = String(item, "file_type") ?? String(item, "mime_type"),
                    SourcePath = String(item, "file_path")
                });
            }
        }
    }

    private static string? Display(JsonElement value)
    {
        if (value.ValueKind == JsonValueKind.String) return value.GetString();
        if (value.ValueKind == JsonValueKind.Array)
        {
            var text = string.Join(Environment.NewLine, value.EnumerateArray().Select(item => String(item, "text")).Where(text => !string.IsNullOrWhiteSpace(text)));
            return text.Length > 0 ? text : value.GetRawText();
        }
        return value.ValueKind is JsonValueKind.Undefined or JsonValueKind.Null ? null : value.GetRawText();
    }

    private static void CopyMetadata(JsonElement source, IDictionary<string, JsonElement> target, IReadOnlyList<string> names)
    {
        foreach (var name in names) if (source.TryGetProperty(name, out var value)) target[name] = value.Clone();
    }

    private static string? String(JsonElement node, string name) =>
        node.ValueKind == JsonValueKind.Object && node.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String ? value.GetString() : null;
    private static DateTimeOffset? Date(JsonElement node, string name) => ClaudeDesktopAdapter.ParseDate(String(node, name));
}
