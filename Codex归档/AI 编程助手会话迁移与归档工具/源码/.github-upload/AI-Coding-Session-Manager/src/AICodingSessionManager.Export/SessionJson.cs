using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace AICodingSessionManager.Export;

/// <summary>Provides the stable Universal Session Format JSON configuration.</summary>
public static class SessionJson
{
    /// <summary>Gets the shared read-only JSON serializer options.</summary>
    public static JsonSerializerOptions Options { get; } = CreateOptions();

    private static JsonSerializerOptions CreateOptions()
    {
        var options = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
            DictionaryKeyPolicy = null,
            Encoder = JavaScriptEncoder.Default,
            TypeInfoResolver = new DefaultJsonTypeInfoResolver(),
            WriteIndented = true,
        };
        options.Converters.Add(new JsonStringEnumConverter(JsonNamingPolicy.SnakeCaseLower));
        options.MakeReadOnly();
        return options;
    }
}
