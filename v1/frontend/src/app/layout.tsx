import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoPPT — 이미지를 editable PPTX로",
  description: "이미지 1장을 업로드하면 텍스트를 검출·제거하고 편집 가능한 PPTX를 생성합니다.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
