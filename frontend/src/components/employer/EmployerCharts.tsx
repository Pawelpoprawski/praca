"use client";

import { useQuery } from "@tanstack/react-query";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { Briefcase, Users, TrendingUp } from "lucide-react";
import api from "@/services/api";
import type { EmployerChartsData } from "@/types/api";

const STATUS_COLORS: Record<string, string> = {
  pending: "#3b82f6",
  reviewed: "#f59e0b",
  accepted: "#22c55e",
  rejected: "#ef4444",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "Oczekujące",
  reviewed: "Przeglądane",
  accepted: "Zaakceptowane",
  rejected: "Odrzucone",
};

const BAR_COLORS = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6"];

function ChartSkeleton() {
  return (
    <div className="bg-white border rounded-lg p-5 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-1/3 mb-4" />
      <div className="h-[240px] bg-gray-100 rounded" />
    </div>
  );
}

function SummarySkeleton() {
  return (
    <div className="bg-white border rounded-lg p-4 animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-8 mb-2" />
      <div className="h-6 bg-gray-200 rounded w-12 mb-1" />
      <div className="h-3 bg-gray-100 rounded w-20" />
    </div>
  );
}

export default function EmployerCharts() {
  const { data: charts, isLoading } = useQuery({
    queryKey: ["employer-charts"],
    queryFn: () =>
      api.get<EmployerChartsData>("/employer/stats/charts").then((r) => r.data),
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <SummarySkeleton key={i} />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <ChartSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (!charts) return null;

  const { applications_over_time, top_jobs, application_status_breakdown, monthly_summary } = charts;

  // Prepare pie chart data
  const pieData = Object.entries(application_status_breakdown)
    .filter(([, value]) => value > 0)
    .map(([key, value]) => ({
      name: STATUS_LABELS[key] || key,
      value,
      color: STATUS_COLORS[key] || "#6b7280",
    }));

  const totalAppsInPie = pieData.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border rounded-lg p-4">
          <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center mb-2">
            <Briefcase className="w-4 h-4 text-blue-600" />
          </div>
          <span className="text-2xl font-bold text-[#0D2240]">
            {monthly_summary.total_jobs}
          </span>
          <p className="text-xs text-gray-500 mt-0.5">Wszystkie oferty</p>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="w-8 h-8 bg-green-50 rounded-lg flex items-center justify-center mb-2">
            <TrendingUp className="w-4 h-4 text-green-600" />
          </div>
          <span className="text-2xl font-bold text-[#0D2240]">
            {monthly_summary.active_jobs}
          </span>
          <p className="text-xs text-gray-500 mt-0.5">Aktywne oferty</p>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="w-8 h-8 bg-[#FFF0F3] rounded-lg flex items-center justify-center mb-2">
            <Users className="w-4 h-4 text-[#E1002A]" />
          </div>
          <span className="text-2xl font-bold text-[#0D2240]">
            {monthly_summary.total_applications}
          </span>
          <p className="text-xs text-gray-500 mt-0.5">Wszystkie aplikacje</p>
        </div>
      </div>

      {/* Charts grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Line chart - Applications over time */}
        <div className="bg-white border rounded-lg p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Aplikacje w czasie (ostatnie 30 dni)
          </h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={applications_over_time}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tickFormatter={(v) => String(v).slice(5)}
                tick={{ fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={30}
              />
              <Tooltip
                labelFormatter={(v) => String(v)}
                contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
              />
              <Line
                type="monotone"
                dataKey="count"
                name="Aplikacje"
                stroke="#ef4444"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Bar chart - Top 5 jobs */}
        <div className="bg-white border rounded-lg p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Top 5 ofert wg aplikacji
          </h3>
          {top_jobs.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart
                data={top_jobs}
                layout="vertical"
                margin={{ left: 0, right: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="job_title"
                  tick={{ fontSize: 11 }}
                  width={120}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => v.length > 18 ? v.slice(0, 18) + "..." : v}
                />
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
                />
                <Bar dataKey="applications" name="Aplikacje" radius={[0, 4, 4, 0]}>
                  {top_jobs.map((_, index) => (
                    <Cell key={index} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                  ))}
                </Bar>
                <Bar dataKey="views" name="Wyświetlenia" fill="#e5e7eb" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[240px] flex items-center justify-center text-sm text-gray-400">
              Brak danych
            </div>
          )}
        </div>

        {/* Pie chart - Status breakdown */}
        <div className="bg-white border rounded-lg p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Rozkład statusów aplikacji
          </h3>
          {totalAppsInPie > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
                  formatter={(value: number | undefined) => {
                    const v = value ?? 0;
                    return [`${v} (${Math.round((v / totalAppsInPie) * 100)}%)`, ""];
                  }}
                />
                <Legend
                  iconType="circle"
                  iconSize={8}
                  wrapperStyle={{ fontSize: 12 }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[240px] flex items-center justify-center text-sm text-gray-400">
              Brak aplikacji
            </div>
          )}
        </div>

        {/* Status breakdown detail card */}
        <div className="bg-white border rounded-lg p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Szczegóły statusów
          </h3>
          <div className="space-y-3">
            {Object.entries(application_status_breakdown).map(([key, value]) => {
              const total = Object.values(application_status_breakdown).reduce((s, v) => s + v, 0);
              const pct = total > 0 ? Math.round((value / total) * 100) : 0;
              return (
                <div key={key}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-gray-600">
                      {STATUS_LABELS[key] || key}
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {value} ({pct}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: STATUS_COLORS[key] || "#6b7280",
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
