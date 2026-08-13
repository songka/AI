using System.Text.Json;
using AICodingSessionManager.Adapters.ClaudeCode;
using AICodingSessionManager.Adapters.Codex;
using AICodingSessionManager.Domain;
using Xunit;

namespace AICodingSessionManager.ParserTests;

public sealed class AdapterRichRecordTests
{
    [Fact]
    public async Task Codex_parser_preserves_tools_reasoning_commands_and_unknown_records()
    {
        var session = await new CodexAdapter().ReadSessionAsync(Fixture("codex", "rich-session.jsonl"));

        Assert.Equal("codex-rich", session.Session.Id);
        Assert.Equal("gpt-test", session.Session.Model);
        Assert.Contains(session.Messages.SelectMany(message => message.Content), part =>
            part.Type == ContentPartKind.Reasoning && part.Text!.Contains("Inspect before editing."));

        var functionCall = Assert.Single(session.Messages.SelectMany(message => message.Content),
            part => part.Type == ContentPartKind.ToolCall && part.ToolCallId == "call-1");
        Assert.Equal("read_file", functionCall.ToolName);
        Assert.Equal("README.md", functionCall.Arguments!.Value.GetProperty("path").GetString());

        var functionResult = Assert.Single(session.Messages.SelectMany(message => message.Content),
            part => part.Type == ContentPartKind.ToolResult && part.ToolCallId == "call-1");
        Assert.Contains("file contents", functionResult.Text);

        Assert.Contains(session.Messages.SelectMany(message => message.Content), part =>
            part.Type == ContentPartKind.Patch && part.ToolCallId == "call-2");
        Assert.Contains(session.Messages.SelectMany(message => message.Content), part =>
            part.Type == ContentPartKind.Command && part.Text == "dotnet test");

        Assert.Contains(session.UnsupportedRecords, record =>
            record.Reason.Contains("unknown_future_item") && record.RawJson.Contains("preserve"));
        Assert.Contains(session.UnsupportedRecords, record =>
            record.Reason.Contains("future_envelope") && record.RawJson.Contains("42"));
        Assert.Contains(session.UnsupportedRecords, record => record.Reason == "Invalid JSONL record");
    }

    [Fact]
    public async Task Claude_parser_preserves_tool_payload_metadata_and_unknown_records()
    {
        var session = await new ClaudeCodeAdapter().ReadSessionAsync(Fixture("claude", "rich-session.jsonl"));

        Assert.Equal("claude-test", session.Session.Model);
        Assert.Equal("feature/safe-parser", session.Metadata["gitBranch"].GetString());

        var assistant = Assert.Single(session.Messages, message => message.Id == "a-rich");
        Assert.True(assistant.Metadata["isSidechain"].GetBoolean());
        Assert.Equal(11, assistant.Metadata["usage"].GetProperty("input_tokens").GetInt32());
        Assert.Contains(assistant.Content, part =>
            part.Type == ContentPartKind.Reasoning && part.Text == "Check the fixture.");

        var toolCall = Assert.Single(assistant.Content, part => part.Type == ContentPartKind.ToolCall);
        Assert.Equal("README.md", toolCall.Arguments!.Value.GetProperty("file_path").GetString());

        var toolResult = Assert.Single(session.Messages.SelectMany(message => message.Content),
            part => part.Type == ContentPartKind.ToolResult);
        Assert.Contains("first line", toolResult.Text);
        Assert.True(toolResult.Metadata["is_error"].ValueKind == JsonValueKind.False);
        Assert.Equal(JsonValueKind.Array, toolResult.Metadata["raw_content"].ValueKind);

        Assert.Contains(session.UnsupportedRecords, record =>
            record.Reason.Contains("progress") && record.RawJson.Contains("working"));
        Assert.Contains(session.UnsupportedRecords, record =>
            record.Reason.Contains("future_block") && record.RawJson.Contains("preserve"));
        Assert.Contains(session.UnsupportedRecords, record => record.Reason == "Invalid JSONL record");
    }

    private static string Fixture(string agent, string fileName) =>
        Path.Combine(AppContext.BaseDirectory, "fixtures", agent, fileName);
}
