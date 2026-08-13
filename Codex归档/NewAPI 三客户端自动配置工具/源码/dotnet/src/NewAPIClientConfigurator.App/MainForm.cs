using System.ComponentModel;
using System.Globalization;
using System.Text;
using System.Text.Json;

namespace NewAPIClientConfigurator.App;

internal sealed class MainForm : Form
{
    private readonly TextBox _urlBox = new();
    private readonly TextBox _tokenBox = new();
    private readonly NumericUpDown _concurrencyBox = new();
    private readonly CheckBox _codexBox = new();
    private readonly CheckBox _claudeBox = new();
    private readonly CheckBox _opencodeBox = new();
    private readonly CheckBox _availableOnlyBox = new();
    private readonly CheckBox _visionOnlyBox = new();
    private readonly CheckBox _deepContextBox = new();
    private readonly Button _scanButton = new();
    private readonly Button _probeButton = new();
    private readonly Button _previewButton = new();
    private readonly Button _applyButton = new();
    private readonly Button _restoreButton = new();
    private readonly DataGridView _grid = new();
    private readonly TextBox _logBox = new();
    private readonly ModelScanner _scanner = new();
    private List<ModelCapability> _models = new();
    private List<string> _modelIds = new();
    private bool _busy;

    public MainForm()
    {
        Text = "NewAPI 三客户端自动配置工具 (.NET)";
        Width = 1340;
        Height = 820;
        StartPosition = FormStartPosition.CenterScreen;

        BuildLayout();
        Load += OnLoad;
    }

    private void BuildLayout()
    {
        var root = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 1,
            RowCount = 5,
            Padding = new Padding(12)
        };
        root.RowStyles.Add(new RowStyle(SizeType.Absolute, 74));
        root.RowStyles.Add(new RowStyle(SizeType.Absolute, 84));
        root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        root.RowStyles.Add(new RowStyle(SizeType.Absolute, 150));
        Controls.Add(root);

        var connection = new GroupBox
        {
            Text = "NewAPI 连接",
            Dock = DockStyle.Fill
        };
        var connectionLayout = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 4,
            RowCount = 2,
            Padding = new Padding(8)
        };
        connectionLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 110));
        connectionLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        connectionLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 110));
        connectionLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        connection.Controls.Add(connectionLayout);

        _urlBox.Dock = DockStyle.Fill;
        _urlBox.Text = "http://10.97.144.27:3000";
        _tokenBox.Dock = DockStyle.Fill;
        _tokenBox.UseSystemPasswordChar = true;

        connectionLayout.Controls.Add(new Label { Text = "网关地址", TextAlign = ContentAlignment.MiddleLeft, Dock = DockStyle.Fill }, 0, 0);
        connectionLayout.Controls.Add(_urlBox, 1, 0);
        connectionLayout.Controls.Add(new Label { Text = "访问令牌", TextAlign = ContentAlignment.MiddleLeft, Dock = DockStyle.Fill }, 2, 0);
        connectionLayout.Controls.Add(_tokenBox, 3, 0);

        connectionLayout.Controls.Add(new Label { Text = "并发模型数", TextAlign = ContentAlignment.MiddleLeft, Dock = DockStyle.Fill }, 0, 1);
        _concurrencyBox.Minimum = 1;
        _concurrencyBox.Maximum = 8;
        _concurrencyBox.Value = 3;
        _concurrencyBox.Dock = DockStyle.Left;
        connectionLayout.Controls.Add(_concurrencyBox, 1, 1);
        connectionLayout.Controls.Add(new Label { Text = "说明", TextAlign = ContentAlignment.MiddleLeft, Dock = DockStyle.Fill }, 2, 1);
        connectionLayout.Controls.Add(new Label
        {
            Text = "先扫描，再探测能力，最后预览并写入配置。",
            TextAlign = ContentAlignment.MiddleLeft,
            Dock = DockStyle.Fill
        }, 3, 1);

        root.Controls.Add(connection, 0, 0);

        var buttonsPanel = new FlowLayoutPanel
        {
            Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.LeftToRight,
            Padding = new Padding(0),
            WrapContents = false
        };
        _scanButton.Text = "1. 扫描模型";
        _probeButton.Text = "2. 探测能力";
        _previewButton.Text = "3. 预览修改";
        _applyButton.Text = "4. 一键配置";
        _restoreButton.Text = "恢复备份";
        foreach (var button in new[] { _scanButton, _probeButton, _previewButton, _applyButton, _restoreButton })
        {
            button.Width = 128;
            button.Height = 34;
            button.Margin = new Padding(0, 0, 10, 0);
            buttonsPanel.Controls.Add(button);
        }

        var optionsPanel = new FlowLayoutPanel
        {
            Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.LeftToRight,
            WrapContents = false
        };
        _availableOnlyBox.Text = "只显示兼容模型";
        _visionOnlyBox.Text = "仅显示支持视觉的模型";
        _deepContextBox.Text = "深度探测上下文（更耗时）";
        _codexBox.Text = "Codex";
        _claudeBox.Text = "Claude Code";
        _opencodeBox.Text = "OpenCode";
        foreach (var box in new[] { _availableOnlyBox, _visionOnlyBox, _deepContextBox, _codexBox, _claudeBox, _opencodeBox })
        {
            box.AutoSize = true;
            box.Margin = new Padding(0, 6, 14, 0);
            optionsPanel.Controls.Add(box);
        }
        _codexBox.Checked = true;
        _claudeBox.Checked = true;
        _opencodeBox.Checked = true;
        optionsPanel.Controls.Add(new Label { Text = "并发", AutoSize = true, Margin = new Padding(12, 8, 4, 0) });
        optionsPanel.Controls.Add(_concurrencyBox);
        buttonsPanel.Controls.Add(optionsPanel);

        root.Controls.Add(buttonsPanel, 0, 1);

        _grid.Dock = DockStyle.Fill;
        _grid.AllowUserToAddRows = false;
        _grid.AllowUserToDeleteRows = false;
        _grid.ReadOnly = true;
        _grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
        _grid.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.AllCells;
        _grid.RowHeadersVisible = false;
        _grid.Columns.Add("Model", "模型");
        _grid.Columns.Add("Responses", "响应接口");
        _grid.Columns.Add("Messages", "消息接口");
        _grid.Columns.Add("Chat", "聊天接口");
        _grid.Columns.Add("Tools", "工具调用");
        _grid.Columns.Add("Vision", "视觉");
        _grid.Columns.Add("Reasoning", "推理能力");
        _grid.Columns.Add("Context", "上下文");
        _grid.Columns.Add("Output", "最大输出");
        _grid.Columns.Add("Codex", "Codex");
        _grid.Columns.Add("ClaudeOpenCode", "Claude / OpenCode");
        root.Controls.Add(_grid, 0, 2);

        _logBox.Dock = DockStyle.Fill;
        _logBox.Multiline = true;
        _logBox.ScrollBars = ScrollBars.Vertical;
        _logBox.ReadOnly = true;
        _logBox.BackColor = Color.White;
        _logBox.Font = new Font(FontFamily.GenericMonospace, 9f);
        root.Controls.Add(_logBox, 0, 3);

        _scanButton.Click += async (_, _) => await ScanModelsAsync();
        _probeButton.Click += async (_, _) => await ProbeModelsAsync();
        _previewButton.Click += async (_, _) => await ShowPreviewAsync();
        _applyButton.Click += async (_, _) => await ApplyAsync();
        _restoreButton.Click += async (_, _) => await RestoreAsync();
        _availableOnlyBox.CheckedChanged += (_, _) => Render();
        _visionOnlyBox.CheckedChanged += (_, _) => Render();
    }

    private void OnLoad(object? sender, EventArgs e)
    {
        _tokenBox.Text = AppPaths.LoadToken();
        var cache = AppPaths.LoadCache();
        if (cache is null)
        {
            Log("没有找到缓存，先扫描模型。");
            return;
        }

        _urlBox.Text = cache.GatewayUrl;
        _models = cache.Capabilities.Select(UserMappings.Apply).Where(model => !model.IsExcluded).ToList();
        _modelIds = _models.Select(model => model.ModelId).ToList();
        Render();
        Log("已加载本地缓存，建议重新扫描后再配置。");
    }

    private async Task ScanModelsAsync()
    {
        if (!ValidateConnection())
        {
            return;
        }

        await RunBusyAsync(async () =>
        {
            var ids = await _scanner.ListModelsAsync(_urlBox.Text, _tokenBox.Text, CancellationToken.None);
            _modelIds = ids.Distinct(StringComparer.OrdinalIgnoreCase).Where(id => !ModelFilters.IsExcludedModel(id)).ToList();
            _models = _modelIds.Select(id => UserMappings.Apply(new ModelCapability { ModelId = id, DisplayName = DisplayName(id) })).ToList();
            AppPaths.SaveCache(new ScanCache { GatewayUrl = _urlBox.Text.Trim().TrimEnd('/'), Capabilities = _models });
            Render();
            Log($"发现 {_modelIds.Count} 个模型，请继续探测能力。");
        });
    }

    private async Task ProbeModelsAsync()
    {
        if (!ValidateConnection())
        {
            return;
        }

        if (_modelIds.Count == 0)
        {
            MessageBox.Show(this, "请先扫描模型。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        if (_deepContextBox.Checked)
        {
            var answer = MessageBox.Show(this, "深度探测会发送更长的上下文请求，可能更耗时也更耗 token。是否继续？", "确认", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
            if (answer != DialogResult.Yes)
            {
                return;
            }
        }

        await RunBusyAsync(async () =>
        {
            var scanned = await _scanner.ScanAsync(
                _urlBox.Text,
                _tokenBox.Text,
                _modelIds,
                (int)_concurrencyBox.Value,
                _deepContextBox.Checked,
                message => Log(message),
                CancellationToken.None);
            _models = scanned.Select(UserMappings.Apply).ToList();
            AppPaths.SaveCache(new ScanCache { GatewayUrl = _urlBox.Text.Trim().TrimEnd('/'), Capabilities = _models });
            Render();
            Log("能力缓存已保存。");
        });
    }

    private async Task ShowPreviewAsync()
    {
        if (_models.Count == 0)
        {
            MessageBox.Show(this, "请先扫描并探测模型能力。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        var configurator = CreateConfigurator();
        var previewText = configurator.Preview(SelectedTargets());
        using var dialog = new Form
        {
            Text = "配置预览",
            Width = 760,
            Height = 460,
            StartPosition = FormStartPosition.CenterParent
        };
        var box = new TextBox
        {
            Multiline = true,
            Dock = DockStyle.Fill,
            ScrollBars = ScrollBars.Vertical,
            ReadOnly = true,
            Text = previewText
        };
        var buttons = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 44, FlowDirection = FlowDirection.RightToLeft };
        var ok = new Button { Text = "关闭", DialogResult = DialogResult.OK, Width = 90 };
        buttons.Controls.Add(ok);
        dialog.Controls.Add(box);
        dialog.Controls.Add(buttons);
        dialog.AcceptButton = ok;
        dialog.ShowDialog(this);
        await Task.CompletedTask;
    }

    private async Task ApplyAsync()
    {
        if (_models.Count == 0 || !ValidateConnection())
        {
            return;
        }

        var now = DateTime.UtcNow;
        if (_models.Any(model => model.TestTime is null || (now - model.TestTime.Value).TotalHours > 24))
        {
            var response = MessageBox.Show(this, "能力缓存已超过 24 小时，建议先重新扫描。仍然继续吗？", "提示", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
            if (response != DialogResult.Yes)
            {
                return;
            }
        }

        await ShowPreviewAsync();
        var confirm = MessageBox.Show(this, "确认写入预览中的配置并保存当前用户环境变量吗？", "确认", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
        if (confirm != DialogResult.Yes)
        {
            return;
        }

        AppPaths.SaveToken(_tokenBox.Text);
        await RunBusyAsync(async () =>
        {
            var result = await CreateConfigurator().ApplyAsync(SelectedTargets(), CancellationToken.None);
            Log(string.Join(Environment.NewLine, result));
            MessageBox.Show(this, string.Join(Environment.NewLine, result), "配置完成", MessageBoxButtons.OK, MessageBoxIcon.Information);
        });
    }

    private async Task RestoreAsync()
    {
        var backups = AppPaths.ListBackups();
        if (backups.Count == 0)
        {
            MessageBox.Show(this, "没有找到可恢复的备份。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        using var dialog = new BackupSelectionDialog(backups);
        if (dialog.ShowDialog(this) != DialogResult.OK || dialog.SelectedBackup is null)
        {
            return;
        }

        var confirm = MessageBox.Show(this, $"将恢复备份：\n{dialog.SelectedBackup}\n\n这会还原 Codex、Claude Code、OpenCode 的配置及相关用户环境变量。继续吗？", "确认恢复", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
        if (confirm != DialogResult.Yes)
        {
            return;
        }

        await RunBusyAsync(() =>
        {
            AppPaths.RestoreBackup(dialog.SelectedBackup);
            Log($"已恢复备份：{dialog.SelectedBackup}");
            MessageBox.Show(this, $"已恢复备份：\n{dialog.SelectedBackup}", "恢复完成", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return Task.CompletedTask;
        });
    }

    private async Task RunBusyAsync(Func<Task> action)
    {
        SetBusy(true);
        try
        {
            await action();
        }
        catch (Exception ex)
        {
            Log($"错误：{ex.Message}");
            MessageBox.Show(this, ex.Message, "操作失败", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        finally
        {
            SetBusy(false);
        }
    }

    private bool ValidateConnection()
    {
        if (string.IsNullOrWhiteSpace(_urlBox.Text) || string.IsNullOrWhiteSpace(_tokenBox.Text))
        {
            MessageBox.Show(this, "请先输入网关地址和访问令牌。", "缺少连接信息", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return false;
        }

        return true;
    }

    private IReadOnlyCollection<string> SelectedTargets()
    {
        var targets = new List<string>();
        if (_codexBox.Checked)
        {
            targets.Add("codex");
        }
        if (_claudeBox.Checked)
        {
            targets.Add("claude");
        }
        if (_opencodeBox.Checked)
        {
            targets.Add("opencode");
        }

        return targets;
    }

    private Configurator CreateConfigurator()
    {
        return new Configurator(_urlBox.Text, _tokenBox.Text, _models);
    }

    private void Render()
    {
        _grid.Rows.Clear();
        var values = _models.Where(model => !_availableOnlyBox.Checked || model.CodexCompatible || model.ClaudeCompatible || model.OpenCodeCompatible)
            .Where(model => !_visionOnlyBox.Checked || model.Vision)
            .ToList();

        foreach (var model in values)
        {
            _grid.Rows.Add(
                model.DisplayName,
                ProtocolLabel(model.Responses),
                ProtocolLabel(model.Messages),
                ProtocolLabel(model.Chat),
                StatusLabel(model.Responses.Tools, model.Messages.Tools, model.Chat.Tools),
                StatusLabel(model.Responses.Vision, model.Messages.Vision, model.Chat.Vision),
                model.ReasoningSummary(),
                model.ContextSummary(),
                model.MaxOutputTokens?.ToString(CultureInfo.InvariantCulture) ?? "Unknown",
                model.ManualClients.Contains("codex") ? "User confirmed" : StatusLabel(model.CodexCompatible),
                model.ManualClients.Contains("claude") ? "User confirmed" : $"{StatusLabel(model.ClaudeCompatible)} / {StatusLabel(model.OpenCodeCompatible)}"
            );
        }
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

    private void SetBusy(bool busy)
    {
        _busy = busy;
        foreach (var button in new[] { _scanButton, _probeButton, _previewButton, _applyButton, _restoreButton })
        {
            button.Enabled = !busy;
        }
    }

    private void Log(string message)
    {
        if (InvokeRequired)
        {
            BeginInvoke(() => Log(message));
            return;
        }

        _logBox.AppendText(message + Environment.NewLine);
    }

    private static string DisplayName(string modelId)
    {
        var text = modelId.Replace('-', ' ').Replace('_', ' ');
        var builder = new StringBuilder();
        foreach (var word in text.Split(' ', StringSplitOptions.RemoveEmptyEntries))
        {
            if (builder.Length > 0)
            {
                builder.Append(' ');
            }
            builder.Append(char.ToUpperInvariant(word[0]));
            if (word.Length > 1)
            {
                builder.Append(word[1..]);
            }
        }
        return builder.ToString();
    }

    private sealed class BackupSelectionDialog : Form
    {
        private readonly ListBox _list = new();

        public BackupSelectionDialog(IReadOnlyList<string> backups)
        {
            Text = "选择要恢复的备份";
            Width = 760;
            Height = 420;
            StartPosition = FormStartPosition.CenterParent;

            _list.Dock = DockStyle.Fill;
            _list.Items.AddRange(backups.Select(Path.GetFileName).ToArray());
            _list.SelectedIndex = 0;
            Controls.Add(_list);

            var panel = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 46, FlowDirection = FlowDirection.RightToLeft };
            var ok = new Button { Text = "确定", DialogResult = DialogResult.OK, Width = 90 };
            var cancel = new Button { Text = "取消", DialogResult = DialogResult.Cancel, Width = 90 };
            panel.Controls.Add(ok);
            panel.Controls.Add(cancel);
            Controls.Add(panel);
            AcceptButton = ok;
            CancelButton = cancel;
        }

        public string? SelectedBackup
        {
            get
            {
                if (_list.SelectedItem is null)
                {
                    return null;
                }

                var backupName = _list.SelectedItem.ToString();
                return string.IsNullOrWhiteSpace(backupName) ? null : Path.Combine(AppPaths.BackupRoot, backupName);
            }
        }
    }
}
