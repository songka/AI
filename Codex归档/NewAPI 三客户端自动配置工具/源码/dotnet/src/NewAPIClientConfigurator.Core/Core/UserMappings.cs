namespace NewAPIClientConfigurator.Core;

internal static class UserMappings
{
    private static readonly HashSet<string> CodexModels = new(StringComparer.OrdinalIgnoreCase)
    {
        "gpt-5.4-mini",
        "gpt-5.4",
        "gpt-5.6-luna"
    };

    private static readonly HashSet<string> RealClientModels = new(StringComparer.OrdinalIgnoreCase)
    {
        "gpt-5.6-luna",
        "deepseek-v4-pro",
        "deepseek-v4-flash"
    };

    private static readonly string[] GptReasoningLevels = ["none", "low", "medium", "high", "xhigh", "max"];

    public static ModelCapability Apply(ModelCapability model)
    {
        var modelId = model.ModelId.Trim();
        var confirmed = new List<string>();
        if (CodexModels.Contains(modelId))
        {
            confirmed.Add("codex");
        }

        if (RealClientModels.Contains(modelId))
        {
            confirmed.Add("claude");
            confirmed.Add("opencode");
        }

        model.ManualClients = confirmed;

        if (modelId.StartsWith("gpt-", StringComparison.OrdinalIgnoreCase))
        {
            model.ManualVision = true;
            model.ManualReasoning = true;
            model.ManualReasoningField = "reasoning_content";
            model.ManualReasoningLevels = GptReasoningLevels.ToList();
        }

        return model;
    }
}
