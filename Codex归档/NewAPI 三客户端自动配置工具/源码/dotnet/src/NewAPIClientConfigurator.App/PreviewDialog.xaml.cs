using System.Windows;

namespace NewAPIClientConfigurator.App;

public partial class PreviewDialog : Window
{
    public PreviewDialog(string previewText)
    {
        InitializeComponent();
        PreviewBox.Text = previewText;
    }

    private void OnCloseClick(object sender, RoutedEventArgs e)
    {
        DialogResult = true;
    }
}
