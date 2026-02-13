"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import {
  Search, FileText, ChevronLeft, ChevronRight,
  CheckCircle, XCircle, Clock, Globe,
} from "lucide-react";
import api from "@/services/api";
import { formatDate } from "@/lib/utils";
import type { PaginatedResponse, AdminCVItem, CVStats } from "@/types/api";

const STATUS_BADGES: Record<string, { label: string; color: string; icon: typeof CheckCircle }> = {
  completed: { label: "Odczytano", color: "bg-green-100 text-green-800", icon: CheckCircle },
  failed: { label: "Błąd", color: "bg-red-100 text-red-800", icon: XCircle },
  pending: { label: "Oczekuje", color: "bg-yellow-100 text-yellow-800", icon: Clock },
};

export default function AdminCVPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: stats } = useQuery({
    queryKey: ["admin-cv-stats"],
    queryFn: () => api.get<CVStats>("/admin/cv-stats").then((r) => r.data),
  });

  const { data, isLoading } = useQuery({
    queryKey: ["admin-cvs", page, searchQuery],
    queryFn: () =>
      api.get<PaginatedResponse<AdminCVItem>>("/admin/cvs", {
        params: {
          page, per_page: 20,
          ...(searchQuery && { q: searchQuery }),
        },
      }).then((r) => r.data),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchQuery(search);
    setPage(1);
  };

  const statCards = [
    { label: "Wszystkie CV", value: stats?.total ?? 0, color: "text-blue-600" },
    { label: "Aktywne", value: stats?.active ?? 0, color: "text-green-600" },
    { label: "Odczytane", value: stats?.extracted ?? 0, color: "text-emerald-600" },
    { label: "Błędy", value: stats?.failed ?? 0, color: "text-red-600" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Baza CV</h1>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {statCards.map((card) => (
          <div key={card.label} className="bg-white border rounded-lg p-4">
            <div className={`flex items-center gap-2 ${card.color} mb-1`}>
              <FileText className="w-4 h-4" />
              <span className="text-2xl font-bold">{card.value}</span>
            </div>
            <p className="text-xs text-gray-500">{card.label}</p>
          </div>
        ))}
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Szukaj po nazwisku, emailu..."
            className="w-full pl-10 pr-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500"
          />
        </div>
        <button type="submit" className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700">
          Szukaj
        </button>
      </form>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="animate-pulse h-14 bg-gray-100 rounded-lg" />
          ))}
        </div>
      ) : data?.data && data.data.length > 0 ? (
        <>
          <div className="bg-white border rounded-lg overflow-hidden overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Użytkownik</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Plik CV</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Dane z CV</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Języki</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Data</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.data.map((cv) => {
                  const statusInfo = STATUS_BADGES[cv.extraction_status] || STATUS_BADGES.pending;
                  const StatusIcon = statusInfo.icon;
                  return (
                    <tr key={cv.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900">{cv.user_name || "—"}</p>
                        <p className="text-gray-500 text-xs">{cv.user_email}</p>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-gray-400" />
                          <div>
                            <p className="text-gray-900 truncate max-w-[200px]">{cv.original_filename}</p>
                            <p className="text-gray-400 text-xs">
                              {(cv.file_size / 1024).toFixed(0)} KB
                              {cv.is_active && (
                                <span className="ml-1 text-green-600">&bull; aktywne</span>
                              )}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded font-medium ${statusInfo.color}`}>
                          <StatusIcon className="w-3 h-3" />
                          {statusInfo.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {cv.extraction_status === "completed" ? (
                          <div className="space-y-0.5">
                            {cv.extracted_name && (
                              <p className="text-gray-900 text-xs">{cv.extracted_name}</p>
                            )}
                            {cv.extracted_email && (
                              <p className="text-gray-500 text-xs">{cv.extracted_email}</p>
                            )}
                            {cv.extracted_phone && (
                              <p className="text-gray-500 text-xs">{cv.extracted_phone}</p>
                            )}
                          </div>
                        ) : (
                          <span className="text-gray-400 text-xs">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {cv.extracted_languages && cv.extracted_languages.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {cv.extracted_languages.map((lang, i) => (
                              <span
                                key={i}
                                className="inline-flex items-center gap-0.5 text-xs bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded"
                              >
                                <Globe className="w-3 h-3" />
                                {lang.lang.toUpperCase()} {lang.level}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-gray-400 text-xs">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                        {cv.created_at ? formatDate(cv.created_at) : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {data.pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-500">
                Strona {data.page} z {data.pages} ({data.total} CV)
              </p>
              <div className="flex gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-30"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                  disabled={page >= data.pages}
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-30"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="bg-white border rounded-lg px-5 py-12 text-center">
          <FileText className="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <p className="text-gray-500">Brak przesłanych CV</p>
        </div>
      )}
    </div>
  );
}
