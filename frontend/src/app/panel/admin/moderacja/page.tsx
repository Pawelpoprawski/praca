"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Check, X, Eye, ChevronLeft, ChevronRight, Download } from "lucide-react";
import Link from "next/link";
import api, { downloadCSV } from "@/services/api";
import { CONTRACT_TYPES, formatDate, formatSalary } from "@/lib/utils";
import type { JobOffer, PaginatedResponse } from "@/types/api";

export default function ModerationPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("pending");
  const [rejectId, setRejectId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [exporting, setExporting] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-jobs", page, statusFilter],
    queryFn: () =>
      api.get<PaginatedResponse<JobOffer>>("/admin/jobs", {
        params: { page, per_page: 15, ...(statusFilter && { status: statusFilter }) },
      }).then((r) => r.data),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => api.put(`/admin/jobs/${id}/approve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-jobs"] }),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      api.put(`/admin/jobs/${id}/reject`, null, { params: { reason } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-jobs"] });
      setRejectId(null);
      setRejectReason("");
    },
  });

  const handleExportCSV = async () => {
    setExporting(true);
    try {
      await downloadCSV("/admin/export/jobs", `ogloszenia_${new Date().toISOString().slice(0, 10)}.csv`);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <h1 className="text-xl sm:text-2xl font-bold font-display text-[#0D2240]">Moderacja ogłoszeń</h1>
        <button
          onClick={handleExportCSV}
          disabled={exporting}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium border rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 w-fit"
        >
          <Download className="w-4 h-4" />
          <span className="hidden sm:inline">{exporting ? "Eksportowanie..." : "Eksportuj CSV"}</span>
          <span className="sm:hidden">CSV</span>
        </button>
      </div>

      <div className="flex gap-2 mb-4 overflow-x-auto pb-2 -mx-4 px-4 sm:mx-0 sm:px-0">
        {[
          { value: "pending", label: "Oczekujące" },
          { value: "active", label: "Aktywne" },
          { value: "rejected", label: "Odrzucone" },
          { value: "", label: "Wszystkie" },
        ].map((f) => (
          <button key={f.value} onClick={() => { setStatusFilter(f.value); setPage(1); }}
            className={`px-3 py-1.5 text-sm rounded-lg border font-medium transition-colors whitespace-nowrap ${
              statusFilter === f.value ? "bg-[#FFF0F3] border-[#FFC2CD] text-[#B8001F]" : "bg-white hover:bg-gray-50 text-gray-600"
            }`}>
            {f.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="animate-pulse h-20 bg-gray-100 rounded-lg" />
          ))}
        </div>
      ) : data?.data && data.data.length > 0 ? (
        <>
          <div className="space-y-3">
            {data.data.map((job) => (
              <div key={job.id} className="bg-white border rounded-lg p-4 sm:p-5">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start sm:items-center gap-2 mb-1 flex-wrap">
                      <h3 className="font-medium text-gray-900 break-words">{job.title}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                        job.status === "pending" ? "bg-yellow-100 text-yellow-800" :
                        job.status === "active" ? "bg-green-100 text-green-800" :
                        "bg-[#FFE0E6] text-[#7A0014]"
                      }`}>
                        {job.status === "pending" ? "Oczekuje" : job.status === "active" ? "Aktywne" : "Odrzucone"}
                      </span>
                    </div>
                    <div className="text-xs sm:text-sm text-gray-500 flex flex-wrap gap-x-3 gap-y-1">
                      <span className="truncate max-w-[150px] sm:max-w-none">{job.employer?.company_name}</span>
                      <span className="whitespace-nowrap">{CONTRACT_TYPES[job.contract_type] || job.contract_type}</span>
                      <span className="whitespace-nowrap">{formatSalary(job.salary_min, job.salary_max, job.salary_type)}</span>
                      <span className="whitespace-nowrap">{formatDate(job.created_at)}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">{job.description}</p>
                  </div>

                  <div className="flex gap-1 flex-shrink-0">
                    <Link href={`/oferty/${job.id}`} className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg" title="Podgląd" aria-label="Podgląd ogłoszenia">
                      <Eye className="w-4 h-4" />
                    </Link>
                    {job.status === "pending" && (
                      <>
                        <button onClick={() => approveMutation.mutate(job.id)}
                          disabled={approveMutation.isPending}
                          className="p-2 text-green-600 hover:bg-green-50 rounded-lg disabled:opacity-50" title="Zatwierdź" aria-label="Zatwierdź ogłoszenie">
                          <Check className="w-4 h-4" />
                        </button>
                        <button onClick={() => setRejectId(job.id)}
                          className="p-2 text-[#E1002A] hover:bg-[#FFF0F3] rounded-lg" title="Odrzuć" aria-label="Odrzuć ogłoszenie">
                          <X className="w-4 h-4" />
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {rejectId === job.id && (
                  <div className="mt-3 pt-3 border-t flex gap-2">
                    <input type="text" value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      placeholder="Podaj powód odrzucenia..."
                      className="flex-1 px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-[#E1002A]/20" />
                    <button
                      onClick={() => rejectMutation.mutate({ id: job.id, reason: rejectReason })}
                      disabled={!rejectReason.trim() || rejectMutation.isPending}
                      className="px-4 py-2 bg-[#E1002A] text-white text-sm rounded-lg hover:bg-[#B8001F] disabled:opacity-50">
                      Odrzuć
                    </button>
                    <button onClick={() => { setRejectId(null); setRejectReason(""); }}
                      className="px-4 py-2 border text-sm rounded-lg hover:bg-gray-50">
                      Anuluj
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>

          {data.pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-500">Strona {data.page} z {data.pages}</p>
              <div className="flex gap-1">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-30">
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button onClick={() => setPage((p) => Math.min(data.pages, p + 1))} disabled={page >= data.pages}
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-30">
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="bg-white border rounded-lg px-5 py-12 text-center">
          <p className="text-gray-500">Brak ogłoszeń do moderacji</p>
        </div>
      )}
    </div>
  );
}
