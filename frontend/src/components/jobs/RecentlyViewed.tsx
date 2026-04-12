"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Clock } from "lucide-react";
import api from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { getViewedJobIds } from "@/lib/viewHistory";
import { formatSalary } from "@/lib/utils";
import type { JobListItem } from "@/types/api";

interface RecentlyViewedProps {
  maxItems?: number;
}

export default function RecentlyViewed({ maxItems = 5 }: RecentlyViewedProps) {
  const { isAuthenticated, user } = useAuthStore();
  const isWorker = isAuthenticated && user?.role === "worker";
  const [localIds, setLocalIds] = useState<string[]>([]);

  // Read localStorage IDs on mount (client-only)
  useEffect(() => {
    setLocalIds(getViewedJobIds());
  }, []);

  // For authenticated workers: fetch from API
  const { data: apiJobs } = useQuery({
    queryKey: ["viewed-jobs"],
    queryFn: () =>
      api.get<JobListItem[]>("/worker/viewed-jobs", {
        params: { limit: maxItems },
      }).then((r) => r.data),
    enabled: isWorker,
    staleTime: 60_000,
  });

  // For non-authenticated / non-workers: fetch individual jobs by localStorage IDs
  const idsToFetch = !isWorker ? localIds.slice(0, maxItems) : [];
  const { data: localJobs } = useQuery({
    queryKey: ["viewed-jobs-local", idsToFetch],
    queryFn: async () => {
      if (idsToFetch.length === 0) return [];
      // Fetch jobs individually (they might not all be active)
      const results = await Promise.allSettled(
        idsToFetch.map((id) =>
          api.get<JobListItem>(`/jobs/${id}`).then((r) => r.data)
        )
      );
      return results
        .filter((r): r is PromiseFulfilledResult<JobListItem> => r.status === "fulfilled")
        .map((r) => r.value);
    },
    enabled: idsToFetch.length > 0,
    staleTime: 2 * 60 * 1000,
  });

  const jobs = isWorker ? apiJobs : localJobs;

  if (!jobs || jobs.length === 0) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <Clock className="w-4 h-4 text-gray-400" />
        <h3 className="font-semibold text-gray-900 text-sm">Ostatnio oglądane</h3>
      </div>
      <ul className="space-y-3">
        {jobs.map((job) => (
          <li key={job.id}>
            <Link
              href={`/oferty/${job.id}`}
              className="block hover:bg-gray-50 -mx-2 px-2 py-1.5 rounded-lg transition-colors"
            >
              <p className="text-sm font-medium text-gray-900 line-clamp-1">
                {job.title}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">
                {job.employer?.company_name} &middot; {formatSalary(job.salary_min, job.salary_max, job.salary_type)}
              </p>
            </Link>
          </li>
        ))}
      </ul>
      {isWorker && (
        <Link
          href="/panel/pracownik/historia"
          className="block text-center text-xs text-red-600 hover:underline font-medium mt-3 pt-3 border-t border-gray-100"
        >
          Zobacz wszystkie
        </Link>
      )}
    </div>
  );
}
