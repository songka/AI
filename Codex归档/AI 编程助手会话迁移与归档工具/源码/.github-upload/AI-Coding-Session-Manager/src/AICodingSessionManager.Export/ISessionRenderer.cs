using AICodingSessionManager.Domain;

namespace AICodingSessionManager.Export;

/// <summary>Renders a provider-neutral session into a portable text representation.</summary>
public interface ISessionRenderer
{
    /// <summary>Gets the file extension, without a leading period.</summary>
    string FileExtension { get; }

    /// <summary>Gets the media type produced by the renderer.</summary>
    string MediaType { get; }

    /// <summary>Renders the supplied session.</summary>
    /// <param name="session">The provider-neutral session to render.</param>
    /// <returns>The complete rendered document.</returns>
    string Render(UniversalSession session);
}
