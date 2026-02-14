"use client";

import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Search, MapPin, SlidersHorizontal, X, Briefcase } from "lucide-react";
import { useState, useEffect, Suspense } from "react";
import api from "@/services/api";
import { formatSalary, formatDate, CONTRACT_TYPES } from "@/lib/utils";
import type { JobListItem, PaginatedResponse, Canton } from "@/types/api";

function JobCardSkeleton() {
  return (
    <div className="bg-white border rounded-lg p-5 animate-pulse">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="h-5 bg-gray-200 rounded w-2/3 mb-3" />
          <div className="h-4 bg-gray-100 rounded w-1/3 mb-3" />
          <div className="flex gap-2">
            <div className="h-5 bg-gray-100 rounded w-20" />
            <div className="h-5 bg-gray-100 rounded w-24" />
          </div>
        </div>
        <div className="text-right">
          <div className="h-5 bg-gray-200 rounded w-28 mb-2" />
          <div className="h-3 bg-gray-100 rounded w-20 ml-auto" />
        </div>
      </div>
    </div>
  );
}

function JobsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [showFilters, setShowFilters] = useState(false);

  const q = searchParams.get("q") || "";
  const canton = searchParams.get("canton") || "";
  const contractType = searchParams.get("contract_type") || "";
  const page = parseInt(searchParams.get("page") || "1");

  // Lock body scroll when mobile filters open
  useEffect(() => {
    if (showFilters) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [showFilters]);

  const { data, isLoading } = useQuery({
    queryKey: ["jobs", q, canton, contractType, page],
    queryFn: () =>
      api.get<PaginatedResponse<JobListItem>>("/jobs", {
        params: {
          q: q || undefined,
          canton: canton || undefined,
          contract_type: contractType || undefined,
          page,
          per_page: 20,
        },
      }).then((r) => r.data),
  });

  const { data: cantons } = useQuery({
    queryKey: ["cantons"],
    queryFn: () => api.get<Canton[]>("/jobs/cantons").then((r) => r.data),
    staleTime: 24 * 60 * 60 * 1000,
  });

  const updateFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    params.delete("page");
    router.push(`/oferty?${params.toString()}`);
  };

  const clearFilters = () => {
    router.push("/oferty");
  };

  const cantonMap = cantons
    ? Object.fromEntries(cantons.map((c) => [c.value, c.label]))
    : {};

  const hasFilters = q || canton || contractType;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Oferty pracy {data ? `(${data.total})` : ""}
        </h1>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="md:hidden flex items-center gap-2 px-3 py-2 bg-white border rounded-lg text-sm hover:bg-gray-50 transition-colors"
        >
          <SlidersHorizontal className="w-4 h-4" />
          Filtry{hasFilters ? " *" : ""}
        </button>
      </div>

      <div className="flex gap-8">
        {/* Mobile backdrop */}
        {showFilters && (
          <div
            className="fixed inset-0 z-30 bg-black/50 md:hidden transition-opacity"
            onClick={() => setShowFilters(false)}
            aria-hidden="true"
          />
        )}

        {/* Filters sidebar */}
        <aside
          className={`${showFilters ? "fixed inset-0 z-40 bg-white p-6 overflow-auto" : "hidden"} md:block md:relative md:w-64 flex-shrink-0`}
        >
          <div className="flex items-center justify-between md:hidden mb-4">
            <h2 className="text-lg font-semibold">Filtry</h2>
            <button
              onClick={() => setShowFilters(false)}
              className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Zamknij filtry"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="space-y-6">
            {/* Szukaj */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Szukaj</label>
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <input
                  type="text"
                  defaultValue={q}
                  placeholder="Stanowisko..."
                  onKeyDown={(e) => {
                    if (e.key === "Enter") updateFilter("q", e.currentTarget.value);
                  }}
                  className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                />
              </div>
            </div>

            {/* Kanton */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Kanton</label>
              <select
                value={canton}
                onChange={(e) => updateFilter("canton", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
              >
                <option value="">Wszystkie</option>
                {cantons?.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>

            {/* Typ umowy */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Typ umowy</label>
              <select
                value={contractType}
                onChange={(e) => updateFilter("contract_type", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
              >
                <option value="">Wszystkie</option>
                {Object.entries(CONTRACT_TYPES).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>

            {hasFilters && (
              <button
                onClick={clearFilters}
                className="w-full text-sm text-red-600 hover:underline"
              >
                Wyczyść filtry
              </button>
            )}
          </div>
        </aside>

        {/* Results */}
        <div className="flex-1">
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <JobCardSkeleton key={i} />
              ))}
            </div>
          ) : data?.data && data.data.length > 0 ? (
            <>
              <div className="space-y-4">
                {data.data.map((job) => (
                  <Link
                    key={job.id}
                    href={`/oferty/${job.id}`}
                    className="block bg-white border border-gray-200 rounded-lg p-5 hover:shadow-md hover:border-red-200 transition-all"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        {job.is_featured && (
                          <span className="inline-block bg-yellow-100 text-yellow-800 text-xs font-semibold px-2 py-0.5 rounded mb-2">
                            Wyróżnione
                          </span>
                        )}
                        <h2 className="text-lg font-semibold text-gray-900 truncate">{job.title}</h2>
                        <p className="text-sm text-gray-500 mt-1 truncate">
                          {job.employer?.company_name}
                        </p>
                        <div className="flex flex-wrap gap-2 mt-2 text-xs text-gray-500">
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {cantonMap[job.canton] || job.canton}{job.city ? `, ${job.city}` : ""}
                          </span>
                          <span className="bg-gray-100 px-2 py-0.5 rounded">
                            {CONTRACT_TYPES[job.contract_type] || job.contract_type}
                          </span>
                          {job.is_remote !== "no" && (
                            <span className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded">
                              {job.is_remote === "yes" ? "Zdalnie" : "Hybrydowo"}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="font-semibold text-gray-900">
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

              {/* Pagination with ARIA */}
              {data.pages > 1 && (
                <nav className="flex justify-center gap-2 mt-8" aria-label="Paginacja ofert pracy">
                  {Array.from({ length: data.pages }, (_, i) => i + 1).map((p) => (
                    <button
                      key={p}
                      onClick={() => updateFilter("page", String(p))}
                      aria-label={`Strona ${p}`}
                      aria-current={p === page ? "page" : undefined}
                      className={`px-3 py-1 rounded text-sm transition-colors ${
                        p === page
                          ? "bg-red-600 text-white"
                          : "bg-white border text-gray-700 hover:bg-gray-50"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </nav>
              )}
            </>
          ) : (
            <div className="text-center py-16 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
              <Briefcase className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p className="text-lg font-medium text-gray-700 mb-2">Brak ofert spełniających kryteria</p>
              {hasFilters && (
                <button onClick={clearFilters} className="text-red-600 hover:underline text-sm">
                  Wyczyść filtry
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function OffertyPage() {
  return (
    <Suspense fallback={
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="h-8 bg-gray-200 rounded w-48 mb-6 animate-pulse" />
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <JobCardSkeleton key={i} />
          ))}
        </div>
      </div>
    }>
      <JobsContent />
    </Suspense>
  );
}
