import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import Providers from "./providers";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";

const inter = Inter({ subsets: ["latin", "latin-ext"] });

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://polacyszwajcaria.ch";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "PolacySzwajcaria - Portal pracy dla Polaków w Szwajcarii",
    template: "%s | PolacySzwajcaria",
  },
  description:
    "Znajdź wymarzoną pracę w Szwajcarii. Portal pracy dla polskojęzycznych pracowników i pracodawców.",
  keywords: [
    "praca Szwajcaria", "praca dla Polaków", "oferty pracy Szwajcaria",
    "polacy w Szwajcarii", "Arbeit Schweiz", "praca za granicą",
    "portal pracy", "rekrutacja Szwajcaria",
  ],
  openGraph: {
    type: "website",
    locale: "pl_PL",
    url: SITE_URL,
    siteName: "PolacySzwajcaria",
    title: "PolacySzwajcaria - Portal pracy dla Polaków w Szwajcarii",
    description: "Znajdź wymarzoną pracę w Szwajcarii. Portal pracy dla polskojęzycznych pracowników i pracodawców.",
  },
  twitter: {
    card: "summary_large_image",
    title: "PolacySzwajcaria - Portal pracy dla Polaków w Szwajcarii",
    description: "Znajdź wymarzoną pracę w Szwajcarii. Portal pracy dla polskojęzycznych pracowników i pracodawców.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "PolacySzwajcaria",
  url: SITE_URL,
  description: "Portal pracy dla Polaków w Szwajcarii",
  potentialAction: {
    "@type": "SearchAction",
    target: {
      "@type": "EntryPoint",
      urlTemplate: `${SITE_URL}/oferty?q={search_term_string}`,
    },
    "query-input": "required name=search_term_string",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pl">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className={`${inter.className} min-h-screen flex flex-col`}>
        <Providers>
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </Providers>
        {process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY && (
          <Script
            src={`https://www.google.com/recaptcha/api.js?render=${process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY}`}
            strategy="lazyOnload"
          />
        )}
      </body>
    </html>
  );
}
