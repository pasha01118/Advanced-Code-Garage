import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { BannerWrapper } from "@/components/BannerWrapper";
import { Analytics } from "@vercel/analytics/next";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Advanced Code Garage | Agent Hub",
  description: "Autonomous Multi-Agent Developer Ecosystem",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-slate-950 text-slate-100 antialiased`}>
        <BannerWrapper>{children}</BannerWrapper>
        <Analytics />
      </body>
    </html>
  );
}
