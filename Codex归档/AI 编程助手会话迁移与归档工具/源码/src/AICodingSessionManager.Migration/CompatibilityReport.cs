using AICodingSessionManager.Domain;

namespace AICodingSessionManager.Migration;

/// <summary>Describes a destination supported by the migration planner.</summary>
public enum MigrationTarget { Codex, ClaudeCode, OpenCode }

/// <summary>Counts source features and how many can be carried into a migration mode.</summary>
public sealed record FeatureCompatibility(string Feature, int SourceCount, int PreservedCount, string Note);

/// <summary>Reports measured archive, context-resume, and native-resume compatibility separately.</summary>
public sealed record CompatibilityReport(
    AgentKind Source,
    MigrationTarget Target,
    int ArchiveScore,
    int ContextResumeScore,
    int NativeResumeScore,
    string Classification,
    bool NativeResumeVerified,
    IReadOnlyList<FeatureCompatibility> Features,
    IReadOnlyList<string> Warnings);

/// <summary>Computes a conservative, evidence-oriented compatibility report.</summary>
public sealed class CompatibilityAnalyzer
{
    /// <summary>Analyzes a session without claiming unverified native resume support.</summary>
    public CompatibilityReport Analyze(UniversalSession session, MigrationTarget target)
    {
        ArgumentNullException.ThrowIfNull(session);
        UniversalSessionJson.Validate(session);

        var parts = session.Messages.SelectMany(static message => message.Content).ToArray();
        var features = new List<FeatureCompatibility>
        {
            Count("Messages", session.Messages.Count, session.Messages.Count, "Context document preserves readable message history."),
            Count("Text", Count(parts, ContentPartKind.Text), Count(parts, ContentPartKind.Text), "Preserved as Markdown text."),
            Count("Reasoning", Count(parts, ContentPartKind.Reasoning), Count(parts, ContentPartKind.Reasoning), "Preserved as an explicitly labelled historical block; not restored as private runtime reasoning."),
            Count("Tool calls", Count(parts, ContentPartKind.ToolCall), Count(parts, ContentPartKind.ToolCall), "Preserved for reference; calls are not replayed."),
            Count("Tool results", Count(parts, ContentPartKind.ToolResult), Count(parts, ContentPartKind.ToolResult), "Preserved for reference; runtime state is not restored."),
            Count("Commands", Count(parts, ContentPartKind.Command), Count(parts, ContentPartKind.Command), "Preserved as inert text and never executed."),
            Count("Command results", Count(parts, ContentPartKind.CommandResult), Count(parts, ContentPartKind.CommandResult), "Preserved as inert text."),
            Count("Patches and diffs", Count(parts, ContentPartKind.Patch) + Count(parts, ContentPartKind.Diff), Count(parts, ContentPartKind.Patch) + Count(parts, ContentPartKind.Diff), "Preserved as inert text; not applied."),
            Count("Attachments", session.Attachments.Count, 0, "Attachment metadata remains in the archive; Context Resume does not transmit local files automatically."),
            Count("Unsupported records", session.UnsupportedRecords.Count, 0, "Raw records remain in .ai-session and are not injected into a new prompt."),
        };

        var sourceUnits = features.Sum(static feature => feature.SourceCount);
        var preservedUnits = features.Sum(static feature => feature.PreservedCount);
        var contextScore = sourceUnits == 0 ? 100 : (int)Math.Round(100d * preservedUnits / sourceUnits, MidpointRounding.AwayFromZero);
        var warnings = new List<string>
        {
            "Context Resume creates a new conversation; it does not recreate approvals, processes, MCP connections, credentials, or private runtime state.",
            "Review the generated context for secrets before sending it to another Agent."
        };
        if (session.Attachments.Count > 0) warnings.Add("Attachments require explicit review and separate transfer.");
        if (session.UnsupportedRecords.Count > 0) warnings.Add("Unknown source records remain archive-only.");

        return new CompatibilityReport(
            session.Session.Source,
            target,
            ArchiveScore: 100,
            ContextResumeScore: contextScore,
            NativeResumeScore: 0,
            Classification: Classify(contextScore),
            NativeResumeVerified: false,
            features,
            warnings);
    }

    private static FeatureCompatibility Count(string feature, int source, int preserved, string note) =>
        new(feature, source, preserved, note);

    private static int Count(IEnumerable<ContentPart> parts, ContentPartKind kind) =>
        parts.Count(part => part.Type == kind);

    private static string Classify(int score) => score switch
    {
        >= 90 => "Highly Compatible Context",
        >= 70 => "Compatible Context",
        >= 50 => "Partial Context",
        _ => "Archive Only"
    };
}
