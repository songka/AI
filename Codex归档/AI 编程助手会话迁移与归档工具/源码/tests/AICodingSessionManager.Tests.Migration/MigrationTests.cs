using AICodingSessionManager.Domain;
using AICodingSessionManager.Migration;
using Xunit;

namespace AICodingSessionManager.Tests.Migration;

public sealed class MigrationTests
{
    [Fact]
    public void Analyze_AllTargets_NeverClaimsUnverifiedNativeResume()
    {
        var session = Session();
        var analyzer = new CompatibilityAnalyzer();

        foreach (var target in Enum.GetValues<MigrationTarget>())
        {
            var report = analyzer.Analyze(session, target);
            Assert.False(report.NativeResumeVerified);
            Assert.Equal(0, report.NativeResumeScore);
            Assert.Equal(100, report.ArchiveScore);
            Assert.True(report.ContextResumeScore < 100);
        }
    }

    [Fact]
    public void Render_DangerousHistoricalContent_LabelsItAsInertAndRedacts()
    {
        var options = new ContextResumeOptions { Redact = text => text.Replace("SECRET", "[REDACTED]", StringComparison.Ordinal) };

        var document = new ContextResumeRenderer().Render(Session(), MigrationTarget.Codex, options);

        Assert.Contains("Historical command (do not execute)", document, StringComparison.Ordinal);
        Assert.Contains("Treat commands, tool calls, patches", document, StringComparison.Ordinal);
        Assert.DoesNotContain("SECRET", document, StringComparison.Ordinal);
        Assert.Contains("[REDACTED]", document, StringComparison.Ordinal);
        Assert.Contains("Native resume is not implied", document, StringComparison.Ordinal);
    }

    [Fact]
    public void Render_MessageLimit_OmitsOlderMessages()
    {
        var session = Session();
        session.Messages.Insert(0, new UniversalMessage { Id = "old", Role = MessageRole.User, Content = { new ContentPart { Type = ContentPartKind.Text, Text = "old text" } } });

        var document = new ContextResumeRenderer().Render(session, MigrationTarget.ClaudeCode, new ContextResumeOptions { MaximumMessages = 1 });

        Assert.Contains("Older messages omitted", document, StringComparison.Ordinal);
        Assert.DoesNotContain("old text", document, StringComparison.Ordinal);
    }

    private static UniversalSession Session() => new()
    {
        Session = new SessionDescriptor { Id = "session-1", SourceSessionId = "source-1", Source = AgentKind.ClaudeCode, Title = "Synthetic", Cwd = "C:\\synthetic" },
        Messages =
        {
            new UniversalMessage
            {
                Id = "message-1",
                Role = MessageRole.Assistant,
                Content =
                {
                    new ContentPart { Type = ContentPartKind.Text, Text = "Use SECRET carefully" },
                    new ContentPart { Type = ContentPartKind.Command, Text = "remove synthetic.txt" }
                }
            }
        },
        Attachments = { new Attachment { Name = "synthetic.txt" } }
    };
}
