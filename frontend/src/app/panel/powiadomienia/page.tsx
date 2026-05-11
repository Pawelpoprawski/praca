"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, Check, CheckCheck, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import api from "@/services/api";
import { formatDate } from "@/lib/utils";
import type {
  Notification,
  PaginatedResponse,
  MessageResponse,
} from "@/types/api";

const NOTIFICATION_TYPE_LABELS: Record<string, string> = {
  application_received: "Nowa aplikacja",
  application_status_changed: "Status aplikacji",
  job_expiring: "Wygasanie oferty",
  job_approved: "Zatwierdzenie oferty",
  job_rejected: "Odrzucenie oferty",
  system: "Systemowe",
};

const NOTIFICATION_TYPE_COLORS: Record<string, string> = {
  application_received: "bg-blue-100 text-blue-800",
  application_status_changed: "bg-yellow-100 text-yellow-800",
  job_expiring: "bg-orange-100 text-orange-800",
  job_approved: "bg-green-100 text-green-800",
  job_rejected: "bg-[#FFE0E6] text-[#7A0014]",
  system: "bg-gray-100 text-gray-800",
};

export default function NotificationsPage() {
  const [page, setPage] = useState(1);
  const perPage = 20;
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["notifications-all", page],
    queryFn: () =>
      api
        .get<PaginatedResponse<Notification>>("/notifications", {
          params: { page, per_page: perPage },
        })
        .then((r) => r.data),
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) =>
      api.patch<MessageResponse>(`/notifications/${id}/read`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications-all"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-recent"] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () =>
      api.post<MessageResponse>("/notifications/mark-all-read"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications-all"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-recent"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      api.delete<MessageResponse>(`/notifications/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications-all"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-recent"] });
    },
  });

  const notifications = data?.data ?? [];
  const totalPages = data?.pages ?? 0;
  const total = data?.total ?? 0;
  const hasUnread = notifications.some((n) => !n.is_read);

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Bell className="w-6 h-6 text-gray-700" />
          <h1 className="text-2xl font-bold font-display text-[#0D2240]">Powiadomienia</h1>
          {total > 0 && (
            <span className="text-sm text-gray-500">({total})</span>
          )}
        </div>
        {hasUnread && (
          <button
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending}
            className="flex items-center gap-2 text-sm text-[#E1002A] hover:text-[#B8001F] font-medium px-3 py-2 rounded-lg hover:bg-[#FFF0F3] transition-colors"
          >
            <CheckCheck className="w-4 h-4" />
            Oznacz wszystkie jako przeczytane
          </button>
        )}
      </div>

      {/* List */}
      {isLoading ? (
        <div className="bg-white border rounded-lg divide-y">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="px-5 py-4 flex items-start gap-4 animate-pulse">
              <div className="pt-1.5 flex-shrink-0">
                <div className="w-2.5 h-2.5 rounded-full bg-gray-200" />
              </div>
              <div className="flex-1">
                <div className="flex gap-2 mb-2">
                  <div className="h-4 bg-gray-200 rounded w-24" />
                  <div className="h-4 bg-gray-100 rounded w-16" />
                </div>
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-1" />
                <div className="h-3 bg-gray-100 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : notifications.length > 0 ? (
        <div className="bg-white border rounded-lg divide-y">
          {notifications.map((n) => {
            const typeLabel =
              NOTIFICATION_TYPE_LABELS[n.type] || n.type;
            const typeColor =
              NOTIFICATION_TYPE_COLORS[n.type] || "bg-gray-100 text-gray-800";

            return (
              <div
                key={n.id}
                className={`px-5 py-4 flex items-start gap-4 hover:bg-gray-50 transition-colors ${
                  !n.is_read ? "bg-[#FFF0F3]/30" : ""
                }`}
              >
                {/* Unread indicator */}
                <div className="pt-1.5 flex-shrink-0">
                  {!n.is_read ? (
                    <div className="w-2.5 h-2.5 rounded-full bg-[#E1002A]" />
                  ) : (
                    <div className="w-2.5 h-2.5" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`inline-block text-[11px] px-2 py-0.5 rounded font-medium ${typeColor}`}
                    >
                      {typeLabel}
                    </span>
                    <span className="text-xs text-gray-400">
                      {formatDate(n.created_at)}
                    </span>
                  </div>
                  <p
                    className={`text-sm ${
                      !n.is_read
                        ? "font-semibold text-gray-900"
                        : "text-gray-700"
                    }`}
                  >
                    {n.title}
                  </p>
                  <p className="text-sm text-gray-500 mt-0.5">{n.message}</p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 flex-shrink-0">
                  {!n.is_read && (
                    <button
                      onClick={() => markReadMutation.mutate(n.id)}
                      disabled={markReadMutation.isPending}
                      className="p-2 text-gray-400 hover:text-green-600 rounded-lg hover:bg-green-50 transition-colors disabled:opacity-50"
                      title="Oznacz jako przeczytane"
                      aria-label="Oznacz jako przeczytane"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => deleteMutation.mutate(n.id)}
                    disabled={deleteMutation.isPending}
                    className="p-2 text-gray-400 hover:text-[#E1002A] rounded-lg hover:bg-[#FFF0F3] transition-colors disabled:opacity-50"
                    title="Usuń"
                    aria-label="Usuń powiadomienie"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-white border rounded-lg px-5 py-16 text-center">
          <Bell className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">Nie masz jeszcze żadnych powiadomień.</p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-6">
          <p className="text-sm text-gray-500">
            Strona {page} z {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="flex items-center gap-1 px-3 py-2 text-sm border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Poprzednia
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="flex items-center gap-1 px-3 py-2 text-sm border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Następna
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
