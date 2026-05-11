"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  BellRing, Plus, Trash2, Pencil, X, Power,
} from "lucide-react";
import api from "@/services/api";
import { formatDate } from "@/lib/utils";
import type { JobAlert, JobAlertList, Canton, CategoryBrief, MessageResponse } from "@/types/api";

const FREQUENCY_LABELS: Record<string, string> = {
  instant: "Natychmiast",
  daily: "Codziennie",
  weekly: "Co tydzień",
};

const WORK_MODE_LABELS: Record<string, string> = {
  no: "Stacjonarnie",
  yes: "Zdalnie",
  hybrid: "Hybrydowo",
};

const alertSchema = z.object({
  name: z.string().min(1, "Nazwa jest wymagana").max(255),
  frequency: z.enum(["instant", "daily", "weekly"]),
  category_id: z.string().optional().or(z.literal("")),
  canton: z.string().optional().or(z.literal("")),
  min_salary: z.number().min(0).optional(),
  max_salary: z.number().min(0).optional(),
  keywords: z.string().max(500).optional().or(z.literal("")),
  work_mode: z.string().optional().or(z.literal("")),
  permit_sponsorship: z.boolean().optional(),
});

type AlertFormData = z.infer<typeof alertSchema>;

function buildPayload(data: AlertFormData) {
  return {
    name: data.name,
    frequency: data.frequency,
    filters: {
      category_id: data.category_id || null,
      canton: data.canton || null,
      min_salary: data.min_salary || null,
      max_salary: data.max_salary || null,
      keywords: data.keywords || null,
      work_mode: data.work_mode || null,
      permit_sponsorship: data.permit_sponsorship || null,
    },
  };
}

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingAlert, setEditingAlert] = useState<JobAlert | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const { data: alertData, isLoading } = useQuery({
    queryKey: ["job-alerts"],
    queryFn: () =>
      api.get<JobAlertList>("/worker/job-alerts").then((r) => r.data),
  });

  const { data: cantons } = useQuery({
    queryKey: ["cantons"],
    queryFn: () => api.get<Canton[]>("/jobs/cantons").then((r) => r.data),
    staleTime: 24 * 60 * 60 * 1000,
  });

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: () =>
      api.get<CategoryBrief[]>("/jobs/categories").then((r) => r.data),
    staleTime: 24 * 60 * 60 * 1000,
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors: formErrors },
  } = useForm<AlertFormData>({
    resolver: zodResolver(alertSchema) as any,
    defaultValues: {
      name: "",
      frequency: "daily",
      category_id: "",
      canton: "",
      min_salary: 0,
      max_salary: 0,
      keywords: "",
      work_mode: "",
      permit_sponsorship: false,
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: AlertFormData) =>
      api.post("/worker/job-alerts", buildPayload(data)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job-alerts"] });
      setShowForm(false);
      setSuccess("Alert został utworzony");
      setError("");
      reset();
      setTimeout(() => setSuccess(""), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || "Nie udało się utworzyć alertu");
      setSuccess("");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: AlertFormData }) =>
      api.put(`/worker/job-alerts/${id}`, buildPayload(data)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job-alerts"] });
      setEditingAlert(null);
      setShowForm(false);
      setSuccess("Alert został zaktualizowany");
      setError("");
      reset();
      setTimeout(() => setSuccess(""), 3000);
    },
    onError: (err: any) => {
      setError(
        err.response?.data?.detail || "Nie udało się zaktualizować alertu"
      );
      setSuccess("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      api.delete<MessageResponse>(`/worker/job-alerts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job-alerts"] });
      setSuccess("Alert został usunięty");
      setError("");
      setTimeout(() => setSuccess(""), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || "Nie udało się usunąć alertu");
    },
  });

  const toggleMutation = useMutation({
    mutationFn: (id: string) =>
      api.patch<JobAlert>(`/worker/job-alerts/${id}/toggle`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job-alerts"] });
    },
    onError: (err: any) => {
      setError(
        err.response?.data?.detail || "Nie udało się zmienić statusu alertu"
      );
    },
  });

  const openCreateForm = () => {
    setEditingAlert(null);
    reset({
      name: "",
      frequency: "daily",
      category_id: "",
      canton: "",
      min_salary: 0,
      max_salary: 0,
      keywords: "",
      work_mode: "",
      permit_sponsorship: false,
    });
    setShowForm(true);
    setError("");
  };

  const openEditForm = (alert: JobAlert) => {
    setEditingAlert(alert);
    reset({
      name: alert.name,
      frequency: alert.frequency as "instant" | "daily" | "weekly",
      category_id: alert.filters.category_id || "",
      canton: alert.filters.canton || "",
      min_salary: alert.filters.min_salary || 0,
      max_salary: alert.filters.max_salary || 0,
      keywords: alert.filters.keywords || "",
      work_mode: alert.filters.work_mode || "",
      permit_sponsorship: alert.filters.permit_sponsorship || false,
    });
    setShowForm(true);
    setError("");
  };

  const onSubmit = (data: AlertFormData) => {
    if (editingAlert) {
      updateMutation.mutate({ id: editingAlert.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const cancelForm = () => {
    setShowForm(false);
    setEditingAlert(null);
    setError("");
    reset();
  };

  const canCreate =
    alertData ? alertData.count < alertData.max_alerts : true;

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold font-display text-[#0D2240] mb-6">
          Alerty o pracy
        </h1>
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="bg-white border rounded-lg p-5 animate-pulse"
            >
              <div className="h-5 bg-gray-200 rounded w-48 mb-3" />
              <div className="h-4 bg-gray-100 rounded w-32" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const alerts = alertData?.alerts || [];

  // Helper: build filter description
  const describeFilters = (alert: JobAlert) => {
    const parts: string[] = [];
    const f = alert.filters;
    if (f.category_id && categories) {
      const cat = categories.find((c) => c.id === f.category_id);
      if (cat) parts.push(cat.name);
    }
    if (f.canton && cantons) {
      const c = cantons.find((ct) => ct.value === f.canton);
      parts.push(c ? c.label : f.canton);
    }
    if (f.min_salary || f.max_salary) {
      if (f.min_salary && f.max_salary) {
        parts.push(`${f.min_salary}-${f.max_salary} CHF`);
      } else if (f.min_salary) {
        parts.push(`od ${f.min_salary} CHF`);
      } else {
        parts.push(`do ${f.max_salary} CHF`);
      }
    }
    if (f.work_mode) {
      parts.push(WORK_MODE_LABELS[f.work_mode] || f.work_mode);
    }
    if (f.keywords) {
      parts.push(`"${f.keywords}"`);
    }
    if (f.permit_sponsorship) {
      parts.push("Sponsoring pozwolenia");
    }
    return parts.length > 0 ? parts.join(" | ") : "Brak filtrów";
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold font-display text-[#0D2240]">Alerty o pracy</h1>
        {!showForm && canCreate && (
          <button
            onClick={openCreateForm}
            className="flex items-center gap-2 bg-[#E1002A] text-white px-4 py-2 rounded-lg hover:bg-[#B8001F] text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nowy alert
          </button>
        )}
      </div>

      {/* Info bar */}
      <div className="bg-blue-50 text-blue-700 px-4 py-3 rounded-lg mb-4 text-sm">
        Otrzymuj powiadomienia email o nowych ofertach pasujących do Twoich
        kryteriów. Możesz utworzyć maksymalnie {alertData?.max_alerts || 5}{" "}
        alertów ({alertData?.count || 0}/{alertData?.max_alerts || 5}).
      </div>

      {success && (
        <div className="bg-green-50 text-green-700 px-4 py-3 rounded-lg mb-4 text-sm">
          {success}
        </div>
      )}
      {error && (
        <div className="bg-[#FFF0F3] text-[#E1002A] px-4 py-3 rounded-lg mb-4 text-sm">
          {error}
        </div>
      )}

      {/* Create / Edit form */}
      {showForm && (
        <div className="bg-white border rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-semibold font-display text-gray-800">
              {editingAlert ? "Edytuj alert" : "Nowy alert"}
            </h2>
            <button
              onClick={cancelForm}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Name + Frequency */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nazwa alertu *
                </label>
                <input
                  type="text"
                  {...register("name")}
                  className={`w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-[#E1002A]/20 ${
                    formErrors.name ? "border-[#E1002A]" : ""
                  }`}
                  placeholder='np. "Praca IT w Zurychu"'
                />
                {formErrors.name && (
                  <p className="text-red-500 text-xs mt-1">
                    {formErrors.name.message}
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Częstotliwość
                </label>
                <select
                  {...register("frequency")}
                  className="w-full px-3 py-2 border rounded-lg text-sm outline-none"
                >
                  <option value="instant">Natychmiast</option>
                  <option value="daily">Codziennie</option>
                  <option value="weekly">Co tydzień</option>
                </select>
              </div>
            </div>

            {/* Filters */}
            <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
              Filtry
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Kategoria
                </label>
                <select
                  {...register("category_id")}
                  className="w-full px-3 py-2 border rounded-lg text-sm outline-none"
                >
                  <option value="">Wszystkie kategorie</option>
                  {categories?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Kanton
                </label>
                <select
                  {...register("canton")}
                  className="w-full px-3 py-2 border rounded-lg text-sm outline-none"
                >
                  <option value="">Wszystkie kantony</option>
                  {cantons?.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Minimalne wynagrodzenie (CHF)
                </label>
                <input
                  type="number"
                  min={0}
                  {...register("min_salary")}
                  className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-[#E1002A]/20"
                  placeholder="np. 4000"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Maksymalne wynagrodzenie (CHF)
                </label>
                <input
                  type="number"
                  min={0}
                  {...register("max_salary")}
                  className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-[#E1002A]/20"
                  placeholder="np. 10000"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Słowa kluczowe
                </label>
                <input
                  type="text"
                  {...register("keywords")}
                  className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-[#E1002A]/20"
                  placeholder='np. "Python developer"'
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tryb pracy
                </label>
                <select
                  {...register("work_mode")}
                  className="w-full px-3 py-2 border rounded-lg text-sm outline-none"
                >
                  <option value="">Dowolny</option>
                  <option value="no">Stacjonarnie</option>
                  <option value="yes">Zdalnie</option>
                  <option value="hybrid">Hybrydowo</option>
                </select>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="permit_sponsorship"
                {...register("permit_sponsorship")}
                className="w-4 h-4 text-[#E1002A] border-gray-300 rounded focus:ring-[#E1002A]/20"
              />
              <label
                htmlFor="permit_sponsorship"
                className="text-sm text-gray-700"
              >
                Tylko oferty ze sponsoringiem pozwolenia na pracę
              </label>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={
                  createMutation.isPending || updateMutation.isPending
                }
                className="bg-[#E1002A] text-white px-6 py-2 rounded-lg hover:bg-[#B8001F] font-medium text-sm disabled:opacity-50 transition-colors"
              >
                {createMutation.isPending || updateMutation.isPending
                  ? "Zapisywanie..."
                  : editingAlert
                    ? "Zapisz zmiany"
                    : "Utwórz alert"}
              </button>
              <button
                type="button"
                onClick={cancelForm}
                className="px-6 py-2 border rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
              >
                Anuluj
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Alerts list */}
      {alerts.length > 0 ? (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`bg-white border rounded-lg p-5 transition-opacity ${
                !alert.is_active ? "opacity-60" : ""
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-900 truncate">
                      {alert.name}
                    </h3>
                    <span
                      className={`inline-block text-xs px-2 py-0.5 rounded font-medium ${
                        alert.is_active
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {alert.is_active ? "Aktywny" : "Wyłączony"}
                    </span>
                    <span className="inline-block text-xs px-2 py-0.5 rounded font-medium bg-blue-100 text-blue-800">
                      {FREQUENCY_LABELS[alert.frequency] || alert.frequency}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mb-2">
                    {describeFilters(alert)}
                  </p>
                  <p className="text-xs text-gray-400">
                    Utworzono: {formatDate(alert.created_at)}
                    {alert.last_sent_at && (
                      <> | Ostatnio wysłano: {formatDate(alert.last_sent_at)}</>
                    )}
                  </p>
                </div>

                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    onClick={() => toggleMutation.mutate(alert.id)}
                    title={alert.is_active ? "Wyłącz alert" : "Włącz alert"}
                    className={`p-2 rounded-lg transition-colors ${
                      alert.is_active
                        ? "text-green-600 hover:bg-green-50"
                        : "text-gray-400 hover:bg-gray-100"
                    }`}
                  >
                    <Power className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => openEditForm(alert)}
                    title="Edytuj"
                    className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm("Czy na pewno chcesz usunąć ten alert?")) {
                        deleteMutation.mutate(alert.id);
                      }
                    }}
                    title="Usuń"
                    className="p-2 text-red-500 hover:bg-[#FFF0F3] rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        !showForm && (
          <div className="bg-white border rounded-lg px-5 py-12 text-center">
            <BellRing className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 mb-2">
              Nie masz jeszcze żadnych alertów o pracy
            </p>
            <p className="text-sm text-gray-400 mb-4">
              Utwórz alert, aby otrzymywać powiadomienia o nowych ofertach
              pasujących do Twoich kryteriów.
            </p>
            <button
              onClick={openCreateForm}
              className="text-sm text-[#E1002A] hover:underline font-medium"
            >
              Utwórz pierwszy alert
            </button>
          </div>
        )
      )}
    </div>
  );
}
