using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Windows.Forms;

namespace BomCheckNetworkLauncher
{
    internal static class Program
    {
        private const string CacheRootName = "BOMCheck";

        [STAThread]
        private static int Main(string[] args)
        {
            try
            {
                string launcherPath = Process.GetCurrentProcess().MainModule.FileName;
                string launcherDir = Path.GetDirectoryName(launcherPath);
                string targetName = ResolveTargetName(launcherPath, args);
                string sourceExe = Path.Combine(launcherDir, targetName);

                if (!File.Exists(sourceExe))
                {
                    ShowError("找不到主程序：\n" + sourceExe + "\n\n请把启动器放在主程序 exe 同一目录。");
                    return 2;
                }

                string localExe = EnsureLocalCopy(sourceExe);
                string[] passThroughArgs = ShouldConsumeFirstArg(args) ? args.Skip(1).ToArray() : args;

                ProcessStartInfo startInfo = new ProcessStartInfo
                {
                    FileName = localExe,
                    Arguments = JoinArguments(passThroughArgs),
                    WorkingDirectory = launcherDir,
                    UseShellExecute = true,
                };
                Process.Start(startInfo);
                return 0;
            }
            catch (Exception ex)
            {
                ShowError("启动失败：\n" + ex.Message);
                return 1;
            }
        }

        private static string ResolveTargetName(string launcherPath, string[] args)
        {
            if (ShouldConsumeFirstArg(args))
            {
                return Path.GetFileName(args[0]);
            }

            string name = Path.GetFileNameWithoutExtension(launcherPath);
            const string suffix = "_launcher";
            if (name.EndsWith(suffix, StringComparison.OrdinalIgnoreCase))
            {
                return name.Substring(0, name.Length - suffix.Length) + ".exe";
            }

            throw new InvalidOperationException("启动器文件名应为 bomcheck_web_launcher.exe 或 bomcheck_app_launcher.exe。");
        }

        private static bool ShouldConsumeFirstArg(string[] args)
        {
            return args.Length > 0
                && args[0].EndsWith(".exe", StringComparison.OrdinalIgnoreCase)
                && !args[0].StartsWith("-", StringComparison.Ordinal);
        }

        private static string EnsureLocalCopy(string sourceExe)
        {
            FileInfo source = new FileInfo(sourceExe);
            string cacheDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                CacheRootName,
                "exe-cache",
                Path.GetFileNameWithoutExtension(source.Name),
                ShortHash(source.DirectoryName.ToLowerInvariant())
            );
            Directory.CreateDirectory(cacheDir);

            string localExe = Path.Combine(cacheDir, source.Name);
            FileInfo local = new FileInfo(localExe);
            bool needsCopy = !local.Exists
                || local.Length != source.Length
                || local.LastWriteTimeUtc != source.LastWriteTimeUtc;

            if (!needsCopy)
            {
                return localExe;
            }

            string tempExe = localExe + ".tmp";
            try
            {
                if (File.Exists(tempExe))
                {
                    File.Delete(tempExe);
                }

                File.Copy(sourceExe, tempExe, true);
                File.SetLastWriteTimeUtc(tempExe, source.LastWriteTimeUtc);

                if (File.Exists(localExe))
                {
                    File.Delete(localExe);
                }

                File.Move(tempExe, localExe);
            }
            catch
            {
                if (File.Exists(tempExe))
                {
                    TryDelete(tempExe);
                }

                if (File.Exists(localExe))
                {
                    return localExe;
                }

                throw;
            }

            return localExe;
        }

        private static string ShortHash(string text)
        {
            using (SHA256 sha = SHA256.Create())
            {
                byte[] bytes = sha.ComputeHash(Encoding.UTF8.GetBytes(text));
                StringBuilder builder = new StringBuilder(16);
                for (int i = 0; i < 8; i++)
                {
                    builder.Append(bytes[i].ToString("x2"));
                }
                return builder.ToString();
            }
        }

        private static void TryDelete(string path)
        {
            try
            {
                File.Delete(path);
            }
            catch
            {
                // Best-effort cleanup only.
            }
        }

        private static string JoinArguments(string[] args)
        {
            return string.Join(" ", args.Select(QuoteArgument));
        }

        private static string QuoteArgument(string arg)
        {
            if (string.IsNullOrEmpty(arg))
            {
                return "\"\"";
            }

            if (arg.IndexOfAny(new[] { ' ', '\t', '"' }) < 0)
            {
                return arg;
            }

            return "\"" + arg.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
        }

        private static void ShowError(string message)
        {
            MessageBox.Show(message, "BOMCheck 启动器", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
