"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import api from "@/services/api";
import { WORK_PERMITS } from "@/lib/utils";
import type { WorkerProfile, Canton } from "@/types/api";

export default function WorkerProfilePage() {
  const queryClient = useQueryClient();
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const { data: profile, isLoading } = useQuery({
    queryKey: ["worker-profile"],
    queryFn: () => api.get<WorkerProfile>("/worker/profile").then((r) => r.data),
  });

  const { data: cantons } = useQuery({
    queryKey: ["cantons"],
    queryFn: () => api.get<Canton[]>("/jobs/cantons").then((r) => r.data),
    staleTime: 24 * 60 * 60 * 1000,
  });

  const [form, setForm] = useState({
    first_name: "", last_name: "", phone: "", canton: "",
    work_permit: "", experience_years: 0, bio: "", industry: "",
  });

  useEffect(() => {
    if (profile) {
      setForm({
        first_name: profile.first_name || "",
        last_name: profile.last_name || "",
        phone: profile.phone || "",
        canton: profile.canton || "",
        work_permit: profile.work_permit || "",
        experience_years: profile.experience_years || 0,
        bio: profile.bio || "",
        industry: profile.industry || "",
      });
    }
  }, [profile]);

  const mutation = useMutation({
    mutationFn: (data: typeof form) => api.put("/worker/profile", data),
    onSuccess: () => {
      setSuccess("Profil zaktualizowany");
      setError("");
      queryClient.invalidateQueries({ queryKey: ["worker-profile"] });
      setTimeout(() => setSuccess(""), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || "Błąd zapisu");
      setSuccess("");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(form);
  };

  if (isLoading) {
    return <div className="animate-pulse h-96 bg-gray-100 rounded-lg" />;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Mój profil</h1>

      {success && <div className="bg-green-50 text-green-700 px-4 py-3 rounded-lg mb-4 text-sm">{success}</div>}
      {error && <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">{error}</div>}

      <form onSubmit={handleSubmit} className="bg-white border rounded-lg p-6 space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Imię</label>
            <input type="text" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nazwisko</label>
            <input type="text" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Telefon</label>
          <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500" placeholder="+41 79 123 45 67" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Kanton zamieszkania</label>
            <select value={form.canton} onChange={(e) => setForm({ ...form, canton: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none">
              <option value="">Wybierz...</option>
              {cantons?.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Pozwolenie na pracę</label>
            <select value={form.work_permit} onChange={(e) => setForm({ ...form, work_permit: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none">
              <option value="">Wybierz...</option>
              {Object.entries(WORK_PERMITS).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lata doświadczenia</label>
            <input type="number" min={0} max={50} value={form.experience_years}
              onChange={(e) => setForm({ ...form, experience_years: parseInt(e.target.value) || 0 })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Branża</label>
            <input type="text" value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500" placeholder="np. Budownictwo" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">O mnie</label>
          <textarea rows={4} value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500 resize-none"
            placeholder="Krótki opis doświadczenia i umiejętności..." />
        </div>

        <button type="submit" disabled={mutation.isPending}
          className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 font-medium text-sm disabled:opacity-50">
          {mutation.isPending ? "Zapisywanie..." : "Zapisz zmiany"}
        </button>
      </form>
    </div>
  );
}
