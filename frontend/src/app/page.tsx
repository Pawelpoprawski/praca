"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Search, MapPin, Briefcase, Users, Building2, Plus, FileSearch, Sparkles, ArrowRight, ChevronDown, TrendingUp, Shield, Clock } from "lucide-react";
import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import api from "@/services/api";
import { formatSalary, formatDate, CONTRACT_TYPES } from "@/lib/utils";
import type { JobListItem, PaginatedResponse, CategoryBrief, Canton } from "@/types/api";

// Category icons mapping
const CATEGORY_ICONS: Record<string, string> = {
  "budownictwo": "🏗️",
  "gastronomia": "🍳",
  "produkcja": "🏭",
  "transport": "🚛",
  "opieka": "💊",
  "sprzatanie": "🧹",
  "magazyn": "📦",
  "it": "💻",
  "finanse": "💰",
  "sprzedaz": "🛒",
  "administracja": "📋",
  "rolnictwo": "🌾",
  "hotelarstwo": "🏨",
  "edukacja": "📚",
  "zdrowie": "🏥",
  "inne": "📌",
};

function getCategoryIcon(name: string): string {
  const lower = name.toLowerCase();
  for (const [key, icon] of Object.entries(CATEGORY_ICONS)) {
    if (lower.includes(key)) return icon;
  }
  return "💼";
}

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [canton, setCanton] = useState("");

  // Autocomplete
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

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
    }, 200);
  }, []);

  const selectSuggestion = (value: string) => {
    setQuery(value);
    setShowSuggestions(false);
    const params = new URLSearchParams();
    params.set("q", value);
    if (canton) params.set("canton", canton);
    router.push(`/oferty?${params.toString()}`);
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

  const { data: jobsData, isLoading: jobsLoading } = useQuery({
    queryKey: ["latest-jobs"],
    queryFn: () =>
      api.get<PaginatedResponse<JobListItem>>("/jobs", {
        params: { per_page: 6, sort_by: "published_at" },
      }).then((r) => r.data),
  });

  const { data: categories, isLoading: categoriesLoading } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<CategoryBrief[]>("/jobs/categories").then((r) => r.data),
    staleTime: 60 * 60 * 1000,
  });

  const { data: cantons } = useQuery({
    queryKey: ["cantons"],
    queryFn: () => api.get<Canton[]>("/jobs/cantons").then((r) => r.data),
    staleTime: 24 * 60 * 60 * 1000,
  });

  const { data: popularSearches } = useQuery({
    queryKey: ["popular-searches"],
    queryFn: () => api.get<string[]>("/jobs/popular-searches").then((r) => r.data),
    staleTime: 10 * 60 * 1000,
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
      <section className="relative overflow-hidden bg-gradient-to-br from-red-600 via-red-700 to-red-900 text-white noise-overlay">
        {/* Animated background elements */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS1vcGFjaXR5PSIwLjA1IiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-40"></div>
          {/* Floating decorative shapes */}
          <div className="absolute top-20 left-[10%] w-64 h-64 bg-white/5 rounded-full blur-3xl animate-float"></div>
          <div className="absolute bottom-10 right-[15%] w-48 h-48 bg-red-400/10 rounded-full blur-3xl animate-float delay-200"></div>
          {/* Swiss cross subtle watermark */}
          <div className="absolute right-[5%] top-1/2 -translate-y-1/2 opacity-[0.04] hidden lg:block">
            <svg width="200" height="200" viewBox="0 0 32 32" fill="currentColor">
              <rect x="13" y="6" width="6" height="20" rx="1" />
              <rect x="6" y="13" width="20" height="6" rx="1" />
            </svg>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32 relative z-10">
          <div className="animate-fade-in-up">
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-center mb-6 leading-[1.1] tracking-tight">
              Znajdź wymarzoną pracę
              <br className="hidden sm:block" />
              <span className="text-red-200">w Szwajcarii</span>
            </h1>
            <p className="text-center text-red-100/90 text-lg md:text-xl mb-12 max-w-2xl mx-auto leading-relaxed">
              Portal pracy dla Polaków mieszkających i pracujących w Szwajcarii
            </p>
          </div>

          {/* Search bar */}
          <form
            onSubmit={handleSearch}
            className="max-w-3xl mx-auto bg-white rounded-2xl shadow-2xl shadow-black/20 p-2 flex flex-col sm:flex-row gap-2 focus-within:ring-2 focus-within:ring-white/60 transition-shadow animate-fade-in-up delay-200"
          >
            {/* Search input with autocomplete */}
            <div className="flex-1 relative" ref={suggestionsRef}>
              <div className="flex items-center gap-3 px-4 h-12">
                <Search className="w-5 h-5 text-gray-400 flex-shrink-0" />
                <input
                  type="text"
                  placeholder="Stanowisko, firma..."
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    fetchSuggestions(e.target.value);
                  }}
                  onFocus={() => { if (suggestions.length > 0 && query.length >= 2) setShowSuggestions(true); }}
                  onKeyDown={(e) => {
                    if (e.key === "ArrowDown") {
                      e.preventDefault();
                      setActiveSuggestion((prev) => Math.min(prev + 1, suggestions.length - 1));
                    } else if (e.key === "ArrowUp") {
                      e.preventDefault();
                      setActiveSuggestion((prev) => Math.max(prev - 1, -1));
                    } else if (e.key === "Enter" && activeSuggestion >= 0 && suggestions[activeSuggestion]) {
                      e.preventDefault();
                      selectSuggestion(suggestions[activeSuggestion]);
                    } else if (e.key === "Escape") {
                      setShowSuggestions(false);
                    }
                  }}
                  className="w-full h-full text-gray-900 placeholder-gray-400 bg-transparent focus:outline-none text-base"
                />
              </div>

              {/* Autocomplete suggestions dropdown */}
              {showSuggestions && suggestions.length > 0 && (
                <div className="absolute z-50 left-0 right-0 top-full mt-2 bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden">
                  {suggestions.map((s, i) => (
                    <button
                      key={i}
                      type="button"
                      onMouseDown={() => selectSuggestion(s)}
                      className={`w-full text-left px-4 py-3 text-sm flex items-center gap-2 transition-colors ${
                        i === activeSuggestion
                          ? "bg-red-50 text-red-700"
                          : "text-gray-700 hover:bg-gray-50"
                      }`}
                    >
                      <Search className="w-3.5 h-3.5 flex-shrink-0 opacity-40" />
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Canton selector */}
            <div className="flex items-center border-t sm:border-t-0 sm:border-l border-gray-200 sm:flex-shrink-0">
              <div className="flex items-center gap-2.5 px-4 h-12 w-full sm:w-auto">
                <MapPin className="w-5 h-5 text-gray-400 flex-shrink-0" />
                <select
                  value={canton}
                  onChange={(e) => setCanton(e.target.value)}
                  className="flex-1 sm:flex-none sm:min-w-[150px] h-full text-gray-900 bg-transparent focus:outline-none cursor-pointer text-base appearance-none pr-6"
                  style={{
                    backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%239CA3AF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E\")",
                    backgroundRepeat: "no-repeat",
                    backgroundPosition: "right 0 center",
                  }}
                >
                  <option value="">Cała Szwajcaria</option>
                  {cantons?.map((c: { value: string; label: string }) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Submit button */}
            <button
              type="submit"
              className="bg-gradient-to-r from-red-600 to-red-700 text-white px-8 h-12 rounded-xl hover:shadow-lg hover:shadow-red-500/25 font-semibold whitespace-nowrap transition-all active:scale-95 w-full sm:w-auto flex-shrink-0 focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2"
            >
              Szukaj
            </button>
          </form>

          {/* Popular tags */}
          <div className="mt-8 text-center text-sm text-red-100 animate-fade-in-up delay-400">
            <span className="opacity-80">Popularne:</span>{" "}
            {(popularSearches || ["spawacz", "kierowca", "opiekun", "kelner", "budowa", "sprzątanie"]).map(
              (tag) => (
                <Link
                  key={tag}
                  href={`/oferty?q=${tag}`}
                  className="inline-block mx-1.5 my-1 px-3.5 py-1.5 bg-white/10 backdrop-blur-sm rounded-full hover:bg-white/20 transition-all focus:outline-none focus:ring-2 focus:ring-white/50 hover:scale-105 border border-white/10"
                >
                  {tag}
                </Link>
              )
            )}
          </div>
        </div>
      </section>

      {/* Trust indicators */}
      <section className="bg-white border-b border-gray-100 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-8">
            <div className="flex items-center gap-3 animate-fade-in-up">
              <div className="w-10 h-10 bg-red-50 rounded-xl flex items-center justify-center flex-shrink-0">
                <Briefcase className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 tracking-tight">
                  {jobsData ? `${jobsData.total}+` : <span className="inline-block w-10 h-7 bg-gray-200 rounded animate-pulse" />}
                </p>
                <p className="text-xs text-gray-500 font-medium">Ofert pracy</p>
              </div>
            </div>
            <div className="flex items-center gap-3 animate-fade-in-up delay-100">
              <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
                <Building2 className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 tracking-tight">26</p>
                <p className="text-xs text-gray-500 font-medium">Kantonów</p>
              </div>
            </div>
            <div className="flex items-center gap-3 animate-fade-in-up delay-200">
              <div className="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center flex-shrink-0">
                <Users className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 tracking-tight">
                  {categories ? categories.length : <span className="inline-block w-6 h-7 bg-gray-200 rounded animate-pulse" />}
                </p>
                <p className="text-xs text-gray-500 font-medium">Kategorii</p>
              </div>
            </div>
            <div className="flex items-center gap-3 animate-fade-in-up delay-300">
              <div className="w-10 h-10 bg-purple-50 rounded-xl flex items-center justify-center flex-shrink-0">
                <Shield className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 tracking-tight">100%</p>
                <p className="text-xs text-gray-500 font-medium">Za darmo</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Categories */}
      {(categoriesLoading || (categories && categories.length > 0)) && (
        <section className="py-16 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-end justify-between mb-8">
              <div>
                <h2 className="text-3xl font-bold text-gray-900 tracking-tight">Przeglądaj kategorie</h2>
                <p className="text-gray-500 mt-1">Znajdź oferty w swojej branży</p>
              </div>
              <Link href="/oferty" className="hidden sm:flex items-center gap-1 text-red-600 hover:text-red-700 font-semibold text-sm group">
                Wszystkie
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {categoriesLoading
                ? [...Array(8)].map((_, i) => (
                    <div key={i} className="bg-white border border-gray-200 rounded-xl p-5 animate-pulse">
                      <div className="h-4 bg-gray-200 rounded w-3/4" />
                    </div>
                  ))
                : categories!.map((cat, i) => (
                    <Link
                      key={cat.id}
                      href={`/oferty?category_id=${cat.id}`}
                      className="bg-white border border-gray-100 rounded-xl p-4 hover:shadow-lg hover:border-red-200 hover:-translate-y-1 transition-all group card-hover animate-fade-in-up"
                      style={{ animationDelay: `${i * 50}ms` }}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl flex-shrink-0" role="img">
                          {getCategoryIcon(cat.name)}
                        </span>
                        <span className="font-semibold text-gray-900 group-hover:text-red-600 transition-colors text-sm leading-tight">
                          {cat.name}
                        </span>
                      </div>
                    </Link>
                  ))}
            </div>
          </div>
        </section>
      )}

      {/* Latest jobs */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-end mb-8">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 tracking-tight">Najnowsze oferty</h2>
              <p className="text-gray-500 mt-1">Dodane w ostatnim czasie</p>
            </div>
            <Link
              href="/oferty"
              className="text-red-600 hover:text-red-700 font-semibold text-sm flex items-center gap-1 group"
            >
              Zobacz wszystkie
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>

          {jobsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-white border border-gray-200 rounded-2xl p-6 animate-pulse">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gray-200 rounded-xl" />
                    <div className="flex-1">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                      <div className="h-3 bg-gray-100 rounded w-1/2" />
                    </div>
                  </div>
                  <div className="flex gap-2 mb-4">
                    <div className="h-6 bg-gray-100 rounded-lg w-24" />
                    <div className="h-6 bg-gray-100 rounded-lg w-28" />
                  </div>
                  <div className="h-5 bg-gray-200 rounded w-32" />
                </div>
              ))}
            </div>
          ) : jobsData?.data && jobsData.data.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {jobsData.data.map((job, i) => (
                <Link
                  key={job.id}
                  href={`/oferty/${job.id}`}
                  className="bg-white border border-gray-100 rounded-2xl p-6 hover:shadow-xl hover:border-red-200 transition-all group card-hover animate-fade-in-up"
                  style={{ animationDelay: `${i * 80}ms` }}
                >
                  {/* Company avatar + title */}
                  <div className="flex items-start gap-3 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-gray-100 to-gray-50 rounded-xl flex items-center justify-center flex-shrink-0 border border-gray-100 group-hover:border-red-200 transition-colors">
                      <span className="text-sm font-bold text-gray-500">
                        {(job.employer?.company_name || "?")[0].toUpperCase()}
                      </span>
                    </div>
                    <div className="min-w-0 flex-1">
                      {job.is_featured && (
                        <span className="inline-flex items-center gap-1 bg-gradient-to-r from-amber-50 to-yellow-50 text-amber-700 text-xs font-semibold px-2 py-0.5 rounded-md mb-1.5 border border-amber-200/60">
                          <TrendingUp className="w-3 h-3" />
                          Wyróżnione
                        </span>
                      )}
                      <h3 className="font-bold text-gray-900 mb-0.5 group-hover:text-red-600 transition-colors line-clamp-2 leading-snug">{job.title}</h3>
                      <p className="text-sm text-gray-500 truncate">
                        {job.employer?.company_name}
                      </p>
                    </div>
                  </div>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-1.5 text-xs text-gray-600 mb-4">
                    <span className="flex items-center gap-1 bg-gray-50 px-2 py-1 rounded-md">
                      <MapPin className="w-3 h-3" />
                      {cantonMap[job.canton] || job.canton}{job.city ? `, ${job.city}` : ""}
                    </span>
                    <span className="bg-blue-50 text-blue-700 px-2 py-1 rounded-md font-medium">
                      {CONTRACT_TYPES[job.contract_type] || job.contract_type}
                    </span>
                  </div>

                  {/* Salary + date */}
                  <div className="flex items-center justify-between pt-3 border-t border-gray-50">
                    <p className="text-base font-bold text-gray-900">
                      {formatSalary(job.salary_min, job.salary_max, job.salary_type)}
                    </p>
                    {job.published_at && (
                      <p className="text-xs text-gray-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDate(job.published_at)}
                      </p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-20 bg-gradient-to-br from-gray-50 to-white rounded-2xl border-2 border-dashed border-gray-200">
              <div className="w-16 h-16 mx-auto mb-6 bg-gray-100 rounded-2xl flex items-center justify-center">
                <Briefcase className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Brak ofert pracy</h3>
              <p className="text-gray-500 mb-8 max-w-md mx-auto leading-relaxed">
                Obecnie nie ma żadnych opublikowanych ofert. Jesteś pracodawcą? Dodaj pierwsze ogłoszenie za darmo!
              </p>
              <Link
                href="/register/employer"
                className="inline-flex items-center gap-2 bg-red-600 text-white px-8 py-4 rounded-xl hover:bg-red-700 hover:shadow-lg font-semibold transition-all active:scale-95"
              >
                <Plus className="w-5 h-5" />
                Dodaj ogłoszenie
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* CV Review CTA */}
      <section className="py-16 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-72 h-72 bg-blue-200/30 rounded-full -translate-y-1/2 translate-x-1/2 blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-56 h-56 bg-purple-200/30 rounded-full translate-y-1/2 -translate-x-1/2 blur-3xl"></div>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="grid md:grid-cols-2 gap-10 items-center">
            <div className="animate-fade-in-up">
              <div className="inline-flex items-center gap-2 bg-blue-100/80 text-blue-700 text-sm font-semibold px-4 py-2 rounded-full mb-6 backdrop-blur-sm">
                <Sparkles className="w-4 h-4" />
                Darmowa analiza CV
              </div>
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4 leading-tight tracking-tight">
                Sprawdź swoje CV
                <span className="text-gradient-blue"> za darmo</span>
              </h2>
              <p className="text-lg text-gray-600 mb-8 leading-relaxed">
                Nasze narzędzie przeanalizuje Twoje CV i podpowie co poprawić, co dodać i jak zwiększyć szanse na pracę w Szwajcarii.
              </p>
              <Link
                href="/sprawdz-cv"
                className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-4 rounded-xl hover:shadow-2xl hover:shadow-blue-500/20 font-bold text-lg transition-all hover:scale-105 active:scale-95 group"
              >
                <FileSearch className="w-5 h-5" />
                Sprawdź CV
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
            <div className="hidden md:flex justify-center">
              <div className="relative">
                <div className="w-64 h-80 bg-white rounded-2xl shadow-xl border border-gray-100 p-6 transform rotate-3 hover:rotate-0 transition-all duration-500 animate-float">
                  <div className="w-16 h-16 bg-gradient-to-br from-green-100 to-emerald-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <span className="text-2xl font-bold text-gradient">8/10</span>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 bg-green-100 rounded-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      </div>
                      <div className="h-2.5 bg-green-100 rounded-full flex-1"></div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 bg-green-100 rounded-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      </div>
                      <div className="h-2.5 bg-green-100 rounded-full w-3/4"></div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 bg-yellow-100 rounded-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                      </div>
                      <div className="h-2.5 bg-yellow-100 rounded-full w-5/6"></div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 bg-red-100 rounded-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                      </div>
                      <div className="h-2.5 bg-red-100 rounded-full w-2/3"></div>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <div className="h-2.5 bg-blue-50 rounded-full w-full mb-2"></div>
                    <div className="h-2.5 bg-blue-50 rounded-full w-4/5"></div>
                  </div>
                </div>
                {/* Decorative badge */}
                <div className="absolute -top-3 -right-3 bg-green-500 text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-lg shadow-green-500/30">
                  AI
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA for employers */}
      <section className="py-20 bg-gray-900 text-white relative overflow-hidden noise-overlay">
        <div className="absolute inset-0 bg-gradient-to-r from-red-900/20 to-transparent"></div>
        {/* Swiss cross pattern */}
        <div className="absolute right-[10%] top-1/2 -translate-y-1/2 opacity-5">
          <svg width="160" height="160" viewBox="0 0 32 32" fill="currentColor">
            <rect x="13" y="6" width="6" height="20" rx="1" />
            <rect x="6" y="13" width="20" height="6" rx="1" />
          </svg>
        </div>
        <div className="max-w-4xl mx-auto px-4 text-center relative z-10">
          <h2 className="text-3xl md:text-4xl font-bold mb-6 leading-tight tracking-tight">
            Szukasz polskojęzycznych
            <br className="hidden sm:block" />
            <span className="text-red-400">pracowników?</span>
          </h2>
          <p className="text-lg text-gray-300 mb-10 max-w-2xl mx-auto leading-relaxed">
            Dodaj ogłoszenie za darmo i dotrzyj do tysięcy Polaków w Szwajcarii.
          </p>
          <Link
            href="/register/employer"
            className="inline-flex items-center gap-2 bg-white text-gray-900 px-10 py-4 rounded-xl hover:shadow-2xl font-bold text-lg transition-all hover:scale-105 active:scale-95 group"
          >
            Dodaj ogłoszenie za darmo
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2 text-center tracking-tight">Najczęściej zadawane pytania</h2>
          <p className="text-gray-500 text-center mb-10">Wszystko co musisz wiedzieć o pracy w Szwajcarii</p>
          <div className="space-y-3">
            {[
              {
                q: "Czy korzystanie z portalu jest bezpłatne?",
                a: "Tak, portal jest w pełni bezpłatny zarówno dla pracowników, jak i dla pracodawców. Publikowanie ogłoszeń, przeglądanie ofert i aplikowanie nie wiąże się z żadnymi opłatami.",
              },
              {
                q: "Jakie dokumenty są potrzebne do pracy w Szwajcarii?",
                a: "Do legalnej pracy w Szwajcarii potrzebujesz pozwolenia na pracę (permit). Obywatele UE/EFTA mogą ubiegać się o pozwolenie typu L (krótkoterminowe) lub B (długoterminowe). Pracodawca zazwyczaj pomaga w uzyskaniu odpowiedniego pozwolenia.",
              },
              {
                q: "Jak mogę sprawdzić swoje CV?",
                a: "Skorzystaj z naszego bezpłatnego narzędzia do analizy CV. Wgraj plik PDF, a nasze narzędzie oceni go i wskaże co poprawić, co dodać i jak dostosować CV do rynku szwajcarskiego.",
              },
              {
                q: "Czy muszę znać język niemiecki lub francuski?",
                a: "Wymagania językowe zależą od kantonu i stanowiska. W niemieckojęzycznej części Szwajcarii (ok. 65% kraju) przydatny jest niemiecki, w zachodniej - francuski. Na budowach i w produkcji wymagania językowe są zazwyczaj niższe.",
              },
              {
                q: "Jak wygląda proces aplikowania?",
                a: "Zarejestruj się jako pracownik, uzupełnij profil i wgraj CV. Następnie możesz aplikować na oferty jednym kliknięciem (szybka aplikacja) lub z listem motywacyjnym. Pracodawca otrzyma powiadomienie o Twojej aplikacji.",
              },
              {
                q: "Ile zarabia się w Szwajcarii?",
                a: "Wynagrodzenia w Szwajcarii są jednymi z najwyższych w Europie. Średnie miesięczne zarobki to ok. 5'000-7'000 CHF brutto w zależności od branży i doświadczenia. W budownictwie stawki godzinowe wynoszą od 25 do 35 CHF.",
              },
            ].map((faq, i) => (
              <details key={i} className="group border border-gray-200 rounded-xl overflow-hidden hover:border-gray-300 transition-colors">
                <summary className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-gray-50 transition-colors font-semibold text-gray-900 list-none [&::-webkit-details-marker]:hidden">
                  {faq.q}
                  <ChevronDown className="w-5 h-5 text-gray-400 group-open:rotate-180 transition-transform duration-300 flex-shrink-0 ml-3" />
                </summary>
                <p className="px-5 pb-4 text-gray-600 leading-relaxed">{faq.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
