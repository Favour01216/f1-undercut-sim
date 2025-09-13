import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/components/ui/toaster";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ErrorLoggingProvider } from "@/components/ErrorLoggingProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "F1 Undercut Strategy Dashboard | Monte Carlo Simulation",
  description:
    "Advanced F1 undercut probability analysis using real Formula 1 data, tire degradation models, and Monte Carlo simulation. Optimize racing strategy with data-driven insights.",
  keywords: [
    "Formula 1",
    "F1 strategy",
    "undercut analysis",
    "Monte Carlo simulation",
    "tire degradation",
    "racing analytics",
    "pit stop strategy",
    "motorsport data",
  ],
  authors: [{ name: "F1 Strategy Analytics Team" }],
  viewport: "width=device-width, initial-scale=1",
  robots: "index, follow",
  openGraph: {
    title: "F1 Undercut Strategy Dashboard",
    description:
      "Analyze F1 undercut opportunities with real-time Monte Carlo simulations",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "F1 Undercut Strategy Dashboard",
    description:
      "Advanced F1 undercut probability analysis with Monte Carlo simulation",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <link rel="icon" type="image/png" href="/favicon.png" />
      </head>
      <body className={inter.className} suppressHydrationWarning>
        <ErrorLoggingProvider>
          <ErrorBoundary>
            <ToastProvider>
              <div id="root" className="min-h-screen">
                {children}
              </div>
            </ToastProvider>
          </ErrorBoundary>
        </ErrorLoggingProvider>
      </body>
    </html>
  );
}
