import "~/styles/globals.css";

import { type Metadata } from "next";
import { Geist } from "next/font/google";

import { TRPCReactProvider } from "~/trpc/react";

export const metadata: Metadata = {
  title: "Epiroc Last-Mile Delivery | ETA Predictor",
  description: "AI-powered last-mile delivery optimization and ETA prediction",
  icons: [{ rel: "icon", url: "/favicon.ico" }],
};

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist-sans",
});

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${geist.variable}`}>
      <body className="min-h-screen bg-gray-50">
        <TRPCReactProvider>
          <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center">
                  <a href="/" className="flex items-center gap-2">
                    <span className="text-2xl">🚚</span>
                    <span className="font-bold text-xl text-gray-900">Epiroc</span>
                    <span className="text-gray-500 text-sm hidden sm:inline">Last-Mile</span>
                  </a>
                </div>
                <div className="flex items-center gap-6">
                  <a href="/" className="text-gray-600 hover:text-gray-900 font-medium">
                    Dashboard
                  </a>
                  <a href="/predict" className="text-gray-600 hover:text-gray-900 font-medium">
                    Predict
                  </a>
                  <a href="/analytics" className="text-gray-600 hover:text-gray-900 font-medium">
                    Analytics
                  </a>
                </div>
              </div>
            </div>
          </nav>
          <main>{children}</main>
        </TRPCReactProvider>
      </body>
    </html>
  );
}
