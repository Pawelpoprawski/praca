"use client";

import { useState, useEffect } from "react";
import { X, Zap, FileText, User as UserIcon } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/services/api";
import type { WorkerProfile } from "@/types/api";

interface QuickApplyModalProps {
  jobId: string;
  jobTitle: string;
  companyName: string;
  profile: WorkerProfile;
  onClose: () => void;
  onSuccess: () => void;
}

export default function QuickApplyModal({
  jobId,
  jobTitle,
  companyName,
  profile,
  onClose,
  onSuccess,
}: QuickApplyModalProps) {
  const [coverLetter, setCoverLetter] = useState("");
  const queryClient = useQueryClient();

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const mutation = useMutation({
    mutationFn: () =>
      api.post(`/worker/quick-apply/${jobId}`, {
        cover_letter: coverLetter || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["worker-applications"] });
      onSuccess();
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-2xl max-w-lg w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-green-50 to-emerald-50">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-green-600" />
            <h2 className="text-lg font-bold font-display text-[#0D2240]">Szybka aplikacja</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Zamknij"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-5 space-y-5">
          {/* Job info */}
          <div className="bg-gray-50 rounded-xl p-4">
            <p className="font-semibold text-gray-900">{jobTitle}</p>
            <p className="text-sm text-gray-500">{companyName}</p>
          </div>

          {/* Profile summary */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Twoje dane z profilu:</h3>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2 text-gray-600">
                <UserIcon className="w-4 h-4 text-gray-400" />
                <span>
                  {profile.first_name} {profile.last_name}
                  {profile.email && ` (${profile.email})`}
                </span>
              </div>
              {profile.has_cv && (
                <div className="flex items-center gap-2 text-gray-600">
                  <FileText className="w-4 h-4 text-gray-400" />
                  <span>CV: {profile.cv_filename || "Przesłane"}</span>
                </div>
              )}
              {profile.experience_years > 0 && (
                <p className="text-gray-600 pl-6">
                  Doświadczenie: {profile.experience_years} lat
                </p>
              )}
              {profile.canton && (
                <p className="text-gray-600 pl-6">
                  Kanton: {profile.canton}
                </p>
              )}
            </div>
          </div>

          {/* Optional cover letter */}
          <div>
            <label
              htmlFor="quick-cover-letter"
              className="block text-sm font-semibold text-gray-700 mb-2"
            >
              Krótka wiadomość (opcjonalnie)
            </label>
            <textarea
              id="quick-cover-letter"
              value={coverLetter}
              onChange={(e) => setCoverLetter(e.target.value)}
              placeholder="Napisz kilka słów do pracodawcy..."
              rows={3}
              maxLength={2000}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 resize-none transition-all"
            />
          </div>

          {/* Error */}
          {mutation.isError && (
            <div className="bg-[#FFF0F3] border border-[#FFC2CD] text-[#B8001F] px-4 py-2.5 rounded-lg text-sm flex items-start gap-2" role="alert">
              <span className="flex-shrink-0 mt-0.5">⚠</span>
              <span>{(mutation.error as any)?.response?.data?.detail || "Wystąpił błąd podczas wysyłania aplikacji"}</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50 flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors"
          >
            Anuluj
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="px-5 py-2.5 text-sm font-semibold text-white bg-green-600 rounded-xl hover:bg-green-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            <Zap className="w-4 h-4" />
            {mutation.isPending ? "Wysyłanie..." : "Aplikuj szybko"}
          </button>
        </div>
      </div>
    </div>
  );
}
