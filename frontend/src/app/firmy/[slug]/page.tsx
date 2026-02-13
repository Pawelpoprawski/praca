"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Building2, Globe, MapPin, Users, BadgeCheck, Briefcase,
  ChevronLeft, ChevronRight,
} from "lucide-react";
import { useState } from "react";
import api from "@/services/api";
import { formatSalary, formatDate, CONTRACT_TYPES } from "@/lib/utils";
import type { JobListItem, PaginatedResponse } from "@/types/api";

interface CompanyPublic {
  id: string;
  company_name: string;
  company_slug: string;
  description: string | null;
  logo_url: string | null;
  website: string | null;
  industry: string | null;
  canton: string | null;
  city: string | null;
  company_size: string | null;
  is_verified: boolean;
}

export default function CompanyPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [page, setPage] = useState(1);

  const { data: company, isLoading: loadingCompany } = useQuery({
    queryKey: ["company", slug],
    queryFn: () => api.get<CompanyPublic>(`/companies/${slug}`).then((r) => r.data),
  });

  const { data: jobsData, isLoading: loadingJobs } = useQuery({
    queryKey: ["company-jobs", slug, page],
    queryFn: () =>
      api.get<PaginatedResponse<JobListItem>>(`/companies/${slug}/jobs`, {
        params: { page, per_page: 10 },
      }).then((r) => r.data),
    enabled: !!company,
  });

  if (loadingCompany) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse h-64 bg-gray-100 rounded-lg" />
      </div>
    );
  }

  if (!company) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <p className="text-gray-500 text-lg">Firma nie została znaleziona</p>
        <Link href="/oferty" className="text-red-600 hover:underline mt-2 block">
          Wróć do ofert
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Company header */}
      <div className="bg-white border rounded-lg p-6 mb-6">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0">
            {company.logo_url ? (
              <img src={company.logo_url} alt={company.company_name} className="w-full h-full object-cover" />
            ) : (
              <Building2 className="w-8 h-8 text-gray-400" />
            )}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-gray-900">{company.company_name}</h1>
              {company.is_verified && (
                <BadgeCheck className="w-5 h-5 text-blue-500" />
              )}
            </div>
            <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-500">
              {company.industry && <span>{company.industry}</span>}
              {(company.canton || company.city) && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {[company.city, company.canton].filter(Boolean).join(", ")}
                </span>
              )}
              {company.company_size && (
                <span className="flex items-center gap-1">
                  <Users className="w-3 h-3" />
                  {company.company_size} pracowników
                </span>
              )}
              {company.website && (
                <a href={company.website} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-1 text-red-600 hover:underline">
                  <Globe className="w-3 h-3" />
                  Strona www
                </a>
              )}
            </div>
          </div>
        </div>

        {company.description && (
          <div className="mt-4 pt-4 border-t">
            <p className="text-sm text-gray-700 whitespace-pre-line">{company.description}</p>
          </div>
        )}
      </div>

      {/* Company jobs */}
      <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Briefcase className="w-5 h-5" />
        Oferty pracy ({jobsData?.total || 0})
      </h2>

      {loadingJobs ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="animate-pulse h-20 bg-gray-100 rounded-lg" />
          ))}
        </div>
      ) : jobsData?.data && jobsData.data.length > 0 ? (
        <>
          <div className="space-y-3">
            {jobsData.data.map((job) => (
              <Link
                key={job.id}
                href={`/oferty/${job.id}`}
                className="block bg-white border rounded-lg p-4 hover:border-red-200 hover:shadow-sm transition-all"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">{job.title}</h3>
                    <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
                      <span>{CONTRACT_TYPES[job.contract_type] || job.contract_type}</span>
                      <span>{formatSalary(job.salary_min, job.salary_max, job.salary_type)}</span>
                      {job.is_remote === "yes" && (
                        <span className="text-green-600 text-xs font-medium">Zdalna</span>
                      )}
                    </div>
                  </div>
                  {job.published_at && (
                    <span className="text-xs text-gray-400 flex-shrink-0">
                      {formatDate(job.published_at)}
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>

          {jobsData.pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-500">Strona {jobsData.page} z {jobsData.pages}</p>
              <div className="flex gap-1">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-30">
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button onClick={() => setPage((p) => Math.min(jobsData.pages, p + 1))} disabled={page >= jobsData.pages}
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-30">
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="bg-white border rounded-lg px-5 py-8 text-center">
          <p className="text-gray-500">Firma nie ma aktualnie aktywnych ofert</p>
        </div>
      )}
    </div>
  );
}
