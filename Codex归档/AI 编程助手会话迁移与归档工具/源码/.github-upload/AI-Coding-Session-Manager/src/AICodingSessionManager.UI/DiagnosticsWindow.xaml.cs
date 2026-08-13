using System.Windows;

namespace AICodingSessionManager.UI;

public partial class DiagnosticsWindow : Window
{
    public DiagnosticsWindow(string content)
    {
        InitializeComponent();
        ContentText.Text = content;
    }

    private void Copy_Click(object sender, RoutedEventArgs e) => Clipboard.SetText(ContentText.Text);
}
