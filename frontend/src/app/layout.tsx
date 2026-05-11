import type { Metadata } from "next";
import { Roboto, Roboto_Slab } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import Providers from "./providers";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";

const roboto = Roboto({
  subsets: ["latin", "latin-ext"],
  weight: ["300", "400", "500", "700"],
  variable: "--font-body",
});
const robotoSlab = Roboto_Slab({
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-display",
});

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://praca-w-szwajcarii.ch";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Praca w Szwajcarii - Portal pracy dla Polaków",
    template: "%s | Praca w Szwajcarii",
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
    siteName: "Praca w Szwajcarii",
    title: "Praca w Szwajcarii - Portal pracy dla Polaków",
    description: "Znajdź wymarzoną pracę w Szwajcarii. Portal pracy dla polskojęzycznych pracowników i pracodawców.",
  },
  twitter: {
    card: "summary_large_image",
    title: "Praca w Szwajcarii - Portal pracy dla Polaków",
    description: "Znajdź wymarzoną pracę w Szwajcarii. Portal pracy dla polskojęzycznych pracowników i pracodawców.",
  },
  robots: process.env.NEXT_PUBLIC_NOINDEX === "false"
    ? { index: true, follow: true }
    : {
        index: false,
        follow: false,
        nocache: true,
        googleBot: { index: false, follow: false },
      },
};

const jsonLd = [
  {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "Praca w Szwajcarii",
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
  },
  {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: [
      {
        "@type": "Question",
        name: "Czy korzystanie z portalu jest bezpłatne?",
        acceptedAnswer: { "@type": "Answer", text: "Tak, portal jest w pełni bezpłatny zarówno dla pracowników, jak i dla pracodawców. Publikowanie ogłoszeń, przeglądanie ofert i aplikowanie nie wiąże się z żadnymi opłatami." },
      },
      {
        "@type": "Question",
        name: "Jakie dokumenty są potrzebne do pracy w Szwajcarii?",
        acceptedAnswer: { "@type": "Answer", text: "Do legalnej pracy w Szwajcarii potrzebujesz pozwolenia na pracę (permit). Obywatele UE/EFTA mogą ubiegać się o pozwolenie typu L (krótkoterminowe) lub B (długoterminowe). Pracodawca zazwyczaj pomaga w uzyskaniu odpowiedniego pozwolenia." },
      },
      {
        "@type": "Question",
        name: "Jak mogę sprawdzić swoje CV?",
        acceptedAnswer: { "@type": "Answer", text: "Skorzystaj z naszego bezpłatnego narzędzia do analizy CV. Wgraj plik PDF, a nasze narzędzie oceni go i wskaże co poprawić, co dodać i jak dostosować CV do rynku szwajcarskiego." },
      },
      {
        "@type": "Question",
        name: "Czy muszę znać język niemiecki lub francuski?",
        acceptedAnswer: { "@type": "Answer", text: "Wymagania językowe zależą od kantonu i stanowiska. W niemieckojęzycznej części Szwajcarii przydatny jest niemiecki, w zachodniej - francuski. Na budowach i w produkcji wymagania językowe są zazwyczaj niższe." },
      },
      {
        "@type": "Question",
        name: "Ile zarabia się w Szwajcarii?",
        acceptedAnswer: { "@type": "Answer", text: "Wynagrodzenia w Szwajcarii są jednymi z najwyższych w Europie. Średnie miesięczne zarobki to ok. 5'000-7'000 CHF brutto w zależności od branży i doświadczenia." },
      },
    ],
  },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pl">
      <head>
        {jsonLd.map((ld, i) => (
          <script
            key={i}
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }}
          />
        ))}
      </head>
      <body className={`${roboto.variable} ${robotoSlab.variable} font-sans min-h-screen flex flex-col`}>
        <a href="#main-content" className="skip-to-content">
          Przejdź do treści
        </a>
        <Providers>
          <Header />
          <main id="main-content" className="flex-1">{children}</main>
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
