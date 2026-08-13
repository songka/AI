namespace AICodingSessionManager.ProjectArchive;

/// <summary>Defensive limits applied while creating and reading project archives.</summary>
public sealed class ProjectArchiveLimits
{
    public int MaximumEntryCount { get; init; } = 100_000;
    public long MaximumEntryBytes { get; init; } = 2L * 1024 * 1024 * 1024;
    public long MaximumTotalBytes { get; init; } = 20L * 1024 * 1024 * 1024;

    internal void Validate()
    {
        if (MaximumEntryCount <= 0 || MaximumEntryBytes <= 0 || MaximumTotalBytes <= 0)
            throw new ArgumentOutOfRangeException(nameof(ProjectArchiveLimits), "All archive limits must be positive.");
    }
}

/// <summary>Options controlling project collection.</summary>
public sealed class ProjectArchiveCreateOptions
{
    public IReadOnlyCollection<string> ExcludedDirectoryNames { get; init; } =
        [".git", "node_modules", "bin", "obj", "dist", "build", ".vs"];
    public ProjectArchiveLimits Limits { get; init; } = new();
}

/// <summary>One explicitly selected session archive bundled with the project archive.</summary>
public sealed record ProjectSessionArchive(string FileName, string SourcePath);

/// <summary>Integrity metadata for one payload entry.</summary>
public sealed class ProjectArchiveEntry
{
    public string Path { get; init; } = string.Empty;
    public long Size { get; init; }
    public string Sha256 { get; init; } = string.Empty;
}

/// <summary>Manifest stored at the root of every <c>.ai-project</c> ZIP.</summary>
public sealed class ProjectArchiveManifest
{
    public string Format { get; init; } = ProjectArchiveWriter.FormatName;
    public string Version { get; init; } = ProjectArchiveWriter.CurrentVersion;
    public DateTimeOffset CreatedAt { get; init; }
    public string ProjectName { get; init; } = string.Empty;
    public List<ProjectArchiveEntry> Entries { get; init; } = [];
}

public sealed record ProjectArchiveWriteResult(string ArchivePath, ProjectArchiveManifest Manifest);
public sealed record ProjectArchiveVerificationResult(string ArchivePath, ProjectArchiveManifest Manifest);

public enum ProjectRestoreConflictStrategy { None, KeepBoth, Skip }
public enum ProjectRestoreAction { Create, Conflict, Skip }

/// <summary>One planned project file operation. Paths are relative to the selected restore directory.</summary>
public sealed record ProjectRestorePlanItem(
    string ArchivePath,
    string DestinationPath,
    ProjectRestoreAction Action,
    string Reason);

public sealed record ProjectRestorePlan(
    string ArchivePath,
    string DestinationDirectory,
    IReadOnlyList<ProjectRestorePlanItem> Items)
{
    public bool HasConflicts => Items.Any(item => item.Action == ProjectRestoreAction.Conflict);
}

public sealed record ProjectRestoreResult(ProjectRestorePlan Plan, string RollbackSnapshotPath);

/// <summary>Optional deterministic fault hook used by hosts and tests.</summary>
public interface IProjectArchiveFaultInjector
{
    void Checkpoint(string operation, string? path = null);
}
