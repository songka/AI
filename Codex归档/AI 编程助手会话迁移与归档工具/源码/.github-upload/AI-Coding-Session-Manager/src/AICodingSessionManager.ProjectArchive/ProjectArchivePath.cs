namespace AICodingSessionManager.ProjectArchive;

internal static class ProjectArchivePath
{
    public static string NormalizeRelative(string relativePath, string parameterName)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(relativePath, parameterName);
        var normalized = relativePath.Replace('\\', '/');
        Validate(normalized, parameterName);
        return normalized;
    }

    public static void Validate(string entryPath, string parameterName)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(entryPath, parameterName);
        if (entryPath.StartsWith('/') || entryPath.StartsWith('\\') || Path.IsPathRooted(entryPath) ||
            entryPath.Contains('\\') || entryPath.Contains('\0'))
            throw new ArgumentException("Archive paths must be normalized relative paths.", parameterName);

        var segments = entryPath.Split('/');
        if (segments.Any(segment => segment.Length == 0 || segment is "." or ".." || segment.Contains(':')))
            throw new ArgumentException("Archive paths cannot contain empty, traversal, or rooted segments.", parameterName);
    }

    public static void ValidateUntrusted(string entryPath)
    {
        try { Validate(entryPath, nameof(entryPath)); }
        catch (ArgumentException exception) { throw new InvalidDataException($"Unsafe archive path: {entryPath}", exception); }
    }

    public static string ResolveBelowRoot(string root, string normalizedRelativePath)
    {
        ValidateUntrusted(normalizedRelativePath);
        var fullRoot = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        var candidate = Path.GetFullPath(Path.Combine(fullRoot, normalizedRelativePath.Replace('/', Path.DirectorySeparatorChar)));
        if (!candidate.StartsWith(fullRoot, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException($"Archive path escapes the destination: {normalizedRelativePath}");
        return candidate;
    }
}
