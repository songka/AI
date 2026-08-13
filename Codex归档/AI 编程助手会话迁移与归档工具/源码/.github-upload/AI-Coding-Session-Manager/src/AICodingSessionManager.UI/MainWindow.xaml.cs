using System.Windows;

namespace AICodingSessionManager.UI;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        DataContext = new MainViewModel();
        Loaded += OnLoaded;
        Closed += OnClosed;
    }

    private async void OnLoaded(object sender, RoutedEventArgs e)
    {
        try
        {
            await ((MainViewModel)DataContext).InitializeAsync();
        }
        catch (OperationCanceledException)
        {
            // 关闭窗口期间取消初始化是正常流程。
        }
        catch (Exception exception)
        {
            MessageBox.Show(exception.Message, "初始化失败", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private void OnClosed(object? sender, EventArgs e) =>
        ((MainViewModel)DataContext).Dispose();
}
