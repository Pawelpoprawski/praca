"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Search, ChevronLeft, ChevronRight, Briefcase, Filter, Eye,
} from "lucide-react";
import api from "@/services/api";
import type { PaginatedResponse, AdminJobBrowserItem, AdminCategory } from "@/types/api";

const CANTON_LABELS: Record<string, string> = {
  AG: "Argovia", AI: "Appenzell I.Rh.", AR: "Appenzell A.Rh.", BE: "Berno",
  BL: "Bazylea-okr.", BS: "Bazylea-m.", FR: "Fryburg", GE: "Genewa",
  GL: "Glarus", GR: "Gryzonia", JU: "Jura", LU: "Lucerna",
  NE: "Neuchatel", NW: "Nidwalden", OW: "Obwalden", SG: "St. Gallen",
  SH: "Szafuza", SO: "Solura", SZ: "Schwyz", TG: "Turgowia",
  TI: "Ticino", UR: "Uri", VD: "Vaud", VS: "Valais",
  ZG: "Zug", ZH: "Zurych",
};

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    active: "bg-green-100 text-green-700",
    pending: "bg-yellow-100 text-yellow-700",
    expired: "bg-gray-100 text-gray-600",
    rejected: "bg-[#FFE0E6] text-[#B8001F]",
  };
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${colors[status] || "bg-gray-100 text-gray-600"}`}>
      {status}
    </span>
  );
}

function SourceBadge({ source }: { source: string | null }) {
  if (!source) return <span className="text-gray-400 text-xs">portal</span>;
  const colors: Record<string, string> = {
    JOBSPL: "bg-blue-100 text-blue-700",
    FACHPRACA: "bg-purple-100 text-purple-700",
    ROLJOB: "bg-orange-100 text-orange-700",
    ADECCO: "bg-teal-100 text-teal-700",
  };
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${colors[source] || "bg-gray-100 text-gray-600"}`}>
      {source}
    </span>
  );
}

export default function AdminOfertyPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [canton, setCanton] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [sourceName, setSourceName] = useState("");
  const [aiExtracted, setAiExtracted] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [selectedJob, setSelectedJob] = useState<AdminJobBrowserItem | null>(null);

  const { data: categories } = useQuery({
    queryKey: ["admin-categories"],
    queryFn: () => api.get<AdminCategory[]>("/admin/categories").then((r) => r.data),
  });

  const { data, isLoading } = useQuery({
    queryKey: ["admin-jobs-browser", page, search, canton, categoryId, sourceName, aiExtracted, statusFilter],
    queryFn: () =>
      api.get<PaginatedResponse<AdminJobBrowserItem>>("/admin/jobs-browser", {
        params: {
          page,
          per_page: 20,
          ...(search && { q: search }),
          ...(canton && { canton }),
          ...(categoryId && { category_id: categoryId }),
          ...(sourceName && { source_name: sourceName }),
          ...(aiExtracted !== "" && { ai_extracted: aiExtracted === "true" }),
          ...(statusFilter && { status: statusFilter }),
        },
      }).then((r) => r.data),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold font-display text-[#0D2240] flex items-center gap-2">
            <Briefcase className="w-5 h-5 sm:w-6 sm:h-6 text-indigo-600" />
            Przegladarka ofert
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {data?.total ?? 0} ofert
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            showFilters ? "bg-indigo-100 text-indigo-700" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          <Filter className="w-4 h-4" />
          Filtry
        </button>
      </div>

      {/* Search & Filters */}
      <div className="bg-white border rounded-lg p-3 sm:p-4 mb-6">
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Szukaj po tytule, AI keywords, opisie..."
              className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />
          </div>
          <button
            type="submit"
            className="bg-indigo-600 text-white px-6 py-2.5 rounded-lg text-sm font-semibold hover:bg-indigo-700 transition-colors w-full sm:w-auto"
          >
            Szukaj
          </button>
        </form>

        {showFilters && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mt-4 pt-4 border-t">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Kanton</label>
              <select
                value={canton}
                onChange={(e) => { setCanton(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              >
                <option value="">Wszystkie</option>
                {Object.entries(CANTON_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v} ({k})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Kategoria</label>
              <select
                value={categoryId}
                onChange={(e) => { setCategoryId(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              >
                <option value="">Wszystkie</option>
                {categories?.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Zrodlo</label>
              <select
                value={sourceName}
                onChange={(e) => { setSourceName(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              >
                <option value="">Wszystkie</option>
                <option value="JOBSPL">JOBSPL</option>
                <option value="FACHPRACA">FACHPRACA</option>
                <option value="ROLJOB">ROLJOB</option>
                <option value="ADECCO">ADECCO</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">AI</label>
              <select
                value={aiExtracted}
                onChange={(e) => { setAiExtracted(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              >
                <option value="">Wszystkie</option>
                <option value="true">Przetworzone</option>
                <option value="false">Nieprzetworzone</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              >
                <option value="">Wszystkie</option>
                <option value="active">Aktywne</option>
                <option value="pending">Oczekujace</option>
                <option value="expired">Wygasle</option>
                <option value="rejected">Odrzucone</option>
              </select>
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-col lg:flex-row gap-4 lg:gap-6">
        {/* Table */}
        <div className="flex-1 min-w-0">
          <div className="bg-white border rounded-lg overflow-hidden overflow-x-auto">
            {isLoading ? (
              <div className="p-8 text-center text-gray-500">Ladowanie...</div>
            ) : data?.data && data.data.length > 0 ? (
              <table className="w-full text-sm min-w-[800px]">
                <thead>
                  <tr className="bg-gray-50 border-b">
                    <th className="text-left px-4 py-3 font-semibold text-gray-600">Tytul</th>
                    <th className="text-left px-4 py-3 font-semibold text-gray-600">Firma</th>
                    <th className="text-left px-4 py-3 font-semibold text-gray-600">Kanton</th>
                    <th className="text-center px-4 py-3 font-semibold text-gray-600">AI</th>
                    <th className="text-center px-4 py-3 font-semibold text-gray-600">Zrodlo</th>
                    <th className="text-center px-4 py-3 font-semibold text-gray-600">Status</th>
                    <th className="text-right px-4 py-3 font-semibold text-gray-600">Wynagrodzenie</th>
                    <th className="text-right px-4 py-3 font-semibold text-gray-600">Data</th>
                  </tr>
                </thead>
                <tbody>
                  {data.data.map((job) => (
                    <tr
                      key={job.id}
                      className={`border-b hover:bg-indigo-50/30 cursor-pointer transition-colors ${
                        selectedJob?.id === job.id ? "bg-indigo-50" : ""
                      }`}
                      onClick={() => setSelectedJob(job)}
                    >
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900 line-clamp-1 max-w-[220px]">{job.title}</p>
                        {job.category_name && (
                          <p className="text-xs text-gray-500">{job.category_name}</p>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-700 text-xs max-w-[140px] truncate">
                        {job.company_name || "-"}
                      </td>
                      <td className="px-4 py-3 text-gray-600 text-xs">{job.canton}</td>
                      <td className="px-4 py-3 text-center">
                        {job.ai_extracted ? (
                          <span className="inline-flex w-5 h-5 items-center justify-center rounded-full bg-green-100 text-green-600 text-xs font-bold">&#10003;</span>
                        ) : (
                          <span className="inline-flex w-5 h-5 items-center justify-center rounded-full bg-gray-100 text-gray-400 text-xs">&ndash;</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <SourceBadge source={job.source_name} />
                      </td>
                      <td className="px-4 py-3 text-center">
                        <StatusBadge status={job.status} />
                      </td>
                      <td className="px-4 py-3 text-right text-xs text-gray-600">
                        {job.salary_min && job.salary_max
                          ? `${job.salary_min}-${job.salary_max}`
                          : job.salary_min
                            ? `od ${job.salary_min}`
                            : job.salary_max
                              ? `do ${job.salary_max}`
                              : "-"}
                      </td>
                      <td className="px-4 py-3 text-right text-xs text-gray-500 whitespace-nowrap">
                        {job.created_at
                          ? new Date(job.created_at).toLocaleDateString("pl-PL")
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-8 text-center text-gray-500">
                <Briefcase className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p className="font-medium">Brak ofert</p>
                <p className="text-sm">Zmien filtry, aby zobaczyc oferty.</p>
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

        {/* Detail side panel */}
        {selectedJob && (
          <div className="lg:w-96 bg-white border rounded-lg p-4 sm:p-5 lg:sticky lg:top-4 max-h-[600px] lg:max-h-[calc(100vh-120px)] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-gray-900">Szczegoly oferty</h3>
              <button onClick={() => setSelectedJob(null)} className="text-gray-400 hover:text-gray-600">&times;</button>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-lg font-bold text-gray-900">{selectedJob.title}</p>
                {selectedJob.company_name && (
                  <p className="text-sm text-gray-600">{selectedJob.company_name}</p>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                <StatusBadge status={selectedJob.status} />
                <SourceBadge source={selectedJob.source_name} />
                {selectedJob.ai_extracted && (
                  <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">AI OK</span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-gray-500">Kanton</p>
                  <p className="text-gray-700">{CANTON_LABELS[selectedJob.canton] || selectedJob.canton}</p>
                </div>
                {selectedJob.city && (
                  <div>
                    <p className="text-xs text-gray-500">Miasto</p>
                    <p className="text-gray-700">{selectedJob.city}</p>
                  </div>
                )}
                {selectedJob.category_name && (
                  <div>
                    <p className="text-xs text-gray-500">Kategoria</p>
                    <p className="text-gray-700">{selectedJob.category_name}</p>
                  </div>
                )}
                <div>
                  <p className="text-xs text-gray-500">Wyswietlenia</p>
                  <p className="text-gray-700">{selectedJob.views_count}</p>
                </div>
              </div>

              {(selectedJob.salary_min || selectedJob.salary_max) && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Wynagrodzenie</p>
                  <p className="text-sm text-gray-700">
                    {selectedJob.salary_min && selectedJob.salary_max
                      ? `${selectedJob.salary_min.toLocaleString("pl-PL")} - ${selectedJob.salary_max.toLocaleString("pl-PL")} CHF`
                      : selectedJob.salary_min
                        ? `od ${selectedJob.salary_min.toLocaleString("pl-PL")} CHF`
                        : `do ${selectedJob.salary_max!.toLocaleString("pl-PL")} CHF`
                    }
                    {selectedJob.salary_type !== "monthly" && ` (${selectedJob.salary_type})`}
                  </p>
                </div>
              )}

              {selectedJob.ai_keywords && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">AI Keywords</p>
                  <div className="flex flex-wrap gap-1">
                    {selectedJob.ai_keywords.split(";").filter(Boolean).map((kw, i) => (
                      <span key={i} className="bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded text-xs">
                        {kw.trim()}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="text-xs text-gray-400">
                Dodano: {selectedJob.created_at ? new Date(selectedJob.created_at).toLocaleString("pl-PL") : "-"}
              </div>

              <a
                href={`/oferty/${selectedJob.id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white py-2.5 rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
              >
                <Eye className="w-4 h-4" />
                Zobacz oferte
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
