import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { DataProvider } from "@/contexts/DataContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { SpeakerProvider } from "@/contexts/SpeakerContext";
import { ErrorBoundary } from "@/components/ErrorBoundary";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Drive-Thru",
  description: "AI-powered drive-thru ordering system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
            <ErrorBoundary>
              <DataProvider>
                <ThemeProvider>
                  <SpeakerProvider>
                    {children}
                  </SpeakerProvider>
                </ThemeProvider>
              </DataProvider>
            </ErrorBoundary>
      </body>
    </html>
  );
}
