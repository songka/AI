using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace NewAPIClientConfigurator.Core;

internal static class AppPaths
{
    private const string AppName = "NewAPIClientConfigurator";
    private const string TokenFileName = "gateway-token.bin";
    private const string CacheFileName = "model-capabilities.json";

    public static string AppDirectory
    {
        get
        {
            var root = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), ".newapi-configurator");
            Directory.CreateDirectory(root);
            return root;
        }
    }

    public static string CachePath => Path.Combine(AppDirectory, CacheFileName);
    public static string TokenPath => Path.Combine(AppDirectory, TokenFileName);
    public static string BackupRoot
    {
        get
        {
            var root = Path.Combine(AppDirectory, "backups");
            Directory.CreateDirectory(root);
            return root;
        }
    }

    public static string CodexConfigPath => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".codex", "config.toml");
    public static string ClaudeSettingsPath => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".claude", "settings.json");
    public static string OpenCodeConfigPath => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".config", "opencode", "opencode.json");

    public static void SaveCache(ScanCache cache)
    {
        File.WriteAllText(CachePath, JsonSerializer.Serialize(cache, JsonOptions.Indented), Encoding.UTF8);
    }

    public static ScanCache? LoadCache()
    {
        try
        {
            var text = File.ReadAllText(CachePath, Encoding.UTF8);
            return JsonSerializer.Deserialize<ScanCache>(text, JsonOptions.Default);
        }
        catch
        {
            return null;
        }
    }

    public static void SaveToken(string token)
    {
        if (string.IsNullOrWhiteSpace(token))
        {
            return;
        }

        var protectedBytes = ProtectedData.Protect(Encoding.UTF8.GetBytes(token), optionalEntropy: null, DataProtectionScope.CurrentUser);
        File.WriteAllBytes(TokenPath, protectedBytes);
    }

    public static string LoadToken()
    {
        try
        {
            if (!File.Exists(TokenPath))
            {
                return string.Empty;
            }

            var bytes = ProtectedData.Unprotect(File.ReadAllBytes(TokenPath), optionalEntropy: null, DataProtectionScope.CurrentUser);
            return Encoding.UTF8.GetString(bytes);
        }
        catch
        {
            return string.Empty;
        }
    }

    public static string CreateBackup()
    {
        var backupId = DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-ffffff");
        var folder = Path.Combine(BackupRoot, backupId);
        Directory.CreateDirectory(folder);

        var files = new Dictionary<string, object?>();
        TrackFile("codex", CodexConfigPath, folder, files);
        TrackFile("claude", ClaudeSettingsPath, folder, files);
        TrackFile("opencode", OpenCodeConfigPath, folder, files);

        var environment = new Dictionary<string, bool>();
        foreach (var name in new[] { "NEWAPI_API_KEY", "ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_MODEL", "ANTHROPIC_SMALL_FAST_MODEL", "OPENCODE_CONFIG" })
        {
            var value = Environment.GetEnvironmentVariable(name, EnvironmentVariableTarget.User);
            environment[name] = value is not null;
            if (value is null)
            {
                continue;
            }

            if (name is "NEWAPI_API_KEY" or "ANTHROPIC_AUTH_TOKEN")
            {
                var protectedBytes = ProtectedData.Protect(Encoding.UTF8.GetBytes(value), optionalEntropy: null, DataProtectionScope.CurrentUser);
                File.WriteAllBytes(Path.Combine(folder, $"env-{name}.bin"), protectedBytes);
            }
            else
            {
                File.WriteAllText(Path.Combine(folder, $"env-{name}.txt"), value, Encoding.UTF8);
            }
        }

        var manifest = new JsonObject
        {
            ["created_at"] = DateTime.UtcNow.ToString("O"),
            ["files"] = JsonSerializer.SerializeToNode(files, JsonOptions.Default),
            ["environment"] = JsonSerializer.SerializeToNode(environment, JsonOptions.Default)
        };
        File.WriteAllText(Path.Combine(folder, "manifest.json"), manifest.ToJsonString(JsonOptions.Indented) + Environment.NewLine, Encoding.UTF8);
        return folder;
    }

    public static IReadOnlyList<string> ListBackups()
    {
        if (!Directory.Exists(BackupRoot))
        {
            return [];
        }

        return Directory.GetDirectories(BackupRoot)
            .Where(folder => File.Exists(Path.Combine(folder, "manifest.json")))
            .OrderByDescending(folder => folder)
            .ToList();
    }

    public static void RestoreBackup(string backupFolder)
    {
        var manifestPath = Path.Combine(backupFolder, "manifest.json");
        var manifest = JsonNode.Parse(File.ReadAllText(manifestPath, Encoding.UTF8))?.AsObject();
        if (manifest is null)
        {
            throw new InvalidOperationException("Backup manifest is invalid.");
        }

        var files = manifest["files"]!.AsObject();
        foreach (var pair in files)
        {
            var entry = pair.Value!.AsObject();
            var target = entry["path"]!.GetValue<string>();
            var existed = entry["existed"]!.GetValue<bool>();
            var backupName = entry["backup"]?.GetValue<string>();
            if (existed)
            {
                var source = Path.Combine(backupFolder, backupName!);
                Directory.CreateDirectory(Path.GetDirectoryName(target)!);
                File.Copy(source, target, overwrite: true);
            }
            else if (File.Exists(target))
            {
                File.Delete(target);
            }
        }

        var environment = manifest["environment"]!.AsObject();
        foreach (var pair in environment)
        {
            var name = pair.Key;
            var existed = pair.Value!.GetValue<bool>();
            if (!existed)
            {
                Environment.SetEnvironmentVariable(name, null, EnvironmentVariableTarget.User);
                continue;
            }

            if (name is "NEWAPI_API_KEY" or "ANTHROPIC_AUTH_TOKEN")
            {
                var secretPath = Path.Combine(backupFolder, $"env-{name}.bin");
                var bytes = ProtectedData.Unprotect(File.ReadAllBytes(secretPath), optionalEntropy: null, DataProtectionScope.CurrentUser);
                Environment.SetEnvironmentVariable(name, Encoding.UTF8.GetString(bytes), EnvironmentVariableTarget.User);
            }
            else
            {
                var value = File.ReadAllText(Path.Combine(backupFolder, $"env-{name}.txt"), Encoding.UTF8);
                Environment.SetEnvironmentVariable(name, value, EnvironmentVariableTarget.User);
            }
        }
    }

    private static void TrackFile(string key, string source, string backupFolder, Dictionary<string, object?> files)
    {
        var target = Path.Combine(backupFolder, Path.GetFileNameWithoutExtension(source) + Path.GetExtension(source) + ".bak");
        if (File.Exists(source))
        {
            Directory.CreateDirectory(Path.GetDirectoryName(target)!);
            File.Copy(source, target, overwrite: true);
            files[key] = new Dictionary<string, object?>
            {
                ["path"] = source,
                ["backup"] = Path.GetFileName(target),
                ["existed"] = true
            };
            return;
        }

        files[key] = new Dictionary<string, object?>
        {
            ["path"] = source,
            ["backup"] = null,
            ["existed"] = false
        };
    }

    private static class JsonOptions
    {
        public static JsonSerializerOptions Default { get; } = Create(false);
        public static JsonSerializerOptions Indented { get; } = Create(true);

        private static JsonSerializerOptions Create(bool indented)
        {
            return new JsonSerializerOptions
            {
                WriteIndented = indented,
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
                DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
            };
        }
    }
}
