import type { Metadata } from "next";
import { Playfair_Display, Inter, Source_Serif_4 } from "next/font/google";
import "./globals.css";

const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
  weight: ["400", "700"],
  style: ["normal", "italic"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const sourceSerif = Source_Serif_4({
  variable: "--font-source-serif",
  subsets: ["latin"],
  weight: ["400", "600"],
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "Faisneis | Irish Parliamentary Intelligence",
  description:
    "Search 315k Dail and Seanad speeches, backed by CSO stats. Every answer links back to the source.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${playfair.variable} ${inter.variable} ${sourceSerif.variable}`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
