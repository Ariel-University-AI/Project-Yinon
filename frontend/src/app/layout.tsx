import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/sidebar";

const geist = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });

export const metadata: Metadata = {
  title: 'יועץ נדל"ן חכם',
  description: "כלי חינמי לניתוח השקעות נדל\"ן בישראל",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he" dir="rtl" className={`${geist.variable} h-full antialiased`}>
      <body className="min-h-full flex bg-[#F5F5F5]">
        <Sidebar />
        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </body>
    </html>
  );
}
