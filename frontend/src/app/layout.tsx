import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/app/providers/ThemeProvider";

export const metadata: Metadata = {
  title: "TriPi — AI Travel Planner",
  description:
    "Plan your next adventure with intelligent AI agents that gather real-time weather, local insights, and budget optimization to craft personalized itineraries.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
