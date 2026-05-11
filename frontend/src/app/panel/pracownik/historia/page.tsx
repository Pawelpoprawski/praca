"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Clock, MapPin, Briefcase } from "lucide-react";
import api from "@/services/api";
import { formatSalary, formatDate, CONTRACT_TYPES } from "@/lib/utils";
import type { JobListItem, Canton } from "@/types/api";

function HistorySkeleton() {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 animate-pulse">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="h-5 bg-gray-200 rounded w-2/3 mb-2" />
          <div className="h-4 bg-gray-100 rounded w-1/3 mb-3" />
          <div className="flex gap-2">
            <div className="h-5 bg-gray-100 rounded w-20" />
            <div className="h-5 bg-gray-100 rounded w-24" />
          </div>
        </div>
        <div className="h-5 bg-gray-200 rounded w-28" />
      </div>
    </div>
  );
}

export default function ViewedJobsHistoryPage() {
  const { data: jobs, isLoading } = useQuery({
    queryKey: ["viewed-jobs"],
    queryFn: () =>
      api.get<JobListItem[]>("/worker/viewed-jobs", {
        params: { limit: 50 },
      }).then((r) => r.data),
  });

  const { data: cantons } = useQuery({
    queryKey: ["cantons"],
    queryFn: () => api.get<Canton[]>("/jobs/cantons").then((r) => r.data),
    staleTime: 24 * 60 * 60 * 1000,
  });

  const cantonMap = cantons
    ? Object.fromEntries(cantons.map((c) => [c.value, c.label]))
    : {};

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Clock className="w-6 h-6 text-gray-400" />
        <h1 className="text-2xl font-bold font-display text-[#0D2240]">Ostatnio oglądane oferty</h1>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <HistorySkeleton key={i} />
          ))}
        </div>
      ) : jobs && jobs.length > 0 ? (
        <div className="space-y-3">
          {jobs.map((job) => (
            <Link
              key={job.id}
              href={`/oferty/${job.id}`}
              className="block bg-white border border-gray-200 rounded-xl p-5 hover:shadow-lg hover:border-[#E1002A]/40 hover:-translate-y-0.5 transition-all group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  {job.is_featured && (
                    <span className="inline-block bg-yellow-100 text-yellow-800 text-xs font-semibold px-2 py-0.5 rounded mb-2">
                      Wyróżnione
                    </span>
                  )}
                  <h2 className="text-lg font-bold font-display text-[#0D2240] group-hover:text-[#E1002A] transition-colors line-clamp-1">
                    {job.title}
                  </h2>
                  <p className="text-sm text-gray-500 mt-1 truncate">
                    {job.employer?.company_name}
                  </p>
                  <div className="flex flex-wrap gap-2 mt-2 text-xs text-gray-500">
                    <span className="flex items-center gap-1 bg-gray-50 px-2 py-1 rounded">
                      <MapPin className="w-3 h-3" />
                      {cantonMap[job.canton] || job.canton}
                      {job.city ? `, ${job.city}` : ""}
                    </span>
                    <span className="bg-blue-50 text-blue-700 px-2 py-1 rounded font-medium">
                      {CONTRACT_TYPES[job.contract_type] || job.contract_type}
                    </span>
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="font-bold text-gray-900">
                    {formatSalary(job.salary_min, job.salary_max, job.salary_type)}
                  </p>
                  {job.published_at && (
                    <p className="text-xs text-gray-400 mt-1">
                      {formatDate(job.published_at)}
                    </p>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
          <Clock className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-lg font-semibold text-gray-700 mb-2">Brak historii</p>
          <p className="text-sm text-gray-500 mb-4">
            Nie przeglądałeś jeszcze żadnych ofert.
          </p>
          <Link
            href="/oferty"
            className="text-[#E1002A] hover:underline font-medium text-sm"
          >
            Przeglądaj oferty
          </Link>
        </div>
      )}
    </div>
  );
}
