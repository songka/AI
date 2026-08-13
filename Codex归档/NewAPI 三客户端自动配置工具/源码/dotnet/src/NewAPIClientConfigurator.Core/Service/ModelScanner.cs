using System.Collections.Concurrent;
using System.Diagnostics;
using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace NewAPIClientConfigurator.Core;

internal sealed class ModelScanner
{
    private readonly MetadataResolver _metadataResolver = new();

    public async Task<IReadOnlyList<ModelCapability>> ScanAsync(
        string baseUrl,
        string token,
        IReadOnlyList<string> modelIds,
        int concurrency,
        bool deepContext,
        Action<string> log,
        CancellationToken cancellationToken)
    {
        await using var gateway = new NewApiGateway(baseUrl, token);
        var results = new ModelCapability[modelIds.Count];
        var gate = new SemaphoreSlim(Math.Max(1, Math.Min(concurrency, 8)));
        var completed = 0;

        var tasks = modelIds.Select((modelId, index) => ProbeAsync(modelId, index)).ToArray();
        await Task.WhenAll(tasks).ConfigureAwait(false);
        return results;

        async Task ProbeAsync(string modelId, int index)
        {
            await gate.WaitAsync(cancellationToken).ConfigureAwait(false);
            try
            {
                var capability = await ScanOneAsync(gateway, modelId, deepContext, log, cancellationToken).ConfigureAwait(false);
                capability = UserMappings.Apply(capability);
                results[index] = capability;
                var current = Interlocked.Increment(ref completed);
                log($"Progress: {current}/{modelIds.Count} complete ({modelId})");
            }
            catch (Exception ex)
            {
                results[index] = UserMappings.Apply(new ModelCapability
                {
                    ModelId = modelId,
                    DisplayName = DisplayName(modelId),
                    Error = ex.Message,
                    TestTime = DateTime.UtcNow
                });
                log($"{modelId}: probe failed, but other models continue.");
            }
            finally
            {
                gate.Release();
            }
        }
    }

    public async Task<IReadOnlyList<string>> ListModelsAsync(string baseUrl, string token, CancellationToken cancellationToken)
    {
        await using var gateway = new NewApiGateway(baseUrl, token);
        return await gateway.ListModelsAsync(cancellationToken).ConfigureAwait(false);
    }

    private async Task<ModelCapability> ScanOneAsync(
        NewApiGateway gateway,
        string modelId,
        bool deepContext,
        Action<string> log,
        CancellationToken cancellationToken)
    {
        var capability = new ModelCapability
        {
            ModelId = modelId,
            DisplayName = DisplayName(modelId)
        };

        var metadata = await _metadataResolver.ResolveAsync(modelId, cancellationToken).ConfigureAwait(false);
        ApplyMetadata(capability, metadata);

        log($"Start: {modelId}");
        capability.Responses = await ProbeAsync(gateway, "/v1/responses", ResponsesBody, modelId, cancellationToken).ConfigureAwait(false);
        capability.Chat = await ProbeAsync(gateway, "/v1/chat/completions", ChatBody, modelId, cancellationToken).ConfigureAwait(false);
        capability.Messages = await ProbeAsync(gateway, "/v1/messages", MessagesBody, modelId, cancellationToken).ConfigureAwait(false);
        await ProbeContextAsync(gateway, modelId, capability, deepContext, log, cancellationToken).ConfigureAwait(false);
        capability.ReasoningField = await ProbeReasoningAsync(gateway, modelId, capability, log, cancellationToken).ConfigureAwait(false);
        capability.TestTime = DateTime.UtcNow;
        return capability;
    }

    private static void ApplyMetadata(ModelCapability capability, Dictionary<string, object> metadata)
    {
        if (metadata.TryGetValue("limit", out var limitObj) && limitObj is Dictionary<string, object> limit)
        {
            if (limit.TryGetValue("context", out var contextObj) && TryInt(contextObj, out var context))
            {
                capability.ContextDeclared = context;
                capability.ContextSource = Source.ModelsDev;
            }

            if (limit.TryGetValue("output", out var outputObj) && TryInt(outputObj, out var output))
            {
                capability.MaxOutputTokens = output;
            }
        }

        if (metadata.TryGetValue("modalities", out var modalitiesObj) && modalitiesObj is Dictionary<string, object> modalities)
        {
            if (modalities.TryGetValue("input", out var inputObj) && inputObj is List<object> input)
            {
                capability.InputModalities = input.Select(item => item.ToString() ?? string.Empty).Where(item => !string.IsNullOrWhiteSpace(item)).ToList();
            }

            if (modalities.TryGetValue("output", out var outputObj) && outputObj is List<object> output)
            {
                capability.OutputModalities = output.Select(item => item.ToString() ?? string.Empty).Where(item => !string.IsNullOrWhiteSpace(item)).ToList();
            }
        }
    }

    private static bool TryInt(object? value, out int result)
    {
        switch (value)
        {
            case int i:
                result = i;
                return true;
            case long l when l is >= int.MinValue and <= int.MaxValue:
                result = (int)l;
                return true;
            case double d:
                result = (int)d;
                return true;
            case JsonElement element when element.ValueKind == JsonValueKind.Number && element.TryGetInt32(out var i):
                result = i;
                return true;
            default:
                result = 0;
                return false;
        }
    }

    private async Task<ProtocolResult> ProbeAsync(
        NewApiGateway gateway,
        string route,
        Func<string, bool, bool, string?, string?, object> bodyFactory,
        string modelId,
        CancellationToken cancellationToken)
    {
        var result = new ProtocolResult();
        try
        {
            var payload = await gateway.PostJsonAsync(route, bodyFactory(modelId, false, false, null, null), cancellationToken).ConfigureAwait(false);
            result.Text = HasText(payload.Json) ? ProbeStatus.Confirmed : ProbeStatus.Failed;
            result.LatencyMs = payload.LatencyMs;
            result.Reasoning = FindReasoningField(payload.Json) is not null ? ProbeStatus.Confirmed : ProbeStatus.Unknown;
        }
        catch (Exception ex)
        {
            result.Error = ex.Message;
            result.Text = ProbeStatus.Failed;
            return result;
        }

        try
        {
            var stream = await gateway.PostStreamAsync(route, bodyFactory(modelId, true, false, null, null), cancellationToken).ConfigureAwait(false);
            result.Streaming = stream.Lines.Count > 0 ? ProbeStatus.Confirmed : ProbeStatus.Failed;
            result.FirstTokenLatencyMs = stream.FirstTokenLatencyMs;
        }
        catch (Exception ex)
        {
            result.Streaming = ProbeStatus.Failed;
            result.Error = ex.Message;
        }

        try
        {
            var payload = await gateway.PostJsonAsync(route, bodyFactory(modelId, false, true, null, null), cancellationToken).ConfigureAwait(false);
            result.Tools = ToolCalled(payload.Json) ? ProbeStatus.Confirmed : ProbeStatus.Failed;
        }
        catch
        {
            result.Tools = ProbeStatus.Failed;
        }

        try
        {
            var (expected, image) = MakeImage();
            var payload = await gateway.PostJsonAsync(route, bodyFactory(modelId, false, false, image, null), cancellationToken).ConfigureAwait(false);
            result.Vision = payload.Json.Contains(expected, StringComparison.Ordinal) ? ProbeStatus.Confirmed : ProbeStatus.Failed;
        }
        catch
        {
            result.Vision = ProbeStatus.Failed;
        }

        return result;
    }

    private async Task ProbeContextAsync(
        NewApiGateway gateway,
        string modelId,
        ModelCapability capability,
        bool deepContext,
        Action<string> log,
        CancellationToken cancellationToken)
    {
        var stages = new List<int> { 8192 };
        if (deepContext)
        {
            foreach (var size in new[] { 32768, 65536, 131072, 262144, 524288, 1048576 })
            {
                if (capability.ContextDeclared is null || size <= capability.ContextDeclared)
                {
                    stages.Add(size);
                }
            }
        }

        foreach (var pair in new (string Route, Func<string, bool, bool, string?, string?, object> Factory, ProtocolResult Result)[]
        {
            ("/v1/responses", ResponsesBody, capability.Responses),
            ("/v1/chat/completions", ChatBody, capability.Chat),
            ("/v1/messages", MessagesBody, capability.Messages)
        })
        {
            if (pair.Result.Text != ProbeStatus.Confirmed)
            {
                continue;
            }

            foreach (var size in stages)
            {
                try
                {
                    var payload = await gateway.PostJsonAsync(pair.Route, ContextBody(pair.Route, modelId, size), cancellationToken).ConfigureAwait(false);
                    var inputTokens = ReadUsageInputTokens(payload.Json);
                    if (inputTokens is not null)
                    {
                        capability.ContextVerifiedMin = capability.ContextVerifiedMin is null ? inputTokens : Math.Max(capability.ContextVerifiedMin.Value, inputTokens.Value);
                        log($"{modelId}: context verified lower bound {capability.ContextVerifiedMin.Value / 1000}K ({pair.Route})");
                    }
                    else
                    {
                        log($"{modelId}: context request succeeded but usage was not returned.");
                    }
                }
                catch
                {
                    log($"{modelId}: context stage {size / 1000}K failed.");
                    break;
                }
            }

            return;
        }
    }

    private async Task<string?> ProbeReasoningAsync(
        NewApiGateway gateway,
        string modelId,
        ModelCapability capability,
        Action<string> log,
        CancellationToken cancellationToken)
    {
        if (capability.Chat.Text != ProbeStatus.Confirmed)
        {
            return null;
        }

        capability.ReasoningControlProtocol = "Chat";
        string? field = null;
        foreach (var level in new[] { "low", "medium", "high", "none", "xhigh", "max" })
        {
            try
            {
                var body = ChatBody(modelId, false, false, null, level);
                var payload = await gateway.PostJsonAsync("/v1/chat/completions", body, cancellationToken).ConfigureAwait(false);
                capability.ReasoningControl[level] = ProbeStatus.Confirmed;
                var found = FindReasoningField(payload.Json);
                field ??= found;
                if (found is not null)
                {
                    capability.Chat.Reasoning = ProbeStatus.Confirmed;
                }
            }
            catch
            {
                capability.ReasoningControl[level] = ProbeStatus.Failed;
            }
        }

        if (capability.ReasoningControl.Values.Any(status => status == ProbeStatus.Confirmed) && capability.Chat.Reasoning != ProbeStatus.Confirmed)
        {
            capability.Chat.Reasoning = ProbeStatus.Declared;
        }

        var accepted = capability.ReasoningControl.Where(pair => pair.Value == ProbeStatus.Confirmed).Select(pair => pair.Key).ToList();
        log($"{modelId}: reasoning control accepted {(accepted.Count > 0 ? string.Join(", ", accepted) : "none")}");
        return field;
    }

    private static object ResponsesBody(string model, bool stream, bool tools, string? image, string? reasoning)
    {
        var content = new List<Dictionary<string, object>>
        {
            new()
            {
                ["type"] = "input_text",
                ["text"] = image is null ? "Only reply: OK" : "Read the 4-digit number in the image. Reply only with the digits."
            }
        };
        if (image is not null)
        {
            content.Add(new Dictionary<string, object>
            {
                ["type"] = "input_image",
                ["image_url"] = $"data:image/png;base64,{image}"
            });
        }

        var body = new Dictionary<string, object>
        {
            ["model"] = model,
            ["input"] = new[] { new Dictionary<string, object> { ["role"] = "user", ["content"] = content } },
            ["stream"] = stream,
            ["max_output_tokens"] = 32
        };

        if (reasoning is not null)
        {
            body["reasoning"] = new Dictionary<string, object> { ["effort"] = reasoning };
        }

        if (tools)
        {
            body["tools"] = new[]
            {
                new Dictionary<string, object>
                {
                    ["type"] = "function",
                    ["name"] = "get_test_code",
                    ["description"] = "Return test code",
                    ["parameters"] = new Dictionary<string, object>
                    {
                        ["type"] = "object",
                        ["properties"] = new Dictionary<string, object>
                        {
                            ["code"] = new Dictionary<string, object> { ["type"] = "string" }
                        },
                        ["required"] = new[] { "code" }
                    }
                }
            };
            body["input"] = "You must call get_test_code with code TEST123. Do not answer directly.";
        }

        return body;
    }

    private static object ChatBody(string model, bool stream, bool tools, string? image, string? reasoning)
    {
        object content = "Only reply: OK";
        if (image is not null)
        {
            content = new object[]
            {
                new Dictionary<string, object> { ["type"] = "text", ["text"] = "Read the 4-digit number in the image. Reply only with the digits." },
                new Dictionary<string, object> { ["type"] = "image_url", ["image_url"] = new Dictionary<string, object> { ["url"] = $"data:image/png;base64,{image}" } }
            };
        }

        if (tools)
        {
            content = "You must call get_test_code with code TEST123. Do not answer directly.";
        }

        var body = new Dictionary<string, object>
        {
            ["model"] = model,
            ["messages"] = new[]
            {
                new Dictionary<string, object>
                {
                    ["role"] = "user",
                    ["content"] = content
                }
            },
            ["stream"] = stream,
            ["max_tokens"] = 32
        };

        if (reasoning is not null)
        {
            body["reasoning_effort"] = reasoning;
        }

        if (tools)
        {
            body["tools"] = new[]
            {
                new Dictionary<string, object>
                {
                    ["type"] = "function",
                    ["function"] = new Dictionary<string, object>
                    {
                        ["name"] = "get_test_code",
                        ["description"] = "Return test code",
                        ["parameters"] = new Dictionary<string, object>
                        {
                            ["type"] = "object",
                            ["properties"] = new Dictionary<string, object>
                            {
                                ["code"] = new Dictionary<string, object> { ["type"] = "string" }
                            },
                            ["required"] = new[] { "code" }
                        }
                    }
                }
            };
        }

        return body;
    }

    private static object MessagesBody(string model, bool stream, bool tools, string? image, string? reasoning)
    {
        object content = "Only reply: OK";
        if (image is not null)
        {
            content = new object[]
            {
                new Dictionary<string, object> { ["type"] = "text", ["text"] = "Read the 4-digit number in the image. Reply only with the digits." },
                new Dictionary<string, object> { ["type"] = "image", ["source"] = new Dictionary<string, object> { ["type"] = "base64", ["media_type"] = "image/png", ["data"] = image } }
            };
        }

        if (tools)
        {
            content = "You must call get_test_code with code TEST123. Do not answer directly.";
        }

        var body = new Dictionary<string, object>
        {
            ["model"] = model,
            ["max_tokens"] = 32,
            ["messages"] = new[]
            {
                new Dictionary<string, object>
                {
                    ["role"] = "user",
                    ["content"] = content
                }
            },
            ["stream"] = stream
        };

        if (tools)
        {
            body["tools"] = new[]
            {
                new Dictionary<string, object>
                {
                    ["name"] = "get_test_code",
                    ["description"] = "Return test code",
                    ["input_schema"] = new Dictionary<string, object>
                    {
                        ["type"] = "object",
                        ["properties"] = new Dictionary<string, object>
                        {
                            ["code"] = new Dictionary<string, object> { ["type"] = "string" }
                        },
                        ["required"] = new[] { "code" }
                    }
                }
            };
        }

        return body;
    }

    private static object ContextBody(string route, string model, int tokens)
    {
        var prompt = string.Concat(Enumerable.Repeat("x ", tokens)) + "\nReply only: OK";
        return route switch
        {
            "/v1/responses" => new Dictionary<string, object> { ["model"] = model, ["input"] = prompt, ["max_output_tokens"] = 1 },
            "/v1/chat/completions" => new Dictionary<string, object> { ["model"] = model, ["messages"] = new[] { new Dictionary<string, object> { ["role"] = "user", ["content"] = prompt } }, ["max_tokens"] = 1 },
            _ => new Dictionary<string, object> { ["model"] = model, ["messages"] = new[] { new Dictionary<string, object> { ["role"] = "user", ["content"] = prompt } }, ["max_tokens"] = 1 }
        };
    }

    private static bool HasText(string json)
    {
        using var doc = JsonDocument.Parse(json);
        return HasText(doc.RootElement);
    }

    private static bool HasText(JsonElement element)
    {
        if (element.ValueKind == JsonValueKind.Object)
        {
            foreach (var property in element.EnumerateObject())
            {
                if (property.NameEquals("text") || property.NameEquals("content") || property.NameEquals("output_text"))
                {
                    if (property.Value.ValueKind == JsonValueKind.String && !string.IsNullOrWhiteSpace(property.Value.GetString()))
                    {
                        return true;
                    }

                    if (property.Value.ValueKind == JsonValueKind.Array)
                    {
                        foreach (var child in property.Value.EnumerateArray())
                        {
                            if (HasText(child))
                            {
                                return true;
                            }
                        }
                    }
                }

                if (HasText(property.Value))
                {
                    return true;
                }
            }
        }
        else if (element.ValueKind == JsonValueKind.Array)
        {
            foreach (var child in element.EnumerateArray())
            {
                if (HasText(child))
                {
                    return true;
                }
            }
        }
        else if (element.ValueKind == JsonValueKind.String)
        {
            return !string.IsNullOrWhiteSpace(element.GetString());
        }

        return false;
    }

    private static string? FindReasoningField(string json)
    {
        foreach (var field in new[] { "reasoning_content", "reasoning_text", "thinking", "reasoning" })
        {
            if (json.Contains($"\"{field}\"", StringComparison.Ordinal))
            {
                return field;
            }
        }

        return null;
    }

    private static bool ToolCalled(string json)
    {
        return json.Contains("get_test_code", StringComparison.Ordinal) && (json.Contains("tool_call", StringComparison.Ordinal) || json.Contains("function_call", StringComparison.Ordinal) || json.Contains("tool_use", StringComparison.Ordinal));
    }

    private static (string Code, string Image) MakeImage()
    {
        var code = Random.Shared.Next(0, 10000).ToString("D4", CultureInfo.InvariantCulture);
        using var bitmap = new System.Drawing.Bitmap(520, 240);
        using var graphics = System.Drawing.Graphics.FromImage(bitmap);
        graphics.Clear(System.Drawing.Color.White);
        using var font = new System.Drawing.Font(System.Drawing.FontFamily.GenericSansSerif, 72, System.Drawing.FontStyle.Regular);
        var size = graphics.MeasureString(code, font);
        graphics.DrawString(code, font, System.Drawing.Brushes.Black, (520 - size.Width) / 2, (240 - size.Height) / 2);
        using var stream = new MemoryStream();
        bitmap.Save(stream, System.Drawing.Imaging.ImageFormat.Png);
        return (code, Convert.ToBase64String(stream.ToArray()));
    }

    private static int? ReadUsageInputTokens(string json)
    {
        using var doc = JsonDocument.Parse(json);
        if (doc.RootElement.ValueKind != JsonValueKind.Object || !doc.RootElement.TryGetProperty("usage", out var usage) || usage.ValueKind != JsonValueKind.Object)
        {
            return null;
        }

        foreach (var field in new[] { "input_tokens", "prompt_tokens" })
        {
            if (usage.TryGetProperty(field, out var property) && property.ValueKind == JsonValueKind.Number && property.TryGetInt32(out var value) && value > 0)
            {
                return value;
            }
        }

        return null;
    }

    private static string DisplayName(string modelId)
    {
        return string.Join(" ", modelId.Replace('-', ' ').Replace('_', ' ').Split(' ', StringSplitOptions.RemoveEmptyEntries).Select(part => char.ToUpperInvariant(part[0]) + part[1..]));
    }
}
