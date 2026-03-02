import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LLM Hidden State Extraction",
  description: "LLMの内部hidden stateベクトルを抽出するプラットフォーム",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className="bg-gray-50 text-gray-900 min-h-screen">{children}</body>
    </html>
  );
}
