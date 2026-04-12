"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, Check, CheckCheck, Trash2 } from "lucide-react";
import Link from "next/link";
import api from "@/services/api";
import { formatDate } from "@/lib/utils";
import type {
  Notification,
  UnreadCount,
  PaginatedResponse,
  MessageResponse,
} from "@/types/api";

const NOTIFICATION_TYPE_ICONS: Record<string, string> = {
  application_received: "📩",
  application_status_changed: "📋",
  job_expiring: "⏰",
  job_approved: "✅",
  job_rejected: "❌",
  system: "🔔",
};

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  // Fetch unread count with auto-refresh every 30s
  const { data: unreadData } = useQuery({
    queryKey: ["notifications-unread-count"],
    queryFn: () =>
      api
        .get<UnreadCount>("/notifications/unread-count")
        .then((r) => r.data),
    refetchInterval: 30000,
  });

  // Fetch recent notifications (for dropdown)
  const { data: notificationsData } = useQuery({
    queryKey: ["notifications-recent"],
    queryFn: () =>
      api
        .get<PaginatedResponse<Notification>>("/notifications", {
          params: { per_page: 8 },
        })
        .then((r) => r.data),
    refetchInterval: 30000,
  });

  // Mark single as read
  const markReadMutation = useMutation({
    mutationFn: (id: string) =>
      api.patch<MessageResponse>(`/notifications/${id}/read`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-recent"] });
    },
  });

  // Mark all as read
  const markAllReadMutation = useMutation({
    mutationFn: () =>
      api.post<MessageResponse>("/notifications/mark-all-read"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-recent"] });
    },
  });

  // Delete notification
  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      api.delete<MessageResponse>(`/notifications/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-recent"] });
    },
  });

  // Close dropdown on outside click or Escape key
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  const unreadCount = unreadData?.unread_count ?? 0;
  const notifications = notificationsData?.data ?? [];

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell button */}
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 text-gray-500 hover:text-gray-700 transition-colors rounded-lg hover:bg-gray-100"
        aria-label={`Powiadomienia${unreadCount > 0 ? ` (${unreadCount} nieprzeczytanych)` : ""}`}
        aria-expanded={open}
        aria-haspopup="true"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 bg-red-600 text-white text-[10px] font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 sm:w-96 bg-white border border-gray-200 rounded-xl shadow-xl z-50 overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between bg-gray-50">
            <h3 className="font-semibold text-gray-900 text-sm">
              Powiadomienia
            </h3>
            {unreadCount > 0 && (
              <button
                onClick={() => markAllReadMutation.mutate()}
                className="text-xs text-red-600 hover:text-red-700 font-medium flex items-center gap-1 transition-colors"
                disabled={markAllReadMutation.isPending}
              >
                <CheckCheck className="w-3.5 h-3.5" />
                Przeczytaj wszystkie
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-[360px] overflow-y-auto">
            {notifications.length > 0 ? (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition-colors flex gap-3 ${
                    !n.is_read ? "bg-red-50/40" : ""
                  }`}
                >
                  <span className="text-lg flex-shrink-0 mt-0.5">
                    {NOTIFICATION_TYPE_ICONS[n.type] || "🔔"}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p
                      className={`text-sm leading-snug ${
                        !n.is_read
                          ? "font-semibold text-gray-900"
                          : "text-gray-700"
                      }`}
                    >
                      {n.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                      {n.message}
                    </p>
                    <p className="text-[11px] text-gray-400 mt-1">
                      {formatDate(n.created_at)}
                    </p>
                  </div>
                  <div className="flex flex-col gap-1 flex-shrink-0">
                    {!n.is_read && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          markReadMutation.mutate(n.id);
                        }}
                        className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                        title="Oznacz jako przeczytane"
                        aria-label="Oznacz jako przeczytane"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteMutation.mutate(n.id);
                      }}
                      className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                      title="Usuń"
                      aria-label="Usuń powiadomienie"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-4 py-8 text-center text-gray-400 text-sm">
                Brak powiadomień
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-2.5 border-t border-gray-100 bg-gray-50">
            <Link
              href="/panel/powiadomienia"
              className="text-sm text-red-600 hover:text-red-700 font-medium block text-center transition-colors"
              onClick={() => setOpen(false)}
            >
              Zobacz wszystkie
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
