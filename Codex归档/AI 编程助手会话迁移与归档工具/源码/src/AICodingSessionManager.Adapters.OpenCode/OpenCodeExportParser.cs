using System.Text.Json;
using AICodingSessionManager.Domain;

namespace AICodingSessionManager.Adapters.OpenCode;

internal static class OpenCodeExportParser
{
    public static void Validate(string json)
    {
        using var document = JsonDocument.Parse(json);
        var root = document.RootElement;
        if (root.ValueKind != JsonValueKind.Object ||
            !root.TryGetProperty("info", out var info) || info.ValueKind != JsonValueKind.Object ||
            !root.TryGetProperty("messages", out var messages) || messages.ValueKind != JsonValueKind.Array)
            throw new InvalidDataException("OpenCode export is missing info or messages.");
    }

    public static UniversalSession Parse(string json)
    {
        using var document = JsonDocument.Parse(json);
        var root = document.RootElement;
        if (!root.TryGetProperty("info", out var info) || info.ValueKind != JsonValueKind.Object ||
            !root.TryGetProperty("messages", out var messages) || messages.ValueKind != JsonValueKind.Array)
            throw new InvalidDataException("OpenCode export is missing info or messages.");

        var id = String(info, "id") ?? throw new InvalidDataException("OpenCode export session info is missing id.");
        var directory = String(info, "directory");
        var model = ObjectString(info, "model", "id");
        var provider = ObjectString(info, "model", "providerID");
        var session = new UniversalSession
        {
            Session = new SessionDescriptor
            {
                Id = id,
                SourceSessionId = id,
                Source = AgentKind.OpenCode,
                Title = String(info, "title") ?? "Untitled session",
                CreatedAt = NestedTimestamp(info, "time", "created"),
                UpdatedAt = NestedTimestamp(info, "time", "updated"),
                Cwd = directory,
                Project = new ProjectReference { Path = directory, Name = directory is null ? null : Path.GetFileName(directory.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)) },
                Model = model,
                Provider = provider
            }
        };
        CopyProperties(info, session.Metadata, ["id", "title", "directory", "time", "model"]);

        var recordNumber = 0;
        foreach (var envelope in messages.EnumerateArray())
        {
            recordNumber++;
            if (envelope.ValueKind != JsonValueKind.Object ||
                !envelope.TryGetProperty("info", out var messageInfo) || messageInfo.ValueKind != JsonValueKind.Object ||
                !envelope.TryGetProperty("parts", out var parts) || parts.ValueKind != JsonValueKind.Array)
            {
                AddUnsupported(session, recordNumber, "Invalid OpenCode message envelope", envelope);
                continue;
            }

            var roleText = String(messageInfo, "role");
            var role = roleText switch
            {
                "user" => MessageRole.User,
                "assistant" => MessageRole.Assistant,
                "system" => MessageRole.System,
                "tool" => MessageRole.Tool,
                _ => (MessageRole?)null
            };
            if (role is null)
            {
                AddUnsupported(session, recordNumber, $"Unsupported OpenCode message role: {roleText ?? "(missing)"}", envelope);
                continue;
            }

            var message = new UniversalMessage
            {
                Id = String(messageInfo, "id") ?? $"opencode-{recordNumber}",
                ParentMessageId = String(messageInfo, "parentID"),
                Role = role.Value,
                Timestamp = NestedTimestamp(messageInfo, "time", "created")
            };
            CopyProperties(messageInfo, message.Metadata, ["id", "parentID", "role", "time"]);
            foreach (var part in parts.EnumerateArray())
            {
                recordNumber++;
                ParsePart(session, message, part, recordNumber);
            }
            if (message.Content.Count > 0) session.Messages.Add(message);
            else AddUnsupported(session, recordNumber, "OpenCode message contains no renderable parts", envelope);
        }
        return session;
    }

    private static void ParsePart(UniversalSession session, UniversalMessage message, JsonElement part, int recordNumber)
    {
        if (part.ValueKind != JsonValueKind.Object)
        {
            AddUnsupported(session, recordNumber, "Invalid OpenCode part", part);
            return;
        }
        var type = String(part, "type");
        switch (type)
        {
            case "text":
                AddTextPart(message, part, ContentPartKind.Text, "text");
                break;
            case "reasoning":
                AddTextPart(message, part, ContentPartKind.Reasoning, "text");
                break;
            case "patch":
                AddTextPart(message, part, ContentPartKind.Patch, "hash", part.TryGetProperty("files", out var files) ? files : null);
                break;
            case "file":
                AddTextPart(message, part, ContentPartKind.File, "url");
                break;
            case "snapshot":
                AddTextPart(message, part, ContentPartKind.Metadata, "snapshot");
                break;
            case "subtask":
                AddTextPart(message, part, ContentPartKind.Command, "prompt");
                break;
            case "tool":
                ParseToolPart(message, part);
                break;
            case "agent":
            case "compaction":
            case "retry":
            case "step-start":
            case "step-finish":
                message.Content.Add(new ContentPart { Type = ContentPartKind.Metadata, Text = part.GetRawText() });
                break;
            default:
                AddUnsupported(session, recordNumber, $"Unsupported OpenCode part type: {type ?? "(missing)"}", part);
                break;
        }
    }

    private static void ParseToolPart(UniversalMessage message, JsonElement part)
    {
        var callId = String(part, "callID") ?? String(part, "id");
        var name = String(part, "tool");
        var state = part.TryGetProperty("state", out var stateValue) && stateValue.ValueKind == JsonValueKind.Object
            ? stateValue : default;
        JsonElement? input = state.ValueKind == JsonValueKind.Object && state.TryGetProperty("input", out var inputValue)
            ? inputValue.Clone() : null;
        var call = new ContentPart { Type = ContentPartKind.ToolCall, ToolCallId = callId, ToolName = name, Arguments = input };
        CopyProperties(part, call.Metadata, ["state"]);
        if (state.ValueKind == JsonValueKind.Object) CopyProperties(state, call.Metadata, ["input", "output", "error"]);
        message.Content.Add(call);

        if (state.ValueKind != JsonValueKind.Object) return;
        var output = String(state, "output") ?? String(state, "error");
        if (output is null) return;
        var result = new ContentPart { Type = ContentPartKind.ToolResult, ToolCallId = callId, ToolName = name, Text = output };
        CopyProperties(state, result.Metadata, ["input", "output", "error"]);
        message.Content.Add(result);
    }

    private static void AddTextPart(UniversalMessage message, JsonElement source, ContentPartKind kind, string textProperty, JsonElement? fallback = null)
    {
        var text = String(source, textProperty) ?? fallback?.GetRawText();
        if (text is null) return;
        var target = new ContentPart { Type = kind, Text = text };
        CopyProperties(source, target.Metadata, [textProperty]);
        message.Content.Add(target);
    }

    private static void CopyProperties(JsonElement source, IDictionary<string, JsonElement> destination, IReadOnlyCollection<string> excluded)
    {
        foreach (var property in source.EnumerateObject())
            if (!excluded.Contains(property.Name, StringComparer.Ordinal)) destination[property.Name] = property.Value.Clone();
    }

    private static void AddUnsupported(UniversalSession session, int number, string reason, JsonElement value) =>
        session.UnsupportedRecords.Add(new UnsupportedRecord { LineNumber = number, Reason = reason, RawJson = value.GetRawText() });

    private static string? String(JsonElement node, string name) =>
        node.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String ? value.GetString() : null;

    private static string? ObjectString(JsonElement node, string parent, string name) =>
        node.TryGetProperty(parent, out var value) && value.ValueKind == JsonValueKind.Object ? String(value, name) : null;

    private static DateTimeOffset? NestedTimestamp(JsonElement node, string parent, string name) =>
        node.TryGetProperty(parent, out var value) && value.ValueKind == JsonValueKind.Object
            ? OpenCodeAdapter.ReadTimestamp(value, name) : null;
}
