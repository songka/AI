using System;
using System.Diagnostics;

public static class UnzipShim {
  public static int Main(string[] args) {
    if (args.Length < 2) return 2;
    string tarArgs;
    if (args[0] == "-Z1") {
      tarArgs = "-tf \"" + args[1] + "\"";
    } else if (args[0] == "-p" && args.Length >= 3) {
      tarArgs = "-xOf \"" + args[1] + "\" \"" + args[2] + "\"";
    } else {
      return 2;
    }
    var p = new Process();
    p.StartInfo.FileName = "tar.exe";
    p.StartInfo.Arguments = tarArgs;
    p.StartInfo.UseShellExecute = false;
    p.StartInfo.RedirectStandardOutput = true;
    p.StartInfo.RedirectStandardError = true;
    p.StartInfo.CreateNoWindow = true;
    p.Start();
    p.StandardOutput.BaseStream.CopyTo(Console.OpenStandardOutput());
    p.StandardError.BaseStream.CopyTo(Console.OpenStandardError());
    p.WaitForExit();
    return p.ExitCode;
  }
}
