import type { Metadata } from "next";
import { notFound } from "next/navigation";
import CompanyClient from "./CompanyClient";

const API_URL = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8001";
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://polacyszwajcaria.ch";

async function getCompany(slug: string) {
  try {
    const res = await fetch(`${API_URL}/api/v1/companies/${slug}`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const { slug } = params;
  const company = await getCompany(slug);

  if (!company) {
    return { title: "Firma nie znaleziona" };
  }

  const description = company.description
    ? company.description.slice(0, 160)
    : `${company.company_name} - profil firmy na PolacySzwajcaria. Zobacz oferty pracy.`;

  return {
    title: company.company_name,
    description,
    openGraph: {
      title: `${company.company_name} - PolacySzwajcaria`,
      description,
      url: `${SITE_URL}/firmy/${slug}`,
      type: "profile",
      ...(company.logo_url && { images: [{ url: `${SITE_URL}${company.logo_url}` }] }),
    },
  };
}

export default async function CompanyPage({
  params,
}: {
  params: { slug: string };
}) {
  const { slug } = params;
  const company = await getCompany(slug);

  if (!company) {
    notFound();
  }

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: company.company_name,
    url: `${SITE_URL}/firmy/${slug}`,
    ...(company.logo_url && { logo: `${SITE_URL}${company.logo_url}` }),
    ...(company.website && { sameAs: [company.website] }),
    ...(company.description && { description: company.description }),
    address: {
      "@type": "PostalAddress",
      ...(company.city && { addressLocality: company.city }),
      ...(company.canton && { addressRegion: company.canton }),
      addressCountry: "CH",
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <CompanyClient initialCompany={company} />
    </>
  );
}
