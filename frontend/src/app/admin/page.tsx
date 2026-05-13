"use client";

import { useState, useEffect, useMemo, useRef } from "react";
import { Lock, BarChart3, Building2, RefreshCcw, TrendingUp, TrendingDown, Minus, Plus, Trash2, Save, X } from "lucide-react";
import api from "@/services/api";

const STORAGE_KEY = "admin-panel-password";

type Tab = "overview" | "companies" | "overrides";

interface WindowMetric { current: number; previous: number; pct_change: number | null }
interface MetricBlock { "7d": WindowMetric; "30d": WindowMetric; "ytd": WindowMetric }
interface OverviewData {
  visits_unique_ips: MetricBlock;
  cv_scans: MetricBlock;
  jobs_published: MetricBlock;
  applications_internal: MetricBlock;
  apply_clicks_external: MetricBlock;
}

interface SeriesPoint {
  date: string;
  visits_unique_ips: number;
  visits_total: number;
  cv_scans: number;
  jobs_added: number;
  applications_internal: number;
  apply_clicks_external: number;
}

interface CompanyRow {
  employer_id: string;
  company_name: string;
  company_slug: string | null;
  company_key: string;
  job_count: number;
  views_total: number;
  applications_internal: number;
  apply_clicks_external: number;
  override_email: string | null;
  override_id: string | null;
  override_note: string | null;
}

interface OverrideRow {
  id: string;
  company_name: string;
  company_key: string;
  apply_email: string;
  note: string | null;
  created_at: string | null;
  updated_at: string | null;
}

const METRIC_LABELS: Record<keyof OverviewData, string> = {
  visits_unique_ips: "Unikalne IP",
  cv_scans: "Skany CV",
  jobs_published: "Nowe oferty",
  applications_internal: "Aplikacje (formularz)",
  apply_clicks_external: "Aplikacje (zewnętrzne)",
};

const SERIES_KEYS: { key: keyof SeriesPoint; label: string; color: string }[] = [
  { key: "visits_unique_ips", label: "Unikalne IP / dzień", color: "#0D2240" },
  { key: "cv_scans", label: "Skany CV", color: "#E1002A" },
  { key: "applications_internal", label: "Aplikacje (formularz)", color: "#16a34a" },
  { key: "apply_clicks_external", label: "Aplikacje (zewnętrzne)", color: "#d97706" },
  { key: "jobs_added", label: "Nowe oferty", color: "#6366f1" },
];

export default function AdminPanelPage() {
  const [password, setPassword] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("overview");

  // Load saved password on mount
  useEffect(() => {
    if (typeof window === "undefined") return;
    const saved = sessionStorage.getItem(STORAGE_KEY);
    if (saved) setPassword(saved);
  }, []);

  if (!password) {
    return <LoginScreen onAuth={(p) => { sessionStorage.setItem(STORAGE_KEY, p); setPassword(p); }} />;
  }

  const handleLogout = () => {
    sessionStorage.removeItem(STORAGE_KEY);
    setPassword(null);
  };

  return (
    <div className="min-h-screen bg-[#F5F6F8]">
      <header className="bg-white border-b border-[#E0E3E8] sticky top-0 z-30">
        <div className="max-w-[1200px] mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2 text-[#0D2240] font-bold font-display">
            <BarChart3 className="w-5 h-5 text-[#E1002A]" />
            Panel administratora
          </div>
          <button
            onClick={handleLogout}
            className="text-xs text-gray-500 hover:text-[#E1002A] transition-colors"
          >
            Wyloguj
          </button>
        </div>
        <div className="max-w-[1200px] mx-auto px-6 flex gap-1 border-t border-[#E0E3E8]">
          {([
            ["overview", "Statystyki"],
            ["companies", "Firmy"],
            ["overrides", "Override emaili"],
          ] as [Tab, string][]).map(([k, label]) => (
            <button
              key={k}
              onClick={() => setTab(k)}
              className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors -mb-px ${
                tab === k
                  ? "border-[#E1002A] text-[#0D2240]"
                  : "border-transparent text-gray-500 hover:text-[#0D2240]"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      <main className="max-w-[1200px] mx-auto px-6 py-6">
        {tab === "overview" && <OverviewTab password={password} />}
        {tab === "companies" && <CompaniesTab password={password} />}
        {tab === "overrides" && <OverridesTab password={password} />}
      </main>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────

function LoginScreen({ onAuth }: { onAuth: (p: string) => void }) {
  const [value, setValue] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      await api.post("/admin-panel/login", { password: value });
      onAuth(value);
    } catch (e: unknown) {
      const ex = e as { response?: { data?: { detail?: string } } };
      setErr(ex.response?.data?.detail || "Niepoprawne hasło");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0D2240] flex items-center justify-center px-4">
      <form onSubmit={submit} className="bg-white rounded-lg shadow-2xl p-8 w-full max-w-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-[#E1002A] flex items-center justify-center">
            <Lock className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-display font-bold text-[#0D2240]">Panel administratora</h1>
            <p className="text-xs text-gray-500">Tylko dla właściciela</p>
          </div>
        </div>
        <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">Hasło</label>
        <input
          type="password"
          autoFocus
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-[#E1002A]"
        />
        {err && <p className="mt-2 text-sm text-[#E1002A]">{err}</p>}
        <button
          type="submit"
          disabled={!value || loading}
          className="mt-4 w-full bg-[#0D2240] text-white py-3 rounded font-semibold hover:bg-[#1B3157] disabled:opacity-50 transition-colors"
        >
          {loading ? "Sprawdzam..." : "Wejdź"}
        </button>
      </form>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────

function useAdminFetch<T>(path: string, password: string): { data: T | null; error: string | null; loading: boolean; reload: () => void } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    api
      .get<T>(path, { headers: { "X-Admin-Password": password } })
      .then((r) => { if (alive) setData(r.data); })
      .catch((e) => {
        if (alive) {
          const detail = (e as { response?: { data?: { detail?: string } } }).response?.data?.detail;
          setError(detail || "Błąd pobierania danych");
        }
      })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [path, password, nonce]);

  return { data, error, loading, reload: () => setNonce((n) => n + 1) };
}

// ────────────────────────────────────────────────────────────────────────────

function OverviewTab({ password }: { password: string }) {
  const overview = useAdminFetch<OverviewData>("/admin-panel/overview", password);
  const series = useAdminFetch<{ days: number; series: SeriesPoint[] }>("/admin-panel/timeseries?days=30", password);

  if (overview.loading || series.loading) return <Loading />;
  if (overview.error) return <ErrorBox text={overview.error} />;
  if (series.error) return <ErrorBox text={series.error} />;
  if (!overview.data || !series.data) return null;

  return (
    <div className="space-y-6">
      {/* Metric cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {(Object.keys(METRIC_LABELS) as (keyof OverviewData)[]).map((k) => (
          <MetricCard key={k} label={METRIC_LABELS[k]} block={overview.data![k]} />
        ))}
      </div>

      {/* Time series chart */}
      <div className="bg-white border border-[#E0E3E8] rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display font-bold text-[#0D2240]">Ostatnie 30 dni</h2>
          <button
            onClick={() => { overview.reload(); series.reload(); }}
            className="text-xs text-gray-500 hover:text-[#E1002A] flex items-center gap-1"
          >
            <RefreshCcw className="w-3 h-3" /> Odśwież
          </button>
        </div>
        <TimeSeriesChart series={series.data.series} />
      </div>
    </div>
  );
}

function MetricCard({ label, block }: { label: string; block: MetricBlock }) {
  return (
    <div className="bg-white border border-[#E0E3E8] rounded-lg p-4">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">{label}</p>
      <div className="space-y-2">
        <PeriodRow label="7 dni" m={block["7d"]} />
        <PeriodRow label="30 dni" m={block["30d"]} />
        <PeriodRow label="YTD" m={block.ytd} />
      </div>
    </div>
  );
}

function PeriodRow({ label, m }: { label: string; m: WindowMetric }) {
  const pct = m.pct_change;
  const isUp = pct !== null && pct > 0;
  const isDown = pct !== null && pct < 0;
  const color = isUp ? "text-green-600" : isDown ? "text-[#E1002A]" : "text-gray-400";
  const Icon = isUp ? TrendingUp : isDown ? TrendingDown : Minus;
  return (
    <div className="flex items-baseline justify-between text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="flex items-baseline gap-2">
        <span className="font-bold text-[#0D2240] tabular-nums">{m.current.toLocaleString("pl-PL")}</span>
        {pct !== null && (
          <span className={`text-xs font-semibold flex items-center gap-0.5 ${color}`}>
            <Icon className="w-3 h-3" />
            {pct > 0 ? "+" : ""}{pct}%
          </span>
        )}
      </span>
    </div>
  );
}

function TimeSeriesChart({ series }: { series: SeriesPoint[] }) {
  const [activeKeys, setActiveKeys] = useState<Set<string>>(
    () => new Set(SERIES_KEYS.map((s) => s.key)),
  );
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);

  const toggle = (k: string) => {
    setActiveKeys((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k); else next.add(k);
      return next;
    });
  };

  const W = 1000, H = 280, P = 36;
  const innerW = W - 2 * P, innerH = H - 2 * P;
  const n = series.length || 1;

  const maxY = useMemo(() => {
    let m = 1;
    for (const p of series) {
      for (const sk of SERIES_KEYS) {
        if (!activeKeys.has(sk.key)) continue;
        const v = p[sk.key] as number;
        if (v > m) m = v;
      }
    }
    return m;
  }, [series, activeKeys]);

  const x = (i: number) => P + (i / Math.max(1, n - 1)) * innerW;
  const y = (v: number) => P + innerH - (v / maxY) * innerH;

  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => ({
    val: Math.round(f * maxY),
    y: P + innerH - f * innerH,
  }));

  const dateLabel = (iso: string) => {
    const d = new Date(iso);
    return `${d.getDate()}.${String(d.getMonth() + 1).padStart(2, "0")}`;
  };

  const handleMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const relX = ((e.clientX - rect.left) / rect.width) * W;
    if (relX < P || relX > W - P) {
      setHoverIdx(null);
      return;
    }
    const ratio = (relX - P) / innerW;
    const idx = Math.round(ratio * (n - 1));
    setHoverIdx(Math.max(0, Math.min(n - 1, idx)));
  };

  const fullDateLabel = (iso: string) => {
    const d = new Date(iso);
    const days = ["niedz", "pon", "wt", "śr", "czw", "pt", "sob"];
    return `${days[d.getDay()]} ${d.getDate()}.${String(d.getMonth() + 1).padStart(2, "0")}.${d.getFullYear()}`;
  };

  return (
    <div className="relative">
      <div className="flex flex-wrap gap-3 mb-4">
        {SERIES_KEYS.map((s) => {
          const active = activeKeys.has(s.key);
          return (
            <button
              key={s.key}
              onClick={() => toggle(s.key)}
              className={`text-xs font-medium flex items-center gap-1.5 px-2.5 py-1 rounded transition-all ${
                active ? "bg-gray-100" : "opacity-30"
              }`}
            >
              <span className="w-2.5 h-2.5 rounded-sm" style={{ background: s.color }} />
              {s.label}
            </button>
          );
        })}
      </div>

      <div className="relative">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${W} ${H}`}
          className="w-full h-auto"
          preserveAspectRatio="none"
          onMouseMove={handleMove}
          onMouseLeave={() => setHoverIdx(null)}
        >
          {/* Grid */}
          {ticks.map((t, i) => (
            <g key={i}>
              <line x1={P} y1={t.y} x2={W - P} y2={t.y} stroke="#E0E3E8" strokeDasharray="2 4" />
              <text x={4} y={t.y + 3} fontSize="10" fill="#888">{t.val}</text>
            </g>
          ))}
          {/* X labels (every ~5 days) */}
          {series.map((p, i) => {
            if (i % Math.max(1, Math.floor(n / 6)) !== 0 && i !== n - 1) return null;
            return (
              <text key={i} x={x(i)} y={H - 8} fontSize="10" fill="#888" textAnchor="middle">
                {dateLabel(p.date)}
              </text>
            );
          })}
          {/* Lines */}
          {SERIES_KEYS.filter((s) => activeKeys.has(s.key)).map((s) => {
            const points = series.map((p, i) => `${x(i)},${y(p[s.key] as number)}`).join(" ");
            return (
              <polyline
                key={s.key}
                fill="none"
                stroke={s.color}
                strokeWidth={2}
                strokeLinejoin="round"
                strokeLinecap="round"
                points={points}
              />
            );
          })}
          {/* Hover guide line + dots */}
          {hoverIdx !== null && (
            <g>
              <line
                x1={x(hoverIdx)}
                y1={P}
                x2={x(hoverIdx)}
                y2={H - P}
                stroke="#0D2240"
                strokeWidth={1}
                strokeDasharray="3 3"
                opacity={0.5}
              />
              {SERIES_KEYS.filter((s) => activeKeys.has(s.key)).map((s) => (
                <circle
                  key={s.key}
                  cx={x(hoverIdx)}
                  cy={y(series[hoverIdx][s.key] as number)}
                  r={4}
                  fill="white"
                  stroke={s.color}
                  strokeWidth={2}
                />
              ))}
            </g>
          )}
        </svg>

        {/* Tooltip */}
        {hoverIdx !== null && (() => {
          const point = series[hoverIdx];
          // position tooltip near hovered x, but clamp inside container
          const leftPct = (x(hoverIdx) / W) * 100;
          const placeRight = leftPct < 65;
          return (
            <div
              className="absolute top-2 pointer-events-none bg-white border border-[#E0E3E8] rounded-lg shadow-lg px-3 py-2 text-xs z-10"
              style={
                placeRight
                  ? { left: `calc(${leftPct}% + 16px)` }
                  : { right: `calc(${100 - leftPct}% + 16px)` }
              }
            >
              <p className="font-semibold text-[#0D2240] mb-1.5 whitespace-nowrap">{fullDateLabel(point.date)}</p>
              <div className="space-y-1">
                {SERIES_KEYS.filter((s) => activeKeys.has(s.key)).map((s) => (
                  <div key={s.key} className="flex items-center gap-2 whitespace-nowrap">
                    <span className="w-2 h-2 rounded-sm" style={{ background: s.color }} />
                    <span className="text-gray-600">{s.label}:</span>
                    <span className="font-bold text-[#0D2240] tabular-nums ml-auto">
                      {(point[s.key] as number).toLocaleString("pl-PL")}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          );
        })()}
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────

type CompanySortKey =
  | "company_name"
  | "job_count"
  | "views_total"
  | "applications_internal"
  | "apply_clicks_external"
  | "override_email";

function CompaniesTab({ password }: { password: string }) {
  const { data, error, loading, reload } = useAdminFetch<{ companies: CompanyRow[] }>("/admin-panel/companies", password);
  const [filter, setFilter] = useState("");
  const [sortKey, setSortKey] = useState<CompanySortKey>("views_total");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const toggleSort = (k: CompanySortKey) => {
    if (k === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(k);
      setSortDir(k === "company_name" || k === "override_email" ? "asc" : "desc");
    }
  };

  const sortedAndFiltered = useMemo(() => {
    if (!data) return [];
    const filtered = data.companies.filter((c) =>
      !filter || (c.company_name || "").toLowerCase().includes(filter.toLowerCase()),
    );
    const dir = sortDir === "asc" ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      // null/empty go to the end regardless of dir, to keep ranking useful
      if (av === null || av === "") return 1;
      if (bv === null || bv === "") return -1;
      if (typeof av === "number" && typeof bv === "number") return (av - bv) * dir;
      return String(av).localeCompare(String(bv), "pl") * dir;
    });
  }, [data, filter, sortKey, sortDir]);

  if (loading) return <Loading />;
  if (error) return <ErrorBox text={error} />;
  if (!data) return null;

  const SortHeader = ({ k, label, align = "left" }: { k: CompanySortKey; label: string; align?: "left" | "right" }) => {
    const active = sortKey === k;
    return (
      <th
        onClick={() => toggleSort(k)}
        className={`px-4 py-2.5 cursor-pointer select-none hover:text-[#0D2240] transition-colors ${align === "right" ? "text-right" : "text-left"}`}
      >
        <span className="inline-flex items-center gap-1">
          {label}
          <span className={`text-[10px] ${active ? "text-[#E1002A]" : "text-gray-300"}`}>
            {active ? (sortDir === "asc" ? "▲" : "▼") : "▾"}
          </span>
        </span>
      </th>
    );
  };

  return (
    <div className="bg-white border border-[#E0E3E8] rounded-lg overflow-hidden">
      <div className="px-5 py-4 border-b border-[#E0E3E8] flex flex-wrap items-center gap-3 justify-between">
        <h2 className="font-display font-bold text-[#0D2240]">Firmy ({data.companies.length})</h2>
        <div className="flex items-center gap-2">
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Szukaj firmy..."
            className="px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-[#E1002A]/40"
          />
          <button onClick={reload} className="text-xs text-gray-500 hover:text-[#E1002A] flex items-center gap-1">
            <RefreshCcw className="w-3 h-3" /> Odśwież
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider">
            <tr>
              <SortHeader k="company_name" label="Firma" />
              <SortHeader k="job_count" label="Ofert" align="right" />
              <SortHeader k="views_total" label="Wyświetleń" align="right" />
              <SortHeader k="applications_internal" label="Aplikacji (formularz)" align="right" />
              <SortHeader k="apply_clicks_external" label="Aplikacji (klik ext)" align="right" />
              <SortHeader k="override_email" label="Override email" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sortedAndFiltered.map((c) => (
              <tr key={c.employer_id} className="hover:bg-gray-50">
                <td className="px-4 py-2.5 font-medium text-[#0D2240]">
                  {c.company_name ? (
                    c.company_slug ? (
                      <a
                        href={`/firmy/${c.company_slug}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-[#E1002A] hover:underline transition-colors"
                      >
                        {c.company_name}
                      </a>
                    ) : (
                      c.company_name
                    )
                  ) : (
                    <em className="text-gray-400">brak nazwy</em>
                  )}
                </td>
                <td className="px-4 py-2.5 text-right tabular-nums">{c.job_count}</td>
                <td className="px-4 py-2.5 text-right tabular-nums">{c.views_total}</td>
                <td className="px-4 py-2.5 text-right tabular-nums">{c.applications_internal}</td>
                <td className="px-4 py-2.5 text-right tabular-nums">{c.apply_clicks_external}</td>
                <td className="px-4 py-2.5 text-xs">
                  {c.override_email ? (
                    <span className="font-mono text-green-700">{c.override_email}</span>
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
              </tr>
            ))}
            {sortedAndFiltered.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">Brak firm pasujących do filtra</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────

function OverridesTab({ password }: { password: string }) {
  const { data, error, loading, reload } = useAdminFetch<{ overrides: OverrideRow[] }>("/admin-panel/overrides", password);
  const [newName, setNewName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newNote, setNewNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitErr, setSubmitErr] = useState<string | null>(null);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitErr(null);
    setSubmitting(true);
    try {
      await api.post(
        "/admin-panel/overrides",
        { company_name: newName, apply_email: newEmail, note: newNote || null },
        { headers: { "X-Admin-Password": password } },
      );
      setNewName(""); setNewEmail(""); setNewNote("");
      reload();
    } catch (ex: unknown) {
      const e = ex as { response?: { data?: { detail?: string } } };
      setSubmitErr(e.response?.data?.detail || "Nie udało się dodać");
    } finally {
      setSubmitting(false);
    }
  };

  const remove = async (id: string) => {
    if (!confirm("Usunąć override?")) return;
    await api.delete(`/admin-panel/overrides/${id}`, { headers: { "X-Admin-Password": password } });
    reload();
  };

  if (loading) return <Loading />;
  if (error) return <ErrorBox text={error} />;
  if (!data) return null;

  return (
    <div className="space-y-5">
      {/* New override */}
      <form onSubmit={create} className="bg-white border border-[#E0E3E8] rounded-lg p-5">
        <h2 className="font-display font-bold text-[#0D2240] mb-3 flex items-center gap-2">
          <Plus className="w-4 h-4 text-[#E1002A]" /> Dodaj nowy mapping firma → email
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Nazwa firmy (np. NJUJOB)" required className="px-3 py-2 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-[#E1002A]/40" />
          <input value={newEmail} onChange={(e) => setNewEmail(e.target.value)} type="email" placeholder="praca@firma.pl" required className="px-3 py-2 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-[#E1002A]/40" />
          <input value={newNote} onChange={(e) => setNewNote(e.target.value)} placeholder="Notatka (opcjonalnie)" className="px-3 py-2 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-[#E1002A]/40" />
        </div>
        {submitErr && <p className="mt-2 text-sm text-[#E1002A]">{submitErr}</p>}
        <button type="submit" disabled={submitting || !newName || !newEmail} className="mt-3 bg-[#0D2240] text-white px-4 py-2 rounded text-sm font-semibold hover:bg-[#1B3157] disabled:opacity-50">
          {submitting ? "Zapisuję..." : "Dodaj"}
        </button>
      </form>

      {/* List */}
      <div className="bg-white border border-[#E0E3E8] rounded-lg overflow-hidden">
        <div className="px-5 py-4 border-b border-[#E0E3E8] flex items-center justify-between">
          <h2 className="font-display font-bold text-[#0D2240]">Aktualne overridy ({data.overrides.length})</h2>
          <button onClick={reload} className="text-xs text-gray-500 hover:text-[#E1002A] flex items-center gap-1">
            <RefreshCcw className="w-3 h-3" /> Odśwież
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider">
              <tr>
                <th className="px-4 py-2.5 text-left">Firma</th>
                <th className="px-4 py-2.5 text-left">Email aplikacji</th>
                <th className="px-4 py-2.5 text-left">Notatka</th>
                <th className="px-4 py-2.5 text-left">Dodano</th>
                <th className="px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.overrides.map((o) => (
                <OverrideEditableRow key={o.id} row={o} password={password} onChange={reload} onDelete={() => remove(o.id)} />
              ))}
              {data.overrides.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">Brak overridów</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function OverrideEditableRow({ row, password, onChange, onDelete }: { row: OverrideRow; password: string; onChange: () => void; onDelete: () => void }) {
  const [editing, setEditing] = useState(false);
  const [email, setEmail] = useState(row.apply_email);
  const [note, setNote] = useState(row.note || "");
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await api.patch(
        `/admin-panel/overrides/${row.id}`,
        { apply_email: email, note: note || null },
        { headers: { "X-Admin-Password": password } },
      );
      setEditing(false);
      onChange();
    } finally {
      setSaving(false);
    }
  };

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-2.5 font-medium text-[#0D2240]">{row.company_name}</td>
      <td className="px-4 py-2.5">
        {editing ? (
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" className="px-2 py-1 text-sm border border-gray-300 rounded w-full" />
        ) : (
          <span className="font-mono text-xs text-green-700">{row.apply_email}</span>
        )}
      </td>
      <td className="px-4 py-2.5 text-xs text-gray-600">
        {editing ? (
          <input value={note} onChange={(e) => setNote(e.target.value)} className="px-2 py-1 text-sm border border-gray-300 rounded w-full" placeholder="Notatka" />
        ) : (
          row.note || <span className="text-gray-400">—</span>
        )}
      </td>
      <td className="px-4 py-2.5 text-xs text-gray-500">{row.created_at ? new Date(row.created_at).toLocaleDateString("pl-PL") : ""}</td>
      <td className="px-4 py-2.5 text-right whitespace-nowrap">
        {editing ? (
          <div className="flex gap-1 justify-end">
            <button onClick={save} disabled={saving} className="px-2 py-1 bg-green-600 text-white rounded text-xs flex items-center gap-1">
              <Save className="w-3 h-3" /> {saving ? "..." : "Zapisz"}
            </button>
            <button onClick={() => { setEditing(false); setEmail(row.apply_email); setNote(row.note || ""); }} className="px-2 py-1 bg-gray-200 text-gray-700 rounded text-xs flex items-center gap-1">
              <X className="w-3 h-3" />
            </button>
          </div>
        ) : (
          <div className="flex gap-1 justify-end">
            <button onClick={() => setEditing(true)} className="px-2 py-1 text-gray-500 hover:text-[#0D2240] text-xs">Edytuj</button>
            <button onClick={onDelete} className="px-2 py-1 text-gray-500 hover:text-[#E1002A] text-xs flex items-center gap-1">
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        )}
      </td>
    </tr>
  );
}

// ────────────────────────────────────────────────────────────────────────────

function Loading() {
  return <div className="text-center text-gray-500 py-20">Ładowanie...</div>;
}

function ErrorBox({ text }: { text: string }) {
  return <div className="bg-[#FFF0F3] border border-[#FFC2CD] text-[#B8001F] px-4 py-3 rounded">{text}</div>;
}
