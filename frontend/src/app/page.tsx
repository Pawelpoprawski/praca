"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Search, MapPin, Briefcase, Users, Building2, FileSearch, ArrowRight,
  ChevronDown, Clock, Check,
  HardHat, ChefHat, Factory, Truck, Heart, Cpu, DollarSign, ShoppingCart,
} from "lucide-react";
import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import api from "@/services/api";
import { formatSalary, formatDate, formatJobLocation, CONTRACT_TYPES } from "@/lib/utils";
import type { JobListItem, PaginatedResponse, CategoryBrief, Canton } from "@/types/api";

const CATEGORY_ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  budownictwo: HardHat,
  gastronomia: ChefHat,
  produkcja: Factory,
  transport: Truck,
  opieka: Heart,
  it: Cpu,
  finanse: DollarSign,
  handel: ShoppingCart,
  sprzedaz: ShoppingCart,
  hotelarstwo: Building2,
};

function getCategoryIcon(name: string) {
  const lower = name.toLowerCase();
  for (const [key, Icon] of Object.entries(CATEGORY_ICON_MAP)) {
    if (lower.includes(key)) return Icon;
  }
  return Briefcase;
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
        params: { per_page: 5, sort_by: "published_at" },
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

  const { data: jobStats } = useQuery({
    queryKey: ["jobs-stats"],
    queryFn: () =>
      api.get<{ total_jobs: number; unique_companies: number; total_jobs_lifetime: number }>(
        "/jobs/stats"
      ).then((r) => r.data),
    staleTime: 60 * 60 * 1000,
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
    <div className="bg-white">
      {/* ============ HERO ============ */}
      <section className="relative overflow-hidden bg-[#0D2240] text-white">
        <div className="absolute inset-0 hays-pattern" />
        <div className="absolute -right-[100px] -top-[100px] w-[500px] h-[500px] hays-red-glow" />

        <div className="relative z-10 max-w-[1200px] mx-auto px-6 py-20 grid lg:grid-cols-[1.2fr_0.8fr] gap-15 items-center">
          {/* Left: heading + search */}
          <div>
            <h1 className="font-display text-[2rem] sm:text-[2.5rem] lg:text-[2.8rem] font-extrabold leading-[1.15] mb-5">
              Specjaliści<br />
              dla <span className="text-[#E1002A]">specjalistów</span>
            </h1>
            <p className="text-[1.1rem] text-white/85 max-w-[480px] mb-8 leading-[1.7] font-light">
              Łączymy polskich profesjonalistów z najlepszymi pracodawcami w Szwajcarii. Indywidualne podejście, ekspertyza branżowa, realne wyniki.
            </p>

            {/* Search */}
            <form
              onSubmit={handleSearch}
              className="max-w-[600px] bg-white/10 border border-white/20 rounded backdrop-blur-md flex flex-col sm:flex-row overflow-hidden"
            >
              <div className="flex-1 relative flex items-center" ref={suggestionsRef}>
                <Search className="w-5 h-5 text-white/50 ml-5 flex-shrink-0" />
                <input
                  type="text"
                  placeholder="Stanowisko, branża lub lokalizacja..."
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
                  className="flex-1 bg-transparent border-none outline-none px-4 py-4 text-[0.95rem] text-white placeholder:text-white/50"
                />

                {showSuggestions && suggestions.length > 0 && (
                  <div className="absolute z-50 left-0 right-0 top-full mt-2 bg-white border border-[#E0E3E8] rounded shadow-xl overflow-hidden">
                    {suggestions.map((s, i) => (
                      <button
                        key={i}
                        type="button"
                        onMouseDown={() => selectSuggestion(s)}
                        className={`w-full text-left px-4 py-3 text-sm flex items-center gap-2 transition-colors ${
                          i === activeSuggestion
                            ? "bg-[#FFF0F3] text-[#E1002A]"
                            : "text-[#1A1A1A] hover:bg-[#F5F6F8]"
                        }`}
                      >
                        <Search className="w-3.5 h-3.5 flex-shrink-0 opacity-40" />
                        {s}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button
                type="submit"
                className="bg-[#E1002A] hover:bg-[#B8001F] text-white px-7 py-4 font-medium text-[0.95rem] transition-colors"
              >
                Szukaj ofert
              </button>
            </form>

          </div>

          {/* Right: stat cards */}
          <div className="hidden lg:flex flex-col gap-4">
            <StatCard
              icon={<Briefcase className="w-[22px] h-[22px] text-white" />}
              number={jobsData ? jobsData.total.toLocaleString("pl-PL") : "—"}
              label="Aktywnych ofert pracy"
            />
            <StatCard
              icon={<Building2 className="w-[22px] h-[22px] text-white" />}
              number="26"
              label="Kantonów Szwajcarii"
            />
            <StatCard
              icon={<Users className="w-[22px] h-[22px] text-white" />}
              number={categories?.length.toString() || "—"}
              label="Branż i specjalizacji"
            />
          </div>
        </div>
      </section>

      {/* ============ DUAL SECTION: Seekers vs Employers ============ */}
      <section className="max-w-[1200px] mx-auto px-6 py-15 grid md:grid-cols-2 gap-6">
        <DualCard
          badge="Dla kandydatów"
          badgeStyle="red"
          title="Szukasz nowego wyzwania zawodowego?"
          description="Pomożemy Ci znaleźć stanowisko dopasowane do Twoich kompetencji i ambicji. Dostęp do tysięcy ofert i indywidualne wsparcie."
          features={[
            "Indywidualny doradca kariery",
            "Dostęp do ukrytego rynku pracy",
            "Pomoc z pozwoleniem na pracę i relokacją",
          ]}
          cta="Przeglądaj oferty"
          href="/oferty"
          ctaStyle="red"
        />
        <DualCard
          badge="Dla pracodawców"
          badgeStyle="navy"
          title="Szukasz wykwalifikowanych specjalistów?"
          description="Dostarczamy sprawdzonych kandydatów z Polski, gotowych do pracy w Szwajcarii. Publikacja ogłoszeń całkowicie za darmo."
          features={[
            "Preselekcja i weryfikacja kompetencji",
            "Rekrutacja stałych i tymczasowych pracowników",
            "Pełne wsparcie administracyjne",
          ]}
          cta="Dodaj ogłoszenie"
          href="/register/employer"
          ctaStyle="navy"
        />
      </section>

      {/* ============ CATEGORIES ============ */}
      {(categoriesLoading || (categories && categories.length > 0)) && (
        <section className="bg-[#F5F6F8] py-15">
          <div className="max-w-[1200px] mx-auto px-6">
            <div className="mb-8">
              <span className="hays-red-line" />
              <h2 className="font-display text-[1.6rem] font-bold text-[#0D2240] mb-1">Ekspertyza branżowa</h2>
              <p className="text-[#555]">Specjalizujemy się w rekrutacji dla kluczowych sektorów gospodarki szwajcarskiej</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {categoriesLoading
                ? [...Array(8)].map((_, i) => (
                    <div key={i} className="bg-white border border-[#E0E3E8] rounded-lg p-6 animate-pulse">
                      <div className="h-4 bg-[#E0E3E8] rounded w-3/4" />
                    </div>
                  ))
                : categories!.slice(0, 8).map((cat) => {
                    const Icon = getCategoryIcon(cat.name);
                    return (
                      <Link
                        key={cat.id}
                        href={`/oferty?category_id=${cat.id}`}
                        className="hays-cat-card bg-white border border-[#E0E3E8] rounded-lg p-6 flex items-center gap-4 transition-all relative overflow-hidden no-underline"
                      >
                        <div className="w-11 h-11 rounded-lg bg-[#F5F6F8] flex items-center justify-center flex-shrink-0">
                          <Icon className="w-5 h-5 text-[#0D2240]" />
                        </div>
                        <div>
                          <div className="font-display text-[0.95rem] font-semibold text-[#0D2240] leading-tight">
                            {cat.name}
                          </div>
                        </div>
                      </Link>
                    );
                  })}
            </div>
          </div>
        </section>
      )}

      {/* ============ FEATURED JOBS ============ */}
      <section className="max-w-[1200px] mx-auto px-6 py-15">
        <div className="flex justify-between items-end mb-6">
          <div>
            <span className="hays-red-line" />
            <h2 className="font-display text-[1.6rem] font-bold text-[#0D2240]">Polecane stanowiska</h2>
          </div>
          <Link
            href="/oferty"
            className="hidden sm:inline-flex items-center gap-2 px-5 py-2.5 border border-[#0D2240] text-[#0D2240] rounded text-[0.88rem] font-medium hover:bg-[#0D2240] hover:text-white transition-all no-underline"
          >
            Wszystkie oferty
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {jobsLoading ? (
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white border border-[#E0E3E8] rounded-lg p-7 animate-pulse">
                <div className="flex items-center gap-5">
                  <div className="w-14 h-14 bg-[#F5F6F8] rounded-lg" />
                  <div className="flex-1">
                    <div className="h-4 bg-[#E0E3E8] rounded w-1/2 mb-2" />
                    <div className="h-3 bg-[#F5F6F8] rounded w-1/3" />
                  </div>
                  <div className="h-6 bg-[#E0E3E8] rounded w-32" />
                </div>
              </div>
            ))}
          </div>
        ) : jobsData?.data && jobsData.data.length > 0 ? (
          <div className="space-y-3">
            {jobsData.data.map((job) => (
              <Link
                key={job.id}
                href={`/oferty/${job.id}`}
                className="hays-job-card bg-white border border-[#E0E3E8] rounded-lg px-7 py-6 grid grid-cols-[auto_1fr_auto] gap-5 items-center transition-all no-underline"
              >
                <div className="w-14 h-14 rounded-lg bg-[#F5F6F8] border border-[#E0E3E8] flex items-center justify-center font-display font-bold text-[#0D2240] flex-shrink-0">
                  {(job.employer?.company_name || "?")[0].toUpperCase()}
                </div>
                <div className="min-w-0">
                  <h3 className="font-display text-[1.05rem] font-semibold text-[#0D2240] mb-1 truncate">
                    {job.title}
                  </h3>
                  <div className="text-[0.9rem] text-[#555] mb-1.5 truncate">
                    {job.employer?.company_name || "—"}
                  </div>
                  <div className="flex flex-wrap gap-4 text-[0.85rem] text-[#888]">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5" />
                      {formatJobLocation(job.canton, job.city, cantonMap)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Briefcase className="w-3.5 h-3.5" />
                      {CONTRACT_TYPES[job.contract_type] || job.contract_type}
                    </span>
                    {job.published_at && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {formatDate(job.published_at)}
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-right hidden md:block">
                  <div className="font-display text-[1.1rem] font-bold text-[#0D2240]">
                    {formatSalary(job.salary_min, job.salary_max, job.salary_type)}
                  </div>
                  {job.is_featured && (
                    <div className="text-[0.78rem] text-[#E1002A] font-medium mt-1">Wyróżnione</div>
                  )}
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-16 bg-[#F5F6F8] rounded-lg border-2 border-dashed border-[#E0E3E8]">
            <Briefcase className="w-12 h-12 text-[#888] mx-auto mb-4" />
            <h3 className="font-display text-xl font-bold text-[#0D2240] mb-2">Brak ofert pracy</h3>
            <p className="text-[#555] mb-6 max-w-md mx-auto">
              Obecnie nie ma żadnych opublikowanych ofert. Jesteś pracodawcą? Dodaj pierwsze ogłoszenie za darmo!
            </p>
            <Link
              href="/register/employer"
              className="inline-flex items-center gap-2 bg-[#E1002A] hover:bg-[#B8001F] text-white px-7 py-3.5 rounded font-medium transition-colors no-underline"
            >
              Dodaj ogłoszenie
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}
      </section>

      {/* ============ CONSULTANTS / TRUST ============ */}
      <section className="bg-[#0D2240] text-white py-15">
        <div className="max-w-[1200px] mx-auto px-6">
          <div className="mb-8">
            <span className="hays-red-line" />
            <h2 className="font-display text-[1.6rem] font-bold text-white mb-1">Dlaczego my?</h2>
            <p className="text-white/85">Eksperci, którzy znają rynek szwajcarski od podszewki</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {[
              {
                title: "Tysiące ofert pracy",
                desc: "Codziennie publikujemy nowe ogłoszenia od pracodawców w Szwajcarii. Licznik rośnie z każdym dodanym ogłoszeniem — od początku istnienia portalu.",
                stat:
                  jobStats?.total_jobs_lifetime != null
                    ? jobStats.total_jobs_lifetime.toLocaleString("pl-PL")
                    : "—",
                statLabel: "Opublikowanych ofert łącznie",
              },
              {
                title: "Indywidualne podejście",
                desc: "Każdy kandydat otrzymuje opiekę dedykowanego konsultanta — od pierwszego kontaktu po pierwszy dzień w pracy.",
                stat: jobStats?.unique_companies != null ? jobStats.unique_companies.toLocaleString("pl-PL") : "—",
                statLabel: "Partnerskich firm",
              },
              {
                title: "AI-driven matching",
                desc: "Inteligentna analiza CV i automatyczne dopasowanie do ofert pracy. Mniej szukania, więcej trafień.",
                stat: "94%",
                statLabel: "Trafność dopasowań",
              },
            ].map((card, i) => (
              <div
                key={i}
                className="bg-white/[0.06] border border-white/10 rounded-lg p-7 hover:bg-white/10 transition-colors"
              >
                <div className="font-display text-[2rem] font-extrabold text-[#E1002A] mb-1 leading-none">
                  {card.stat}
                </div>
                <div className="text-[0.85rem] text-white/60 mb-5">{card.statLabel}</div>
                <h3 className="font-display text-[1.05rem] font-semibold text-white mb-2">{card.title}</h3>
                <p className="text-[0.9rem] text-white/70 leading-relaxed">{card.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ CV REVIEW + SALARY GUIDE ============ */}
      <section className="max-w-[1200px] mx-auto px-6 py-15 grid lg:grid-cols-2 gap-6">
        {/* CV review */}
        <div className="bg-[#F5F6F8] border border-[#E0E3E8] rounded-lg p-10 flex flex-col">
          <span className="hays-red-line" />
          <h2 className="font-display text-[1.6rem] font-bold text-[#0D2240] mb-3">
            Sprawdź swoje CV — bezpłatnie
          </h2>
          <p className="text-[#555] mb-6 leading-[1.7]">
            Nasze AI przeanalizuje Twoje CV, oceni je w skali 1–10 i podpowie co poprawić, by zwiększyć szanse na pracę w Szwajcarii.
          </p>
          <ul className="space-y-3 mb-7">
            {["Ocena jakości CV w skali 1–10", "Konkretne sugestie poprawek", "Dopasowanie do rynku szwajcarskiego"].map((f) => (
              <li key={f} className="flex items-center gap-3 text-[0.9rem] text-[#555]">
                <Check className="w-4 h-4 text-[#E1002A] flex-shrink-0" />
                {f}
              </li>
            ))}
          </ul>
          <Link
            href="/sprawdz-cv"
            className="self-start inline-flex items-center gap-2 bg-[#E1002A] hover:bg-[#B8001F] text-white px-8 py-3.5 rounded font-medium transition-colors no-underline"
          >
            <FileSearch className="w-4 h-4" />
            Sprawdź CV
          </Link>
        </div>

        {/* Salary guide */}
        <div className="bg-[#F5F6F8] border border-[#E0E3E8] rounded-lg p-10 grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-8 items-center">
          <div>
            <span className="hays-red-line" />
            <h2 className="font-display text-[1.4rem] font-bold text-[#0D2240] mb-3">
              Raport wynagrodzeń Szwajcaria 2026
            </h2>
            <p className="text-[#555] mb-5 leading-[1.7] text-[0.95rem]">
              Sprawdź ile zarabiają specjaliści w Twojej branży. Dane z 8 sektorów i 120+ stanowisk.
            </p>
            <ul className="flex flex-wrap gap-4 mb-6 text-[0.85rem] text-[#555]">
              <li className="flex items-center gap-1.5"><Check className="w-3.5 h-3.5 text-[#E1002A]" /> 8 branż</li>
              <li className="flex items-center gap-1.5"><Check className="w-3.5 h-3.5 text-[#E1002A]" /> 120+ stanowisk</li>
              <li className="flex items-center gap-1.5"><Check className="w-3.5 h-3.5 text-[#E1002A]" /> Dane 2026</li>
            </ul>
            <button className="inline-flex items-center gap-2 bg-[#0D2240] hover:bg-[#1A3A5C] text-white px-7 py-3 rounded font-medium text-[0.9rem] transition-colors">
              Pobierz bezpłatnie
            </button>
          </div>
          {/* Book mockup */}
          <div className="hidden sm:flex items-center justify-center">
            <div className="w-[140px] h-[180px] bg-[#0D2240] rounded p-5 flex flex-col items-center justify-center text-center text-white hays-book-shadow">
              <div className="font-display text-[1.8rem] font-extrabold leading-none">2026</div>
              <div className="font-display text-[0.78rem] font-semibold mt-2 leading-tight">Raport wynagrodzeń</div>
              <div className="text-[0.68rem] text-white/60 mt-1">Szwajcaria</div>
            </div>
          </div>
        </div>
      </section>

      {/* ============ FAQ ============ */}
      <section className="bg-[#F5F6F8] py-15">
        <div className="max-w-[800px] mx-auto px-6">
          <div className="text-center mb-10">
            <span className="hays-red-line mx-auto" />
            <h2 className="font-display text-[1.8rem] font-bold text-[#0D2240] mb-2">Najczęściej zadawane pytania</h2>
            <p className="text-[#555]">Wszystko co musisz wiedzieć o pracy w Szwajcarii</p>
          </div>
          <div className="space-y-3">
            {FAQ_ITEMS.map((faq, i) => (
              <details key={i} className="group bg-white border border-[#E0E3E8] rounded-lg overflow-hidden hover:border-[#0D2240] transition-colors">
                <summary className="flex items-center justify-between px-6 py-4 cursor-pointer font-display font-semibold text-[#0D2240] list-none [&::-webkit-details-marker]:hidden">
                  {faq.q}
                  <ChevronDown className="w-5 h-5 text-[#888] group-open:rotate-180 transition-transform flex-shrink-0 ml-3" />
                </summary>
                <p className="px-6 pb-5 text-[#555] leading-[1.7] text-[0.95rem]">{faq.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

/* ============ Sub-components ============ */

function StatCard({ icon, number, label }: { icon: React.ReactNode; number: string; label: string }) {
  return (
    <div className="bg-white/[0.08] border border-white/10 rounded-lg p-5 flex items-center gap-4 backdrop-blur-md">
      <div className="w-12 h-12 rounded-lg bg-[#E1002A] flex items-center justify-center flex-shrink-0">
        {icon}
      </div>
      <div>
        <div className="font-display text-[1.6rem] font-bold leading-none">{number}</div>
        <div className="text-[0.85rem] text-white/60 mt-1">{label}</div>
      </div>
    </div>
  );
}

function DualCard({
  badge, badgeStyle, title, description, features, cta, href, ctaStyle,
}: {
  badge: string;
  badgeStyle: "red" | "navy";
  title: string;
  description: string;
  features: string[];
  cta: string;
  href: string;
  ctaStyle: "red" | "navy";
}) {
  const badgeClass = badgeStyle === "red"
    ? "bg-[#FFF0F3] text-[#E1002A]"
    : "bg-[#E8EDF4] text-[#0D2240]";
  const ctaClass = ctaStyle === "red"
    ? "bg-[#E1002A] hover:bg-[#B8001F] text-white"
    : "bg-[#0D2240] hover:bg-[#1A3A5C] text-white";

  return (
    <div className="bg-white border border-[#E0E3E8] rounded-lg p-10 transition-shadow hover:shadow-[0_8px_32px_rgba(0,0,0,0.08)] flex flex-col h-full">
      <span className={`inline-block self-start text-[0.72rem] font-semibold uppercase tracking-[0.1em] px-3 py-1 rounded mb-4 ${badgeClass}`}>
        {badge}
      </span>
      <h3 className="font-display text-[1.3rem] font-bold text-[#0D2240] mb-3">{title}</h3>
      <p className="text-[#555] leading-[1.7] mb-6">{description}</p>
      <ul className="space-y-3 mb-7">
        {features.map((f) => (
          <li key={f} className="flex items-start gap-3 text-[0.9rem] text-[#555]">
            <Check className="w-[18px] h-[18px] text-[#E1002A] flex-shrink-0 mt-0.5" />
            {f}
          </li>
        ))}
      </ul>
      <Link
        href={href}
        className={`mt-auto inline-flex items-center gap-2 self-start px-8 py-3.5 rounded font-medium transition-colors no-underline ${ctaClass}`}
      >
        {cta}
        <ArrowRight className="w-4 h-4" />
      </Link>
    </div>
  );
}

const FAQ_ITEMS = [
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
    a: "Skorzystaj z naszego bezpłatnego narzędzia AI do analizy CV. Wgraj plik PDF, a system oceni je i wskaże co poprawić, co dodać i jak dostosować CV do rynku szwajcarskiego.",
  },
  {
    q: "Czy muszę znać język niemiecki lub francuski?",
    a: "Wymagania językowe zależą od kantonu i stanowiska. W niemieckojęzycznej części Szwajcarii (ok. 65% kraju) przydatny jest niemiecki, w zachodniej — francuski. Na budowach i w produkcji wymagania językowe są zazwyczaj niższe.",
  },
  {
    q: "Jak wygląda proces aplikowania?",
    a: "Zarejestruj się jako pracownik, uzupełnij profil i wgraj CV. Następnie możesz aplikować na oferty jednym kliknięciem (szybka aplikacja) lub z listem motywacyjnym. Pracodawca otrzyma powiadomienie o Twojej aplikacji.",
  },
  {
    q: "Ile zarabia się w Szwajcarii?",
    a: "Wynagrodzenia w Szwajcarii są jednymi z najwyższych w Europie. Średnie miesięczne zarobki to ok. 5'000–7'000 CHF brutto w zależności od branży i doświadczenia. W budownictwie stawki godzinowe wynoszą od 25 do 35 CHF.",
  },
];
