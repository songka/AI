using AICodingSessionManager.Domain;
using AICodingSessionManager.Library;
using Xunit;

namespace AICodingSessionManager.Tests.Library;

public sealed class ArchiveLibraryAdapterTests
{
    [Fact]
    public async Task ImportedArchive_ListAndRead_ReturnsVerifiedOfflineSessionAndRaw()
    {
        using var temp = new TemporaryDirectory();
        var sourceDirectory = Directory.CreateDirectory(Path.Combine(temp.Path, "source")).FullName;
        var archive = await LibraryTestFixture.CreateArchiveAsync(sourceDirectory, "sample.ai-session", "synthetic raw", "offline-session");
        var libraryRoot = Path.Combine(temp.Path, "library");
        await new SessionArchiveLibrary(libraryRoot).ImportAsync(archive, LibraryConflictStrategy.KeepBoth);
        var adapter = new ArchiveLibraryAdapter(libraryRoot);

        var references = new List<SessionReference>();
        await foreach (var reference in adapter.ListSessionsAsync()) references.Add(reference);
        var item = Assert.Single(references);
        var session = await adapter.ReadSessionAsync(item.SourcePath);
        var raw = await adapter.ReadRawSessionAsync(item.SourcePath);

        Assert.Equal("offline-session", session.Session.Id);
        Assert.Contains("synthetic raw", raw, StringComparison.Ordinal);
        Assert.Equal(AgentKind.ArchiveLibrary, adapter.Agent);
    }
}
