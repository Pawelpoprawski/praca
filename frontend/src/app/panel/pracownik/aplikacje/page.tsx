"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import Link from "next/link";
import { Briefcase, ChevronLeft, ChevronRight } from "lucide-react";
import api from "@/services/api";
import { APPLICATION_STATUSES, formatDate } from "@/lib/utils";
import type { Application, PaginatedResponse } from "@/types/api";

export default function ApplicationsPage() {
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["worker-applications", page],
    queryFn: () =>
      api
        .get<PaginatedResponse<Application>>("/worker/applications", {
          params: { page, per_page: 15 },
        })
        .then((r) => r.data),
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="animate-pulse h-16 bg-gray-100 rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Moje aplikacje</h1>

      {data?.data && data.data.length > 0 ? (
        <>
          <div className="bg-white border rounded-lg divide-y">
            {data.data.map((app) => {
              const statusInfo =
                APPLICATION_STATUSES[app.status] || {
                  label: app.status,
                  color: "bg-gray-100 text-gray-800",
                };
              return (
                <div
                  key={app.id}
                  className="px-5 py-4 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-9 h-9 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Briefcase className="w-4 h-4 text-gray-500" />
                    </div>
                    <div className="min-w-0">
                      <Link
                        href={`/oferty/${app.job_offer_id}`}
                        className="font-medium text-gray-900 hover:text-red-600 truncate block"
                      >
                        {app.job_title || "Oferta pracy"}
                      </Link>
                      <p className="text-sm text-gray-500 truncate">
                        {app.company_name}
                      </p>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0 ml-4">
                    <span
                      className={`inline-block text-xs px-2 py-0.5 rounded font-medium ${statusInfo.color}`}
                    >
                      {statusInfo.label}
                    </span>
                    <p className="text-xs text-gray-400 mt-1">
                      {formatDate(app.created_at)}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {data.pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-500">
                Strona {data.page} z {data.pages} ({data.total} aplikacji)
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
          <Briefcase className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 mb-2">
            Nie masz jeszcze żadnych aplikacji
          </p>
          <Link
            href="/oferty"
            className="text-sm text-red-600 hover:underline"
          >
            Przeglądaj oferty pracy
          </Link>
        </div>
      )}
    </div>
  );
}
