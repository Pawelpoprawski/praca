import type { Metadata } from "next";
import { notFound } from "next/navigation";
import JobDetailClient from "./JobDetailClient";

const API_URL = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8002";
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://praca-w-szwajcarii.ch";

const CONTRACT_TYPES: Record<string, string> = {
  full_time: "Pełny etat",
  part_time: "Część etatu",
  temporary: "Tymczasowa",
  contract: "Zlecenie",
  internship: "Praktyka",
  freelance: "Freelance",
};

async function getJob(id: string) {
  try {
    const res = await fetch(`${API_URL}/api/v1/jobs/${id}`, {
      next: { revalidate: 60 },
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
  params: { id: string };
}): Promise<Metadata> {
  const { id } = params;
  const job = await getJob(id);

  if (!job) {
    return { title: "Oferta nie znaleziona" };
  }

  const salary =
    job.salary_min && job.salary_max
      ? `${job.salary_min.toLocaleString("pl-PL")} - ${job.salary_max.toLocaleString("pl-PL")} CHF`
      : "";
  const description = `${job.title} - ${job.employer?.company_name || ""}${salary ? ` | ${salary}` : ""} | ${CONTRACT_TYPES[job.contract_type] || job.contract_type}`;

  return {
    title: job.title,
    description,
    openGraph: {
      title: `${job.title} - Praca w Szwajcarii`,
      description,
      url: `${SITE_URL}/oferty/${id}`,
      type: "article",
    },
    twitter: {
      card: "summary",
      title: job.title,
      description,
    },
  };
}

export default async function JobDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const { id } = params;
  const job = await getJob(id);

  if (!job) {
    notFound();
  }

  // JSON-LD structured data for JobPosting
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "JobPosting",
    title: job.title,
    description: job.description,
    datePosted: job.published_at || job.created_at,
    validThrough: job.expires_at,
    employmentType: job.contract_type === "full_time" ? "FULL_TIME" : job.contract_type === "part_time" ? "PART_TIME" : "OTHER",
    jobLocation: {
      "@type": "Place",
      address: {
        "@type": "PostalAddress",
        addressLocality: job.city || undefined,
        addressRegion: job.canton,
        addressCountry: "CH",
      },
    },
    ...(job.salary_min && {
      baseSalary: {
        "@type": "MonetaryAmount",
        currency: "CHF",
        value: {
          "@type": "QuantitativeValue",
          minValue: job.salary_min,
          maxValue: job.salary_max || job.salary_min,
          unitText: job.salary_type === "hourly" ? "HOUR" : job.salary_type === "yearly" ? "YEAR" : "MONTH",
        },
      },
    }),
    ...(job.employer && {
      hiringOrganization: {
        "@type": "Organization",
        name: job.employer.company_name,
        sameAs: `${SITE_URL}/firmy/${job.employer.company_slug}`,
        ...(job.employer.logo_url && { logo: `${SITE_URL}${job.employer.logo_url}` }),
      },
    }),
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <JobDetailClient initialJob={job} />
    </>
  );
}
