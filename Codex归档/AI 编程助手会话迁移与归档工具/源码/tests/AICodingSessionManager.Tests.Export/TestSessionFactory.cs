using System.Text.Json;
using AICodingSessionManager.Domain;

namespace AICodingSessionManager.Tests.Export;

internal static class TestSessionFactory
{
    public static UniversalSession Create(string title = "Review <unsafe> & archive")
    {
        using var priority = JsonDocument.Parse("\"high\"");
        using var arguments = JsonDocument.Parse("{\"path\":\"src/app.cs\"}");

        return new UniversalSession
        {
            Session = new SessionDescriptor
            {
                Id = "session-001",
                SourceSessionId = "provider-001",
                Source = AgentKind.ClaudeCode,
                Title = title,
                CreatedAt = DateTimeOffset.Parse("2026-08-13T01:02:03+00:00"),
                UpdatedAt = DateTimeOffset.Parse("2026-08-13T02:03:04+00:00"),
                Cwd = "C:\\workspace\\<sample>",
                Model = "model&one",
                Provider = "provider<one>",
                Project = new ProjectReference
                {
                    Name = "sample & project",
                    Path = "C:\\workspace\\sample",
                    Fingerprint = "fingerprint-001",
                },
            },
            Metadata = { ["priority"] = priority.RootElement.Clone() },
            Messages =
            {
                new UniversalMessage
                {
                    Id = "message-001",
                    Role = MessageRole.User,
                    Timestamp = DateTimeOffset.Parse("2026-08-13T01:02:04+00:00"),
                    Content =
                    {
                        new ContentPart
                        {
                            Type = ContentPartKind.Text,
                            Text = "Hello <script>alert('xss')</script> & goodbye",
                        },
                        new ContentPart
                        {
                            Type = ContentPartKind.ToolCall,
                            ToolName = "read<file>",
                            ToolCallId = "tool&1",
                            Arguments = arguments.RootElement.Clone(),
                        },
                    },
                },
            },
        };
    }
}
