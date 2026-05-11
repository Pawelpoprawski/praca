"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { MapPin } from "lucide-react";
import api from "@/services/api";
import { formatSalary, CONTRACT_TYPES } from "@/lib/utils";
import type { JobListItem, Canton } from "@/types/api";

interface SimilarJobsProps {
  jobId: string;
}

function SimilarJobSkeleton() {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 animate-pulse">
      <div className="h-5 bg-gray-200 rounded w-3/4 mb-2" />
      <div className="h-4 bg-gray-100 rounded w-1/2 mb-3" />
      <div className="flex gap-2">
        <div className="h-5 bg-gray-100 rounded w-20" />
        <div className="h-5 bg-gray-100 rounded w-24" />
      </div>
      <div className="h-5 bg-gray-200 rounded w-28 mt-3" />
    </div>
  );
}

export default function SimilarJobs({ jobId }: SimilarJobsProps) {
  const { data: jobs, isLoading } = useQuery({
    queryKey: ["similar-jobs", jobId],
    queryFn: () =>
      api.get<JobListItem[]>(`/jobs/${jobId}/similar`).then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });

  const { data: cantons } = useQuery({
    queryKey: ["cantons"],
    queryFn: () => api.get<Canton[]>("/jobs/cantons").then((r) => r.data),
    staleTime: 24 * 60 * 60 * 1000,
  });

  const cantonMap = cantons
    ? Object.fromEntries(cantons.map((c) => [c.value, c.label]))
    : {};

  if (isLoading) {
    return (
      <section className="mt-10">
        <h2 className="text-xl font-bold font-display text-[#0D2240] mb-4">Podobne oferty</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <SimilarJobSkeleton key={i} />
          ))}
        </div>
      </section>
    );
  }

  if (!jobs || jobs.length === 0) {
    return null;
  }

  return (
    <section className="mt-10">
      <h2 className="text-xl font-bold font-display text-[#0D2240] mb-4">Podobne oferty</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {jobs.map((job) => (
          <Link
            key={job.id}
            href={`/oferty/${job.id}`}
            className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-lg hover:border-[#E1002A]/40 hover:-translate-y-0.5 transition-all group"
          >
            {job.is_featured && (
              <span className="inline-block bg-yellow-100 text-yellow-800 text-xs font-semibold px-2 py-0.5 rounded mb-2">
                Wyróżnione
              </span>
            )}
            <h3 className="font-semibold text-gray-900 group-hover:text-[#E1002A] transition-colors line-clamp-2 text-sm">
              {job.title}
            </h3>
            {job.employer && (
              <p className="text-xs text-gray-500 mt-1 truncate">
                {job.employer.company_name}
              </p>
            )}
            <div className="flex flex-wrap gap-1.5 mt-2 text-xs text-gray-500">
              <span className="flex items-center gap-1 bg-gray-50 px-2 py-0.5 rounded">
                <MapPin className="w-3 h-3" />
                {cantonMap[job.canton] || job.canton}
              </span>
              <span className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-medium">
                {CONTRACT_TYPES[job.contract_type] || job.contract_type}
              </span>
            </div>
            <p className="text-sm font-bold text-gray-900 mt-3">
              {formatSalary(job.salary_min, job.salary_max, job.salary_type)}
            </p>
          </Link>
        ))}
      </div>
    </section>
  );
}
