"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Briefcase, Users, Send, BarChart3 } from "lucide-react";
import api from "@/services/api";
import type { EmployerDashboard, QuotaInfo } from "@/types/api";
import { useAuthStore } from "@/store/authStore";

export default function EmployerDashboardPage() {
  const user = useAuthStore((s) => s.user);

  const { data: dashboard } = useQuery({
    queryKey: ["employer-dashboard"],
    queryFn: () => api.get<EmployerDashboard>("/employer/dashboard").then((r) => r.data),
  });

  const { data: quota } = useQuery({
    queryKey: ["employer-quota"],
    queryFn: () => api.get<QuotaInfo>("/employer/quota").then((r) => r.data),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        Witaj, {user?.first_name || "Pracodawco"}!
      </h1>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center gap-2 text-blue-600 mb-1">
            <Briefcase className="w-4 h-4" />
            <span className="text-2xl font-bold">{dashboard?.active_jobs ?? 0}</span>
          </div>
          <p className="text-xs text-gray-500">Aktywne ogłoszenia</p>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center gap-2 text-green-600 mb-1">
            <Users className="w-4 h-4" />
            <span className="text-2xl font-bold">{dashboard?.total_applications ?? 0}</span>
          </div>
          <p className="text-xs text-gray-500">Wszystkie aplikacje</p>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center gap-2 text-yellow-600 mb-1">
            <Send className="w-4 h-4" />
            <span className="text-2xl font-bold">{dashboard?.new_applications ?? 0}</span>
          </div>
          <p className="text-xs text-gray-500">Nowe aplikacje</p>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center gap-2 text-purple-600 mb-1">
            <BarChart3 className="w-4 h-4" />
            <span className="text-2xl font-bold">
              {dashboard ? `${dashboard.quota_used}/${dashboard.quota_limit}` : "0/0"}
            </span>
          </div>
          <p className="text-xs text-gray-500">Limit ogłoszeń</p>
        </div>
      </div>

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

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
