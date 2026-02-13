"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Search, MapPin, Briefcase, Users, Building2 } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/services/api";
import { formatSalary, formatDate, CONTRACT_TYPES } from "@/lib/utils";
import type { JobListItem, PaginatedResponse, CategoryBrief, Canton } from "@/types/api";

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [canton, setCanton] = useState("");

  const { data: jobsData } = useQuery({
    queryKey: ["latest-jobs"],
    queryFn: () =>
      api.get<PaginatedResponse<JobListItem>>("/jobs", {
        params: { per_page: 6, sort_by: "published_at" },
      }).then((r) => r.data),
  });

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<CategoryBrief[]>("/jobs/categories").then((r) => r.data),
    staleTime: 60 * 60 * 1000,
  });

  const { data: cantons } = useQuery({
    queryKey: ["cantons"],
    queryFn: () => api.get<Canton[]>("/jobs/cantons").then((r) => r.data),
    staleTime: 24 * 60 * 60 * 1000,
  });

  const cantonMap = cantons
    ? Object.fromEntries(cantons.map((c) => [c.value, c.label]))
    : {};

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (canton) params.set("canton", canton);
    router.push(`/oferty?${params.toString()}`);
  };

  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-red-700 via-red-600 to-red-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24">
          <h1 className="text-3xl md:text-5xl font-bold text-center mb-4">
            Znajdź wymarzoną pracę w Szwajcarii
          </h1>
          <p className="text-center text-red-100 text-lg mb-8 max-w-2xl mx-auto">
            Portal pracy dla Polaków mieszkających i pracujących w Szwajcarii
          </p>

          {/* Search bar */}
          <form
            onSubmit={handleSearch}
            className="max-w-3xl mx-auto bg-white rounded-xl shadow-lg p-2 flex flex-col sm:flex-row gap-2"
          >
            <div className="flex-1 flex items-center gap-2 px-3">
              <Search className="w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Stanowisko, firma..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full py-2 text-gray-900 placeholder-gray-400 outline-none"
              />
            </div>
            <div className="flex items-center gap-2 px-3 border-t sm:border-t-0 sm:border-l border-gray-200">
              <MapPin className="w-5 h-5 text-gray-400" />
              <select
                value={canton}
                onChange={(e) => setCanton(e.target.value)}
                className="py-2 text-gray-900 outline-none bg-transparent min-w-[140px]"
              >
                <option value="">Cała Szwajcaria</option>
                {cantons?.map((c: { value: string; label: string }) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="submit"
              className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 font-semibold whitespace-nowrap"
            >
              Szukaj
            </button>
          </form>

          {/* Popular tags */}
          <div className="mt-6 text-center text-sm text-red-200">
            Popularne:{" "}
            {["spawacz", "kierowca", "opiekun/ka", "kelner/ka", "sprzątanie"].map(
              (tag) => (
                <Link
                  key={tag}
                  href={`/oferty?q=${tag}`}
                  className="inline-block mx-1 px-2 py-1 bg-white/10 rounded hover:bg-white/20"
                >
                  {tag}
                </Link>
              )
            )}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-3 gap-8 text-center">
            <div>
              <div className="flex items-center justify-center gap-2 text-red-600 mb-1">
                <Briefcase className="w-5 h-5" />
                <span className="text-2xl font-bold">{jobsData?.total || 0}+</span>
              </div>
              <p className="text-sm text-gray-500">Ofert pracy</p>
            </div>
            <div>
              <div className="flex items-center justify-center gap-2 text-red-600 mb-1">
                <Building2 className="w-5 h-5" />
                <span className="text-2xl font-bold">26</span>
              </div>
              <p className="text-sm text-gray-500">Kantonów</p>
            </div>
            <div>
              <div className="flex items-center justify-center gap-2 text-red-600 mb-1">
                <Users className="w-5 h-5" />
                <span className="text-2xl font-bold">{categories?.length || 0}</span>
              </div>
              <p className="text-sm text-gray-500">Kategorii</p>
            </div>
          </div>
        </div>
      </section>

      {/* Categories */}
      {categories && categories.length > 0 && (
        <section className="py-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Kategorie</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {categories.map((cat) => (
                <Link
                  key={cat.id}
                  href={`/oferty?category_id=${cat.id}`}
                  className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md hover:border-red-200 transition-all"
                >
                  <span className="font-medium text-gray-900">{cat.name}</span>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Latest jobs */}
      <section className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Najnowsze oferty</h2>
            <Link
              href="/oferty"
              className="text-red-600 hover:text-red-700 font-medium text-sm"
            >
              Zobacz wszystkie &rarr;
            </Link>
          </div>

          {jobsData?.data && jobsData.data.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {jobsData.data.map((job) => (
                <Link
                  key={job.id}
                  href={`/oferty/${job.id}`}
                  className="bg-gray-50 border border-gray-200 rounded-lg p-5 hover:shadow-md hover:border-red-200 transition-all"
                >
                  {job.is_featured && (
                    <span className="inline-block bg-yellow-100 text-yellow-800 text-xs font-semibold px-2 py-0.5 rounded mb-2">
                      Wyróżnione
                    </span>
                  )}
                  <h3 className="font-semibold text-gray-900 mb-1">{job.title}</h3>
                  <p className="text-sm text-gray-500 mb-2">
                    {job.employer?.company_name}
                  </p>
                  <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {cantonMap[job.canton] || job.canton}{job.city ? `, ${job.city}` : ""}
                    </span>
                    <span className="bg-gray-100 px-2 py-0.5 rounded">
                      {CONTRACT_TYPES[job.contract_type] || job.contract_type}
                    </span>
                  </div>
                  <p className="text-sm font-semibold text-gray-900 mt-3">
                    {formatSalary(job.salary_min, job.salary_max, job.salary_type)}
                  </p>
                  {job.published_at && (
                    <p className="text-xs text-gray-400 mt-2">
                      {formatDate(job.published_at)}
                    </p>
                  )}
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <Briefcase className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>Brak ofert pracy. Dodaj pierwsze ogłoszenie!</p>
            </div>
          )}
        </div>
      </section>

      {/* CTA for employers */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
            Szukasz polskojęzycznych pracowników?
          </h2>
          <p className="text-gray-600 mb-8">
            Dodaj ogłoszenie za darmo i dotrzyj do tysięcy Polaków w Szwajcarii.
          </p>
          <Link
            href="/register/employer"
            className="inline-block bg-red-600 text-white px-8 py-3 rounded-lg hover:bg-red-700 font-semibold text-lg"
          >
            Dodaj ogłoszenie za darmo
          </Link>
        </div>
      </section>
    </div>
  );
}
