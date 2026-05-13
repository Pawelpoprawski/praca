"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Send, Eye, CheckCircle, XCircle } from "lucide-react";
import api from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { APPLICATION_STATUSES, formatDate } from "@/lib/utils";
import type { Application, PaginatedResponse } from "@/types/api";

export default function WorkerDashboard() {
  const user = useAuthStore((s) => s.user);

  const { data, isLoading } = useQuery({
    queryKey: ["worker-applications"],
    queryFn: () =>
      api.get<PaginatedResponse<Application>>("/worker/applications", {
        params: { per_page: 5 },
      }).then((r) => r.data),
  });

  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ["worker-applications-stats"],
    queryFn: () =>
      api
        .get<{ sent: number; viewed: number; accepted: number; rejected: number; total: number }>(
          "/worker/applications/stats",
        )
        .then((r) => r.data),
  });

  const stats = {
    sent: statsData?.sent ?? 0,
    viewed: statsData?.viewed ?? 0,
    accepted: statsData?.accepted ?? 0,
    rejected: statsData?.rejected ?? 0,
  };

  return (
    <div>
      <h1 className="text-xl sm:text-2xl font-bold font-display text-[#0D2240] mb-6">
        Witaj, {user?.first_name || "Pracowniku"}!
      </h1>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
        {statsLoading ? (
          <>
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white border rounded-lg p-3 sm:p-4 animate-pulse">
                <div className="h-7 bg-gray-200 rounded w-12 mb-2" />
                <div className="h-3 bg-gray-100 rounded w-20" />
              </div>
            ))}
          </>
        ) : (
          <>
            <div className="bg-white border rounded-lg p-3 sm:p-4">
              <div className="flex items-center gap-2 text-blue-600 mb-1">
                <Send className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="text-xl sm:text-2xl font-bold">{stats.sent}</span>
              </div>
              <p className="text-xs text-gray-500 truncate">Wysłane</p>
            </div>
            <div className="bg-white border rounded-lg p-3 sm:p-4">
              <div className="flex items-center gap-2 text-yellow-600 mb-1">
                <Eye className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="text-xl sm:text-2xl font-bold">{stats.viewed}</span>
              </div>
              <p className="text-xs text-gray-500 truncate">Przeglądane</p>
            </div>
            <div className="bg-white border rounded-lg p-3 sm:p-4">
              <div className="flex items-center gap-2 text-green-600 mb-1">
                <CheckCircle className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="text-xl sm:text-2xl font-bold">{stats.accepted}</span>
              </div>
              <p className="text-xs text-gray-500 truncate">Zaakceptowane</p>
            </div>
            <div className="bg-white border rounded-lg p-3 sm:p-4">
              <div className="flex items-center gap-2 text-[#E1002A] mb-1">
                <XCircle className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="text-xl sm:text-2xl font-bold">{stats.rejected}</span>
              </div>
              <p className="text-xs text-gray-500 truncate">Odrzucone</p>
            </div>
          </>
        )}
      </div>

      {/* Recent applications */}
      <div className="bg-white border rounded-lg">
        <div className="px-5 py-4 border-b flex justify-between items-center">
          <h2 className="font-semibold font-display text-[#0D2240]">Ostatnie aplikacje</h2>
          <Link href="/panel/pracownik/aplikacje" className="text-sm text-[#E1002A] hover:underline">
            Zobacz wszystkie
          </Link>
        </div>
        {isLoading ? (
          <ul className="divide-y">
            {[...Array(3)].map((_, i) => (
              <li key={i} className="px-5 py-3 animate-pulse flex items-center justify-between">
                <div>
                  <div className="h-4 bg-gray-200 rounded w-40 mb-2" />
                  <div className="h-3 bg-gray-100 rounded w-24" />
                </div>
                <div className="h-5 bg-gray-100 rounded w-16" />
              </li>
            ))}
          </ul>
        ) : data?.data && data.data.length > 0 ? (
          <ul className="divide-y">
            {data.data.map((app) => {
              const statusInfo = APPLICATION_STATUSES[app.status] || { label: app.status, color: "bg-gray-100 text-gray-800" };
              return (
                <li key={app.id} className="px-5 py-3 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{app.job_title || "Oferta"}</p>
                    <p className="text-sm text-gray-500">{app.company_name}</p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-block text-xs px-2 py-0.5 rounded font-medium ${statusInfo.color}`}>
                      {statusInfo.label}
                    </span>
                    <p className="text-xs text-gray-400 mt-1">{formatDate(app.created_at)}</p>
                  </div>
                </li>
              );
            })}
          </ul>
        ) : (
          <div className="px-5 py-8 text-center text-gray-500 text-sm">
            Nie masz jeszcze żadnych aplikacji.{" "}
            <Link href="/oferty" className="text-[#E1002A] hover:underline">Przeglądaj oferty</Link>
          </div>
        )}
      </div>
    </div>
  );
}
