"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Plus, X } from "lucide-react";
import Link from "next/link";
import api from "@/services/api";
import { CONTRACT_TYPES, WORK_PERMITS } from "@/lib/utils";
import type { Canton, CategoryBrief } from "@/types/api";

const LANG_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];
const LANGUAGES = ["de", "fr", "it", "en", "pl", "pt", "es"];
const LANG_NAMES: Record<string, string> = {
  de: "Niemiecki", fr: "Francuski", it: "Włoski", en: "Angielski",
  pl: "Polski", pt: "Portugalski", es: "Hiszpański",
};

export default function NewJobPage() {
  const router = useRouter();
  const [error, setError] = useState("");

  const { data: cantons } = useQuery({
    queryKey: ["cantons"],
    queryFn: () => api.get<Canton[]>("/jobs/cantons").then((r) => r.data),
    staleTime: 24 * 60 * 60 * 1000,
  });

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<CategoryBrief[]>("/jobs/categories").then((r) => r.data),
    staleTime: 24 * 60 * 60 * 1000,
  });

  const [form, setForm] = useState({
    title: "",
    description: "",
    canton: "",
    city: "",
    category_id: "",
    contract_type: "full_time",
    salary_min: "",
    salary_max: "",
    salary_type: "monthly",
    experience_min: 0,
    work_permit_required: "",
    work_permit_sponsored: false,
    is_remote: "no",
    languages_required: [] as { lang: string; level: string }[],
    contact_email: "",
    apply_via: "portal",
    external_url: "",
  });

  const mutation = useMutation({
    mutationFn: (data: any) => api.post("/employer/jobs", data),
    onSuccess: () => {
      router.push("/panel/pracodawca/ogloszenia");
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || "Błąd tworzenia ogłoszenia");
    },
  });

  const addLanguage = () => {
    setForm({ ...form, languages_required: [...form.languages_required, { lang: "de", level: "B1" }] });
  };

  const removeLanguage = (index: number) => {
    setForm({ ...form, languages_required: form.languages_required.filter((_, i) => i !== index) });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    mutation.mutate({
      ...form,
      salary_min: form.salary_min ? parseInt(form.salary_min) : null,
      salary_max: form.salary_max ? parseInt(form.salary_max) : null,
      category_id: form.category_id || null,
      work_permit_required: form.work_permit_required || null,
      contact_email: form.contact_email || null,
      external_url: form.external_url || null,
    });
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link href="/panel/pracodawca/ogloszenia" className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Nowe ogłoszenie</h1>
      </div>

      {error && <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">{error}</div>}

      <form onSubmit={handleSubmit} className="bg-white border rounded-lg p-6 space-y-6">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Tytuł stanowiska *</label>
          <input type="text" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500"
            placeholder="np. Monter instalacji sanitarnych" />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Opis stanowiska *</label>
          <textarea rows={6} required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500 resize-none"
            placeholder="Opisz zakres obowiązków, wymagania, oferowane warunki..." />
        </div>

        {/* Category & Contract */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Kategoria</label>
            <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none">
              <option value="">Wybierz...</option>
              {categories?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Typ umowy *</label>
            <select value={form.contract_type} onChange={(e) => setForm({ ...form, contract_type: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none">
              {Object.entries(CONTRACT_TYPES).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Location */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Kanton *</label>
            <select required value={form.canton} onChange={(e) => setForm({ ...form, canton: e.target.value })}
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
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Praca zdalna</label>
            <select value={form.is_remote} onChange={(e) => setForm({ ...form, is_remote: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none">
              <option value="no">Nie</option>
              <option value="yes">Tak</option>
              <option value="hybrid">Hybrydowa</option>
            </select>
          </div>
        </div>

        {/* Salary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Wynagrodzenie od (CHF)</label>
            <input type="number" min={0} value={form.salary_min} onChange={(e) => setForm({ ...form, salary_min: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Wynagrodzenie do (CHF)</label>
            <input type="number" min={0} value={form.salary_max} onChange={(e) => setForm({ ...form, salary_max: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Okres</label>
            <select value={form.salary_type} onChange={(e) => setForm({ ...form, salary_type: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none">
              <option value="monthly">Miesięcznie</option>
              <option value="yearly">Rocznie</option>
              <option value="hourly">Za godzinę</option>
              <option value="negotiable">Do uzgodnienia</option>
            </select>
          </div>
        </div>

        {/* Experience & Work permit */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Min. doświadczenie (lata)</label>
            <input type="number" min={0} max={50} value={form.experience_min}
              onChange={(e) => setForm({ ...form, experience_min: parseInt(e.target.value) || 0 })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Wymagane pozwolenie</label>
            <select value={form.work_permit_required} onChange={(e) => setForm({ ...form, work_permit_required: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none">
              <option value="">Bez wymagań</option>
              {Object.entries(WORK_PERMITS).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 px-3 py-2">
              <input type="checkbox" checked={form.work_permit_sponsored}
                onChange={(e) => setForm({ ...form, work_permit_sponsored: e.target.checked })}
                className="rounded border-gray-300 text-red-600 focus:ring-red-500" />
              <span className="text-sm text-gray-700">Sponsoring pozwolenia</span>
            </label>
          </div>
        </div>

        {/* Languages */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-700">Wymagane języki</label>
            <button type="button" onClick={addLanguage}
              className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1">
              <Plus className="w-3 h-3" /> Dodaj język
            </button>
          </div>
          {form.languages_required.map((lr, i) => (
            <div key={i} className="flex items-center gap-2 mb-2">
              <select value={lr.lang} onChange={(e) => {
                const updated = [...form.languages_required];
                updated[i] = { ...updated[i], lang: e.target.value };
                setForm({ ...form, languages_required: updated });
              }} className="px-3 py-2 border rounded-lg text-sm outline-none">
                {LANGUAGES.map((l) => <option key={l} value={l}>{LANG_NAMES[l]}</option>)}
              </select>
              <select value={lr.level} onChange={(e) => {
                const updated = [...form.languages_required];
                updated[i] = { ...updated[i], level: e.target.value };
                setForm({ ...form, languages_required: updated });
              }} className="px-3 py-2 border rounded-lg text-sm outline-none">
                {LANG_LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
              <button type="button" onClick={() => removeLanguage(i)}
                className="p-2 text-gray-400 hover:text-red-600">
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>

        {/* Apply method */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sposób aplikowania</label>
            <select value={form.apply_via} onChange={(e) => setForm({ ...form, apply_via: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none">
              <option value="portal">Przez portal</option>
              <option value="email">Email</option>
              <option value="external_url">Zewnętrzny link</option>
            </select>
          </div>
          {form.apply_via === "email" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email kontaktowy</label>
              <input type="email" value={form.contact_email} onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500" />
            </div>
          )}
          {form.apply_via === "external_url" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Link do aplikowania</label>
              <input type="url" value={form.external_url} onChange={(e) => setForm({ ...form, external_url: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500"
                placeholder="https://..." />
            </div>
          )}
        </div>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={mutation.isPending}
            className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 font-medium text-sm disabled:opacity-50">
            {mutation.isPending ? "Publikowanie..." : "Opublikuj ogłoszenie"}
          </button>
          <Link href="/panel/pracodawca/ogloszenia"
            className="px-6 py-2 border rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50">
            Anuluj
          </Link>
        </div>
      </form>
    </div>
  );
}
