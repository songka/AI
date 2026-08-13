using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace AICodingSessionManager.Domain;

/// <summary>Serializes and validates the Universal Session Format 1.0 wire representation.</summary>
public static class UniversalSessionJson
{
    private static readonly JsonSerializerOptions SerializerOptions = CreateOptions();

    /// <summary>Gets the shared read-only JSON options used by USF serializers and renderers.</summary>
    public static JsonSerializerOptions Options => SerializerOptions;

    /// <summary>Serializes a session to deterministic, UTF-8, snake-case JSON.</summary>
    /// <param name="session">The session to serialize.</param>
    /// <param name="indented">Whether the output should be indented.</param>
    /// <returns>The serialized USF document.</returns>
    public static string Serialize(UniversalSession session, bool indented = true)
    {
        ArgumentNullException.ThrowIfNull(session);
        Validate(session);

        var node = JsonSerializer.SerializeToNode(session, SerializerOptions)
                   ?? throw new JsonException("USF serialization returned an empty document.");
        var canonical = Canonicalize(node);
        return canonical.ToJsonString(new JsonSerializerOptions
        {
            WriteIndented = indented,
            Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
        });
    }

    /// <summary>Serializes a session into UTF-8 bytes without a byte-order mark.</summary>
    public static byte[] SerializeToUtf8Bytes(UniversalSession session, bool indented = true) =>
        Encoding.UTF8.GetBytes(Serialize(session, indented));

    /// <summary>Deserializes and validates a USF 1.0 document.</summary>
    /// <param name="json">The JSON document.</param>
    /// <returns>The validated session.</returns>
    public static UniversalSession Deserialize(string json)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(json);
        var session = JsonSerializer.Deserialize<UniversalSession>(json, SerializerOptions)
                      ?? throw new JsonException("The USF document is empty.");
        Validate(session);
        return session;
    }

    /// <summary>Validates fields required to identify a USF 1.0 document.</summary>
    public static void Validate(UniversalSession session)
    {
        ArgumentNullException.ThrowIfNull(session);
        if (!string.Equals(session.Format, UniversalSession.FormatName, StringComparison.Ordinal))
            throw new InvalidDataException($"Unsupported session format '{session.Format}'.");
        if (!string.Equals(session.Version, UniversalSession.CurrentVersion, StringComparison.Ordinal))
            throw new InvalidDataException($"Unsupported USF version '{session.Version}'.");
        if (session.Session is null)
            throw new InvalidDataException("USF session metadata is required.");
        if (string.IsNullOrWhiteSpace(session.Session.Id))
            throw new InvalidDataException("USF session.id is required.");
    }

    private static JsonSerializerOptions CreateOptions()
    {
        var options = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
            DictionaryKeyPolicy = null,
            PropertyNameCaseInsensitive = true,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
            TypeInfoResolver = new DefaultJsonTypeInfoResolver()
        };
        options.Converters.Add(new JsonStringEnumConverter(JsonNamingPolicy.SnakeCaseLower));
        options.MakeReadOnly();
        return options;
    }

    private static JsonNode Canonicalize(JsonNode node)
    {
        return node switch
        {
            JsonObject jsonObject => CanonicalizeObject(jsonObject),
            JsonArray jsonArray => CanonicalizeArray(jsonArray),
            _ => node.DeepClone()
        };
    }

    private static JsonObject CanonicalizeObject(JsonObject source)
    {
        var result = new JsonObject();
        foreach (var property in source.OrderBy(static property => property.Key, StringComparer.Ordinal))
            result[property.Key] = property.Value is null ? null : Canonicalize(property.Value);
        return result;
    }

    private static JsonArray CanonicalizeArray(JsonArray source)
    {
        var result = new JsonArray();
        foreach (var item in source)
            result.Add(item is null ? null : Canonicalize(item));
        return result;
    }
}
