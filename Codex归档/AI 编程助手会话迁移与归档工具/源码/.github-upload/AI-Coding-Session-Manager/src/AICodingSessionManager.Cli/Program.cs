using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using AICodingSessionManager.Adapters.ClaudeCode;
using AICodingSessionManager.Adapters.Codex;
using AICodingSessionManager.Adapters.OpenCode;
using AICodingSessionManager.Domain;

namespace AICodingSessionManager.Cli;

internal static class Program
{
    private static readonly IAgentAdapter[] Adapters =
    [
        new OpenCodeAdapter(),
        new CodexAdapter(),
        new ClaudeCodeAdapter()
    ];

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        Converters = { new JsonStringEnumConverter() }
    };

    public static async Task<int> Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        var launchedWithoutArguments = args.Length == 0;

        try
        {
            if (launchedWithoutArguments)
            {
                PrintBanner();
                await PrintFriendlyDiagnosticsAsync();
                PauseBeforeExit();
                return 0;
            }

            if (args[0].Equals("diagnostics", StringComparison.OrdinalIgnoreCase))
            {
                await PrintJsonDiagnosticsAsync();
                return 0;
            }

            if (args.Length == 3 && args[0].Equals("read", StringComparison.OrdinalIgnoreCase))
            {
                return await ReadSessionAsync(args[1], args[2]);
            }

            PrintUsage();
            return 2;
        }
        catch (Exception exception)
        {
            Console.ForegroundColor = ConsoleColor.Red;
            Console.Error.WriteLine($"运行失败：{exception.Message}");
            Console.ResetColor();
            Console.Error.WriteLine("详细信息：");
            Console.Error.WriteLine(exception);
            if (launchedWithoutArguments) PauseBeforeExit();
            return 1;
        }
    }

    private static async Task PrintFriendlyDiagnosticsAsync()
    {
        Console.WriteLine("正在只读扫描本机 AI 编程助手会话……\n");
        foreach (var adapter in Adapters)
        {
            var installation = await adapter.DetectInstallationAsync();
            var count = 0;
            await foreach (var _ in adapter.ListSessionsAsync()) count++;

            Console.ForegroundColor = installation.IsDetected ? ConsoleColor.Green : ConsoleColor.DarkGray;
            Console.Write(installation.IsDetected ? "[已检测] " : "[未检测] ");
            Console.ResetColor();
            Console.WriteLine($"{DisplayName(adapter.Agent),-12} 会话数：{count}");
            foreach (var directory in installation.DataDirectories)
                Console.WriteLine($"           数据目录：{directory}");
        }

        Console.WriteLine("\n当前版本：安全只读扫描器；完整版图形界面请运行 AICodingSessionManager.exe。");
    }

    private static async Task PrintJsonDiagnosticsAsync()
    {
        var diagnostics = new List<object>();
        foreach (var adapter in Adapters)
        {
            var installation = await adapter.DetectInstallationAsync();
            var count = 0;
            await foreach (var _ in adapter.ListSessionsAsync()) count++;
            diagnostics.Add(new
            {
                Agent = adapter.Agent,
                installation.IsDetected,
                installation.Version,
                installation.DataDirectories,
                Sessions = count,
                Mode = "Read-only archive prototype"
            });
        }
        Console.WriteLine(JsonSerializer.Serialize(diagnostics, JsonOptions));
    }

    private static async Task<int> ReadSessionAsync(string agentName, string sourcePath)
    {
        var adapter = Adapters.SingleOrDefault(x =>
            x.Agent.ToString().Equals(agentName, StringComparison.OrdinalIgnoreCase));
        if (adapter is null)
        {
            Console.Error.WriteLine("未知 Agent。请使用 OpenCode、Codex 或 ClaudeCode。");
            return 2;
        }

        if (!File.Exists(sourcePath))
        {
            Console.Error.WriteLine($"找不到会话文件：{sourcePath}");
            return 2;
        }

        var session = await adapter.ReadSessionAsync(sourcePath);
        Console.WriteLine(JsonSerializer.Serialize(session, JsonOptions));
        return 0;
    }

    private static void PrintBanner()
    {
        Console.Title = "AI Coding Session Manager";
        Console.WriteLine("AI Coding Session Manager");
        Console.WriteLine("AI 编程助手会话迁移工具（只读原型）");
        Console.WriteLine(new string('─', 54));
    }

    private static void PrintUsage() => Console.Error.WriteLine(
        "用法：\n" +
        "  AICodingSessionManager.exe diagnostics\n" +
        "  AICodingSessionManager.exe read <OpenCode|Codex|ClaudeCode> <session.jsonl>");

    private static void PauseBeforeExit()
    {
        Console.WriteLine("\n按任意键关闭窗口……");
        if (!Console.IsInputRedirected) Console.ReadKey(intercept: true);
    }

    private static string DisplayName(AgentKind agent) => agent switch
    {
        AgentKind.ClaudeCode => "Claude Code",
        _ => agent.ToString()
    };
}
