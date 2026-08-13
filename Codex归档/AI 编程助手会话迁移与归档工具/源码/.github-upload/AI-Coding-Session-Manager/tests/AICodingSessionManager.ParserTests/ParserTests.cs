using AICodingSessionManager.Adapters.ClaudeCode;
using AICodingSessionManager.Adapters.ClaudeDesktop;
using AICodingSessionManager.Adapters.Codex;
using AICodingSessionManager.Adapters.OpenCode;
using AICodingSessionManager.Domain;
using System.IO.Compression;
using Xunit;

namespace AICodingSessionManager.ParserTests;

public sealed class ParserTests
{
    [Fact]
    public async Task Codex_parser_reads_messages_and_metadata()
    {
        var session = await new CodexAdapter().ReadSessionAsync(Fixture("codex"));
        Assert.Equal("fixture-codex", session.Session.Id);
        Assert.Equal("C:\\workspace\\sample", session.Session.Cwd);
        Assert.Equal(2, session.Messages.Count);
    }

    [Fact]
    public async Task Claude_parser_keeps_malformed_records_without_aborting()
    {
        var session = await new ClaudeCodeAdapter().ReadSessionAsync(Fixture("claude"));
        Assert.Equal(2, session.Messages.Count);
        Assert.Single(session.UnsupportedRecords);
        Assert.Equal("u1", session.Messages[1].ParentMessageId);
    }

    [Fact]
    public async Task OpenCode_parser_reads_a_minimal_jsonl_fixture()
    {
        var session = await new OpenCodeAdapter().ReadSessionAsync(Fixture("opencode"));
        Assert.Equal(2, session.Messages.Count);
        Assert.Equal("Inspect the project.", session.Messages[0].Content[0].Text);
    }

    [Fact]
    public async Task OpenCode_parser_reads_official_legacy_storage_layout()
    {
        var root = Path.Combine(Path.GetTempPath(), "AICSM-opencode-tests", Guid.NewGuid().ToString("N"));
        var sessionDirectory = Path.Combine(root, "storage", "session", "project-1");
        var messageDirectory = Path.Combine(root, "storage", "message", "ses_test");
        var firstPartDirectory = Path.Combine(root, "storage", "part", "msg_user");
        var secondPartDirectory = Path.Combine(root, "storage", "part", "msg_assistant");
        Directory.CreateDirectory(sessionDirectory);
        Directory.CreateDirectory(messageDirectory);
        Directory.CreateDirectory(firstPartDirectory);
        Directory.CreateDirectory(secondPartDirectory);

        try
        {
            var sessionPath = Path.Combine(sessionDirectory, "ses_test.json");
            await File.WriteAllTextAsync(sessionPath, """
                {"id":"ses_test","projectID":"project-1","directory":"C:\\work\\sample","title":"真实 OpenCode 会话","version":"1.2.3","time":{"created":1700000000000,"updated":1700000002000}}
                """);
            await File.WriteAllTextAsync(Path.Combine(messageDirectory, "msg_user.json"), """
                {"id":"msg_user","sessionID":"ses_test","role":"user","agent":"build","model":{"providerID":"openai","modelID":"gpt-test"},"time":{"created":1700000000000}}
                """);
            await File.WriteAllTextAsync(Path.Combine(firstPartDirectory, "prt_text.json"), """
                {"id":"prt_text","sessionID":"ses_test","messageID":"msg_user","type":"text","text":"请检查这个项目。"}
                """);
            await File.WriteAllTextAsync(Path.Combine(messageDirectory, "msg_assistant.json"), """
                {"id":"msg_assistant","sessionID":"ses_test","role":"assistant","parentID":"msg_user","modelID":"gpt-test","providerID":"openai","time":{"created":1700000001000}}
                """);
            await File.WriteAllTextAsync(Path.Combine(secondPartDirectory, "prt_tool.json"), """
                {"id":"prt_tool","sessionID":"ses_test","messageID":"msg_assistant","type":"tool","callID":"call-1","tool":"read","state":{"status":"completed","input":{"filePath":"README.md"},"output":"文件正文","title":"Read","metadata":{},"time":{"start":1700000001000,"end":1700000001500}}}
                """);
            await File.WriteAllTextAsync(Path.Combine(secondPartDirectory, "prt_reasoning.json"), """
                {"id":"prt_reasoning","sessionID":"ses_test","messageID":"msg_assistant","type":"reasoning","text":"先只读检查。","time":{"start":1700000001000,"end":1700000001200}}
                """);

            var adapter = new OpenCodeAdapter([root], executablePath: Path.Combine(root, "missing-opencode.exe"));
            var references = new List<SessionReference>();
            await foreach (var item in adapter.ListSessionsAsync()) references.Add(item);
            var reference = Assert.Single(references);
            Assert.Equal("ses_test", reference.Id);

            var session = await adapter.ReadSessionAsync(reference.SourcePath);
            Assert.Equal("真实 OpenCode 会话", session.Session.Title);
            Assert.Equal("C:\\work\\sample", session.Session.Cwd);
            Assert.Equal(2, session.Messages.Count);
            Assert.Contains(session.Messages.SelectMany(message => message.Content), part =>
                part.Type == ContentPartKind.Reasoning && part.Text == "先只读检查。");
            var call = Assert.Single(session.Messages.SelectMany(message => message.Content), part => part.Type == ContentPartKind.ToolCall);
            Assert.Equal("README.md", call.Arguments!.Value.GetProperty("filePath").GetString());
            Assert.Contains(session.Messages.SelectMany(message => message.Content), part =>
                part.Type == ContentPartKind.ToolResult && part.Text == "文件正文");
        }
        finally
        {
            if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        }
    }

    [Fact]
    public async Task Claude_Desktop_official_export_imports_and_reads_complete_conversation()
    {
        var root = Path.Combine(Path.GetTempPath(), "AICSM-claude-desktop-tests", Guid.NewGuid().ToString("N"));
        var exportPath = Path.Combine(root, "conversations.json");
        var importRoot = Path.Combine(root, "imports");
        Directory.CreateDirectory(root);
        try
        {
            await File.WriteAllTextAsync(exportPath, """
                [
                  {
                    "uuid": "conv_test",
                    "name": "桌面端真实导出测试",
                    "created_at": "2026-08-13T01:00:00Z",
                    "updated_at": "2026-08-13T01:03:00Z",
                    "chat_messages": [
                      {
                        "uuid": "msg_user",
                        "sender": "human",
                        "created_at": "2026-08-13T01:00:00Z",
                        "text": "请检查这份设计。",
                        "attachments": [{"file_name":"design.md","file_type":"text/markdown"}]
                      },
                      {
                        "uuid": "msg_assistant",
                        "sender": "assistant",
                        "created_at": "2026-08-13T01:01:00Z",
                        "content": [
                          {"type":"thinking","thinking":"先理解目标。"},
                          {"type":"text","text":"我已经完成检查。"},
                          {"type":"tool_use","id":"tool_1","name":"search","input":{"query":"fixture"}},
                          {"type":"tool_result","tool_use_id":"tool_1","content":"找到 1 条"}
                        ]
                      }
                    ]
                  }
                ]
                """);

            var imported = await new ClaudeDesktopExportImporter(importRoot).ImportAsync(exportPath);
            Assert.Equal(1, imported);
            var adapter = new ClaudeDesktopAdapter(importRoot);
            var references = new List<SessionReference>();
            await foreach (var item in adapter.ListSessionsAsync()) references.Add(item);
            var reference = Assert.Single(references);
            var session = await adapter.ReadSessionAsync(reference.SourcePath);

            Assert.Equal(AgentKind.ClaudeDesktop, session.Session.Source);
            Assert.Equal("桌面端真实导出测试", session.Session.Title);
            Assert.Equal(2, session.Messages.Count);
            Assert.Contains(session.Messages.SelectMany(message => message.Content), part => part.Type == ContentPartKind.Reasoning && part.Text == "先理解目标。");
            Assert.Contains(session.Messages.SelectMany(message => message.Content), part => part.Type == ContentPartKind.ToolCall && part.ToolName == "search");
            Assert.Contains(session.Messages.SelectMany(message => message.Content), part => part.Type == ContentPartKind.ToolResult && part.Text == "找到 1 条");
            Assert.Contains(session.Attachments, attachment => attachment.Name == "design.md");
        }
        finally
        {
            if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        }
    }

    [Fact]
    public async Task Claude_Desktop_importer_reads_official_zip_and_rejects_ambiguous_exports()
    {
        var root = Path.Combine(Path.GetTempPath(), "AICSM-claude-desktop-zip-tests", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            const string json = """
                [{"uuid":"zip_conv","name":"ZIP 会话","created_at":"2026-08-13T01:00:00Z","updated_at":"2026-08-13T01:01:00Z","chat_messages":[{"uuid":"zip_msg","sender":"human","created_at":"2026-08-13T01:00:00Z","text":"来自官方 ZIP。"}]}]
                """;
            var zipPath = Path.Combine(root, "claude-export.zip");
            using (var archive = ZipFile.Open(zipPath, ZipArchiveMode.Create))
            {
                await using var writer = new StreamWriter(archive.CreateEntry("data/conversations.json").Open());
                await writer.WriteAsync(json);
            }
            var importRoot = Path.Combine(root, "imports");
            Assert.Equal(1, await new ClaudeDesktopExportImporter(importRoot).ImportAsync(zipPath));
            Assert.Single(Directory.GetFiles(importRoot, "*.json"));

            var ambiguousPath = Path.Combine(root, "ambiguous.zip");
            using (var archive = ZipFile.Open(ambiguousPath, ZipArchiveMode.Create))
            {
                foreach (var name in new[] { "one/conversations.json", "two/conversations.json" })
                {
                    await using var writer = new StreamWriter(archive.CreateEntry(name).Open());
                    await writer.WriteAsync(json);
                }
            }
            await Assert.ThrowsAsync<InvalidDataException>(() =>
                new ClaudeDesktopExportImporter(Path.Combine(root, "ambiguous-imports")).ImportAsync(ambiguousPath));
        }
        finally
        {
            if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        }
    }

    [Fact]
    public void Preview_compacts_only_consecutive_synthetic_filler_lines()
    {
        var source = string.Join('\n',
            "真实问题：请找出最后一行",
            "FILLER-00001 The quick brown fox jumps over the lazy dog 0123456789 repeat filler line.",
            "FILLER-00002 The quick brown fox jumps over the lazy dog 0123456789 repeat filler line.",
            "FILLER-00003 The quick brown fox jumps over the lazy dog 0123456789 repeat filler line.",
            "MARKER-LINE: LAST-TOKEN-7K3QZ-END");

        var result = PreviewTextFormatter.CompactRepeatedFiller(source);

        Assert.Contains("真实问题", result);
        Assert.Contains("已隐藏 3 行测试占位数据", result);
        Assert.Contains("真实正文", result);
        Assert.Contains("MARKER-LINE: LAST-TOKEN-7K3QZ-END", result);
        Assert.DoesNotContain("quick brown fox", result);
    }

    [Fact]
    public void Preview_formatter_leaves_normal_conversation_unchanged()
    {
        const string source = "这是一段正常的 Claude Code 对话。";
        Assert.Equal(source, PreviewTextFormatter.CompactRepeatedFiller(source));
    }

    private static string Fixture(string agent) => Path.Combine(AppContext.BaseDirectory, "fixtures", agent, "session.jsonl");
}
