import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Text Layer Separator",
  description: "Upload an image, separate text, restore background",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="bg-gray-950 text-gray-100 antialiased">{children}</body>
    </html>
  );
}
