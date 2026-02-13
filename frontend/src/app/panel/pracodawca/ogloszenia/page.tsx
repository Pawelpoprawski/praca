"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import Link from "next/link";
import { Plus, Eye, Edit, Trash2, XCircle, ChevronLeft, ChevronRight } from "lucide-react";
import api from "@/services/api";
import { CONTRACT_TYPES, formatDate, formatSalary } from "@/lib/utils";
import type { JobOffer, PaginatedResponse } from "@/types/api";

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: "Oczekuje", color: "bg-yellow-100 text-yellow-800" },
  active: { label: "Aktywne", color: "bg-green-100 text-green-800" },
  rejected: { label: "Odrzucone", color: "bg-red-100 text-red-800" },
  closed: { label: "Zamknięte", color: "bg-gray-100 text-gray-800" },
  expired: { label: "Wygasłe", color: "bg-gray-100 text-gray-600" },
};

export default function EmployerJobsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["employer-jobs", page, statusFilter],
    queryFn: () =>
      api.get<PaginatedResponse<JobOffer>>("/employer/jobs", {
        params: { page, per_page: 15, ...(statusFilter && { status: statusFilter }) },
      }).then((r) => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/employer/jobs/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["employer-jobs"] }),
  });

  const closeMutation = useMutation({
    mutationFn: (id: string) => api.patch(`/employer/jobs/${id}/close`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["employer-jobs"] }),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Moje ogłoszenia</h1>
        <Link
          href="/panel/pracodawca/ogloszenia/nowe"
          className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 text-sm font-medium flex items-center gap-2"
        >
          <Plus className="w-4 h-4" /> Nowe ogłoszenie
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4">
        {[
          { value: "", label: "Wszystkie" },
          { value: "active", label: "Aktywne" },
          { value: "pending", label: "Oczekujące" },
          { value: "closed", label: "Zamknięte" },
        ].map((f) => (
          <button
            key={f.value}
            onClick={() => { setStatusFilter(f.value); setPage(1); }}
            className={`px-3 py-1.5 text-sm rounded-lg border font-medium transition-colors ${
              statusFilter === f.value
                ? "bg-red-50 border-red-200 text-red-700"
                : "bg-white hover:bg-gray-50 text-gray-600"
            }`}
          >
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
          <div className="bg-white border rounded-lg divide-y">
            {data.data.map((job) => {
              const statusInfo = STATUS_LABELS[job.status] || { label: job.status, color: "bg-gray-100 text-gray-800" };
              return (
                <div key={job.id} className="px-5 py-4">
                  <div className="flex items-start justify-between">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Link
                          href={`/panel/pracodawca/ogloszenia/${job.id}`}
                          className="font-medium text-gray-900 hover:text-red-600 truncate"
                        >
                          {job.title}
                        </Link>
                        <span className={`text-xs px-2 py-0.5 rounded font-medium ${statusInfo.color}`}>
                          {statusInfo.label}
                        </span>
                        {job.is_featured && (
                          <span className="text-xs px-2 py-0.5 rounded font-medium bg-amber-100 text-amber-800">
                            Wyróżnione
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-sm text-gray-500">
                        <span>{CONTRACT_TYPES[job.contract_type] || job.contract_type}</span>
                        <span>{formatSalary(job.salary_min, job.salary_max, job.salary_type)}</span>
                        <span className="flex items-center gap-1">
                          <Eye className="w-3 h-3" /> {job.views_count}
                        </span>
                        <span>{formatDate(job.created_at)}</span>
                      </div>
                    </div>
                    <div className="flex gap-1 ml-4 flex-shrink-0">
                      <Link
                        href={`/panel/pracodawca/ogloszenia/${job.id}/kandydaci`}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                        title="Kandydaci"
                      >
                        <Eye className="w-4 h-4" />
                      </Link>
                      <Link
                        href={`/panel/pracodawca/ogloszenia/${job.id}`}
                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg"
                        title="Edytuj"
                      >
                        <Edit className="w-4 h-4" />
                      </Link>
                      {job.status === "active" && (
                        <button
                          onClick={() => closeMutation.mutate(job.id)}
                          className="p-2 text-gray-400 hover:text-yellow-600 hover:bg-yellow-50 rounded-lg"
                          title="Zamknij"
                        >
                          <XCircle className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => {
                          if (confirm("Czy na pewno chcesz usunąć to ogłoszenie?")) {
                            deleteMutation.mutate(job.id);
                          }
                        }}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                        title="Usuń"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {data.pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-500">
                Strona {data.page} z {data.pages}
              </p>
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
          <p className="text-gray-500 mb-2">Nie masz jeszcze żadnych ogłoszeń</p>
          <Link href="/panel/pracodawca/ogloszenia/nowe" className="text-sm text-red-600 hover:underline">
            Dodaj pierwsze ogłoszenie
          </Link>
        </div>
      )}
    </div>
  );
}
