"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, User, FileText, Mail } from "lucide-react";
import api from "@/services/api";
import { APPLICATION_STATUSES, formatDate } from "@/lib/utils";
import type { Candidate } from "@/types/api";

export default function CandidatesPage() {
  const params = useParams();
  const jobId = params.id as string;
  const queryClient = useQueryClient();

  const { data: candidates, isLoading } = useQuery({
    queryKey: ["candidates", jobId],
    queryFn: () =>
      api.get<Candidate[]>(`/employer/jobs/${jobId}/applications`).then((r) => r.data),
  });

  const statusMutation = useMutation({
    mutationFn: ({ appId, status }: { appId: string; status: string }) =>
      api.put(`/employer/applications/${appId}/status`, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidates", jobId] });
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="animate-pulse h-24 bg-gray-100 rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link href="/panel/pracodawca/ogloszenia" className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Kandydaci</h1>
        <span className="text-sm text-gray-500">({candidates?.length || 0})</span>
      </div>

      {candidates && candidates.length > 0 ? (
        <div className="space-y-3">
          {candidates.map((candidate) => {
            const statusInfo =
              APPLICATION_STATUSES[candidate.status] || {
                label: candidate.status,
                color: "bg-gray-100 text-gray-800",
              };
            return (
              <div key={candidate.id} className="bg-white border rounded-lg p-5">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                      <User className="w-5 h-5 text-gray-500" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        {candidate.worker_name || "Anonimowy"}
                      </p>
                      {candidate.worker_email && (
                        <div className="flex items-center gap-1 text-sm text-gray-500">
                          <Mail className="w-3 h-3" />
                          <a href={`mailto:${candidate.worker_email}`} className="hover:text-red-600">
                            {candidate.worker_email}
                          </a>
                        </div>
                      )}
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-xs px-2 py-0.5 rounded font-medium ${statusInfo.color}`}>
                          {statusInfo.label}
                        </span>
                        {candidate.has_cv && (
                          <span className="flex items-center gap-1 text-xs text-green-600">
                            <FileText className="w-3 h-3" /> CV
                          </span>
                        )}
                        <span className="text-xs text-gray-400">{formatDate(candidate.created_at)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-1">
                    {candidate.status === "sent" && (
                      <button
                        onClick={() => statusMutation.mutate({ appId: candidate.id, status: "viewed" })}
                        className="px-3 py-1 text-xs border rounded-lg hover:bg-gray-50 font-medium"
                      >
                        Oznacz jako przeglądane
                      </button>
                    )}
                    {(candidate.status === "sent" || candidate.status === "viewed") && (
                      <>
                        <button
                          onClick={() => statusMutation.mutate({ appId: candidate.id, status: "shortlisted" })}
                          className="px-3 py-1 text-xs bg-green-50 text-green-700 border border-green-200 rounded-lg hover:bg-green-100 font-medium"
                        >
                          Krótka lista
                        </button>
                        <button
                          onClick={() => statusMutation.mutate({ appId: candidate.id, status: "rejected" })}
                          className="px-3 py-1 text-xs bg-red-50 text-red-700 border border-red-200 rounded-lg hover:bg-red-100 font-medium"
                        >
                          Odrzuć
                        </button>
                      </>
                    )}
                    {candidate.status === "shortlisted" && (
                      <button
                        onClick={() => statusMutation.mutate({ appId: candidate.id, status: "accepted" })}
                        className="px-3 py-1 text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg hover:bg-emerald-100 font-medium"
                      >
                        Zaakceptuj
                      </button>
                    )}
                  </div>
                </div>

                {candidate.cover_letter && (
                  <div className="mt-3 pt-3 border-t">
                    <p className="text-xs font-medium text-gray-500 mb-1">List motywacyjny:</p>
                    <p className="text-sm text-gray-700 whitespace-pre-line">{candidate.cover_letter}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-white border rounded-lg px-5 py-12 text-center">
          <User className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">Brak kandydatów na to ogłoszenie</p>
        </div>
      )}
    </div>
  );
}
