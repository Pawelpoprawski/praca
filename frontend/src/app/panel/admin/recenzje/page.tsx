"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Check, X, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import api from "@/services/api";
import { formatDate } from "@/lib/utils";
import ReviewStars from "@/components/common/ReviewStars";
import type { AdminReview, PaginatedResponse } from "@/types/api";

export default function AdminReviewsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("pending");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-reviews", page, statusFilter],
    queryFn: () =>
      api
        .get<PaginatedResponse<AdminReview>>("/admin/reviews", {
          params: {
            page,
            per_page: 15,
            ...(statusFilter && { status: statusFilter }),
          },
        })
        .then((r) => r.data),
  });

  const moderateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.patch(`/admin/reviews/${id}`, { status }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin-reviews"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/admin/reviews/${id}`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin-reviews"] }),
  });

  return (
    <div>
      <h1 className="text-xl sm:text-2xl font-bold font-display text-[#0D2240] mb-6">
        Moderacja recenzji
      </h1>

      <div className="flex gap-2 mb-4 overflow-x-auto pb-2 -mx-4 px-4 sm:mx-0 sm:px-0">
        {[
          { value: "pending", label: "Oczekujace" },
          { value: "approved", label: "Zatwierdzone" },
          { value: "rejected", label: "Odrzucone" },
          { value: "", label: "Wszystkie" },
        ].map((f) => (
          <button
            key={f.value}
            onClick={() => {
              setStatusFilter(f.value);
              setPage(1);
            }}
            className={`px-3 py-1.5 text-sm rounded-lg border font-medium transition-colors whitespace-nowrap ${
              statusFilter === f.value
                ? "bg-[#FFF0F3] border-[#FFC2CD] text-[#B8001F]"
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
            <div
              key={i}
              className="animate-pulse h-24 bg-gray-100 rounded-lg"
            />
          ))}
        </div>
      ) : data?.data && data.data.length > 0 ? (
        <>
          <div className="space-y-3">
            {data.data.map((review) => (
              <div key={review.id} className="bg-white border rounded-lg p-4 sm:p-5">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="font-medium text-gray-900 break-words">
                        {review.worker_name}
                      </span>
                      <span className="text-gray-400 text-sm">o firmie</span>
                      <span className="font-medium text-gray-900 break-words">
                        {review.company_name}
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-medium ${
                          review.status === "pending"
                            ? "bg-yellow-100 text-yellow-800"
                            : review.status === "approved"
                              ? "bg-green-100 text-green-800"
                              : "bg-[#FFE0E6] text-[#7A0014]"
                        }`}
                      >
                        {review.status === "pending"
                          ? "Oczekuje"
                          : review.status === "approved"
                            ? "Zatwierdzona"
                            : "Odrzucona"}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 mb-2">
                      <ReviewStars rating={review.rating} size="sm" />
                      <span className="text-xs text-gray-400">
                        {formatDate(review.created_at)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 whitespace-pre-line break-words">
                      {review.comment}
                    </p>
                  </div>

                  <div className="flex gap-1 flex-shrink-0">
                    {review.status === "pending" && (
                      <>
                        <button
                          onClick={() =>
                            moderateMutation.mutate({
                              id: review.id,
                              status: "approved",
                            })
                          }
                          disabled={moderateMutation.isPending}
                          className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                          title="Zatwierdz"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() =>
                            moderateMutation.mutate({
                              id: review.id,
                              status: "rejected",
                            })
                          }
                          disabled={moderateMutation.isPending}
                          className="p-2 text-[#E1002A] hover:bg-[#FFF0F3] rounded-lg"
                          title="Odrzuc"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </>
                    )}
                    {review.status !== "pending" && (
                      <button
                        onClick={() => {
                          if (
                            window.confirm(
                              "Czy na pewno chcesz usunac te recenzje?"
                            )
                          ) {
                            deleteMutation.mutate(review.id);
                          }
                        }}
                        disabled={deleteMutation.isPending}
                        className="p-2 text-gray-400 hover:text-[#E1002A] hover:bg-[#FFF0F3] rounded-lg"
                        title="Usun"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {data.pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-500">
                Strona {data.page} z {data.pages}
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
                  onClick={() =>
                    setPage((p) => Math.min(data.pages, p + 1))
                  }
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
          <p className="text-gray-500">Brak recenzji do moderacji</p>
        </div>
      )}
    </div>
  );
}
