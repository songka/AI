using System.Windows;

namespace AICodingSessionManager.UI;

public partial class RawDataWindow : Window
{
    public RawDataWindow(string title, string content, string status)
    {
        InitializeComponent();
        Title = $"原始数据 · {title}（只读、未脱敏）";
        RawText.Text = content;
        RawStatus.Text = status;
    }
}
