using System.Text.Json;
using AICodingSessionManager.Domain;
using Xunit;

namespace AICodingSessionManager.ParserTests;

public sealed class UniversalSessionJsonTests
{
    [Fact]
    public void Serialize_ValidSession_UsesStableSnakeCaseWireFormat()
    {
        var session = CreateSession();
        session.Metadata["z_provider_field"] = JsonSerializer.SerializeToElement(2);
        session.Metadata["a_provider_field"] = JsonSerializer.SerializeToElement(1);

        var first = UniversalSessionJson.Serialize(session);
        var second = UniversalSessionJson.Serialize(session);

        Assert.Equal(first, second);
        Assert.Contains("\"source_session_id\"", first);
        Assert.Contains("\"tool_call\"", first);
        Assert.True(first.IndexOf("a_provider_field", StringComparison.Ordinal) < first.IndexOf("z_provider_field", StringComparison.Ordinal));
    }

    [Fact]
    public void Deserialize_SerializedSession_PreservesUnknownMetadata()
    {
        var original = CreateSession();
        original.Metadata["provider_unknown"] = JsonSerializer.SerializeToElement(new { nested = true });

        var restored = UniversalSessionJson.Deserialize(UniversalSessionJson.Serialize(original));

        Assert.True(restored.Metadata["provider_unknown"].GetProperty("nested").GetBoolean());
        Assert.Equal(ContentPartKind.ToolCall, restored.Messages[0].Content[0].Type);
    }

    [Theory]
    [InlineData("other-format", "1.0")]
    [InlineData("ai-coding-session", "9.0")]
    public void Validate_UnknownFormatOrVersion_RejectsDocument(string format, string version)
    {
        var session = new UniversalSession
        {
            Format = format,
            Version = version,
            Session = new SessionDescriptor { Id = "session-1", Source = AgentKind.Codex }
        };

        Assert.Throws<InvalidDataException>(() => UniversalSessionJson.Validate(session));
    }

    private static UniversalSession CreateSession() => new()
    {
        Session = new SessionDescriptor
        {
            Id = "session-1",
            SourceSessionId = "source-1",
            Source = AgentKind.Codex,
            CreatedAt = DateTimeOffset.Parse("2026-08-13T01:02:03Z")
        },
        Messages =
        [
            new UniversalMessage
            {
                Id = "message-1",
                Role = MessageRole.Assistant,
                Content =
                [
                    new ContentPart
                    {
                        Type = ContentPartKind.ToolCall,
                        ToolName = "shell",
                        ToolCallId = "call-1",
                        Arguments = JsonSerializer.SerializeToElement(new { command = "dotnet test" })
                    }
                ]
            }
        ]
    };
}
