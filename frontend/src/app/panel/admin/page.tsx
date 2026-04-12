"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  Users, Briefcase, Send, Shield, UserCheck, Building2, Clock,
  Eye, TrendingUp, TrendingDown, ArrowRight, FileSearch,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import api from "@/services/api";
import type { AdminDashboard, TrendsResponse, PeriodComparison } from "@/types/api";

type Period = "7d" | "14d" | "30d";

function ChangeBadge({ comparison }: { comparison: PeriodComparison | undefined }) {
  if (!comparison) return null;
  const pct = comparison.pct_change;
  const isUp = pct > 0;
  const isZero = pct === 0;

  if (isZero) return <span className="text-xs text-gray-400 ml-1">0%</span>;

  return (
    <span className={`inline-flex items-center gap-0.5 text-xs font-medium ml-1 ${isUp ? "text-green-600" : "text-red-600"}`}>
      {isUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
      {isUp ? "+" : ""}{pct}%
    </span>
  );
}

export default function AdminDashboardPage() {
  const [period, setPeriod] = useState<Period>("7d");

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["admin-dashboard"],
    queryFn: () => api.get<AdminDashboard>("/admin/dashboard").then((r) => r.data),
  });

  const { data: trends } = useQuery({
    queryKey: ["admin-trends"],
    queryFn: () => api.get<TrendsResponse>("/admin/stats/trends").then((r) => r.data),
  });

  const periodDays = period === "7d" ? 7 : period === "14d" ? 14 : 30;
  const chartData = trends?.daily.slice(-periodDays) ?? [];

  const c = trends?.comparisons;

  const cards = [
    { label: "Użytkownicy", value: stats?.total_users ?? 0, icon: Users, color: "text-blue-600", bg: "bg-blue-50", href: "/panel/admin/uzytkownicy", comp: c?.users[period] },
    { label: "Pracownicy", value: stats?.total_workers ?? 0, icon: UserCheck, color: "text-green-600", bg: "bg-green-50" },
    { label: "Pracodawcy", value: stats?.total_employers ?? 0, icon: Building2, color: "text-purple-600", bg: "bg-purple-50" },
    { label: "Oferty", value: stats?.total_jobs ?? 0, icon: Briefcase, color: "text-gray-600", bg: "bg-gray-50", comp: c?.jobs[period] },
    { label: "Aktywne oferty", value: stats?.active_jobs ?? 0, icon: Briefcase, color: "text-green-600", bg: "bg-green-50" },
    { label: "Do moderacji", value: stats?.pending_jobs ?? 0, icon: Clock, color: "text-yellow-600", bg: "bg-yellow-50", href: "/panel/admin/moderacja" },
    { label: "Aplikacje", value: stats?.total_applications ?? 0, icon: Send, color: "text-red-600", bg: "bg-red-50", comp: c?.applications[period] },
    { label: "Wyświetlenia", value: trends?.total_views ?? 0, icon: Eye, color: "text-indigo-600", bg: "bg-indigo-50" },
  ];

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Panel administratora</h1>
        <div className="flex bg-gray-100 rounded-lg p-0.5 w-fit">
          {(["7d", "14d", "30d"] as Period[]).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                period === p ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
        {statsLoading ? (
          [...Array(8)].map((_, i) => (
            <div key={i} className="bg-white border rounded-lg p-3 sm:p-4 animate-pulse">
              <div className="w-7 h-7 bg-gray-200 rounded-lg mb-2" />
              <div className="h-7 bg-gray-200 rounded w-12 mb-1" />
              <div className="h-3 bg-gray-100 rounded w-20" />
            </div>
          ))
        ) : (
          cards.map((card) => {
            const Icon = card.icon;
            const content = (
              <div className="bg-white border rounded-lg p-3 sm:p-4">
                <div className="flex items-center justify-between mb-1 sm:mb-2">
                  <div className={`w-7 h-7 sm:w-8 sm:h-8 ${card.bg} rounded-lg flex items-center justify-center`}>
                    <Icon className={`w-3.5 h-3.5 sm:w-4 sm:h-4 ${card.color}`} />
                  </div>
                  {"comp" in card && card.comp && <ChangeBadge comparison={card.comp} />}
                </div>
                <span className="text-xl sm:text-2xl font-bold text-gray-900 block">{card.value.toLocaleString("pl-PL")}</span>
                <p className="text-xs text-gray-500 mt-0.5 truncate">{card.label}</p>
              </div>
            );
            return card.href ? (
              <Link key={card.label} href={card.href}>{content}</Link>
            ) : (
              <div key={card.label}>{content}</div>
            );
          })
        )}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
        <div className="bg-white border rounded-lg p-4 sm:p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 sm:mb-4">Nowi użytkownicy i oferty</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorJobs" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tickFormatter={(v) => String(v).slice(5)}
                tick={{ fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} width={30} />
              <Tooltip
                labelFormatter={(v) => String(v)}
                contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
              />
              <Area type="monotone" dataKey="new_users" name="Użytkownicy" stroke="#3b82f6" fill="url(#colorUsers)" strokeWidth={2} />
              <Area type="monotone" dataKey="new_jobs" name="Oferty" stroke="#22c55e" fill="url(#colorJobs)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white border rounded-lg p-4 sm:p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 sm:mb-4">Aplikacje</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorApps" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tickFormatter={(v) => String(v).slice(5)}
                tick={{ fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} width={30} />
              <Tooltip
                labelFormatter={(v) => String(v)}
                contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
              />
              <Area type="monotone" dataKey="new_applications" name="Aplikacje" stroke="#ef4444" fill="url(#colorApps)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Moderation banner */}
      {(stats?.pending_jobs ?? 0) > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-yellow-600" />
            <p className="font-medium text-yellow-800">
              {stats!.pending_jobs} ogłoszeń czeka na moderację
            </p>
          </div>
          <Link href="/panel/admin/moderacja" className="text-sm text-yellow-700 hover:underline mt-1 block">
            Przejdź do moderacji
          </Link>
        </div>
      )}

      {/* Quick nav */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <Link href="/panel/admin/moderacja" className="bg-white border rounded-lg p-5 hover:bg-gray-50 transition-colors group">
          <div className="flex items-center justify-between">
            <div>
              <Shield className="w-6 h-6 text-yellow-600 mb-2" />
              <h3 className="font-semibold text-gray-900">Moderacja</h3>
              <p className="text-sm text-gray-500">Zatwierdzaj i odrzucaj ogłoszenia</p>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors" />
          </div>
        </Link>
        <Link href="/panel/admin/uzytkownicy" className="bg-white border rounded-lg p-5 hover:bg-gray-50 transition-colors group">
          <div className="flex items-center justify-between">
            <div>
              <Users className="w-6 h-6 text-blue-600 mb-2" />
              <h3 className="font-semibold text-gray-900">Użytkownicy</h3>
              <p className="text-sm text-gray-500">Zarządzaj kontami użytkowników</p>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors" />
          </div>
        </Link>
        <Link href="/panel/admin/kategorie" className="bg-white border rounded-lg p-5 hover:bg-gray-50 transition-colors group">
          <div className="flex items-center justify-between">
            <div>
              <Briefcase className="w-6 h-6 text-green-600 mb-2" />
              <h3 className="font-semibold text-gray-900">Kategorie</h3>
              <p className="text-sm text-gray-500">Zarządzaj kategoriami ofert</p>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors" />
          </div>
        </Link>
        <Link href="/panel/admin/baza-cv" className="bg-white border rounded-lg p-5 hover:bg-gray-50 transition-colors group">
          <div className="flex items-center justify-between">
            <div>
              <FileSearch className="w-6 h-6 text-indigo-600 mb-2" />
              <h3 className="font-semibold text-gray-900">Baza CV</h3>
              <p className="text-sm text-gray-500">Przeglądaj CV kandydatów</p>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors" />
          </div>
        </Link>
      </div>
    </div>
  );
}
