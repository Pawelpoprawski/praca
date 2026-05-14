"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BellRing, Users, Send, UserMinus, Search, TrendingUp, Clock, Hash,
  ChevronLeft, ChevronRight,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import api from "@/services/api";

type AlertStats = {
  total_subscribers: number;
  total_alerts: number;
  total_unsubscribes: number;
  sent_last_7d: number;
  never_sent: number;
  new_last_7d: number;
  new_last_30d: number;
  unique_keywords: number;
  avg_keywords_per_email: number;
  top_keywords: { keyword: string; subscribers: number; first_seen: string | null }[];
  daily_new: { date: string; count: number }[];
  recent_unsubscribes: {
    email: string;
    query: string | null;
    unsubscribed_at: string | null;
    subscribed_at: string | null;
    days_subscribed: number | null;
  }[];
};

type Subscriber = {
  email: string;
  keywords: string[];
  alert_rows: number;
  last_sent_at: string | null;
  subscribed_at: string | null;
};

type SubscribersResponse = {
  data: Subscriber[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
};

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("pl-PL", { day: "2-digit", month: "2-digit", year: "numeric" });
}

function formatDateTime(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("pl-PL", {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export default function AdminAlertyPage() {
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [q, setQ] = useState("");

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["admin-alerts-stats"],
    queryFn: () => api.get<AlertStats>("/admin/alerts/stats").then((r) => r.data),
    refetchInterval: 60000,
  });

  const { data: subs, isLoading: subsLoading } = useQuery({
    queryKey: ["admin-alerts-subs", page, q],
    queryFn: () =>
      api.get<SubscribersResponse>("/admin/alerts/subscribers", {
        params: { page, per_page: 30, ...(q ? { q } : {}) },
      }).then((r) => r.data),
  });

  const cards = [
    {
      label: "Subskrybenci",
      value: stats?.total_subscribers ?? 0,
      sub: `${stats?.total_alerts ?? 0} zapisów łącznie`,
      icon: Users,
      bg: "bg-blue-50",
      color: "text-blue-600",
    },
    {
      label: "Wysłane (7 dni)",
      value: stats?.sent_last_7d ?? 0,
      sub: `${stats?.never_sent ?? 0} jeszcze nie wysłanych`,
      icon: Send,
      bg: "bg-green-50",
      color: "text-green-600",
    },
    {
      label: "Nowe zapisy (7 dni)",
      value: stats?.new_last_7d ?? 0,
      sub: `${stats?.new_last_30d ?? 0} w ostatnie 30 dni`,
      icon: TrendingUp,
      bg: "bg-indigo-50",
      color: "text-indigo-600",
    },
    {
      label: "Wypisani",
      value: stats?.total_unsubscribes ?? 0,
      sub: "łącznie historycznie",
      icon: UserMinus,
      bg: "bg-[#FFF0F3]",
      color: "text-[#E1002A]",
    },
    {
      label: "Unikalne frazy",
      value: stats?.unique_keywords ?? 0,
      sub: `śr. ${stats?.avg_keywords_per_email ?? 0} fraz/email`,
      icon: Hash,
      bg: "bg-purple-50",
      color: "text-purple-600",
    },
  ];

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold font-display text-[#0D2240] flex items-center gap-2">
            <BellRing className="w-5 h-5 sm:w-6 sm:h-6 text-[#E1002A]" />
            Alerty mailowe
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Publiczne (bez logowania) powiadomienia o nowych ofertach pracy. Auto-odświeżanie co 60s.
          </p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-6">
        {cards.map((c) => {
          const Icon = c.icon;
          return (
            <div key={c.label} className="bg-white border rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <span className="text-xs text-gray-500 font-medium">{c.label}</span>
                <div className={`${c.bg} ${c.color} p-1.5 rounded`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="text-2xl font-bold text-[#0D2240]">
                {statsLoading ? "…" : c.value.toLocaleString("pl-PL")}
              </div>
              <p className="text-[11px] text-gray-500 mt-1">{c.sub}</p>
            </div>
          );
        })}
      </div>

      {/* Trend chart */}
      <div className="bg-white border rounded-lg p-4 mb-6">
        <h2 className="text-sm font-semibold text-[#0D2240] mb-3 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-indigo-600" />
          Nowe zapisy — ostatnie 30 dni
        </h2>
        <div style={{ width: "100%", height: 180 }}>
          <ResponsiveContainer>
            <AreaChart data={stats?.daily_new ?? []} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="alertsGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366F1" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#6366F1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#EEF1F5" />
              <XAxis
                dataKey="date"
                tickFormatter={(d) => d.slice(5)}
                tick={{ fontSize: 11, fill: "#6B7484" }}
                interval={4}
              />
              <YAxis tick={{ fontSize: 11, fill: "#6B7484" }} allowDecimals={false} />
              <Tooltip
                labelFormatter={(d) => formatDate(d as string)}
                contentStyle={{ fontSize: 12, borderRadius: 8 }}
              />
              <Area type="monotone" dataKey="count" stroke="#6366F1" fill="url(#alertsGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Two-column: keywords + unsubscribes */}
      <div className="grid lg:grid-cols-2 gap-4 mb-6">
        <div className="bg-white border rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b bg-gray-50">
            <h2 className="text-sm font-semibold text-[#0D2240] flex items-center gap-2">
              <Hash className="w-4 h-4 text-purple-600" />
              Najpopularniejsze frazy
              <span className="text-xs font-normal text-gray-500">
                ({stats?.top_keywords?.length ?? 0})
              </span>
            </h2>
          </div>
          <div className="overflow-x-auto max-h-[400px]">
            <table className="w-full text-sm">
              <thead className="bg-white sticky top-0">
                <tr className="border-b">
                  <th className="text-left px-4 py-2 font-semibold text-gray-600">Fraza</th>
                  <th className="text-right px-4 py-2 font-semibold text-gray-600">Subskrybenci</th>
                  <th className="text-right px-4 py-2 font-semibold text-gray-600">Pierwszy zapis</th>
                </tr>
              </thead>
              <tbody>
                {(stats?.top_keywords ?? []).map((k) => (
                  <tr key={k.keyword} className="border-b hover:bg-gray-50/50">
                    <td className="px-4 py-2 font-medium text-[#0D2240]">{k.keyword}</td>
                    <td className="px-4 py-2 text-right">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 text-xs font-semibold">
                        {k.subscribers}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right text-gray-500 text-xs whitespace-nowrap">
                      {formatDate(k.first_seen)}
                    </td>
                  </tr>
                ))}
                {!statsLoading && (stats?.top_keywords?.length ?? 0) === 0 && (
                  <tr>
                    <td colSpan={3} className="px-4 py-6 text-center text-gray-400 text-sm">
                      Brak danych
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white border rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b bg-gray-50">
            <h2 className="text-sm font-semibold text-[#0D2240] flex items-center gap-2">
              <UserMinus className="w-4 h-4 text-[#E1002A]" />
              Ostatnie wypisania
              <span className="text-xs font-normal text-gray-500">
                ({stats?.recent_unsubscribes?.length ?? 0})
              </span>
            </h2>
          </div>
          <div className="overflow-x-auto max-h-[400px]">
            <table className="w-full text-sm">
              <thead className="bg-white sticky top-0">
                <tr className="border-b">
                  <th className="text-left px-4 py-2 font-semibold text-gray-600">Email</th>
                  <th className="text-left px-4 py-2 font-semibold text-gray-600">Fraza</th>
                  <th className="text-right px-4 py-2 font-semibold text-gray-600">Subskrybowane</th>
                  <th className="text-right px-4 py-2 font-semibold text-gray-600">Wypisał się</th>
                </tr>
              </thead>
              <tbody>
                {(stats?.recent_unsubscribes ?? []).map((u, i) => (
                  <tr key={`${u.email}-${i}`} className="border-b hover:bg-gray-50/50">
                    <td className="px-4 py-2 text-[#0D2240]">{u.email}</td>
                    <td className="px-4 py-2 text-gray-600 text-xs">{u.query || "—"}</td>
                    <td className="px-4 py-2 text-right text-xs text-gray-500 whitespace-nowrap">
                      {u.days_subscribed !== null ? `${u.days_subscribed} dni` : "—"}
                    </td>
                    <td className="px-4 py-2 text-right text-xs text-gray-500 whitespace-nowrap">
                      {formatDateTime(u.unsubscribed_at)}
                    </td>
                  </tr>
                ))}
                {!statsLoading && (stats?.recent_unsubscribes?.length ?? 0) === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-gray-400 text-sm">
                      Brak wypisanych
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Subscribers list */}
      <div className="bg-white border rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b bg-gray-50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <h2 className="text-sm font-semibold text-[#0D2240] flex items-center gap-2">
            <Users className="w-4 h-4 text-blue-600" />
            Subskrybenci
            <span className="text-xs font-normal text-gray-500">
              ({subs?.total ?? 0})
            </span>
          </h2>
          <form
            onSubmit={(e) => { e.preventDefault(); setPage(1); setQ(searchInput.trim()); }}
            className="relative w-full sm:w-72"
          >
            <Search className="w-4 h-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Szukaj po emailu lub frazie..."
              className="w-full pl-8 pr-3 py-1.5 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </form>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead>
              <tr className="bg-white border-b">
                <th className="text-left px-4 py-2 font-semibold text-gray-600">Email</th>
                <th className="text-left px-4 py-2 font-semibold text-gray-600">Frazy</th>
                <th className="text-right px-4 py-2 font-semibold text-gray-600">Zapisów</th>
                <th className="text-right px-4 py-2 font-semibold text-gray-600">Zapisany</th>
                <th className="text-right px-4 py-2 font-semibold text-gray-600">Ostatni mail</th>
              </tr>
            </thead>
            <tbody>
              {subsLoading ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Ładowanie...</td></tr>
              ) : (subs?.data ?? []).length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Brak wyników</td></tr>
              ) : (
                subs!.data.map((s) => (
                  <tr key={s.email} className="border-b hover:bg-gray-50/50">
                    <td className="px-4 py-2 text-[#0D2240] font-medium break-all">{s.email}</td>
                    <td className="px-4 py-2">
                      <div className="flex flex-wrap gap-1">
                        {s.keywords.map((k) => (
                          <span
                            key={k}
                            className="inline-flex items-center px-2 py-0.5 rounded-full bg-gray-100 text-gray-700 text-xs"
                          >
                            {k}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-2 text-right text-xs text-gray-600">{s.alert_rows}</td>
                    <td className="px-4 py-2 text-right text-xs text-gray-500 whitespace-nowrap">
                      {formatDate(s.subscribed_at)}
                    </td>
                    <td className="px-4 py-2 text-right text-xs text-gray-500 whitespace-nowrap">
                      {s.last_sent_at ? (
                        <span className="inline-flex items-center gap-1 text-green-700">
                          <Clock className="w-3 h-3" />
                          {formatDateTime(s.last_sent_at)}
                        </span>
                      ) : (
                        <span className="text-amber-600">Nigdy</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {(subs?.pages ?? 0) > 1 && (
          <div className="px-4 py-3 border-t bg-gray-50 flex items-center justify-between text-sm">
            <span className="text-gray-500 text-xs">
              Strona {subs!.page} z {subs!.pages}
            </span>
            <div className="flex gap-1">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="p-1.5 rounded border bg-white disabled:opacity-40 hover:bg-gray-100"
                aria-label="Poprzednia"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                disabled={page >= (subs?.pages ?? 1)}
                onClick={() => setPage((p) => p + 1)}
                className="p-1.5 rounded border bg-white disabled:opacity-40 hover:bg-gray-100"
                aria-label="Następna"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
