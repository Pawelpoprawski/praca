"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect, useRef } from "react";
import { Upload, Building2 } from "lucide-react";
import api from "@/services/api";
import type { EmployerProfile } from "@/types/api";

export default function EmployerProfilePage() {
  const queryClient = useQueryClient();
  const logoInputRef = useRef<HTMLInputElement>(null);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const { data: profile, isLoading } = useQuery({
    queryKey: ["employer-profile"],
    queryFn: () => api.get<EmployerProfile>("/employer/profile").then((r) => r.data),
  });

  const [form, setForm] = useState({
    company_name: "", description: "", website: "",
  });

  useEffect(() => {
    if (profile) {
      setForm({
        company_name: profile.company_name || "",
        description: profile.description || "",
        website: profile.website || "",
      });
    }
  }, [profile]);

  const mutation = useMutation({
    mutationFn: (data: typeof form) => api.put("/employer/profile", data),
    onSuccess: () => {
      setSuccess("Profil zaktualizowany");
      setError("");
      queryClient.invalidateQueries({ queryKey: ["employer-profile"] });
      setTimeout(() => setSuccess(""), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || "Błąd zapisu");
      setSuccess("");
    },
  });

  const logoMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return api.post("/employer/profile/logo", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    },
    onSuccess: () => {
      setSuccess("Logo zostało przesłane");
      queryClient.invalidateQueries({ queryKey: ["employer-profile"] });
      setTimeout(() => setSuccess(""), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || "Błąd przesyłania logo");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(form);
  };

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setError("Dozwolone formaty: JPG, PNG, WebP");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setError("Maksymalny rozmiar logo: 2 MB");
      return;
    }
    logoMutation.mutate(file);
  };

  if (isLoading) {
    return <div className="animate-pulse h-96 bg-gray-100 rounded-lg" />;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Profil firmy</h1>

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4 text-sm flex items-center gap-2" role="status">
          <span className="flex-shrink-0">✓</span>
          {success}
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm flex items-center gap-2" role="alert">
          <span className="flex-shrink-0">⚠</span>
          {error}
        </div>
      )}

      {/* Logo */}
      <div className="bg-white border rounded-lg p-6 mb-6">
        <h2 className="font-semibold text-gray-900 mb-4">Logo firmy</h2>
        <div className="flex items-center gap-4">
          <div className="w-20 h-20 bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden">
            {profile?.logo_url ? (
              <img src={profile.logo_url} alt="Logo" className="w-full h-full object-cover" />
            ) : (
              <Building2 className="w-8 h-8 text-gray-400" />
            )}
          </div>
          <div>
            <button
              onClick={() => logoInputRef.current?.click()}
              disabled={logoMutation.isPending}
              className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 font-medium disabled:opacity-50"
            >
              {logoMutation.isPending ? "Przesyłanie..." : "Zmień logo"}
            </button>
            <p className="text-xs text-gray-500 mt-1">JPG, PNG lub WebP, max 2 MB</p>
          </div>
          <input ref={logoInputRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={handleLogoChange} className="hidden" />
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white border rounded-lg p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nazwa firmy</label>
          <input type="text" value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500" />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Opis firmy</label>
          <textarea rows={4} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500 resize-none"
            placeholder="Krótki opis Twojej firmy..." />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Strona internetowa</label>
          <input type="url" value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500"
            placeholder="https://..." />
        </div>

        <button type="submit" disabled={mutation.isPending}
          className="w-full sm:w-auto bg-red-600 text-white px-6 py-2.5 rounded-lg hover:bg-red-700 font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          {mutation.isPending ? "Zapisywanie..." : "Zapisz zmiany"}
        </button>
      </form>
    </div>
  );
}
