namespace AICodingSessionManager.Backup;

/// <summary>Identifies a provider source file that must be preserved byte-for-byte.</summary>
/// <param name="ArchivePath">The relative path below the archive's <c>raw/</c> directory.</param>
/// <param name="SourcePath">The local source file path.</param>
public sealed record ArchiveSourceFile(string ArchivePath, string SourcePath);

/// <summary>Identifies an additional caller-provided export.</summary>
/// <param name="ArchivePath">The relative path below the archive's <c>exports/</c> directory.</param>
/// <param name="Content">The export bytes.</param>
/// <param name="MediaType">The export media type.</param>
public sealed record ArchiveExportFile(string ArchivePath, ReadOnlyMemory<byte> Content, string MediaType);

/// <summary>Describes the contents and integrity metadata of an AI session archive.</summary>
public sealed class AiSessionArchiveManifest
{
    /// <summary>Gets the archive format identifier.</summary>
    public string Format { get; init; } = AiSessionArchiveWriter.FormatName;

    /// <summary>Gets the archive format version.</summary>
    public string Version { get; init; } = AiSessionArchiveWriter.CurrentVersion;

    /// <summary>Gets the UTC time at which the archive was created.</summary>
    public DateTimeOffset CreatedAt { get; init; }

    /// <summary>Gets the provider-neutral session identifier.</summary>
    public string SessionId { get; init; } = string.Empty;

    /// <summary>Gets the source provider name.</summary>
    public string Source { get; init; } = string.Empty;

    /// <summary>Gets integrity metadata for every payload entry.</summary>
    public List<AiSessionArchiveEntry> Entries { get; init; } = [];
}

/// <summary>Describes one payload entry in an AI session archive.</summary>
public sealed class AiSessionArchiveEntry
{
    /// <summary>Gets the normalized ZIP entry path.</summary>
    public string Path { get; init; } = string.Empty;

    /// <summary>Gets the uncompressed byte size.</summary>
    public long Size { get; init; }

    /// <summary>Gets the lowercase hexadecimal SHA-256 digest.</summary>
    public string Sha256 { get; init; } = string.Empty;

    /// <summary>Gets the entry media type.</summary>
    public string MediaType { get; init; } = "application/octet-stream";
}

/// <summary>Reports a successfully committed archive.</summary>
/// <param name="ArchivePath">The full destination path.</param>
/// <param name="Manifest">The verified archive manifest.</param>
public sealed record AiSessionArchiveWriteResult(string ArchivePath, AiSessionArchiveManifest Manifest);

/// <summary>Reports a successfully verified archive.</summary>
/// <param name="ArchivePath">The full verified archive path.</param>
/// <param name="Manifest">The verified archive manifest.</param>
public sealed record AiSessionArchiveVerificationResult(string ArchivePath, AiSessionArchiveManifest Manifest);

/// <summary>Defines defensive bounds used while verifying untrusted ZIP files.</summary>
public sealed class ArchiveVerificationLimits
{
    /// <summary>Gets or sets the maximum ZIP entry count.</summary>
    public int MaximumEntryCount { get; init; } = 10_000;

    /// <summary>Gets or sets the maximum uncompressed size of one entry.</summary>
    public long MaximumEntryBytes { get; init; } = 512L * 1024 * 1024;

    /// <summary>Gets or sets the maximum aggregate uncompressed size.</summary>
    public long MaximumTotalBytes { get; init; } = 2L * 1024 * 1024 * 1024;
}
