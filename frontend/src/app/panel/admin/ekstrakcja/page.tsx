"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Cpu, Play, Loader2, CheckCircle2, XCircle, Clock, AlertTriangle } from "lucide-react";
import api from "@/services/api";
import type { ExtractionStatus, ExtractionTriggerResult } from "@/types/api";

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}) {
  return (
    <div className="bg-white border rounded-lg p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-xs text-gray-500">{label}</p>
        </div>
      </div>
    </div>
  );
}

export default function AdminEkstrakcjaPage() {
  const queryClient = useQueryClient();
  const [cvRunning, setCvRunning] = useState(false);
  const [jobsRunning, setJobsRunning] = useState(false);

  // Poll faster when extraction is running
  const isRunning = cvRunning || jobsRunning;

  const { data: status, isLoading } = useQuery({
    queryKey: ["admin-extraction-status"],
    queryFn: () =>
      api.get<ExtractionStatus>("/admin/extraction/status").then((r) => r.data),
    refetchInterval: isRunning ? 3000 : 15000,
  });

  // Auto-stop polling indicators when counts reach 0
  useEffect(() => {
    if (status) {
      if (cvRunning && status.cv.pending === 0 && status.cv.processing === 0) {
        setCvRunning(false);
      }
      if (jobsRunning && status.jobs.pending === 0) {
        setJobsRunning(false);
      }
    }
  }, [status, cvRunning, jobsRunning]);

  const runCv = useMutation({
    mutationFn: () =>
      api.post<ExtractionTriggerResult>("/admin/extraction/run-cv").then((r) => r.data),
    onSuccess: (data) => {
      if (data.triggered) {
        setCvRunning(true);
      }
      queryClient.invalidateQueries({ queryKey: ["admin-extraction-status"] });
    },
  });

  const runJobs = useMutation({
    mutationFn: () =>
      api.post<ExtractionTriggerResult>("/admin/extraction/run-jobs").then((r) => r.data),
    onSuccess: (data) => {
      if (data.triggered) {
        setJobsRunning(true);
      }
      queryClient.invalidateQueries({ queryKey: ["admin-extraction-status"] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[40vh]">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Cpu className="w-5 h-5 sm:w-6 sm:h-6 text-indigo-600" />
          Ekstrakcja AI
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Status ekstrakcji danych z CV i ofert pracy
          {isRunning && (
            <span className="ml-2 inline-flex items-center gap-1 text-indigo-600">
              <Loader2 className="w-3 h-3 animate-spin" />
              Przetwarzanie...
            </span>
          )}
        </p>
      </div>

      {/* CV Section */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800">Ekstrakcja CV</h2>
          <button
            onClick={() => runCv.mutate()}
            disabled={runCv.isPending || cvRunning || (status?.cv.pending === 0)}
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {cvRunning ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {cvRunning ? "Przetwarzanie..." : "Uruchom ekstrakcje"}
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard
            label="Oczekujace"
            value={status?.cv.pending ?? 0}
            icon={Clock}
            color="bg-yellow-100 text-yellow-700"
          />
          <StatCard
            label="Przetwarzane"
            value={status?.cv.processing ?? 0}
            icon={Loader2}
            color="bg-blue-100 text-blue-700"
          />
          <StatCard
            label="Ukonczone"
            value={status?.cv.completed ?? 0}
            icon={CheckCircle2}
            color="bg-green-100 text-green-700"
          />
          <StatCard
            label="Bledy"
            value={status?.cv.failed ?? 0}
            icon={XCircle}
            color="bg-red-100 text-red-700"
          />
        </div>

        {status && status.cv.total > 0 && (
          <div className="mt-3">
            <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
              <span>Postep: {status.cv.completed}/{status.cv.total}</span>
              <span>({status.cv.total > 0 ? Math.round((status.cv.completed / status.cv.total) * 100) : 0}%)</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${status.cv.total > 0 ? (status.cv.completed / status.cv.total) * 100 : 0}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Jobs Section */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800">Ekstrakcja ofert pracy</h2>
          <button
            onClick={() => runJobs.mutate()}
            disabled={runJobs.isPending || jobsRunning || (status?.jobs.pending === 0)}
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {jobsRunning ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {jobsRunning ? "Przetwarzanie..." : "Uruchom ekstrakcje"}
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <StatCard
            label="Oczekujace"
            value={status?.jobs.pending ?? 0}
            icon={Clock}
            color="bg-yellow-100 text-yellow-700"
          />
          <StatCard
            label="Przetworzone"
            value={status?.jobs.extracted ?? 0}
            icon={CheckCircle2}
            color="bg-green-100 text-green-700"
          />
          <StatCard
            label="Lacznie ofert"
            value={status?.jobs.total ?? 0}
            icon={AlertTriangle}
            color="bg-gray-100 text-gray-700"
          />
        </div>

        {status && status.jobs.total > 0 && (
          <div className="mt-3">
            <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
              <span>Postep: {status.jobs.extracted}/{status.jobs.total}</span>
              <span>({status.jobs.total > 0 ? Math.round((status.jobs.extracted / status.jobs.total) * 100) : 0}%)</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${status.jobs.total > 0 ? (status.jobs.extracted / status.jobs.total) * 100 : 0}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="bg-gray-50 border rounded-lg p-4 text-sm text-gray-600">
        <p className="font-medium text-gray-700 mb-1">Jak to dziala?</p>
        <ul className="list-disc ml-5 space-y-1">
          <li>Ekstrakcja CV uruchamia sie automatycznie co 2 minuty (scheduler)</li>
          <li>Ekstrakcja ofert uruchamia sie automatycznie co 5 minut (scheduler)</li>
          <li>Przycisk &quot;Uruchom ekstrakcje&quot; wymusza natychmiastowe przetworzenie</li>
          <li>Dane odswiezaja sie co 3s podczas przetwarzania, co 15s normalnie</li>
        </ul>
      </div>
    </div>
  );
}
