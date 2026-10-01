import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dr.RopoSky — AI-powered full-project software auditor",
  description:
    "Dr.RopoSky analyzes your codebase for security, reliability, quality, performance, architecture, and completeness issues — then explains what to fix and tracks your progress after every re-scan.",
  openGraph: {
    title: "Dr.RopoSky — AI-powered full-project software auditor",
    description:
      "Automated software engineering and cybersecurity audit platform providing deterministic scoring, vulnerability detection, and AI-guided remediation.",
    siteName: "Dr.RopoSky",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Dr.RopoSky — AI-powered full-project software auditor",
    description:
      "Automated software engineering and cybersecurity audit platform providing deterministic scoring, vulnerability detection, and AI-guided remediation.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-text-primary antialiased flex flex-col">
        {children}
      </body>
    </html>
  );
}
