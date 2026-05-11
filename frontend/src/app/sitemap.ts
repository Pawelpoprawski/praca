import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://praca-w-szwajcarii.ch";
const API_URL = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8002";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticPages: MetadataRoute.Sitemap = [
    { url: SITE_URL, lastModified: new Date(), changeFrequency: "daily", priority: 1.0 },
    { url: `${SITE_URL}/oferty`, lastModified: new Date(), changeFrequency: "daily", priority: 0.9 },
    { url: `${SITE_URL}/login`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.3 },
    { url: `${SITE_URL}/register`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.3 },
  ];

  // Fetch active job offers for dynamic pages (paginate, max 100 per page)
  let jobPages: MetadataRoute.Sitemap = [];
  try {
    let page = 1;
    let hasMore = true;
    while (hasMore) {
      const res = await fetch(`${API_URL}/api/v1/jobs?per_page=100&page=${page}`, {
        next: { revalidate: 3600 },
      });
      if (!res.ok) break;
      const data = await res.json();
      const jobs = data.data || [];
      jobPages.push(
        ...jobs.map((job: { id: string; published_at?: string }) => ({
          url: `${SITE_URL}/oferty/${job.id}`,
          lastModified: job.published_at ? new Date(job.published_at) : new Date(),
          changeFrequency: "weekly" as const,
          priority: 0.7,
        }))
      );
      hasMore = page < (data.pages || 1);
      page++;
    }
  } catch {
    // Silently fail - sitemap will just have static pages
  }

  return [...staticPages, ...jobPages];
}
