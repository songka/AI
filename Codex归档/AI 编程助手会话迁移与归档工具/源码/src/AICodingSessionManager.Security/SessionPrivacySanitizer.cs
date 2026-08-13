using System.Text.Json;
using System.Text.Json.Nodes;
using AICodingSessionManager.Domain;

namespace AICodingSessionManager.Security;

/// <summary>Creates a structurally equivalent USF session with every string value privacy-redacted.</summary>
public sealed class SessionPrivacySanitizer(PrivacyRedactor? redactor = null)
{
    private readonly PrivacyRedactor privacyRedactor = redactor ?? new PrivacyRedactor();

    /// <summary>Sanitizes a session without mutating the source object.</summary>
    public UniversalSession Sanitize(UniversalSession session)
    {
        ArgumentNullException.ThrowIfNull(session);
        UniversalSessionJson.Validate(session);
        var node = JsonNode.Parse(UniversalSessionJson.Serialize(session, indented: false))
            ?? throw new JsonException("USF privacy serialization returned no document.");
        RedactNode(node);
        return UniversalSessionJson.Deserialize(node.ToJsonString());
    }

    private void RedactNode(JsonNode node)
    {
        if (node is JsonObject obj)
        {
            foreach (var property in obj.ToArray())
            {
                if (property.Value is JsonValue value && value.TryGetValue<string>(out var text))
                    obj[property.Key] = privacyRedactor.Redact(text).Text;
                else if (property.Value is not null)
                    RedactNode(property.Value);
            }
        }
        else if (node is JsonArray array)
        {
            for (var index = 0; index < array.Count; index++)
            {
                if (array[index] is JsonValue value && value.TryGetValue<string>(out var text))
                    array[index] = privacyRedactor.Redact(text).Text;
                else if (array[index] is not null)
                    RedactNode(array[index]!);
            }
        }
    }
}
