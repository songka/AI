import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "弈五子｜在线五子棋",
  description: "一款雅致、轻松的在线五子棋游戏，支持人机对战与双人对弈。",
  icons: { icon: "/favicon.svg", shortcut: "/favicon.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
