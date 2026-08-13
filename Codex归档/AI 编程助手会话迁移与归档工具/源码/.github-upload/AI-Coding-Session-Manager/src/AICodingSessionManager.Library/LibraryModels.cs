namespace AICodingSessionManager.Library;

/// <summary>Controls how an import handles an existing logical session fingerprint.</summary>
public enum LibraryConflictStrategy
{
    /// <summary>Creates another library record, sharing the content object when bytes are identical.</summary>
    KeepBoth,

    /// <summary>Returns the existing library record without changing the library.</summary>
    Skip,

    /// <summary>Repoints the existing record to the imported archive and removes an unreferenced old library object.</summary>
    ReplaceLibraryCopy,
}

/// <summary>Describes the result of an archive import.</summary>
public enum LibraryImportOutcome
{
    /// <summary>A new library record was added.</summary>
    Imported,

    /// <summary>An existing logical session was retained.</summary>
    Skipped,

    /// <summary>An existing library record was replaced.</summary>
    Replaced,
}

/// <summary>Describes one program-owned archive library record.</summary>
public sealed class SessionArchiveLibraryEntry
{
    /// <summary>Gets the unique library record identifier.</summary>
    public string Id { get; init; } = string.Empty;

    /// <summary>Gets the logical session fingerprint used for conflict detection.</summary>
    public string Fingerprint { get; init; } = string.Empty;

    /// <summary>Gets the SHA-256 digest of the complete archive bytes.</summary>
    public string ContentHash { get; init; } = string.Empty;

    /// <summary>Gets the normalized path to the content object, relative to the library root.</summary>
    public string ObjectPath { get; init; } = string.Empty;

    /// <summary>Gets the Universal Session identifier from the verified archive manifest.</summary>
    public string SessionId { get; init; } = string.Empty;

    /// <summary>Gets the source provider from the verified archive manifest.</summary>
    public string Source { get; init; } = string.Empty;

    /// <summary>Gets the UTC import timestamp.</summary>
    public DateTimeOffset ImportedAt { get; init; }
}

/// <summary>Reports an archive import decision and resulting record.</summary>
/// <param name="Outcome">The conflict resolution outcome.</param>
/// <param name="Entry">The resulting library record.</param>
public sealed record SessionArchiveLibraryImportResult(
    LibraryImportOutcome Outcome,
    SessionArchiveLibraryEntry Entry);

internal sealed class SessionArchiveLibraryIndex
{
    public string Format { get; init; } = "ai-session-library";

    public string Version { get; init; } = "1.0";

    public List<SessionArchiveLibraryEntry> Entries { get; init; } = [];
}
