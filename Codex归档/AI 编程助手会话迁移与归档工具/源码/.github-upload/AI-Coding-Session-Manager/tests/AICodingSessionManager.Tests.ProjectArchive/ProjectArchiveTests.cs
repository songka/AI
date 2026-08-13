using System.IO.Compression;
using System.Text.Json;
using AICodingSessionManager.ProjectArchive;
using AICodingSessionManager.Backup;
using AICodingSessionManager.Domain;
using Xunit;

namespace AICodingSessionManager.Tests.ProjectArchive;

public sealed class ProjectArchiveTests
{
    [Fact]
    public async Task WriteAsync_DefaultExclusions_PreservesFilesAndSkipsBuildTrees()
    {
        using var temp = new TemporaryDirectory();
        var project = temp.CreateDirectory("project");
        Directory.CreateDirectory(Path.Combine(project, "src"));
        Directory.CreateDirectory(Path.Combine(project, "node_modules", "package"));
        Directory.CreateDirectory(Path.Combine(project, "bin"));
        await File.WriteAllTextAsync(Path.Combine(project, "src", "app.cs"), "synthetic");
        await File.WriteAllTextAsync(Path.Combine(project, "node_modules", "package", "index.js"), "excluded");
        await File.WriteAllTextAsync(Path.Combine(project, "bin", "app.dll"), "excluded");
        var archivePath = Path.Combine(temp.Path, "project.ai-project");

        var result = await new ProjectArchiveWriter().WriteAsync(project, archivePath);
        var verified = await new ProjectArchiveVerifier().VerifyAsync(archivePath);

        Assert.Equal(result.Manifest.Entries.Count, verified.Manifest.Entries.Count);
        Assert.Contains(verified.Manifest.Entries, entry => entry.Path == "project/src/app.cs");
        Assert.DoesNotContain(verified.Manifest.Entries, entry => entry.Path.Contains("node_modules", StringComparison.Ordinal));
        Assert.DoesNotContain(verified.Manifest.Entries, entry => entry.Path.Contains("/bin/", StringComparison.Ordinal));
    }

    [Fact]
    public async Task VerifyAsync_TraversalEntry_RejectsArchive()
    {
        using var temp = new TemporaryDirectory();
        var archivePath = Path.Combine(temp.Path, "unsafe.ai-project");
        await using (var stream = new FileStream(archivePath, FileMode.CreateNew, FileAccess.Write))
        using (var archive = new ZipArchive(stream, ZipArchiveMode.Create))
            archive.CreateEntry("../outside.txt");

        await Assert.ThrowsAsync<InvalidDataException>(() => new ProjectArchiveVerifier().VerifyAsync(archivePath));
    }

    [Fact]
    public async Task DryRunAsync_ExistingFile_RequiresExplicitConflictStrategy()
    {
        using var temp = new TemporaryDirectory();
        var archivePath = await CreateArchiveAsync(temp);
        var destination = temp.CreateDirectory("restore");
        Directory.CreateDirectory(Path.Combine(destination, "src"));
        await File.WriteAllTextAsync(Path.Combine(destination, "src", "app.cs"), "local");

        var conflict = await new ProjectArchiveRestorer().DryRunAsync(archivePath, destination);
        var keepBoth = await new ProjectArchiveRestorer().DryRunAsync(archivePath, destination, ProjectRestoreConflictStrategy.KeepBoth);
        var skip = await new ProjectArchiveRestorer().DryRunAsync(archivePath, destination, ProjectRestoreConflictStrategy.Skip);

        Assert.True(conflict.HasConflicts);
        Assert.Contains(keepBoth.Items, item => item.DestinationPath.Contains("(2)", StringComparison.Ordinal));
        Assert.Contains(skip.Items, item => item.Action == ProjectRestoreAction.Skip);
    }

    [Fact]
    public async Task RestoreAsync_InjectedFailure_RemovesCreatedFilesAndLeavesNoOverwrite()
    {
        using var temp = new TemporaryDirectory();
        var archivePath = await CreateArchiveAsync(temp, includeSecondFile: true);
        var destination = temp.CreateDirectory("restore");
        var injector = new ThrowAfterFirstEntry();

        await Assert.ThrowsAsync<SyntheticFailure>(() =>
            new ProjectArchiveRestorer(faultInjector: injector).RestoreAsync(archivePath, destination));

        Assert.False(File.Exists(Path.Combine(destination, "src", "app.cs")));
        Assert.False(File.Exists(Path.Combine(destination, "README.md")));
        Assert.Empty(Directory.EnumerateFiles(destination, "*.tmp", SearchOption.AllDirectories));
    }

    [Fact]
    public async Task RestoreAsync_ValidArchive_RestoresOnlyProjectPayloadAndCreatesSnapshot()
    {
        using var temp = new TemporaryDirectory();
        var archivePath = await CreateArchiveAsync(temp);
        var destination = temp.CreateDirectory("restore");

        var result = await new ProjectArchiveRestorer().RestoreAsync(archivePath, destination);

        Assert.Equal("synthetic", await File.ReadAllTextAsync(Path.Combine(destination, "src", "app.cs")));
        Assert.True(File.Exists(result.RollbackSnapshotPath));
    }

    [Fact]
    public async Task DryRunAsync_AgentDataDirectory_RejectsBeforeWriting()
    {
        using var temp = new TemporaryDirectory();
        var archivePath = await CreateArchiveAsync(temp);
        var protectedPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".codex", "synthetic-restore-test");

        await Assert.ThrowsAsync<UnauthorizedAccessException>(() =>
            new ProjectArchiveRestorer().DryRunAsync(archivePath, protectedPath));
    }

    [Fact]
    public async Task WriteAsync_EmbeddedSession_PreservesVerifiedAiSessionBytes()
    {
        using var temp = new TemporaryDirectory();
        var project = temp.CreateDirectory("project-with-session");
        await File.WriteAllTextAsync(Path.Combine(project, "app.cs"), "synthetic");
        var raw = Path.Combine(temp.Path, "raw.jsonl");
        await File.WriteAllTextAsync(raw, "{\"synthetic\":true}");
        var sessionPath = Path.Combine(temp.Path, "session.ai-session");
        await new AiSessionArchiveWriter().WriteAsync(new UniversalSession
        {
            Session = new SessionDescriptor { Id = "embedded", SourceSessionId = "embedded", Source = AgentKind.Codex }
        }, [new ArchiveSourceFile("codex/raw.jsonl", raw)], sessionPath);
        var projectArchive = Path.Combine(temp.Path, "with-session.ai-project");

        await new ProjectArchiveWriter().WriteAsync(project, projectArchive, [new ProjectSessionArchive("session.ai-session", sessionPath)]);
        var verified = await new ProjectArchiveVerifier().VerifyAsync(projectArchive);
        using var zip = ZipFile.OpenRead(projectArchive);
        var embedded = zip.GetEntry("sessions/session.ai-session")!;
        var extracted = Path.Combine(temp.Path, "extracted.ai-session");
        await using (var input = embedded.Open())
        await using (var output = File.Create(extracted)) await input.CopyToAsync(output);

        Assert.Contains(verified.Manifest.Entries, entry => entry.Path == "sessions/session.ai-session");
        var session = await new AiSessionArchiveVerifier().VerifyAsync(extracted);
        Assert.Equal("embedded", session.Manifest.SessionId);
    }

    private static async Task<string> CreateArchiveAsync(TemporaryDirectory temp, bool includeSecondFile = false)
    {
        var project = temp.CreateDirectory($"project-{Guid.NewGuid():N}");
        Directory.CreateDirectory(Path.Combine(project, "src"));
        await File.WriteAllTextAsync(Path.Combine(project, "src", "app.cs"), "synthetic");
        if (includeSecondFile) await File.WriteAllTextAsync(Path.Combine(project, "README.md"), "second");
        var archivePath = Path.Combine(temp.Path, $"{Guid.NewGuid():N}.ai-project");
        await new ProjectArchiveWriter().WriteAsync(project, archivePath);
        return archivePath;
    }

    private sealed class ThrowAfterFirstEntry : IProjectArchiveFaultInjector
    {
        private int count;
        public void Checkpoint(string operation, string? path = null)
        {
            if (operation == "after-restore-entry" && Interlocked.Increment(ref count) == 1) throw new SyntheticFailure();
        }
    }

    private sealed class SyntheticFailure : Exception;
}

internal sealed class TemporaryDirectory : IDisposable
{
    public TemporaryDirectory()
    {
        Path = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "ai-project-tests", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(Path);
    }

    public string Path { get; }
    public string CreateDirectory(string name) => Directory.CreateDirectory(System.IO.Path.Combine(Path, name)).FullName;
    public void Dispose() { if (Directory.Exists(Path)) Directory.Delete(Path, true); }
}
