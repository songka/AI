using System.Windows;
using System.IO;
using NewAPIClientConfigurator.Core;

namespace NewAPIClientConfigurator.App;

public partial class BackupDialog : Window
{
    public BackupDialog(IReadOnlyList<string> backups)
    {
        InitializeComponent();
        foreach (var backup in backups)
        {
            BackupList.Items.Add(Path.GetFileName(backup));
        }

        if (BackupList.Items.Count > 0)
        {
            BackupList.SelectedIndex = 0;
        }
    }

    public string? SelectedBackup
    {
        get
        {
            var backupName = BackupList.SelectedItem?.ToString();
            return string.IsNullOrWhiteSpace(backupName) ? null : Path.Combine(AppPaths.BackupRoot, backupName);
        }
    }

    private void OnOkClick(object sender, RoutedEventArgs e)
    {
        DialogResult = true;
    }
}
