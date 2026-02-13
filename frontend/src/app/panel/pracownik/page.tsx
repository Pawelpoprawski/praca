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

  const { data } = useQuery({
    queryKey: ["worker-applications"],
    queryFn: () =>
      api.get<PaginatedResponse<Application>>("/worker/applications", {
        params: { per_page: 5 },
      }).then((r) => r.data),
  });

  const stats = {
    sent: data?.data.filter((a) => a.status === "sent").length || 0,
    viewed: data?.data.filter((a) => a.status === "viewed").length || 0,
    accepted: data?.data.filter((a) => a.status === "accepted" || a.status === "shortlisted").length || 0,
    rejected: data?.data.filter((a) => a.status === "rejected").length || 0,
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        Witaj, {user?.first_name || "Pracowniku"}!
      </h1>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center gap-2 text-blue-600 mb-1">
            <Send className="w-4 h-4" />
            <span className="text-2xl font-bold">{stats.sent}</span>
          </div>
          <p className="text-xs text-gray-500">Wysłane</p>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center gap-2 text-yellow-600 mb-1">
            <Eye className="w-4 h-4" />
            <span className="text-2xl font-bold">{stats.viewed}</span>
          </div>
          <p className="text-xs text-gray-500">Przeglądane</p>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center gap-2 text-green-600 mb-1">
            <CheckCircle className="w-4 h-4" />
            <span className="text-2xl font-bold">{stats.accepted}</span>
          </div>
          <p className="text-xs text-gray-500">Zaakceptowane</p>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-600 mb-1">
            <XCircle className="w-4 h-4" />
            <span className="text-2xl font-bold">{stats.rejected}</span>
          </div>
          <p className="text-xs text-gray-500">Odrzucone</p>
        </div>
      </div>

      {/* Recent applications */}
      <div className="bg-white border rounded-lg">
        <div className="px-5 py-4 border-b flex justify-between items-center">
          <h2 className="font-semibold text-gray-900">Ostatnie aplikacje</h2>
          <Link href="/panel/pracownik/aplikacje" className="text-sm text-red-600 hover:underline">
            Zobacz wszystkie
          </Link>
        </div>
        {data?.data && data.data.length > 0 ? (
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
            <Link href="/oferty" className="text-red-600 hover:underline">Przeglądaj oferty</Link>
          </div>
        )}
      </div>
    </div>
  );
}
