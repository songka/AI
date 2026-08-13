using System;
using System.IO;
using System.IO.Compression;
using System.Text;

public static class UnzipCompat
{
    public static int Main(string[] args)
    {
        Console.OutputEncoding = new UTF8Encoding(false);
        if (args.Length < 2) return 2;
        using (var zip = ZipFile.OpenRead(args[1]))
        {
            if (args[0] == "-Z1")
            {
                foreach (var entry in zip.Entries) Console.WriteLine(entry.FullName);
                return 0;
            }
            if (args[0] == "-p" && args.Length >= 3)
            {
                var entry = zip.GetEntry(args[2].Replace('\\', '/'));
                if (entry == null) return 1;
                using (var input = entry.Open())
                using (var output = Console.OpenStandardOutput()) input.CopyTo(output);
                return 0;
            }
        }
        return 2;
    }
}
