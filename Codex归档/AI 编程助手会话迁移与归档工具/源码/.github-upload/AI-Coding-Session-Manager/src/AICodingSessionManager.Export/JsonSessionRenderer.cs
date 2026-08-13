using AICodingSessionManager.Domain;

namespace AICodingSessionManager.Export;

/// <summary>Renders a session as Universal Session Format JSON.</summary>
public sealed class JsonSessionRenderer : ISessionRenderer
{
    /// <inheritdoc />
    public string FileExtension => "json";

    /// <inheritdoc />
    public string MediaType => "application/json";

    /// <inheritdoc />
    public string Render(UniversalSession session)
    {
        ArgumentNullException.ThrowIfNull(session);
        return UniversalSessionJson.Serialize(session);
    }
}
