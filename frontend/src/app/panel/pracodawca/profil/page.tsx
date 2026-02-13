"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect, useRef } from "react";
import { Upload, Building2 } from "lucide-react";
import api from "@/services/api";
import type { EmployerProfile, Canton } from "@/types/api";

const COMPANY_SIZES = ["1-10", "11-50", "51-200", "201-500", "500+"];

export default function EmployerProfilePage() {
  const queryClient = useQueryClient();
  const logoInputRef = useRef<HTMLInputElement>(null);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const { data: profile, isLoading } = useQuery({
    queryKey: ["employer-profile"],
    queryFn: () => api.get<EmployerProfile>("/employer/profile").then((r) => r.data),
  });

  const { data: cantons } = useQuery({
    queryKey: ["cantons"],
    queryFn: () => api.get<Canton[]>("/jobs/cantons").then((r) => r.data),
    staleTime: 24 * 60 * 60 * 1000,
  });

  const [form, setForm] = useState({
    company_name: "", description: "", website: "", industry: "",
    canton: "", city: "", address: "", uid_number: "", company_size: "",
  });

  useEffect(() => {
    if (profile) {
      setForm({
        company_name: profile.company_name || "",
        description: profile.description || "",
        website: profile.website || "",
        industry: profile.industry || "",
        canton: profile.canton || "",
        city: profile.city || "",
        address: profile.address || "",
        uid_number: profile.uid_number || "",
        company_size: profile.company_size || "",
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

      {success && <div className="bg-green-50 text-green-700 px-4 py-3 rounded-lg mb-4 text-sm">{success}</div>}
      {error && <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">{error}</div>}

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

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Strona internetowa</label>
            <input type="url" value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500"
              placeholder="https://..." />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Branża</label>
            <input type="text" value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500"
              placeholder="np. IT, Budownictwo..." />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Kanton</label>
            <select value={form.canton} onChange={(e) => setForm({ ...form, canton: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none">
              <option value="">Wybierz...</option>
              {cantons?.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Miasto</label>
            <input type="text" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Adres</label>
          <input type="text" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Numer UID (CHE-...)</label>
            <input type="text" value={form.uid_number} onChange={(e) => setForm({ ...form, uid_number: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500"
              placeholder="CHE-123.456.789" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Wielkość firmy</label>
            <select value={form.company_size} onChange={(e) => setForm({ ...form, company_size: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none">
              <option value="">Wybierz...</option>
              {COMPANY_SIZES.map((size) => <option key={size} value={size}>{size} pracowników</option>)}
            </select>
          </div>
        </div>

        <button type="submit" disabled={mutation.isPending}
          className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 font-medium text-sm disabled:opacity-50">
          {mutation.isPending ? "Zapisywanie..." : "Zapisz zmiany"}
        </button>
      </form>
    </div>
  );
}
