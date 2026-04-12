"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Briefcase, Users, Send, BarChart3, Eye, MousePointerClick } from "lucide-react";
import api from "@/services/api";
import type { EmployerDashboard, QuotaInfo } from "@/types/api";
import { useAuthStore } from "@/store/authStore";
import EmployerCharts from "@/components/employer/EmployerCharts";

export default function EmployerDashboardPage() {
  const user = useAuthStore((s) => s.user);

  const { data: dashboard, isLoading: dashLoading } = useQuery({
    queryKey: ["employer-dashboard"],
    queryFn: () => api.get<EmployerDashboard>("/employer/dashboard").then((r) => r.data),
  });

  const { data: quota } = useQuery({
    queryKey: ["employer-quota"],
    queryFn: () => api.get<QuotaInfo>("/employer/quota").then((r) => r.data),
  });

  return (
    <div>
      <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-6">
        Witaj, {user?.first_name || "Pracodawco"}!
      </h1>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mb-6 sm:mb-8">
        {dashLoading ? (
          [...Array(6)].map((_, i) => (
            <div key={i} className="bg-white border rounded-lg p-3 sm:p-4 animate-pulse">
              <div className="h-7 bg-gray-200 rounded w-12 mb-2" />
              <div className="h-3 bg-gray-100 rounded w-24" />
            </div>
          ))
        ) : (
          <>
            <Link href="/panel/pracodawca/ogloszenia" className="bg-white border rounded-lg p-3 sm:p-4 hover:shadow-md hover:border-blue-200 transition-all">
              <div className="flex items-center gap-2 text-blue-600 mb-1">
                <Briefcase className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="text-xl sm:text-2xl font-bold">{dashboard?.active_jobs ?? 0}</span>
              </div>
              <p className="text-xs text-gray-500 truncate">Aktywne ogłoszenia</p>
            </Link>
            <Link href="/panel/pracodawca/ogloszenia" className="bg-white border rounded-lg p-3 sm:p-4 hover:shadow-md hover:border-green-200 transition-all">
              <div className="flex items-center gap-2 text-green-600 mb-1">
                <Users className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="text-xl sm:text-2xl font-bold">{dashboard?.total_applications ?? 0}</span>
              </div>
              <p className="text-xs text-gray-500 truncate">Wszystkie aplikacje</p>
            </Link>
            <Link href="/panel/pracodawca/ogloszenia" className="bg-white border rounded-lg p-3 sm:p-4 hover:shadow-md hover:border-yellow-200 transition-all">
              <div className="flex items-center gap-2 text-yellow-600 mb-1">
                <Send className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="text-xl sm:text-2xl font-bold">{dashboard?.new_applications ?? 0}</span>
              </div>
              <p className="text-xs text-gray-500 truncate">Nowe aplikacje</p>
            </Link>
            <div className="bg-white border rounded-lg p-3 sm:p-4">
              <div className="flex items-center gap-2 text-indigo-600 mb-1">
                <Eye className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="text-xl sm:text-2xl font-bold">{dashboard?.total_views ?? 0}</span>
              </div>
              <p className="text-xs text-gray-500 truncate">Wyświetlenia ofert</p>
            </div>
            <div className="bg-white border rounded-lg p-3 sm:p-4">
              <div className="flex items-center gap-2 text-orange-600 mb-1">
                <MousePointerClick className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="text-xl sm:text-2xl font-bold">{dashboard?.total_clicks ?? 0}</span>
              </div>
              <p className="text-xs text-gray-500 truncate">Kliknięcia „Aplikuj"</p>
            </div>
            <div className="bg-white border rounded-lg p-3 sm:p-4">
              <div className="flex items-center gap-2 text-purple-600 mb-1">
                <BarChart3 className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="text-xl sm:text-2xl font-bold">
                  {dashboard ? `${dashboard.quota_used}/${dashboard.quota_limit}` : "—"}
                </span>
              </div>
              <p className="text-xs text-gray-500 truncate">Limit ogłoszeń</p>
            </div>
          </>
        )}
      </div>

      {/* Application clicks breakdown */}
      {dashboard && dashboard.total_clicks > 0 && (
        <div className="bg-white border rounded-lg p-5 mb-6">
          <h2 className="font-semibold text-gray-900 mb-3">Rozbicie kliknięć „Aplikuj"</h2>
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <p className="text-lg font-bold text-blue-700">{dashboard.clicks_by_type?.portal ?? 0}</p>
              <p className="text-xs text-blue-600">Przez portal</p>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <p className="text-lg font-bold text-green-700">{dashboard.clicks_by_type?.external ?? 0}</p>
              <p className="text-xs text-green-600">Zewnętrzny link</p>
            </div>
            <div className="text-center p-3 bg-yellow-50 rounded-lg">
              <p className="text-lg font-bold text-yellow-700">{dashboard.clicks_by_type?.email ?? 0}</p>
              <p className="text-xs text-yellow-600">Email</p>
            </div>
          </div>
        </div>
      )}

      {/* Quota info */}
      {quota && (
        <div className="bg-white border rounded-lg p-5 mb-6">
          <h2 className="font-semibold text-gray-900 mb-3">Limit ogłoszeń</h2>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
            <div
              className="bg-red-600 h-2 rounded-full transition-all"
              style={{ width: `${Math.min(100, (quota.used_count / quota.monthly_limit) * 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-sm text-gray-500">
            <span>Wykorzystane: {quota.used_count} z {quota.monthly_limit}</span>
            <span>Reset za {quota.days_until_reset} dni</span>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Statystyki</h2>
        <EmployerCharts />
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        <Link
          href="/panel/pracodawca/ogloszenia/nowe"
          className="bg-red-600 text-white rounded-lg p-5 hover:bg-red-700 transition-colors"
        >
          <h3 className="font-semibold mb-1">Dodaj ogłoszenie</h3>
          <p className="text-sm text-red-100">Opublikuj nową ofertę pracy</p>
        </Link>
        <Link
          href="/panel/pracodawca/ogloszenia"
          className="bg-white border rounded-lg p-5 hover:bg-gray-50 transition-colors"
        >
          <h3 className="font-semibold text-gray-900 mb-1">Moje ogłoszenia</h3>
          <p className="text-sm text-gray-500">Zarządzaj swoimi ofertami</p>
        </Link>
      </div>
    </div>
  );
}
