"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, ChevronLeft, ChevronRight } from "lucide-react";
import api from "@/services/api";
import type { PaginatedResponse, ActivityLogEntry } from "@/types/api";

const EVENT_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  cv_submitted: { label: "CV dodane", color: "bg-blue-100 text-blue-700" },
  cv_extraction_completed: { label: "CV ekstrakcja OK", color: "bg-green-100 text-green-700" },
  cv_extraction_failed: { label: "CV ekstrakcja fail", color: "bg-red-100 text-red-700" },
  job_ai_extracted: { label: "Oferta AI OK", color: "bg-green-100 text-green-700" },
  job_extraction_failed: { label: "Oferta AI fail", color: "bg-red-100 text-red-700" },
  job_created: { label: "Oferta dodana", color: "bg-indigo-100 text-indigo-700" },
  scraper_sync: { label: "Scraper sync", color: "bg-purple-100 text-purple-700" },
};

const ENTITY_FILTERS = [
  { value: "", label: "Wszystkie" },
  { value: "cv_database", label: "CV" },
  { value: "job_offer", label: "Oferty" },
  { value: "scraper", label: "Scraper" },
];

function EventBadge({ eventType }: { eventType: string }) {
  const info = EVENT_TYPE_LABELS[eventType] || { label: eventType, color: "bg-gray-100 text-gray-700" };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${info.color}`}>
      {info.label}
    </span>
  );
}

export default function AdminLogiPage() {
  const [page, setPage] = useState(1);
  const [entityType, setEntityType] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-activity-logs", page, entityType],
    queryFn: () =>
      api.get<PaginatedResponse<ActivityLogEntry>>("/admin/activity-logs", {
        params: {
          page,
          per_page: 30,
          ...(entityType && { entity_type: entityType }),
        },
      }).then((r) => r.data),
    refetchInterval: 30000,
  });

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Activity className="w-5 h-5 sm:w-6 sm:h-6 text-purple-600" />
            Logi aktywnosci
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {data?.total ?? 0} zdarzen (auto-odswiezanie co 30s)
          </p>
        </div>
      </div>

      {/* Entity type filter tabs */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {ENTITY_FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => { setEntityType(f.value); setPage(1); }}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              entityType === f.value
                ? "bg-purple-100 text-purple-700"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white border rounded-lg overflow-hidden overflow-x-auto">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Ladowanie...</div>
        ) : data?.data && data.data.length > 0 ? (
          <table className="w-full text-sm min-w-[600px]">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="text-left px-4 py-3 font-semibold text-gray-600 w-40">Czas</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 w-44">Typ</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Opis</th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((log) => (
                <tr key={log.id} className="border-b hover:bg-gray-50/50">
                  <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                    {log.created_at
                      ? new Date(log.created_at).toLocaleString("pl-PL", {
                          day: "2-digit", month: "2-digit", year: "numeric",
                          hour: "2-digit", minute: "2-digit", second: "2-digit",
                        })
                      : "-"}
                  </td>
                  <td className="px-4 py-3">
                    <EventBadge eventType={log.event_type} />
                  </td>
                  <td className="px-4 py-3 text-gray-700">
                    <p className="line-clamp-2">{log.summary}</p>
                    {log.details && (
                      <p className="text-xs text-gray-400 mt-0.5">
                        {JSON.stringify(log.details).slice(0, 120)}
                      </p>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-8 text-center text-gray-500">
            <Activity className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p className="font-medium">Brak logow</p>
            <p className="text-sm">Logi pojawia sie automatycznie po akcjach w systemie.</p>
          </div>
        )}
      </div>

      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-sm text-gray-500">
            Strona {data.page} z {data.pages} ({data.total} wynikow)
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage(Math.min(data.pages, page + 1))}
              disabled={page >= data.pages}
              className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
