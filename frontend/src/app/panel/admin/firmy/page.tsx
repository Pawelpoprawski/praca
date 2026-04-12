"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Search, ChevronLeft, ChevronRight, Building2, Eye, CheckCircle2,
  XCircle, ExternalLink, Save, Loader2,
} from "lucide-react";
import api from "@/services/api";
import type {
  PaginatedResponse, AdminCompanyListItem, AdminCompanyDetail,
  MessageResponse,
} from "@/types/api";

const STATUS_BADGE: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  pending: "bg-yellow-100 text-yellow-700",
  rejected: "bg-red-100 text-red-700",
  expired: "bg-gray-100 text-gray-500",
};

function VerifiedBadge({ verified }: { verified: boolean }) {
  if (verified) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-700">
        <CheckCircle2 className="w-3 h-3" />
        Zweryfikowana
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-500">
      <XCircle className="w-3 h-3" />
      Niezweryfikowana
    </span>
  );
}

function QuotaDisplay({ limit, used, custom }: { limit: number | null; used: number; custom: number | null }) {
  const effectiveLimit = custom ?? limit;
  if (effectiveLimit == null) {
    return <span className="text-gray-400 text-sm">-</span>;
  }
  const pct = effectiveLimit > 0 ? Math.round((used / effectiveLimit) * 100) : 0;
  const color = pct >= 90 ? "text-red-600" : pct >= 60 ? "text-yellow-600" : "text-green-600";
  return (
    <span className={`text-sm font-medium ${color}`}>
      {used}/{effectiveLimit}
    </span>
  );
}

export default function AdminCompaniesPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Quota edit state
  const [editMonthly, setEditMonthly] = useState<string>("");
  const [editCustom, setEditCustom] = useState<string>("");
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-companies", page, search],
    queryFn: () =>
      api
        .get<PaginatedResponse<AdminCompanyListItem>>("/admin/companies", {
          params: {
            page,
            per_page: 20,
            ...(search && { q: search }),
          },
        })
        .then((r) => r.data),
  });

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ["admin-company-detail", selectedId],
    queryFn: () =>
      api
        .get<AdminCompanyDetail>(`/admin/companies/${selectedId}`)
        .then((r) => r.data),
    enabled: !!selectedId,
  });

  // When detail loads, populate edit fields
  const populateEditFields = (d: AdminCompanyDetail) => {
    setEditMonthly(d.quota?.monthly_limit?.toString() ?? "");
    setEditCustom(d.quota?.custom_limit?.toString() ?? "");
  };

  // Update quota mutation
  const quotaMutation = useMutation({
    mutationFn: (params: { companyId: string; monthly_limit: number; custom_limit?: number }) =>
      api
        .put<MessageResponse>(`/admin/companies/${params.companyId}/quota`, null, {
          params: {
            monthly_limit: params.monthly_limit,
            ...(params.custom_limit !== undefined && { custom_limit: params.custom_limit }),
          },
        })
        .then((r) => r.data),
    onSuccess: (resp) => {
      setSuccessMsg(resp.message);
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ["admin-companies"] });
      queryClient.invalidateQueries({ queryKey: ["admin-company-detail", selectedId] });
    },
    onError: () => {
      setErrorMsg("Nie udalo sie zaktualizowac limitu");
      setSuccessMsg(null);
    },
  });

  // Verify mutation
  const verifyMutation = useMutation({
    mutationFn: (params: { companyId: string; is_verified: boolean }) =>
      api
        .put<MessageResponse>(`/admin/companies/${params.companyId}/verify`, null, {
          params: { is_verified: params.is_verified },
        })
        .then((r) => r.data),
    onSuccess: (resp) => {
      setSuccessMsg(resp.message);
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ["admin-companies"] });
      queryClient.invalidateQueries({ queryKey: ["admin-company-detail", selectedId] });
    },
    onError: () => {
      setErrorMsg("Nie udalo sie zmienic statusu weryfikacji");
      setSuccessMsg(null);
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  const handleSelectCompany = (id: string) => {
    setSelectedId(id);
    setSuccessMsg(null);
    setErrorMsg(null);
    // Find the company in the list first for quick population
    const item = data?.data.find((c) => c.id === id);
    if (item) {
      setEditMonthly(item.quota?.monthly_limit?.toString() ?? "");
      setEditCustom(item.quota?.custom_limit?.toString() ?? "");
    }
  };

  const handleSaveQuota = () => {
    if (!selectedId) return;
    const monthly = parseInt(editMonthly);
    if (isNaN(monthly) || monthly < 0) {
      setErrorMsg("Limit miesięczny musi być liczbą >= 0");
      return;
    }
    const custom = editCustom.trim() === "" ? undefined : parseInt(editCustom);
    if (custom !== undefined && (isNaN(custom) || custom < 0)) {
      setErrorMsg("Limit nadpisany musi być liczbą >= 0 lub pusty");
      return;
    }
    quotaMutation.mutate({ companyId: selectedId, monthly_limit: monthly, custom_limit: custom });
  };

  const handleToggleVerify = () => {
    if (!selectedId || !detail) return;
    verifyMutation.mutate({ companyId: selectedId, is_verified: !detail.is_verified });
  };

  // When detail data arrives, populate fields
  if (detail && selectedId) {
    const currentMonthly = detail.quota?.monthly_limit?.toString() ?? "";
    const currentCustom = detail.quota?.custom_limit?.toString() ?? "";
    // Only update if we haven't touched them yet (avoid overwriting user edits)
    if (editMonthly === "" && editCustom === "" && currentMonthly !== "") {
      populateEditFields(detail);
    }
  }

  return (
    <div>
      {/* Success / Error banners */}
      {successMsg && (
        <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex items-center justify-between">
          <span className="text-sm">{successMsg}</span>
          <button onClick={() => setSuccessMsg(null)} className="text-green-500 hover:text-green-700 font-bold">&times;</button>
        </div>
      )}
      {errorMsg && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center justify-between">
          <span className="text-sm">{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="text-red-500 hover:text-red-700 font-bold">&times;</button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4 mb-6">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Building2 className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600" />
            Firmy
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {data?.total ?? 0} firm w systemie
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="bg-white border rounded-lg p-3 sm:p-4 mb-6">
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Szukaj po nazwie firmy..."
              className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>
          <button
            type="submit"
            className="bg-blue-600 text-white px-6 py-2.5 rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors w-full sm:w-auto"
          >
            Szukaj
          </button>
        </form>
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
                    <th className="text-left px-4 py-3 font-semibold text-gray-600">Firma</th>
                    <th className="text-center px-4 py-3 font-semibold text-gray-600">Status</th>
                    <th className="text-center px-4 py-3 font-semibold text-gray-600">Aktywne</th>
                    <th className="text-center px-4 py-3 font-semibold text-gray-600">Limit mies.</th>
                    <th className="text-center px-4 py-3 font-semibold text-gray-600">Nadpisany</th>
                    <th className="text-center px-4 py-3 font-semibold text-gray-600">Wykorzystanie</th>
                    <th className="text-center px-4 py-3 font-semibold text-gray-600">Akcje</th>
                  </tr>
                </thead>
                <tbody>
                  {data.data.map((company) => (
                    <tr
                      key={company.id}
                      className={`border-b hover:bg-blue-50/30 cursor-pointer transition-colors ${
                        selectedId === company.id ? "bg-blue-50" : ""
                      }`}
                      onClick={() => handleSelectCompany(company.id)}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          {company.logo_url ? (
                            <img
                              src={company.logo_url}
                              alt={company.company_name}
                              className="w-8 h-8 rounded-lg object-cover border"
                            />
                          ) : (
                            <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center">
                              <Building2 className="w-4 h-4 text-gray-400" />
                            </div>
                          )}
                          <div>
                            <p className="font-semibold text-gray-900">{company.company_name}</p>
                            <p className="text-xs text-gray-500">{company.company_slug}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <VerifiedBadge verified={company.is_verified} />
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-sm font-medium text-gray-700">
                          {company.active_postings}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-sm text-gray-600">
                          {company.quota?.monthly_limit ?? "-"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-sm text-gray-600">
                          {company.quota?.custom_limit != null ? company.quota.custom_limit : "-"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        {company.quota ? (
                          <QuotaDisplay
                            limit={company.quota.monthly_limit}
                            used={company.quota.used_count}
                            custom={company.quota.custom_limit}
                          />
                        ) : (
                          <span className="text-gray-400 text-sm">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectCompany(company.id);
                          }}
                          className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
                          title="Szczegoly"
                        >
                          <Eye className="w-4 h-4 text-gray-500" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-8 text-center text-gray-500">
                <Building2 className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p className="font-medium">Brak firm</p>
                <p className="text-sm">Firmy pojawia sie po rejestracji pracodawcow.</p>
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

        {/* Detail Panel */}
        {selectedId && (
          <div className="lg:w-96 bg-white border rounded-lg p-4 sm:p-5 lg:sticky lg:top-4 max-h-[600px] lg:max-h-[calc(100vh-120px)] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-gray-900">Szczegoly firmy</h3>
              <button
                onClick={() => { setSelectedId(null); setSuccessMsg(null); setErrorMsg(null); }}
                className="text-gray-400 hover:text-gray-600"
              >
                &times;
              </button>
            </div>

            {detailLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : detail ? (
              <div className="space-y-4">
                {/* Company name & logo */}
                <div className="flex items-start gap-3">
                  {detail.logo_url ? (
                    <img
                      src={detail.logo_url}
                      alt={detail.company_name}
                      className="w-12 h-12 rounded-lg object-cover border"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center">
                      <Building2 className="w-6 h-6 text-gray-400" />
                    </div>
                  )}
                  <div>
                    <p className="text-lg font-bold text-gray-900">{detail.company_name}</p>
                    <p className="text-xs text-gray-500">{detail.company_slug}</p>
                  </div>
                </div>

                {/* Verification status + toggle */}
                <div className="flex items-center justify-between">
                  <VerifiedBadge verified={detail.is_verified} />
                  <button
                    onClick={handleToggleVerify}
                    disabled={verifyMutation.isPending}
                    className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors ${
                      detail.is_verified
                        ? "bg-red-50 text-red-600 hover:bg-red-100"
                        : "bg-green-50 text-green-600 hover:bg-green-100"
                    } disabled:opacity-50`}
                  >
                    {verifyMutation.isPending ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : detail.is_verified ? (
                      "Cofnij weryfikacje"
                    ) : (
                      "Zweryfikuj"
                    )}
                  </button>
                </div>

                {/* Company info */}
                <div className="border-t pt-3 space-y-2">
                  <p className="text-xs font-semibold text-gray-500 uppercase">Informacje o firmie</p>

                  {detail.user_email && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Email</span>
                      <span className="text-gray-700">{detail.user_email}</span>
                    </div>
                  )}
                  {detail.user_name && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Wlasciciel</span>
                      <span className="text-gray-700">{detail.user_name}</span>
                    </div>
                  )}
                  {detail.website && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Strona www</span>
                      <a
                        href={detail.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline flex items-center gap-1"
                      >
                        Link <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  )}
                  {detail.description && (
                    <div className="mt-2">
                      <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Opis</p>
                      <p className="text-sm text-gray-700 line-clamp-4">{detail.description}</p>
                    </div>
                  )}
                </div>

                {/* Quota editor */}
                <div className="border-t pt-3">
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Limity ogloszen</p>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Plan</span>
                      <span className="text-gray-700 font-medium">{detail.quota?.plan_type ?? "free"}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Wykorzystano</span>
                      <span className="text-gray-700 font-medium">{detail.quota?.used_count ?? 0}</span>
                    </div>
                    {detail.quota?.period_end && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-500">Reset</span>
                        <span className="text-gray-700">{new Date(detail.quota.period_end).toLocaleDateString("pl-PL")}</span>
                      </div>
                    )}

                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Limit miesięczny</label>
                      <input
                        type="number"
                        min="0"
                        value={editMonthly}
                        onChange={(e) => setEditMonthly(e.target.value)}
                        placeholder="np. 10"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Limit nadpisany (opcjonalnie)</label>
                      <input
                        type="number"
                        min="0"
                        value={editCustom}
                        onChange={(e) => setEditCustom(e.target.value)}
                        placeholder="Pusty = brak nadpisania"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <p className="text-xs text-gray-400 mt-1">Jesli ustawiony, zastepuje limit miesięczny</p>
                    </div>

                    <button
                      onClick={handleSaveQuota}
                      disabled={quotaMutation.isPending}
                      className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-2.5 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50"
                    >
                      {quotaMutation.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Save className="w-4 h-4" />
                      )}
                      Zapisz limity
                    </button>
                  </div>
                </div>

                {/* Recent jobs */}
                {detail.recent_jobs && detail.recent_jobs.length > 0 && (
                  <div className="border-t pt-3">
                    <p className="text-xs font-semibold text-gray-500 uppercase mb-2">
                      Ostatnie ogloszenia ({detail.recent_jobs.length})
                    </p>
                    <div className="space-y-2">
                      {detail.recent_jobs.map((job) => (
                        <a
                          key={job.id}
                          href={`/panel/admin/moderacja`}
                          className="block p-2.5 rounded-lg border hover:border-blue-200 hover:bg-blue-50/30 transition-colors"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <p className="text-sm font-medium text-gray-900 line-clamp-1">{job.title}</p>
                            <span
                              className={`text-xs px-2 py-0.5 rounded-full font-medium whitespace-nowrap ${
                                STATUS_BADGE[job.status] || "bg-gray-100 text-gray-500"
                              }`}
                            >
                              {job.status}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                            <span>{job.views_count} wyswietl.</span>
                            {job.is_featured && (
                              <span className="text-amber-600 font-medium">Wyrozn.</span>
                            )}
                            {job.created_at && (
                              <span>{new Date(job.created_at).toLocaleDateString("pl-PL")}</span>
                            )}
                          </div>
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Created at */}
                {detail.created_at && (
                  <div className="border-t pt-3 text-xs text-gray-400">
                    Firma dodana: {new Date(detail.created_at).toLocaleDateString("pl-PL")}
                  </div>
                )}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
