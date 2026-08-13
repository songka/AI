using System.IO.Compression;
using System.Text;
using AICodingSessionManager.Library;
using Xunit;

namespace AICodingSessionManager.Tests.Library;

public sealed class SessionArchiveLibraryTests
{
    [Fact]
    public async Task ImportAsync_ValidArchive_StoresContentAddressedCopyAndUpdatesIndex()
    {
        using var temp = new TemporaryDirectory();
        var source = await LibraryTestFixture.CreateArchiveAsync(temp.Path, "source.ai-session", "{\"raw\":1}");
        var libraryRoot = Path.Combine(temp.Path, "library");
        var library = new SessionArchiveLibrary(libraryRoot);

        var result = await library.ImportAsync(source, LibraryConflictStrategy.Skip);
        var entries = await library.ListAsync();

        Assert.Equal(LibraryImportOutcome.Imported, result.Outcome);
        var entry = Assert.Single(entries);
        Assert.Equal(result.Entry.Id, entry.Id);
        Assert.Matches("^[a-f0-9]{64}$", entry.Fingerprint);
        Assert.Matches("^[a-f0-9]{64}$", entry.ContentHash);
        var storedPath = library.GetArchivePath(entry);
        Assert.StartsWith(Path.GetFullPath(libraryRoot), storedPath, StringComparison.OrdinalIgnoreCase);
        Assert.True(File.Exists(storedPath));
        Assert.True(File.Exists(Path.Combine(libraryRoot, "index.json")));
    }

    [Fact]
    public async Task ImportAsync_DuplicateWithSkip_ReturnsExistingWithoutAddingRecord()
    {
        using var temp = new TemporaryDirectory();
        var source = await LibraryTestFixture.CreateArchiveAsync(temp.Path, "source.ai-session", "{}");
        var library = new SessionArchiveLibrary(Path.Combine(temp.Path, "library"));
        var first = await library.ImportAsync(source, LibraryConflictStrategy.Skip);

        var second = await library.ImportAsync(source, LibraryConflictStrategy.Skip);

        Assert.Equal(LibraryImportOutcome.Skipped, second.Outcome);
        Assert.Equal(first.Entry.Id, second.Entry.Id);
        Assert.Single(await library.ListAsync());
    }

    [Fact]
    public async Task ImportAsync_DuplicateWithKeepBoth_AddsRecordAndSharesContentObject()
    {
        using var temp = new TemporaryDirectory();
        var source = await LibraryTestFixture.CreateArchiveAsync(temp.Path, "source.ai-session", "{}");
        var library = new SessionArchiveLibrary(Path.Combine(temp.Path, "library"));
        await library.ImportAsync(source, LibraryConflictStrategy.Skip);

        var second = await library.ImportAsync(source, LibraryConflictStrategy.KeepBoth);
        var entries = await library.ListAsync();

        Assert.Equal(LibraryImportOutcome.Imported, second.Outcome);
        Assert.Equal(2, entries.Count);
        Assert.Single(Directory.EnumerateFiles(Path.Combine(temp.Path, "library", "objects"), "*.ai-session", SearchOption.AllDirectories));
    }

    [Fact]
    public async Task ImportAsync_SameFingerprintReplace_ReplacesOnlyLibraryCopyAndRemovesOrphanObject()
    {
        using var temp = new TemporaryDirectory();
        var firstArchive = await LibraryTestFixture.CreateArchiveAsync(temp.Path, "first.ai-session", "{\"raw\":1}");
        var secondArchive = await LibraryTestFixture.CreateArchiveAsync(temp.Path, "second.ai-session", "{\"raw\":2}");
        var libraryRoot = Path.Combine(temp.Path, "library");
        var library = new SessionArchiveLibrary(libraryRoot);
        var first = await library.ImportAsync(firstArchive, LibraryConflictStrategy.Skip);

        var replacement = await library.ImportAsync(secondArchive, LibraryConflictStrategy.ReplaceLibraryCopy);
        var entries = await library.ListAsync();

        Assert.Equal(LibraryImportOutcome.Replaced, replacement.Outcome);
        var entry = Assert.Single(entries);
        Assert.Equal(first.Entry.Fingerprint, entry.Fingerprint);
        Assert.NotEqual(first.Entry.ContentHash, entry.ContentHash);
        Assert.True(File.Exists(firstArchive));
        Assert.True(File.Exists(secondArchive));
        Assert.False(File.Exists(library.GetArchivePath(first.Entry)));
        Assert.True(File.Exists(library.GetArchivePath(entry)));
    }

    [Fact]
    public async Task ImportAsync_TamperedHash_RejectsWithoutCreatingLibraryState()
    {
        using var temp = new TemporaryDirectory();
        var source = await LibraryTestFixture.CreateArchiveAsync(temp.Path, "source.ai-session", "{\"raw\":1}");
        using (var archive = ZipFile.Open(source, ZipArchiveMode.Update))
        {
            var raw = archive.GetEntry("raw/provider/session.jsonl")!;
            raw.Delete();
            raw = archive.CreateEntry("raw/provider/session.jsonl");
            await using var writer = new StreamWriter(raw.Open(), Encoding.UTF8);
            await writer.WriteAsync("tampered");
        }

        var libraryRoot = Path.Combine(temp.Path, "library");
        var library = new SessionArchiveLibrary(libraryRoot);
        await Assert.ThrowsAsync<InvalidDataException>(() => library.ImportAsync(source, LibraryConflictStrategy.Skip));

        Assert.Empty(await library.ListAsync());
        Assert.False(Directory.Exists(Path.Combine(libraryRoot, "objects")));
        Assert.False(File.Exists(Path.Combine(libraryRoot, "index.json")));
    }

    [Fact]
    public async Task ImportAsync_TraversalArchive_RejectsWithoutCreatingLibraryState()
    {
        using var temp = new TemporaryDirectory();
        var source = Path.Combine(temp.Path, "unsafe.ai-session");
        await using (var stream = new FileStream(source, FileMode.CreateNew, FileAccess.Write, FileShare.None, 4096, true))
        using (var archive = new ZipArchive(stream, ZipArchiveMode.Create))
        {
            archive.CreateEntry("../outside.txt");
        }

        var libraryRoot = Path.Combine(temp.Path, "library");
        var library = new SessionArchiveLibrary(libraryRoot);
        await Assert.ThrowsAsync<InvalidDataException>(() => library.ImportAsync(source, LibraryConflictStrategy.Skip));

        Assert.False(Directory.Exists(libraryRoot));
    }

    [Fact]
    public async Task DeleteAsync_ExistingEntry_RequiresExplicitCallAndRemovesUnreferencedObject()
    {
        using var temp = new TemporaryDirectory();
        var source = await LibraryTestFixture.CreateArchiveAsync(temp.Path, "source.ai-session", "{}");
        var library = new SessionArchiveLibrary(Path.Combine(temp.Path, "library"));
        var imported = await library.ImportAsync(source, LibraryConflictStrategy.Skip);
        var storedPath = library.GetArchivePath(imported.Entry);

        var deleted = await library.DeleteAsync(imported.Entry.Id);

        Assert.True(deleted);
        Assert.Empty(await library.ListAsync());
        Assert.False(File.Exists(storedPath));
        Assert.True(File.Exists(source));
    }

    [Fact]
    public async Task ImportAsync_PreCancelled_DoesNotCreateLibraryState()
    {
        using var temp = new TemporaryDirectory();
        var source = await LibraryTestFixture.CreateArchiveAsync(temp.Path, "source.ai-session", "{}");
        var libraryRoot = Path.Combine(temp.Path, "library");
        var library = new SessionArchiveLibrary(libraryRoot);
        using var cancellation = new CancellationTokenSource();
        cancellation.Cancel();

        await Assert.ThrowsAnyAsync<OperationCanceledException>(() =>
            library.ImportAsync(source, LibraryConflictStrategy.Skip, cancellation.Token));

        Assert.False(Directory.Exists(libraryRoot));
    }

    [Fact]
    public async Task ImportAsync_ConcurrentKeepBoth_SerializesIndexUpdatesWithoutLostRecords()
    {
        using var temp = new TemporaryDirectory();
        var source = await LibraryTestFixture.CreateArchiveAsync(temp.Path, "source.ai-session", "{}");
        var libraryRoot = Path.Combine(temp.Path, "library");
        var libraries = Enumerable.Range(0, 8).Select(_ => new SessionArchiveLibrary(libraryRoot)).ToArray();

        await Task.WhenAll(libraries.Select(library =>
            library.ImportAsync(source, LibraryConflictStrategy.KeepBoth)));

        Assert.Equal(8, (await libraries[0].ListAsync()).Count);
    }
}
