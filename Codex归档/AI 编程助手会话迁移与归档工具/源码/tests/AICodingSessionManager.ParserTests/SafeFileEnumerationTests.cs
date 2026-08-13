using AICodingSessionManager.Domain;
using Xunit;

namespace AICodingSessionManager.ParserTests;

public sealed class SafeFileEnumerationTests : IDisposable
{
    private readonly string _root = Path.Combine(Path.GetTempPath(), "AICSM-tests", Guid.NewGuid().ToString("N"));

    [Fact]
    public void EnumerateFiles_NestedTree_ReturnsOnlyMatchingFiles()
    {
        Directory.CreateDirectory(Path.Combine(_root, "nested"));
        File.WriteAllText(Path.Combine(_root, "one.jsonl"), "{}");
        File.WriteAllText(Path.Combine(_root, "nested", "two.jsonl"), "{}");
        File.WriteAllText(Path.Combine(_root, "ignored.txt"), "ignored");

        var files = SafeFileEnumeration.EnumerateFiles(_root, "*.jsonl")
            .Select(file => Path.GetFileName(file)!)
            .Order()
            .ToArray();

        Assert.Equal(["one.jsonl", "two.jsonl"], files);
    }

    [Fact]
    public void EnumerateFiles_CancelledToken_ThrowsCancellation()
    {
        Directory.CreateDirectory(_root);
        using var source = new CancellationTokenSource();
        source.Cancel();

        Assert.Throws<OperationCanceledException>(() => SafeFileEnumeration.EnumerateFiles(_root, "*.jsonl", source.Token).ToArray());
    }

    public void Dispose()
    {
        if (Directory.Exists(_root)) Directory.Delete(_root, recursive: true);
    }
}
