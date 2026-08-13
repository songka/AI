using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

[StructLayout(LayoutKind.Sequential)] public struct SIZE { public int cx, cy; public SIZE(int x,int y){cx=x;cy=y;} }
[ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown), Guid("bcc18b79-ba16-442f-80c4-8a59c30c463b")]
interface IShellItemImageFactory { void GetImage(SIZE size, int flags, out IntPtr phbm); }
public static class VideoThumbnail {
  [DllImport("shell32.dll", CharSet=CharSet.Unicode, PreserveSig=false)]
  static extern void SHCreateItemFromParsingName(string path, IntPtr bind, ref Guid riid, [MarshalAs(UnmanagedType.Interface)] out IShellItemImageFactory item);
  [DllImport("gdi32.dll")] static extern bool DeleteObject(IntPtr hObject);
  public static int Main(string[] args) {
    if(args.Length<2) return 2;
    Guid iid=new Guid("bcc18b79-ba16-442f-80c4-8a59c30c463b");
    IShellItemImageFactory f; SHCreateItemFromParsingName(args[0],IntPtr.Zero,ref iid,out f);
    IntPtr hb; f.GetImage(new SIZE(1280,720),0x0,out hb);
    using(var img=Image.FromHbitmap(hb)) img.Save(args[1],ImageFormat.Png);
    DeleteObject(hb); return 0;
  }
}
