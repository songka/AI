using System.Windows;

namespace AICodingSessionManager.UI;

public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        DispatcherUnhandledException += (_, args) =>
        {
            _ = AppLogger.WriteAsync("FATAL", args.Exception.ToString());
            MessageBox.Show(args.Exception.Message, "AI Coding Session Manager", MessageBoxButton.OK, MessageBoxImage.Error);
            args.Handled = true;
        };
        base.OnStartup(e);
    }
}
