"use client";

import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Search, MapPin, SlidersHorizontal, X, Briefcase, ChevronLeft, ChevronRight, Clock } from "lucide-react";
import { useState, useEffect, useRef, useCallback, Suspense } from "react";
import api from "@/services/api";
import { formatSalary, formatDate, CONTRACT_TYPES } from "@/lib/utils";
import RecentlyViewed from "@/components/jobs/RecentlyViewed";
import SaveJobButton from "@/components/jobs/SaveJobButton";
import type { JobListItem, PaginatedResponse, Canton, CategoryBrief } from "@/types/api";

function JobCardSkeleton() {
  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4 sm:p-6 animate-pulse">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div className="flex items-start gap-3 flex-1">
          <div className="w-10 h-10 bg-gray-200 rounded-xl flex-shrink-0" />
          <div className="flex-1">
            <div className="h-5 bg-gray-200 rounded-lg w-3/4 mb-2" />
            <div className="h-4 bg-gray-100 rounded-lg w-1/3 mb-3" />
            <div className="flex gap-2">
              <div className="h-6 bg-gray-100 rounded-lg w-24" />
              <div className="h-6 bg-gray-100 rounded-lg w-28" />
            </div>
          </div>
        </div>
        <div className="sm:text-right">
          <div className="h-6 bg-gray-200 rounded-lg w-36 mb-2" />
          <div className="h-4 bg-gray-100 rounded w-20 sm:ml-auto" />
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
  const categoryId = searchParams.get("category_id") || "";
  const recruiterType = searchParams.get("recruiter_type") || "";
  const page = parseInt(searchParams.get("page") || "1");

  // Autocomplete
  const [searchInput, setSearchInput] = useState(q);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    setSearchInput(q);
  }, [q]);

  const fetchSuggestions = useCallback((value: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (value.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await api.get<string[]>("/jobs/suggestions", { params: { q: value } });
        setSuggestions(res.data);
        setShowSuggestions(res.data.length > 0);
        setActiveSuggestion(-1);
      } catch {
        setSuggestions([]);
      }
    }, 250);
  }, []);

  const selectSuggestion = (value: string) => {
    setSearchInput(value);
    setShowSuggestions(false);
    updateFilter("q", value);
  };

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    if (showFilters) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [showFilters]);

  const { data, isLoading } = useQuery({
    queryKey: ["jobs", q, canton, contractType, categoryId, recruiterType, page],
    queryFn: () =>
      api.get<PaginatedResponse<JobListItem>>("/jobs", {
        params: {
          q: q || undefined,
          canton: canton || undefined,
          contract_type: contractType || undefined,
          category_id: categoryId || undefined,
          recruiter_type: recruiterType || undefined,
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

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<CategoryBrief[]>("/jobs/categories").then((r) => r.data),
    staleTime: 60 * 60 * 1000,
  });

  const updateFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    if (key !== "page") {
      params.delete("page");
    }
    router.push(`/oferty?${params.toString()}`);
    if (key !== "page") {
      setShowFilters(false);
    }
  };

  const clearFilters = () => {
    router.push("/oferty");
    setShowFilters(false);
  };

  const cantonMap = cantons
    ? Object.fromEntries(cantons.map((c) => [c.value, c.label]))
    : {};

  const hasFilters = q || canton || contractType || categoryId || recruiterType;
  const activeFilterCount = [q, canton, contractType, categoryId, recruiterType].filter(Boolean).length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
      {/* Page header */}
      <div className="flex items-center justify-between mb-6 sm:mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 tracking-tight">
            Oferty pracy
          </h1>
          {data && (
            <p className="text-gray-500 text-sm mt-1">{data.total} ofert znalezionych</p>
          )}
        </div>

        {/* Mobile filter toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`md:hidden flex items-center gap-2 px-4 py-2.5 border rounded-xl text-sm font-medium transition-all active:scale-95 ${
            hasFilters
              ? "bg-red-600 border-red-600 text-white shadow-md shadow-red-500/20"
              : "bg-white border-gray-200 hover:bg-gray-50 hover:shadow-md"
          }`}
          aria-expanded={showFilters}
          aria-controls="mobile-filters-panel"
        >
          <SlidersHorizontal className="w-4 h-4" />
          Filtry
          {activeFilterCount > 0 && (
            <span className="bg-white text-red-600 text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center leading-none">
              {activeFilterCount}
            </span>
          )}
        </button>
      </div>

      <div className="flex gap-8">
        {/* Mobile backdrop */}
        {showFilters && (
          <div
            className="fixed inset-0 z-30 bg-black/50 md:hidden"
            onClick={() => setShowFilters(false)}
            aria-hidden="true"
          />
        )}

        {/* Filters sidebar / mobile bottom sheet */}
        <aside
          id="mobile-filters-panel"
          className={`
            fixed bottom-0 left-0 right-0 z-40 bg-white rounded-t-2xl shadow-2xl
            transition-transform duration-300 ease-out
            max-h-[90vh] overflow-y-auto
            md:static md:block md:max-h-none md:shadow-none md:rounded-none md:w-72 md:flex-shrink-0 md:translate-y-0
            ${showFilters ? "translate-y-0" : "translate-y-full md:translate-y-0"}
          `}
          aria-label="Filtry wyszukiwania"
        >
          {/* Mobile handle + header */}
          <div className="md:hidden">
            <div className="flex justify-center pt-3 pb-1">
              <div className="w-10 h-1 bg-gray-300 rounded-full" />
            </div>
            <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowFilters(false)}
                  className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors -ml-1.5"
                  aria-label="Zamknij filtry"
                >
                  <ChevronLeft className="w-5 h-5 text-gray-600" />
                </button>
                <h2 className="text-lg font-bold text-gray-900">Filtry wyszukiwania</h2>
              </div>
              {hasFilters && (
                <button
                  onClick={clearFilters}
                  className="text-sm text-red-600 font-semibold hover:text-red-700"
                >
                  Wyczyść
                </button>
              )}
            </div>
          </div>

          {/* Filter fields */}
          <div className="p-5 md:p-0 space-y-5 md:bg-white md:border md:border-gray-100 md:rounded-2xl md:shadow-sm md:p-5">
            {/* Szukaj */}
            <div ref={suggestionsRef}>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Szukaj stanowiska
              </label>
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-3.5 text-gray-400 pointer-events-none" />
                <input
                  type="text"
                  value={searchInput}
                  placeholder="np. spawacz, kierowca..."
                  onChange={(e) => {
                    setSearchInput(e.target.value);
                    fetchSuggestions(e.target.value);
                  }}
                  onFocus={() => {
                    if (suggestions.length > 0 && searchInput.length >= 2) setShowSuggestions(true);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      if (activeSuggestion >= 0 && suggestions[activeSuggestion]) {
                        selectSuggestion(suggestions[activeSuggestion]);
                      } else {
                        setShowSuggestions(false);
                        updateFilter("q", searchInput);
                      }
                    } else if (e.key === "ArrowDown") {
                      e.preventDefault();
                      setActiveSuggestion((prev) => Math.min(prev + 1, suggestions.length - 1));
                    } else if (e.key === "ArrowUp") {
                      e.preventDefault();
                      setActiveSuggestion((prev) => Math.max(prev - 1, -1));
                    } else if (e.key === "Escape") {
                      setShowSuggestions(false);
                    }
                  }}
                  className="w-full pl-10 pr-3 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all bg-gray-50 focus:bg-white"
                />
                {searchInput && (
                  <button
                    type="button"
                    onClick={() => {
                      setSearchInput("");
                      setSuggestions([]);
                      setShowSuggestions(false);
                      updateFilter("q", "");
                    }}
                    className="absolute right-3 top-3.5 text-gray-400 hover:text-gray-600"
                    aria-label="Wyczyść wyszukiwanie"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
                {showSuggestions && suggestions.length > 0 && (
                  <div className="absolute z-50 left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden">
                    {suggestions.map((s, i) => (
                      <button
                        key={i}
                        type="button"
                        onMouseDown={() => selectSuggestion(s)}
                        className={`w-full text-left px-4 py-2.5 text-sm transition-colors ${
                          i === activeSuggestion ? "bg-red-50 text-red-700" : "text-gray-700 hover:bg-gray-50"
                        }`}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={() => {
                  setShowSuggestions(false);
                  updateFilter("q", searchInput);
                }}
                className="md:hidden w-full mt-2 bg-red-600 text-white py-2.5 rounded-xl text-sm font-semibold hover:bg-red-700 transition-colors flex items-center justify-center gap-2"
              >
                <Search className="w-4 h-4" />
                Szukaj
              </button>
            </div>

            {/* Kategoria */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Kategoria</label>
              <select
                value={categoryId}
                onChange={(e) => updateFilter("category_id", e.target.value)}
                className="w-full px-3 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 cursor-pointer transition-all bg-gray-50 focus:bg-white"
              >
                <option value="">Wszystkie kategorie</option>
                {categories?.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            {/* Kanton */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Kanton</label>
              <select
                value={canton}
                onChange={(e) => updateFilter("canton", e.target.value)}
                className="w-full px-3 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 cursor-pointer transition-all bg-gray-50 focus:bg-white"
              >
                <option value="">Wszystkie kantony</option>
                {cantons?.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>

            {/* Typ umowy */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Typ umowy</label>
              <select
                value={contractType}
                onChange={(e) => updateFilter("contract_type", e.target.value)}
                className="w-full px-3 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 cursor-pointer transition-all bg-gray-50 focus:bg-white"
              >
                <option value="">Wszystkie typy</option>
                {Object.entries(CONTRACT_TYPES).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>

            {/* Typ rekrutera */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Typ rekrutera</label>
              <select
                value={recruiterType}
                onChange={(e) => updateFilter("recruiter_type", e.target.value)}
                className="w-full px-3 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 cursor-pointer transition-all bg-gray-50 focus:bg-white"
              >
                <option value="">Wszyscy</option>
                <option value="polish">Polski rekruter</option>
                <option value="swiss">Szwajcarski rekruter</option>
              </select>
            </div>

            {hasFilters && (
              <button
                onClick={clearFilters}
                className="hidden md:block w-full text-sm text-red-600 hover:text-red-700 hover:underline font-semibold transition-colors"
              >
                Wyczyść filtry
              </button>
            )}
          </div>

          {/* Recently viewed (desktop only) */}
          <div className="hidden md:block mt-6">
            <RecentlyViewed maxItems={5} />
          </div>

          <div className="md:hidden h-6" />
        </aside>

        {/* Results */}
        <div className="flex-1 min-w-0">
          {/* Active filters summary bar (mobile only) */}
          {hasFilters && (
            <div className="md:hidden flex flex-wrap items-center gap-2 mb-4 p-3 bg-red-50/80 border border-red-100 rounded-xl">
              <span className="text-xs font-semibold text-red-700 mr-1">Aktywne filtry:</span>
              {q && (
                <span className="inline-flex items-center gap-1 bg-white border border-red-200 text-red-700 text-xs font-medium px-2.5 py-1 rounded-lg">
                  Szukaj: {q}
                  <button
                    onClick={() => { setSearchInput(""); updateFilter("q", ""); }}
                    aria-label={`Usuń filtr: ${q}`}
                    className="ml-0.5 hover:text-red-900"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {canton && cantonMap[canton] && (
                <span className="inline-flex items-center gap-1 bg-white border border-red-200 text-red-700 text-xs font-medium px-2.5 py-1 rounded-lg">
                  {cantonMap[canton]}
                  <button
                    onClick={() => updateFilter("canton", "")}
                    aria-label={`Usuń filtr: ${cantonMap[canton]}`}
                    className="ml-0.5 hover:text-red-900"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {contractType && CONTRACT_TYPES[contractType] && (
                <span className="inline-flex items-center gap-1 bg-white border border-red-200 text-red-700 text-xs font-medium px-2.5 py-1 rounded-lg">
                  {CONTRACT_TYPES[contractType]}
                  <button
                    onClick={() => updateFilter("contract_type", "")}
                    aria-label={`Usuń filtr: ${CONTRACT_TYPES[contractType]}`}
                    className="ml-0.5 hover:text-red-900"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {recruiterType && (
                <span className="inline-flex items-center gap-1 bg-white border border-red-200 text-red-700 text-xs font-medium px-2.5 py-1 rounded-lg">
                  {recruiterType === "polish" ? "Polski rekruter" : "Szwajcarski rekruter"}
                  <button
                    onClick={() => updateFilter("recruiter_type", "")}
                    aria-label={`Usuń filtr: typ rekrutera`}
                    className="ml-0.5 hover:text-red-900"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              <button
                onClick={clearFilters}
                className="ml-auto text-xs text-red-600 font-semibold hover:text-red-800 underline"
              >
                Wyczyść
              </button>
            </div>
          )}

          {isLoading ? (
            <div className="space-y-3 sm:space-y-4">
              {[...Array(5)].map((_, i) => (
                <JobCardSkeleton key={i} />
              ))}
            </div>
          ) : data?.data && data.data.length > 0 ? (
            <>
              <div className="space-y-3 sm:space-y-3">
                {data.data.map((job, i) => (
                  <Link
                    key={job.id}
                    href={`/oferty/${job.id}`}
                    className="block bg-white border border-gray-100 rounded-xl p-4 sm:p-5 hover:shadow-lg hover:border-red-200 hover:-translate-y-0.5 transition-all group card-hover"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between sm:gap-6">
                      {/* Left: avatar + title, company, tags */}
                      <div className="flex items-start gap-3 flex-1 min-w-0">
                        {/* Company initial avatar */}
                        <div className="hidden sm:flex w-10 h-10 bg-gradient-to-br from-gray-100 to-gray-50 rounded-xl items-center justify-center flex-shrink-0 border border-gray-100 group-hover:border-red-200 transition-colors">
                          <span className="text-sm font-bold text-gray-500">
                            {(job.employer?.company_name || "?")[0].toUpperCase()}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          {job.is_featured && (
                            <span className="inline-block bg-gradient-to-r from-amber-50 to-yellow-50 text-amber-700 text-xs font-semibold px-2 py-0.5 rounded-md mb-1.5 border border-amber-200/60">
                              Wyróżnione
                            </span>
                          )}
                          <h2 className="text-base sm:text-lg font-bold text-gray-900 group-hover:text-red-600 transition-colors leading-snug line-clamp-2">
                            {job.title}
                          </h2>
                          {job.employer?.company_name && (
                            <p className="text-sm text-gray-500 mt-0.5 font-medium truncate">
                              {job.employer.company_name}
                            </p>
                          )}

                          {/* Salary - prominent on mobile */}
                          <p className="sm:hidden font-bold text-base text-gray-900 mt-2">
                            {formatSalary(job.salary_min, job.salary_max, job.salary_type)}
                          </p>

                          <div className="flex flex-wrap gap-1.5 mt-2 sm:mt-2.5 text-xs text-gray-600">
                            <span className="flex items-center gap-1 bg-gray-50 px-2 py-1 rounded-md">
                              <MapPin className="w-3 h-3 flex-shrink-0" />
                              <span>{cantonMap[job.canton] || job.canton}{job.city ? `, ${job.city}` : ""}</span>
                            </span>
                            <span className="bg-blue-50 text-blue-700 px-2 py-1 rounded-md font-medium">
                              {CONTRACT_TYPES[job.contract_type] || job.contract_type}
                            </span>
                            {job.recruiter_type === "polish" && (
                              <span className="bg-red-50 text-red-700 px-2 py-1 rounded-md font-bold">PL</span>
                            )}
                            {job.recruiter_type === "swiss" && (
                              <span className="bg-sky-50 text-sky-700 px-2 py-1 rounded-md font-bold">CH</span>
                            )}
                          </div>

                          {job.published_at && (
                            <p className="sm:hidden text-xs text-gray-400 mt-2 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {formatDate(job.published_at)}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Right: salary + date + save */}
                      <div className="hidden sm:flex items-start gap-3 justify-end flex-shrink-0 mt-0">
                        <div className="text-right">
                          <p className="font-bold text-lg text-gray-900 whitespace-nowrap">
                            {formatSalary(job.salary_min, job.salary_max, job.salary_type)}
                          </p>
                          {job.published_at && (
                            <p className="text-xs text-gray-400 mt-1.5 text-right flex items-center gap-1 justify-end">
                              <Clock className="w-3 h-3" />
                              {formatDate(job.published_at)}
                            </p>
                          )}
                        </div>
                        <SaveJobButton jobId={job.id} size="sm" />
                      </div>
                    </div>
                  </Link>
                ))}
              </div>

              {/* Pagination with prev/next arrows */}
              {data.pages > 1 && (
                <nav className="flex items-center justify-center gap-1.5 mt-10" aria-label="Paginacja ofert pracy">
                  {/* Previous button */}
                  <button
                    onClick={() => page > 1 && updateFilter("page", String(page - 1))}
                    disabled={page <= 1}
                    aria-label="Poprzednia strona"
                    className={`flex items-center gap-1 px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                      page <= 1
                        ? "text-gray-300 cursor-not-allowed"
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900 border border-gray-200"
                    }`}
                  >
                    <ChevronLeft className="w-4 h-4" />
                    <span className="hidden sm:inline">Wstecz</span>
                  </button>

                  {/* Page numbers */}
                  {(() => {
                    const pages: (number | string)[] = [];
                    const total = data.pages;
                    if (total <= 7) {
                      for (let i = 1; i <= total; i++) pages.push(i);
                    } else {
                      pages.push(1);
                      if (page > 3) pages.push("...");
                      for (let i = Math.max(2, page - 1); i <= Math.min(total - 1, page + 1); i++) {
                        pages.push(i);
                      }
                      if (page < total - 2) pages.push("...");
                      pages.push(total);
                    }
                    return pages.map((p, idx) =>
                      typeof p === "string" ? (
                        <span key={`ellipsis-${idx}`} className="min-w-[36px] px-1 py-2 text-sm text-gray-400 flex items-center justify-center">
                          ...
                        </span>
                      ) : (
                        <button
                          key={p}
                          onClick={() => updateFilter("page", String(p))}
                          aria-label={`Strona ${p}`}
                          aria-current={p === page ? "page" : undefined}
                          className={`min-w-[36px] px-3 py-2 rounded-xl text-sm font-semibold transition-all ${
                            p === page
                              ? "bg-red-600 text-white shadow-md shadow-red-500/20"
                              : "text-gray-600 hover:bg-gray-50 hover:text-gray-900 border border-transparent hover:border-gray-200"
                          }`}
                        >
                          {p}
                        </button>
                      )
                    );
                  })()}

                  {/* Next button */}
                  <button
                    onClick={() => page < data.pages && updateFilter("page", String(page + 1))}
                    disabled={page >= data.pages}
                    aria-label="Następna strona"
                    className={`flex items-center gap-1 px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                      page >= data.pages
                        ? "text-gray-300 cursor-not-allowed"
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900 border border-gray-200"
                    }`}
                  >
                    <span className="hidden sm:inline">Dalej</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </nav>
              )}
            </>
          ) : (
            <div className="text-center py-16 sm:py-20 bg-gradient-to-br from-gray-50 to-white rounded-2xl border-2 border-dashed border-gray-200">
              <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-2xl flex items-center justify-center">
                <Briefcase className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-lg sm:text-xl font-bold text-gray-700 mb-2">
                {hasFilters ? "Brak ofert spełniających kryteria" : "Brak dostępnych ofert"}
              </p>
              <p className="text-sm text-gray-500 mb-5 px-4">
                {hasFilters
                  ? "Spróbuj zmienić lub usunąć filtry wyszukiwania."
                  : "Aktualnie nie ma żadnych aktywnych ofert."}
              </p>
              {hasFilters && (
                <button
                  onClick={clearFilters}
                  className="inline-flex items-center gap-2 bg-red-600 text-white px-5 py-2.5 rounded-xl hover:bg-red-700 font-semibold text-sm transition-colors"
                >
                  <X className="w-4 h-4" />
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
