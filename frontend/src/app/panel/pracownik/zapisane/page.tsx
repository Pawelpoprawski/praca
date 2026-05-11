"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import Link from "next/link";
import { Heart, Briefcase, MapPin, ChevronLeft, ChevronRight, Trash2 } from "lucide-react";
import api from "@/services/api";
import { formatSalary, formatDate, CONTRACT_TYPES } from "@/lib/utils";
import type { SavedJob, PaginatedResponse } from "@/types/api";

export default function SavedJobsPage() {
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["saved-jobs", page],
    queryFn: () =>
      api
        .get<PaginatedResponse<SavedJob>>("/worker/saved-jobs", {
          params: { page, per_page: 15 },
        })
        .then((r) => r.data),
  });

  const removeMutation = useMutation({
    mutationFn: (jobId: string) => api.post(`/worker/saved-jobs/${jobId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["saved-job-check"] });
    },
  });

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold font-display text-[#0D2240] mb-6">Zapisane oferty</h1>
        <div className="bg-white border rounded-lg divide-y">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="px-5 py-4 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <div className="w-9 h-9 bg-gray-200 rounded-lg" />
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 rounded w-48 mb-2" />
                    <div className="h-3 bg-gray-100 rounded w-32" />
                  </div>
                </div>
                <div className="h-8 w-20 bg-gray-100 rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold font-display text-[#0D2240] mb-6">
        Zapisane oferty
        {data && data.total > 0 && (
          <span className="text-gray-400 text-lg font-normal ml-2">({data.total})</span>
        )}
      </h1>

      {data?.data && data.data.length > 0 ? (
        <>
          <div className="bg-white border rounded-lg divide-y">
            {data.data.map((saved) => {
              const job = saved.job;
              if (!job) return null;

              return (
                <div
                  key={saved.id}
                  className="px-5 py-4 flex items-center justify-between gap-4 hover:bg-gray-50 transition-colors"
                >
                  <Link
                    href={`/oferty/${saved.job_offer_id}`}
                    className="flex items-center gap-3 min-w-0 flex-1"
                  >
                    <div className="w-9 h-9 bg-[#FFF0F3] rounded-lg flex items-center justify-center flex-shrink-0">
                      <Heart className="w-4 h-4 text-red-500 fill-current" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-gray-900 hover:text-[#E1002A] truncate max-w-sm">
                        {job.title}
                      </p>
                      <div className="flex items-center gap-3 text-sm text-gray-500">
                        <span className="truncate">{job.employer?.company_name}</span>
                        {job.canton && (
                          <span className="flex items-center gap-1 flex-shrink-0">
                            <MapPin className="w-3 h-3" />
                            {job.canton}
                          </span>
                        )}
                      </div>
                    </div>
                  </Link>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    <div className="text-right hidden sm:block">
                      <p className="text-sm font-medium text-gray-900">
                        {formatSalary(job.salary_min, job.salary_max, job.salary_type)}
                      </p>
                      <p className="text-xs text-gray-400">
                        {CONTRACT_TYPES[job.contract_type] || job.contract_type}
                      </p>
                    </div>
                    <button
                      onClick={() => removeMutation.mutate(saved.job_offer_id)}
                      disabled={removeMutation.isPending}
                      title="Usuń z ulubionych"
                      aria-label="Usuń z ulubionych"
                      className="p-2 text-gray-400 hover:text-red-500 hover:bg-[#FFF0F3] rounded-lg transition-colors disabled:opacity-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {data.pages > 1 && (
            <nav className="flex items-center justify-between mt-4" aria-label="Paginacja zapisanych ofert">
              <p className="text-sm text-gray-500">
                Strona {data.page} z {data.pages} ({data.total} ofert)
              </p>
              <div className="flex gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  aria-label="Poprzednia strona"
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-30 transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                  disabled={page >= data.pages}
                  aria-label="Następna strona"
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-30 transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </nav>
          )}
        </>
      ) : (
        <div className="bg-white border rounded-lg px-5 py-12 text-center">
          <Heart className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 mb-2">
            Nie masz jeszcze zapisanych ofert
          </p>
          <Link
            href="/oferty"
            className="text-sm text-[#E1002A] hover:underline"
          >
            Przeglądaj oferty pracy
          </Link>
        </div>
      )}
    </div>
  );
}
