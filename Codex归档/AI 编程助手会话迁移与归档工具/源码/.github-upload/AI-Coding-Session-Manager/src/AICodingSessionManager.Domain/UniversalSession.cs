using System.Text.Json;

namespace AICodingSessionManager.Domain;

/// <summary>Versioned, loss-aware representation used between provider adapters.</summary>
public sealed class UniversalSession
{
    public const string FormatName = "ai-coding-session";
    public const string CurrentVersion = "1.0";

    public string Format { get; init; } = FormatName;
    public string Version { get; init; } = CurrentVersion;
    public SessionDescriptor Session { get; init; } = new();
    public List<UniversalMessage> Messages { get; init; } = [];
    public Dictionary<string, JsonElement> Metadata { get; init; } = [];
    public List<Attachment> Attachments { get; init; } = [];
    public Dictionary<string, JsonElement> Environment { get; init; } = [];
    public List<UnsupportedRecord> UnsupportedRecords { get; init; } = [];
}

public sealed class SessionDescriptor
{
    public string Id { get; set; } = "";
    public string Title { get; set; } = "Untitled session";
    public AgentKind Source { get; init; }
    public string SourceSessionId { get; set; } = "";
    public DateTimeOffset? CreatedAt { get; set; }
    public DateTimeOffset? UpdatedAt { get; set; }
    public string? Cwd { get; set; }
    public ProjectReference Project { get; init; } = new();
    public string? Model { get; set; }
    public string? Provider { get; set; }
}

public sealed class ProjectReference
{
    public string? Name { get; set; }
    public string? Path { get; set; }
    public string? Fingerprint { get; set; }
}

public sealed class UniversalMessage
{
    public string Id { get; init; } = Guid.NewGuid().ToString("N");
    public string? ParentMessageId { get; set; }
    public MessageRole Role { get; init; }
    public DateTimeOffset? Timestamp { get; set; }
    public List<ContentPart> Content { get; init; } = [];
    public Dictionary<string, JsonElement> Metadata { get; init; } = [];
}

public sealed class ContentPart
{
    public ContentPartKind Type { get; init; }
    public string? Text { get; set; }
    public string? ToolName { get; set; }
    public string? ToolCallId { get; set; }
    public JsonElement? Arguments { get; set; }
    public Dictionary<string, JsonElement> Metadata { get; init; } = [];
}

public sealed class Attachment
{
    public string Name { get; init; } = "";
    public string? MediaType { get; init; }
    public string? SourcePath { get; init; }
}

public sealed class UnsupportedRecord
{
    public int LineNumber { get; init; }
    public string Reason { get; init; } = "";
    public string RawJson { get; init; } = "";
}

public enum AgentKind { OpenCode, Codex, ClaudeCode, ClaudeDesktop, ArchiveLibrary }
public enum MessageRole { System, User, Assistant, Tool }
public enum ContentPartKind { Text, Reasoning, ToolCall, ToolResult, File, Image, Command, CommandResult, Patch, Diff, System, Metadata }
