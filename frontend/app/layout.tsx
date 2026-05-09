import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Logistics Analytics",
  description: "AI-powered logistics analytics dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">
        <nav className="bg-white border-b border-gray-200 px-6 py-3 flex gap-6 items-center">
          <span className="font-semibold text-lg tracking-tight">📦 LogisticsAI</span>
          <a href="/" className="text-sm text-gray-600 hover:text-gray-900">Dashboard</a>
          <a href="/chat" className="text-sm text-gray-600 hover:text-gray-900">Ask AI</a>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
