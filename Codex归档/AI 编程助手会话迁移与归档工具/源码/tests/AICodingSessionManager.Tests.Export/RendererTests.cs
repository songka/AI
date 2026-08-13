using System.Text.Json;
using AICodingSessionManager.Export;
using Xunit;

namespace AICodingSessionManager.Tests.Export;

public sealed class RendererTests
{
    [Fact]
    public void JsonRenderer_SameSession_ProducesDeterministicSnakeCaseJson()
    {
        var session = TestSessionFactory.Create();
        var renderer = new JsonSessionRenderer();

        var first = renderer.Render(session);
        var second = renderer.Render(session);

        Assert.Equal(first, second);
        Assert.Contains("\"source_session_id\": \"provider-001\"", first, StringComparison.Ordinal);
        Assert.Contains("\"source\": \"claude_code\"", first, StringComparison.Ordinal);
        Assert.DoesNotContain("SourceSessionId", first, StringComparison.Ordinal);
        using var document = JsonDocument.Parse(first);
        Assert.Equal("ai-coding-session", document.RootElement.GetProperty("format").GetString());
    }

    [Fact]
    public void MarkdownRenderer_SessionWithMessages_ProducesReadableProviderNeutralDocument()
    {
        var markdown = new MarkdownSessionRenderer().Render(TestSessionFactory.Create());

        Assert.Contains("# Review <unsafe> & archive", markdown, StringComparison.Ordinal);
        Assert.Contains("**Source:** Claude Code", markdown, StringComparison.Ordinal);
        Assert.Contains("## User", markdown, StringComparison.Ordinal);
        Assert.Contains("Hello <script>alert('xss')</script> & goodbye", markdown, StringComparison.Ordinal);
        Assert.Contains("Tool call: `read<file>`", markdown, StringComparison.Ordinal);
    }

    [Fact]
    public void HtmlRenderer_UntrustedSourceFields_EncodesMarkupAndHasNoExternalDependencies()
    {
        var html = new HtmlSessionRenderer().Render(TestSessionFactory.Create("<script>title()</script>"));

        Assert.Contains("&lt;script&gt;title()&lt;/script&gt;", html, StringComparison.Ordinal);
        Assert.Contains("&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;", html, StringComparison.Ordinal);
        Assert.Contains("read&lt;file&gt;", html, StringComparison.Ordinal);
        Assert.DoesNotContain("<script>title()", html, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("<script>alert", html, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("http://", html, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("https://", html, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("src=", html, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("id=\"search\"", html, StringComparison.Ordinal);
        Assert.Contains("data-theme", html, StringComparison.Ordinal);
        Assert.Contains("@media print", html, StringComparison.Ordinal);
        Assert.Contains("<details", html, StringComparison.Ordinal);
        Assert.Contains("href=\"#message-1\"", html, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData(null)]
    public void Render_NullSession_ThrowsArgumentNullException(string? _)
    {
        Assert.Throws<ArgumentNullException>(() => new JsonSessionRenderer().Render(null!));
        Assert.Throws<ArgumentNullException>(() => new MarkdownSessionRenderer().Render(null!));
        Assert.Throws<ArgumentNullException>(() => new HtmlSessionRenderer().Render(null!));
    }
}
