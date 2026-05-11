import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  // Tymczasowo: blokujemy CALY index dla wszystkich botow (pre-launch).
  // Po uruchomieniu produkcji zmienic na allow + disallow tylko /panel/ i /api/.
  const noIndex = (process.env.NEXT_PUBLIC_NOINDEX || "true").toLowerCase() === "true";

  if (noIndex) {
    return {
      rules: [{ userAgent: "*", disallow: "/" }],
    };
  }

  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/panel/", "/api/"],
      },
    ],
    sitemap: `${process.env.NEXT_PUBLIC_SITE_URL || "https://praca-w-szwajcarii.ch"}/sitemap.xml`,
  };
}
