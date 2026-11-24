import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RIPPLE | AI-Powered Travel Disruption Recovery",
  description:
    "Cross-provider travel disruption recovery orchestrated with LangGraph, MCP, Trip Dependency Graphs, and Google OR-Tools.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#050A14] text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
