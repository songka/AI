using AICodingSessionManager.Backup;
using AICodingSessionManager.Domain;

namespace AICodingSessionManager.Tests.Library;

internal static class LibraryTestFixture
{
    public static async Task<string> CreateArchiveAsync(
        string directory,
        string fileName,
        string rawContent,
        string sessionId = "session-001")
    {
        var rawPath = Path.Combine(directory, $"{fileName}.jsonl");
        await File.WriteAllTextAsync(rawPath, rawContent);
        var archivePath = Path.Combine(directory, fileName);
        await new AiSessionArchiveWriter().WriteAsync(
            CreateSession(sessionId),
            [new ArchiveSourceFile("provider/session.jsonl", rawPath)],
            archivePath);
        return archivePath;
    }

    public static UniversalSession CreateSession(string sessionId) => new()
    {
        Session = new SessionDescriptor
        {
            Id = sessionId,
            SourceSessionId = $"source-{sessionId}",
            Source = AgentKind.Codex,
            Title = "Synthetic session",
            CreatedAt = DateTimeOffset.Parse("2026-08-13T01:00:00Z"),
            UpdatedAt = DateTimeOffset.Parse("2026-08-13T02:00:00Z"),
        },
        Messages =
        {
            new UniversalMessage
            {
                Id = "message-001",
                Role = MessageRole.User,
                Content = { new ContentPart { Type = ContentPartKind.Text, Text = "Synthetic content" } },
            },
        },
    };
}

internal sealed class TemporaryDirectory : IDisposable
{
    public TemporaryDirectory()
    {
        Path = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "ai-session-library-tests", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(Path);
    }

    public string Path { get; }

    public void Dispose()
    {
        if (Directory.Exists(Path))
        {
            Directory.Delete(Path, true);
        }
    }
}
