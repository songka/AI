using System.IO.Compression;
using System.Text;
using System.Text.Json;
using AICodingSessionManager.Backup;
using Xunit;

namespace AICodingSessionManager.Tests.Export;

public sealed class ArchiveTests
{
    [Fact]
    public async Task WriteAsync_ValidInput_WritesVerifiableArchiveWithExactRawBytesAndExports()
    {
        using var directory = new TemporaryDirectory();
        var rawPath = Path.Combine(directory.Path, "session.jsonl");
        var rawBytes = new byte[] { 0, 1, 2, 10, 13, 255 };
        await File.WriteAllBytesAsync(rawPath, rawBytes);
        var archivePath = Path.Combine(directory.Path, "sample.ai-session");

        var result = await new AiSessionArchiveWriter().WriteAsync(
            TestSessionFactory.Create(),
            [new ArchiveSourceFile("provider/session.jsonl", rawPath)],
            archivePath);

        Assert.Equal(archivePath, result.ArchivePath);
        Assert.True(File.Exists(archivePath));
        var verified = await new AiSessionArchiveVerifier().VerifyAsync(archivePath);
        Assert.Equal("ai-session-archive", verified.Manifest.Format);
        Assert.Equal("1.0", verified.Manifest.Version);

        using var archive = ZipFile.OpenRead(archivePath);
        var names = archive.Entries.Select(entry => entry.FullName).ToArray();
        Assert.Contains("manifest.json", names);
        Assert.Contains("universal/session.json", names);
        Assert.Contains("raw/provider/session.jsonl", names);
        Assert.Contains("exports/session.json", names);
        Assert.Contains("exports/session.md", names);
        Assert.Contains("exports/session.html", names);

        await using var rawStream = archive.GetEntry("raw/provider/session.jsonl")!.Open();
        using var rawCopy = new MemoryStream();
        await rawStream.CopyToAsync(rawCopy);
        Assert.Equal(rawBytes, rawCopy.ToArray());
    }

    [Fact]
    public async Task WriteAsync_TraversalEntry_RejectsInputAndCreatesNoArchive()
    {
        using var directory = new TemporaryDirectory();
        var rawPath = Path.Combine(directory.Path, "session.jsonl");
        await File.WriteAllTextAsync(rawPath, "{}", Encoding.UTF8);
        var archivePath = Path.Combine(directory.Path, "sample.ai-session");

        await Assert.ThrowsAsync<ArgumentException>(() => new AiSessionArchiveWriter().WriteAsync(
            TestSessionFactory.Create(),
            [new ArchiveSourceFile("../outside.jsonl", rawPath)],
            archivePath));

        Assert.False(File.Exists(archivePath));
        Assert.Empty(Directory.EnumerateFiles(directory.Path, "*.tmp"));
    }

    [Fact]
    public async Task WriteAsync_FailureBeforeCommit_PreservesExistingArchive()
    {
        using var directory = new TemporaryDirectory();
        var archivePath = Path.Combine(directory.Path, "sample.ai-session");
        var original = Encoding.UTF8.GetBytes("existing archive");
        await File.WriteAllBytesAsync(archivePath, original);

        await Assert.ThrowsAsync<FileNotFoundException>(() => new AiSessionArchiveWriter().WriteAsync(
            TestSessionFactory.Create(),
            [new ArchiveSourceFile("provider/missing.jsonl", Path.Combine(directory.Path, "missing.jsonl"))],
            archivePath));

        Assert.Equal(original, await File.ReadAllBytesAsync(archivePath));
    }

    [Fact]
    public async Task VerifyAsync_ZipTraversalEntry_RejectsArchive()
    {
        using var directory = new TemporaryDirectory();
        var archivePath = Path.Combine(directory.Path, "malicious.ai-session");
        await using (var stream = new FileStream(archivePath, FileMode.CreateNew, FileAccess.Write, FileShare.None, 4096, true))
        using (var archive = new ZipArchive(stream, ZipArchiveMode.Create))
        {
            archive.CreateEntry("../outside.txt");
        }

        await Assert.ThrowsAsync<InvalidDataException>(
            () => new AiSessionArchiveVerifier().VerifyAsync(archivePath));
    }

    [Fact]
    public async Task WriteAsync_DuplicateEntryPath_RejectsInput()
    {
        using var directory = new TemporaryDirectory();
        var firstPath = Path.Combine(directory.Path, "first.jsonl");
        var secondPath = Path.Combine(directory.Path, "second.jsonl");
        await File.WriteAllTextAsync(firstPath, "{\"first\":true}", Encoding.UTF8);
        await File.WriteAllTextAsync(secondPath, "{\"second\":true}", Encoding.UTF8);

        await Assert.ThrowsAsync<ArgumentException>(() => new AiSessionArchiveWriter().WriteAsync(
            TestSessionFactory.Create(),
            [
                new ArchiveSourceFile("provider/session.jsonl", firstPath),
                new ArchiveSourceFile("PROVIDER/SESSION.JSONL", secondPath),
            ],
            Path.Combine(directory.Path, "sample.ai-session")));
    }

    [Fact]
    public async Task VerifyAsync_DuplicateZipEntry_RejectsArchive()
    {
        using var directory = new TemporaryDirectory();
        var archivePath = Path.Combine(directory.Path, "duplicate.ai-session");
        await using (var stream = new FileStream(archivePath, FileMode.CreateNew, FileAccess.Write, FileShare.None, 4096, true))
        using (var archive = new ZipArchive(stream, ZipArchiveMode.Create))
        {
            archive.CreateEntry("raw/session.jsonl");
            archive.CreateEntry("RAW/SESSION.JSONL");
        }

        await Assert.ThrowsAsync<InvalidDataException>(
            () => new AiSessionArchiveVerifier().VerifyAsync(archivePath));
    }

    [Fact]
    public async Task VerifyAsync_EntryBeyondConfiguredLimit_RejectsArchive()
    {
        using var directory = new TemporaryDirectory();
        var archivePath = Path.Combine(directory.Path, "oversized.ai-session");
        await using (var stream = new FileStream(archivePath, FileMode.CreateNew, FileAccess.Write, FileShare.None, 4096, true))
        using (var archive = new ZipArchive(stream, ZipArchiveMode.Create))
        {
            var entry = archive.CreateEntry("raw/session.jsonl");
            await using var entryStream = entry.Open();
            await entryStream.WriteAsync(new byte[32]);
        }

        var verifier = new AiSessionArchiveVerifier(new ArchiveVerificationLimits
        {
            MaximumEntryCount = 10,
            MaximumEntryBytes = 16,
            MaximumTotalBytes = 1024,
        });
        await Assert.ThrowsAsync<InvalidDataException>(() => verifier.VerifyAsync(archivePath));
    }

    [Fact]
    public async Task VerifyAsync_TamperedPayload_RejectsArchive()
    {
        using var directory = new TemporaryDirectory();
        var rawPath = Path.Combine(directory.Path, "session.jsonl");
        await File.WriteAllTextAsync(rawPath, "{\"original\":true}", Encoding.UTF8);
        var archivePath = Path.Combine(directory.Path, "sample.ai-session");
        await new AiSessionArchiveWriter().WriteAsync(
            TestSessionFactory.Create(),
            [new ArchiveSourceFile("session.jsonl", rawPath)],
            archivePath);

        using (var archive = ZipFile.Open(archivePath, ZipArchiveMode.Update))
        {
            var entry = archive.GetEntry("raw/session.jsonl")!;
            entry.Delete();
            entry = archive.CreateEntry("raw/session.jsonl");
            await using var writer = new StreamWriter(entry.Open(), Encoding.UTF8);
            await writer.WriteAsync("tampered");
        }

        await Assert.ThrowsAsync<InvalidDataException>(
            () => new AiSessionArchiveVerifier().VerifyAsync(archivePath));
    }

    [Fact]
    public async Task Manifest_ContainsSizeAndSha256ForEveryPayloadEntry()
    {
        using var directory = new TemporaryDirectory();
        var rawPath = Path.Combine(directory.Path, "session.jsonl");
        await File.WriteAllTextAsync(rawPath, "{}", Encoding.UTF8);
        var archivePath = Path.Combine(directory.Path, "sample.ai-session");
        await new AiSessionArchiveWriter().WriteAsync(
            TestSessionFactory.Create(),
            [new ArchiveSourceFile("session.jsonl", rawPath)],
            archivePath);

        using var archive = ZipFile.OpenRead(archivePath);
        await using var manifestStream = archive.GetEntry("manifest.json")!.Open();
        using var manifestDocument = await JsonDocument.ParseAsync(manifestStream);
        foreach (var entry in manifestDocument.RootElement.GetProperty("entries").EnumerateArray())
        {
            Assert.True(entry.GetProperty("size").GetInt64() >= 0);
            Assert.Matches("^[a-f0-9]{64}$", entry.GetProperty("sha256").GetString()!);
        }
    }
}

internal sealed class TemporaryDirectory : IDisposable
{
    public TemporaryDirectory()
    {
        Path = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "ai-session-tests", Guid.NewGuid().ToString("N"));
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
