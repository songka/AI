using System.Globalization;
using NewAPIClientConfigurator.Core;

namespace NewAPIClientConfigurator.App;

/// <summary>Display row model used by the WPF data grid.</summary>
public sealed class ModelRow
{
    public required string DisplayName { get; init; }
    public required string Responses { get; init; }
    public required string Messages { get; init; }
    public required string Chat { get; init; }
    public required string Tools { get; init; }
    public required string Vision { get; init; }
    public required string Reasoning { get; init; }
    public required string Context { get; init; }
    public required string Output { get; init; }
    public required string Codex { get; init; }
    public required string ClaudeOpenCode { get; init; }

    internal static ModelRow From(ModelCapability model)
    {
        return new ModelRow
        {
            DisplayName = model.DisplayName,
            Responses = ProtocolLabel(model.Responses),
            Messages = ProtocolLabel(model.Messages),
            Chat = ProtocolLabel(model.Chat),
            Tools = StatusLabel(model.Responses.Tools, model.Messages.Tools, model.Chat.Tools),
            Vision = StatusLabel(model.Responses.Vision, model.Messages.Vision, model.Chat.Vision),
            Reasoning = model.ReasoningSummary(),
            Context = model.ContextSummary(),
            Output = model.MaxOutputTokens?.ToString(CultureInfo.InvariantCulture) ?? "Unknown",
            Codex = model.ManualClients.Contains("codex") ? "User confirmed" : StatusLabel(model.CodexCompatible),
            ClaudeOpenCode = model.ManualClients.Contains("claude")
                ? "User confirmed"
                : $"{StatusLabel(model.ClaudeCompatible)} / {StatusLabel(model.OpenCodeCompatible)}"
        };
    }

    private static string ProtocolLabel(ProtocolResult result)
    {
        return $"Text:{Label(result.Text)} / Stream:{Label(result.Streaming)}";
    }

    private static string StatusLabel(bool confirmed)
    {
        return confirmed ? "Confirmed" : "Failed";
    }

    private static string StatusLabel(ProbeStatus left, ProbeStatus middle, ProbeStatus right)
    {
        return $"{Label(left)}/{Label(middle)}/{Label(right)}";
    }

    private static string Label(ProbeStatus status)
    {
        return status switch
        {
            ProbeStatus.Confirmed => "OK",
            ProbeStatus.Declared => "Declared",
            ProbeStatus.Unknown => "Unknown",
            ProbeStatus.Failed => "Failed",
            _ => "Unknown"
        };
    }
}
