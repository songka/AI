using System.Text.Json.Serialization;

namespace NewAPIClientConfigurator.Core;

internal enum Source
{
    ApiProbe,
    ModelsDev,
    OfficialMetadata,
    Manual,
    Unknown
}

internal enum ProbeStatus
{
    Confirmed,
    Declared,
    Unknown,
    Failed
}

internal sealed class ProtocolResult
{
    public ProbeStatus Text { get; set; } = ProbeStatus.Unknown;
    public ProbeStatus Streaming { get; set; } = ProbeStatus.Unknown;
    public ProbeStatus Tools { get; set; } = ProbeStatus.Unknown;
    public ProbeStatus Vision { get; set; } = ProbeStatus.Unknown;
    public ProbeStatus Reasoning { get; set; } = ProbeStatus.Unknown;
    public double? LatencyMs { get; set; }
    public double? FirstTokenLatencyMs { get; set; }
    public string? Error { get; set; }
}

internal sealed class ModelCapability
{
    public string ModelId { get; set; } = string.Empty;
    public string DisplayName { get; set; } = string.Empty;
    public bool Available { get; set; } = true;
    public ProtocolResult Responses { get; set; } = new();
    public ProtocolResult Messages { get; set; } = new();
    public ProtocolResult Chat { get; set; } = new();
    public Dictionary<string, ProbeStatus> ReasoningControl { get; set; } = new();
    public string? ReasoningControlProtocol { get; set; }
    public string? ReasoningField { get; set; }
    public int? ContextDeclared { get; set; }
    public int? ContextVerifiedMin { get; set; }
    public Source ContextSource { get; set; } = Source.Unknown;
    public int? MaxOutputTokens { get; set; }
    public List<string> InputModalities { get; set; } = new() { "text" };
    public List<string> OutputModalities { get; set; } = new() { "text" };
    public DateTime? TestTime { get; set; }
    public string? Error { get; set; }
    public List<string> ManualClients { get; set; } = new();
    public bool ManualVision { get; set; }
    public bool ManualReasoning { get; set; }
    public string? ManualReasoningField { get; set; }
    public List<string> ManualReasoningLevels { get; set; } = new();

    [JsonIgnore]
    public bool IsCodexAlias => ModelId.Trim().Equals("gpt-5.4", StringComparison.OrdinalIgnoreCase) || ModelId.Trim().Equals("gpt-5.4-mini", StringComparison.OrdinalIgnoreCase);

    [JsonIgnore]
    public bool IsExcluded
    {
        get
        {
            var modelId = ModelId.Trim().ToLowerInvariant();
            return modelId == "codex-auto-review" || modelId.StartsWith("codex-auto-review-", StringComparison.Ordinal);
        }
    }

    [JsonIgnore]
    public bool CodexCompatible =>
        !IsExcluded && (ManualClients.Contains("codex") || (Responses.Text == ProbeStatus.Confirmed && Responses.Streaming == ProbeStatus.Confirmed && Responses.Tools == ProbeStatus.Confirmed));

    [JsonIgnore]
    public bool ClaudeCompatible =>
        !IsExcluded && !IsCodexAlias && (ManualClients.Contains("claude") || (Messages.Text == ProbeStatus.Confirmed && Messages.Streaming == ProbeStatus.Confirmed));

    [JsonIgnore]
    public bool OpenCodeCompatible
    {
        get
        {
            var route = Chat.Text == ProbeStatus.Confirmed ? Chat : Responses;
            var probed = route.Text == ProbeStatus.Confirmed && route.Streaming == ProbeStatus.Confirmed;
            return !IsExcluded && !IsCodexAlias && (ManualClients.Contains("opencode") || probed);
        }
    }

    [JsonIgnore]
    public bool Vision => ManualVision || Responses.Vision == ProbeStatus.Confirmed || Messages.Vision == ProbeStatus.Confirmed || Chat.Vision == ProbeStatus.Confirmed;

    [JsonIgnore]
    public bool Reasoning => ManualReasoning || ReasoningField is not null || Responses.Reasoning == ProbeStatus.Confirmed || Messages.Reasoning == ProbeStatus.Confirmed || Chat.Reasoning == ProbeStatus.Confirmed;

    [JsonIgnore]
    public string? EffectiveReasoningField => ManualReasoningField ?? ReasoningField;

    [JsonIgnore]
    public IReadOnlyList<string> EffectiveReasoningLevels
    {
        get
        {
            var probed = ReasoningControl.Where(pair => pair.Value == ProbeStatus.Confirmed).Select(pair => pair.Key).ToList();
            return probed.Count > 0 ? probed : ManualReasoningLevels;
        }
    }

    public string ShortContext()
    {
        if (ContextDeclared is null)
        {
            return "Unknown";
        }

        return ContextDeclared >= 1_000_000 ? $"{ContextDeclared.Value / 1_000_000d:0.#}M" : $"{ContextDeclared.Value / 1000}K";
    }

    public string ContextSummary()
    {
        var declared = $"Declared: {ShortContext()}";
        var verified = ContextVerifiedMin is null ? "Verified: not passed" : $"Verified: {ContextVerifiedMin.Value / 1000}K";
        return $"{declared}\n{verified}";
    }

    public string ReasoningSummary()
    {
        if (ManualReasoning)
        {
            return $"User confirmed: {string.Join(", ", EffectiveReasoningLevels)}\nField: {EffectiveReasoningField ?? "reasoning_content"}";
        }

        if (ReasoningControl.Count == 0)
        {
            return "Not tested";
        }

        var accepted = ReasoningControl.Where(pair => pair.Value == ProbeStatus.Confirmed).Select(pair => pair.Key).ToList();
        if (accepted.Count == 0)
        {
            return "Control: unsupported";
        }

        var field = ReasoningField ?? "not returned";
        return $"Control: {string.Join(", ", accepted)}\nField: {field}";
    }
}

internal sealed class ScanCache
{
    public string GatewayUrl { get; set; } = string.Empty;
    public List<ModelCapability> Capabilities { get; set; } = new();
    public DateTime SavedAt { get; set; } = DateTime.UtcNow;
}
