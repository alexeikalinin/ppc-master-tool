import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "PPC Master Tool",
  description: "Автоматический анализ и создание PPC-кампаний для Яндекс, Google и VK",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className="dark">
      <body className={`${inter.variable} font-sans antialiased bg-[#111827] text-gray-50 min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
