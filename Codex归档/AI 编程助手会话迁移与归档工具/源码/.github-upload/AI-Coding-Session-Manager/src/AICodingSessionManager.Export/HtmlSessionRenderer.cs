using System.Globalization;
using System.Net;
using System.Text;
using AICodingSessionManager.Domain;

namespace AICodingSessionManager.Export;

/// <summary>Renders a searchable, printable, self-contained offline HTML session archive.</summary>
public sealed class HtmlSessionRenderer : ISessionRenderer
{
    public string FileExtension => "html";
    public string MediaType => "text/html";

    /// <inheritdoc />
    public string Render(UniversalSession session)
    {
        ArgumentNullException.ThrowIfNull(session);
        UniversalSessionJson.Validate(session);
        var output = new StringBuilder();
        output.AppendLine("<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">");
        output.AppendLine("<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">");
        output.Append("<title>").Append(Encode(session.Session.Title)).AppendLine("</title>");
        AppendStyle(output);
        output.AppendLine("</head><body><header class=\"hero\">");
        output.Append("<h1>").Append(Encode(session.Session.Title)).AppendLine("</h1><div class=\"meta\">");
        Meta(output, "Agent", Display(session.Session.Source));
        Meta(output, "Model", session.Session.Model);
        Meta(output, "Project", session.Session.Project.Name);
        Meta(output, "Date", Format(session.Session.UpdatedAt));
        Meta(output, "Messages", session.Messages.Count.ToString(CultureInfo.InvariantCulture));
        Meta(output, "Session ID", session.Session.Id);
        Meta(output, "Working directory", session.Session.Cwd);
        output.AppendLine("</div><div class=\"toolbar\"><label>搜索 <input id=\"search\" type=\"search\" placeholder=\"消息、工具、路径…\"></label><button id=\"theme\" type=\"button\">深色 / 浅色</button><button type=\"button\" onclick=\"window.print()\">打印 / PDF</button></div></header>");
        output.AppendLine("<div class=\"layout\"><nav><strong>目录</strong><ol>");
        for (var index = 0; index < session.Messages.Count; index++)
        {
            var message = session.Messages[index];
            output.Append("<li><a href=\"#message-").Append(index + 1).Append("\">")
                .Append(index + 1).Append(". ").Append(Encode(Display(message.Role))).AppendLine("</a></li>");
        }
        output.AppendLine("</ol></nav><main id=\"messages\">");
        for (var index = 0; index < session.Messages.Count; index++) AppendMessage(output, session.Messages[index], index + 1);
        if (session.UnsupportedRecords.Count > 0)
            output.Append("<p class=\"warning\">").Append(session.UnsupportedRecords.Count.ToString(CultureInfo.InvariantCulture)).AppendLine(" 条未知来源记录保留在 JSON 与原始归档中。</p>");
        output.AppendLine("</main></div>");
        AppendScript(output);
        output.AppendLine("</body></html>");
        return output.ToString();
    }

    private static void AppendMessage(StringBuilder output, UniversalMessage message, int index)
    {
        var searchText = string.Join(' ', message.Content.Select(part => $"{part.Type} {part.ToolName} {part.Text} {part.Arguments?.GetRawText()}"));
        output.Append("<article id=\"message-").Append(index).Append("\" data-search=\"").Append(EncodeAttribute(searchText)).AppendLine("\">");
        output.Append("<div class=\"message-head\"><a class=\"anchor\" href=\"#message-").Append(index).Append("\">#").Append(index).Append("</a><strong>")
            .Append(Encode(Display(message.Role))).Append("</strong><time>").Append(Encode(Format(message.Timestamp))).AppendLine("</time></div>");
        foreach (var part in message.Content) AppendPart(output, part);
        output.AppendLine("</article>");
    }

    private static void AppendPart(StringBuilder output, ContentPart part)
    {
        var collapsible = part.Type is ContentPartKind.Reasoning or ContentPartKind.ToolCall or ContentPartKind.ToolResult
            or ContentPartKind.Command or ContentPartKind.CommandResult or ContentPartKind.Patch or ContentPartKind.Diff;
        if (collapsible)
        {
            output.Append("<details class=\"part ").Append(Css(part.Type)).Append("\"><summary>")
                .Append(Encode(Label(part.Type)));
            if (!string.IsNullOrWhiteSpace(part.ToolName)) output.Append(" · ").Append(Encode(part.ToolName));
            output.AppendLine("</summary>");
        }
        else output.Append("<section class=\"part ").Append(Css(part.Type)).Append("\"><div class=\"kind\">").Append(Encode(Label(part.Type))).AppendLine("</div>");

        var value = part.Text ?? part.Arguments?.GetRawText() ?? string.Empty;
        output.Append("<pre><code>").Append(Encode(value)).AppendLine("</code></pre>");
        output.AppendLine(collapsible ? "</details>" : "</section>");
    }

    private static void AppendStyle(StringBuilder output) => output.AppendLine("""
<style>
:root{color-scheme:light;--bg:#f5f7fb;--panel:#fff;--text:#172033;--muted:#64748b;--border:#dfe4ec;--accent:#2563eb;--code:#f1f5f9}
:root[data-theme=dark]{color-scheme:dark;--bg:#0f172a;--panel:#172033;--text:#e5e7eb;--muted:#94a3b8;--border:#334155;--accent:#60a5fa;--code:#0b1220}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 system-ui,"Microsoft YaHei UI",sans-serif}.hero{padding:1.4rem max(1rem,calc((100vw - 1180px)/2));background:var(--panel);border-bottom:1px solid var(--border)}h1{margin:.2rem 0 1rem;overflow-wrap:anywhere}.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.4rem 1.4rem}.meta span{overflow-wrap:anywhere}.label,.kind{color:var(--muted);font-weight:650}.toolbar{display:flex;flex-wrap:wrap;align-items:center;gap:.7rem;margin-top:1rem}.toolbar input{min-width:260px;padding:.55rem;border:1px solid var(--border);border-radius:7px;background:var(--bg);color:var(--text)}button{padding:.55rem .8rem;border:1px solid var(--border);border-radius:7px;background:var(--panel);color:var(--text);cursor:pointer}.layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:1rem;max-width:1180px;margin:1rem auto;padding:0 1rem}nav{position:sticky;top:1rem;align-self:start;max-height:calc(100vh - 2rem);overflow:auto;background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:1rem}nav ol{padding-left:1.4rem}nav a,.anchor{color:var(--accent);text-decoration:none}article{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:1rem 1.2rem;margin:0 0 1rem}.message-head{display:flex;gap:.7rem;align-items:center;border-bottom:1px solid var(--border);padding-bottom:.6rem}.message-head time{margin-left:auto;color:var(--muted)}.part{margin:.8rem 0}.part summary{cursor:pointer;color:var(--muted);font-weight:650}.reasoning{border-left:3px solid #8b5cf6;padding-left:.8rem}.tool_call,.tool_result{border-left:3px solid #0ea5e9;padding-left:.8rem}.command,.command_result{border-left:3px solid #f59e0b;padding-left:.8rem}.patch,.diff{border-left:3px solid #22c55e;padding-left:.8rem}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:var(--code);border-radius:7px;padding:.8rem;overflow:auto}code{font-family:"Cascadia Mono",Consolas,monospace}.warning{color:#b45309}.hidden{display:none!important}
@media(max-width:760px){.layout{grid-template-columns:1fr}nav{position:static;max-height:240px}.toolbar input{min-width:180px;width:100%}}
@media print{.toolbar,nav{display:none}.layout{display:block;max-width:none}.hero,article{border:0;box-shadow:none}details:not([open])>*:not(summary){display:block}body{background:#fff;color:#000}}
</style>
""");

    private static void AppendScript(StringBuilder output) => output.AppendLine("""
<script>
(()=>{const root=document.documentElement,search=document.getElementById('search');
document.getElementById('theme').addEventListener('click',()=>{root.dataset.theme=root.dataset.theme==='dark'?'light':'dark'});
search.addEventListener('input',()=>{const q=search.value.trim().toLocaleLowerCase();document.querySelectorAll('article[data-search]').forEach(x=>x.classList.toggle('hidden',q&&!x.dataset.search.toLocaleLowerCase().includes(q)));});
})();
</script>
""");

    private static void Meta(StringBuilder output, string label, string? value)
    {
        if (!string.IsNullOrWhiteSpace(value)) output.Append("<span><b class=\"label\">").Append(Encode(label)).Append(":</b> ").Append(Encode(value)).AppendLine("</span>");
    }

    private static string Encode(string? value) => WebUtility.HtmlEncode(value ?? string.Empty);
    private static string EncodeAttribute(string? value) => WebUtility.HtmlEncode(value ?? string.Empty);
    private static string Format(DateTimeOffset? value) => value?.ToLocalTime().ToString("yyyy-MM-dd HH:mm:ss zzz", CultureInfo.InvariantCulture) ?? string.Empty;
    private static string Css(ContentPartKind type) => type.ToString().ToLowerInvariant();
    private static string Display(AgentKind agent) => agent switch
    {
        AgentKind.ClaudeCode => "Claude Code",
        AgentKind.ClaudeDesktop => "Claude Desktop",
        _ => agent.ToString()
    };
    private static string Display(MessageRole role) => role switch { MessageRole.User => "USER", MessageRole.Assistant => "ASSISTANT", MessageRole.System => "SYSTEM", _ => "TOOL" };
    private static string Label(ContentPartKind type) => type switch
    {
        ContentPartKind.Reasoning => "Thinking / Reasoning",
        ContentPartKind.ToolCall => "Tool Call",
        ContentPartKind.ToolResult => "Tool Result",
        ContentPartKind.Command => "Shell Command",
        ContentPartKind.CommandResult => "Command Output",
        ContentPartKind.Patch => "Patch",
        ContentPartKind.Diff => "Diff",
        _ => type.ToString()
    };
}
