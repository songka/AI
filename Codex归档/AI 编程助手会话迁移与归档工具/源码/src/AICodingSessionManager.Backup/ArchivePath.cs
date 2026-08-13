namespace AICodingSessionManager.Backup;

internal static class ArchivePath
{
    public static string CombineAndValidate(string prefix, string relativePath, string parameterName)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(relativePath, parameterName);
        var normalized = relativePath.Replace('\\', '/');
        Validate(normalized, parameterName);
        return $"{prefix}/{normalized}";
    }

    public static void Validate(string entryPath, string parameterName)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(entryPath, parameterName);
        if (entryPath.StartsWith("/", StringComparison.Ordinal) ||
            entryPath.StartsWith('\\') ||
            Path.IsPathRooted(entryPath) ||
            entryPath.Contains('\\') ||
            entryPath.Contains('\0'))
        {
            throw new ArgumentException("Archive entry paths must be normalized relative paths.", parameterName);
        }

        var segments = entryPath.Split('/');
        if (segments.Any(segment =>
                segment.Length == 0 ||
                segment is "." or ".." ||
                segment.Contains(':')))
        {
            throw new ArgumentException("Archive entry paths cannot contain empty, traversal, or rooted segments.", parameterName);
        }
    }

    public static void ValidateZipEntry(string entryPath)
    {
        try
        {
            Validate(entryPath, nameof(entryPath));
        }
        catch (ArgumentException exception)
        {
            throw new InvalidDataException($"Unsafe ZIP entry path: {entryPath}", exception);
        }
    }
}
