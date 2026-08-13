import argparse
import ctypes
import subprocess
import time
from pathlib import Path

from PIL import ImageGrab

user32 = ctypes.windll.user32

SW_RESTORE = 9


def enum_windows_for_pid(pid):
    hwnds = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def callback(hwnd, _):
        window_pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
        if window_pid.value == pid and user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, length + 1)
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            if width > 200 and height > 160:
                hwnds.append((hwnd, title.value, width, height))
        return True

    user32.EnumWindows(callback, 0)
    return hwnds


def capture_window(hwnd, out_path, width=1180, height=760):
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.MoveWindow(hwnd, 80, 60, width, height, True)
    user32.SetForegroundWindow(hwnd)
    time.sleep(1.2)

    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    bbox = (rect.left, rect.top, rect.right, rect.bottom)
    image = ImageGrab.grab(bbox=bbox)
    image.save(out_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--wait", type=float, default=8.0)
    parser.add_argument("--width", type=int, default=1180)
    parser.add_argument("--height", type=int, default=760)
    args = parser.parse_args()

    exe = Path(args.exe)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    proc = subprocess.Popen([str(exe)], cwd=str(exe.parent))
    hwnd = None
    seen = []
    deadline = time.time() + args.wait
    while time.time() < deadline:
        seen = enum_windows_for_pid(proc.pid)
        if seen:
            hwnd = max(seen, key=lambda item: item[2] * item[3])[0]
            break
        time.sleep(0.5)

    if not hwnd:
        proc.terminate()
        raise SystemExit(f"No visible window found for pid {proc.pid}; seen={seen}")

    capture_window(hwnd, out, args.width, args.height)
    print(f"saved={out}")
    print(f"pid={proc.pid}")
    for _, title, width, height in seen:
        print(f"window={title!r} {width}x{height}")

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


if __name__ == "__main__":
    main()
