"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import Image from "next/image";
import {
  Building2, Globe, BadgeCheck, Briefcase,
  ChevronLeft, ChevronRight,
} from "lucide-react";
import { useState } from "react";
import api from "@/services/api";
import { formatSalary, formatDate, CONTRACT_TYPES } from "@/lib/utils";
import ReviewSection from "@/components/common/ReviewSection";
import type { JobListItem, PaginatedResponse } from "@/types/api";

interface CompanyPublic {
  id: string;
  company_name: string;
  company_slug: string;
  description: string | null;
  logo_url: string | null;
  website: string | null;
  is_verified: boolean;
}

interface Props {
  initialCompany: CompanyPublic;
}

export default function CompanyClient({ initialCompany }: Props) {
  const [page, setPage] = useState(1);

  const { data: company } = useQuery({
    queryKey: ["company", initialCompany.company_slug],
    queryFn: () => api.get<CompanyPublic>(`/companies/${initialCompany.company_slug}`).then((r) => r.data),
    initialData: initialCompany,
  });

  const { data: jobsData, isLoading: loadingJobs } = useQuery({
    queryKey: ["company-jobs", company.company_slug, page],
    queryFn: () =>
      api.get<PaginatedResponse<JobListItem>>(`/companies/${company.company_slug}/jobs`, {
        params: { page, per_page: 10 },
      }).then((r) => r.data),
  });

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Company header */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 bg-gray-100 rounded-xl flex items-center justify-center overflow-hidden flex-shrink-0">
            {company.logo_url ? (
              <Image src={company.logo_url} alt={company.company_name} width={64} height={64} className="w-full h-full object-cover" />
            ) : (
              <Building2 className="w-8 h-8 text-gray-400" />
            )}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold font-display text-[#0D2240]">{company.company_name}</h1>
              {company.is_verified && (
                <BadgeCheck className="w-5 h-5 text-blue-500" />
              )}
            </div>
            {company.website && (
              <div className="mt-2">
                <a href={company.website} target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-[#E1002A] hover:underline">
                  <Globe className="w-3 h-3" />
                  Strona www
                </a>
              </div>
            )}
          </div>
        </div>

        {company.description && (
          <div className="mt-4 pt-4 border-t">
            <p className="text-sm text-gray-700 whitespace-pre-line">{company.description}</p>
          </div>
        )}
      </div>

      {/* Company jobs */}
      <h2 className="text-lg font-semibold font-display text-[#0D2240] mb-4 flex items-center gap-2">
        <Briefcase className="w-5 h-5" />
        Oferty pracy ({jobsData?.total || 0})
      </h2>

      {loadingJobs ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="bg-white border border-gray-200 rounded-xl p-4 animate-pulse">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-2/3 mb-2" />
                  <div className="flex gap-3">
                    <div className="h-3 bg-gray-100 rounded w-24" />
                    <div className="h-3 bg-gray-100 rounded w-20" />
                  </div>
                </div>
                <div className="h-3 bg-gray-100 rounded w-16 ml-4" />
              </div>
            </div>
          ))}
        </div>
      ) : jobsData?.data && jobsData.data.length > 0 ? (
        <>
          <div className="space-y-3">
            {jobsData.data.map((job) => (
              <Link
                key={job.id}
                href={`/oferty/${job.id}`}
                className="block bg-white border border-gray-200 rounded-xl p-4 hover:border-[#FFC2CD] hover:shadow-md transition-all"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">{job.title}</h3>
                    <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
                      <span>{CONTRACT_TYPES[job.contract_type] || job.contract_type}</span>
                      <span>{formatSalary(job.salary_min, job.salary_max, job.salary_type)}</span>
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

      {/* Reviews section */}
      <ReviewSection companySlug={company.company_slug} />
    </div>
  );
}
