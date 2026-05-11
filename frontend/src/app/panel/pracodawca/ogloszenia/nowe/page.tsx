"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { useState, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  Plus,
  X,
  Sparkles,
  FileText,
  MapPin,
  Banknote,
  Briefcase,
  Languages,
  Send,
  ChevronDown,
  ChevronUp,
  Loader2,
  CheckCircle2,
  AlertCircle,
  ClipboardPaste,
  Eye,
  Pencil,
} from "lucide-react";
import Link from "next/link";
import api from "@/services/api";
import { CONTRACT_TYPES } from "@/lib/utils";
import type { Canton, CategoryBrief } from "@/types/api";

const LANG_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];
const LANGUAGES = ["de", "fr", "it", "en", "pl", "pt", "es"];
const LANG_NAMES: Record<string, string> = {
  de: "Niemiecki",
  fr: "Francuski",
  it: "Włoski",
  en: "Angielski",
  pl: "Polski",
  pt: "Portugalski",
  es: "Hiszpański",
};

const AI_STAGES = [
  "Analizujemy treść ogłoszenia...",
  "Wyciągamy kluczowe informacje...",
  "Poprawiamy literówki i formatowanie...",
  "Dopasowujemy kategorię i lokalizację...",
  "Finalizujemy dane...",
];

interface AIParseResult {
  title: string | null;
  description: string | null;
  city: string | null;
  canton: string | null;
  contract_type: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_type: string | null;
  is_remote: string | null;
  experience_min: number | null;
  requirements: string[];
  benefits: string[];
  languages: { lang: string; level: string }[];
  category_slug: string | null;
  car_required: boolean;
  driving_license_required: boolean;
}

// --- Section Card Component ---
function SectionCard({
  icon: Icon,
  title,
  children,
  defaultOpen = true,
}: {
  icon: React.ElementType;
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-[#FFF0F3] rounded-lg flex items-center justify-center flex-shrink-0">
            <Icon className="w-5 h-5 text-[#E1002A]" />
          </div>
          <h2 className="text-base font-semibold font-display text-[#0D2240]">{title}</h2>
        </div>
        {open ? (
          <ChevronUp className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        )}
      </button>
      {open && <div className="px-5 pb-5 space-y-4">{children}</div>}
    </div>
  );
}

// --- AI Progress Bar ---
function AIProgressBar() {
  const [stage, setStage] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const progressInterval = setInterval(() => {
      setProgress((p) => {
        if (p >= 95) return 95;
        return p + Math.random() * 3 + 0.5;
      });
    }, 200);

    const stageInterval = setInterval(() => {
      setStage((s) => (s < AI_STAGES.length - 1 ? s + 1 : s));
    }, 2500);

    return () => {
      clearInterval(progressInterval);
      clearInterval(stageInterval);
    };
  }, []);

  return (
    <div className="space-y-3 py-2">
      <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
        <div
          className="bg-gradient-to-r from-red-500 to-orange-500 h-full rounded-full transition-all duration-300 ease-out"
          style={{ width: `${Math.min(progress, 95)}%` }}
        />
      </div>
      <div className="flex items-center gap-2">
        <Loader2 className="w-4 h-4 animate-spin text-[#E1002A]" />
        <span className="text-sm text-gray-600 animate-pulse">
          {AI_STAGES[stage]}
        </span>
      </div>
    </div>
  );
}

// --- Input styling helpers ---
const inputClass =
  "w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-[#E1002A]/20 focus:border-[#E1002A] transition-shadow bg-white placeholder:text-gray-400";
const selectClass =
  "w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-[#E1002A]/20 focus:border-[#E1002A] transition-shadow bg-white";
const labelClass = "block text-sm font-medium text-gray-700 mb-1.5";

export default function NewJobPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const copyId = searchParams.get("copy");
  const [error, setError] = useState("");
  const [aiOpen, setAiOpen] = useState(false);
  const [aiText, setAiText] = useState("");
  const [aiError, setAiError] = useState("");
  const [aiFilled, setAiFilled] = useState(false);
  const [descPreview, setDescPreview] = useState(false);
  const [copyLoaded, setCopyLoaded] = useState(false);

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
    car_required: false,
    driving_license_required: false,
    languages_required: [] as { lang: string; level: string }[],
    contact_email: "",
    apply_via: "portal",
    external_url: "",
  });

  // Load data from copied job
  useEffect(() => {
    if (!copyId || copyLoaded) return;
    api.get(`/employer/jobs/${copyId}/copy`).then((r) => {
      const d = r.data;
      setForm({
        title: d.title || "",
        description: d.description || "",
        canton: d.canton || "",
        city: d.city || "",
        category_id: d.category_id || "",
        contract_type: d.contract_type || "full_time",
        salary_min: d.salary_min != null ? String(d.salary_min) : "",
        salary_max: d.salary_max != null ? String(d.salary_max) : "",
        salary_type: d.salary_type || "monthly",
        experience_min: d.experience_min ?? 0,
        car_required: d.car_required ?? false,
        driving_license_required: d.driving_license_required ?? false,
        languages_required: d.languages_required || [],
        contact_email: d.contact_email || "",
        apply_via: d.apply_via || "portal",
        external_url: d.external_url || "",
      });
      setCopyLoaded(true);
      if (d.description && /<[a-z][\s\S]*>/i.test(d.description)) {
        setDescPreview(true);
      }
    }).catch(() => {});
  }, [copyId, copyLoaded]);

  // AI parsing mutation
  const aiMutation = useMutation({
    mutationFn: (text: string) =>
      api
        .post<AIParseResult>("/employer/parse-job-posting", { text })
        .then((r) => r.data),
    onSuccess: (data) => {
      setAiError("");

      // Find category_id by slug
      let categoryId = "";
      if (data.category_slug && categories) {
        const matched = categories.find((c) => c.slug === data.category_slug);
        if (matched) {
          categoryId = matched.id;
        }
      }

      setForm({
        ...form,
        title: data.title || form.title,
        description: data.description || form.description,
        canton: data.canton || form.canton,
        city: data.city || form.city,
        category_id: categoryId || form.category_id,
        contract_type: data.contract_type || form.contract_type,
        salary_min:
          data.salary_min != null ? String(data.salary_min) : form.salary_min,
        salary_max:
          data.salary_max != null ? String(data.salary_max) : form.salary_max,
        salary_type: data.salary_type || form.salary_type,
        experience_min:
          data.experience_min != null
            ? data.experience_min
            : form.experience_min,
        languages_required:
          data.languages && data.languages.length > 0
            ? data.languages
            : form.languages_required,
        car_required: data.car_required ?? form.car_required,
        driving_license_required: data.driving_license_required ?? form.driving_license_required,
      });

      setAiFilled(true);
      setAiOpen(false);
      // Show preview after AI fills the form
      if (data.description) {
        setDescPreview(true);
      }
    },
    onError: (err: any) => {
      setAiError(
        err.response?.data?.detail ||
          "Nie udało się przeanalizować ogłoszenia. Spróbuj ponownie."
      );
    },
  });

  const handleAiParse = () => {
    if (aiText.trim().length < 50) {
      setAiError(
        "Tekst ogłoszenia jest za krótki. Wklej pełną treść ogłoszenia (min. 50 znaków)."
      );
      return;
    }
    setAiError("");
    aiMutation.mutate(aiText);
  };

  const mutation = useMutation({
    mutationFn: (data: any) => api.post("/employer/jobs", data),
    onSuccess: () => {
      router.push("/panel/pracodawca/ogloszenia");
    },
    onError: (err: any) => {
      setError(
        err.response?.data?.detail || "Błąd tworzenia ogłoszenia"
      );
    },
  });

  const addLanguage = () => {
    setForm({
      ...form,
      languages_required: [
        ...form.languages_required,
        { lang: "de", level: "B1" },
      ],
    });
  };

  const removeLanguage = (index: number) => {
    setForm({
      ...form,
      languages_required: form.languages_required.filter(
        (_, i) => i !== index
      ),
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    mutation.mutate({
      ...form,
      salary_min: form.salary_min ? parseInt(form.salary_min) : null,
      salary_max: form.salary_max ? parseInt(form.salary_max) : null,
      category_id: form.category_id || null,
      contact_email: form.contact_email || null,
      external_url: form.external_url || null,
    });
  };

  const hasHtml = /<[a-z][\s\S]*>/i.test(form.description);

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Link
          href="/panel/pracodawca/ogloszenia"
          className="p-2 hover:bg-gray-100 rounded-lg flex-shrink-0 transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </Link>
        <div>
          <h1 className="text-xl sm:text-2xl font-bold font-display text-[#0D2240]">
            {copyId ? "Kopiuj ogłoszenie" : "Nowe ogłoszenie"}
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {copyId ? "Sprawdź dane i opublikuj lub zmień co potrzebujesz" : "Wypełnij formularz lub wczytaj dane z innego portalu"}
          </p>
        </div>
      </div>

      {/* AI Import Section */}
      <div className="mb-6">
        <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-[#FFC2CD] rounded-xl overflow-hidden">
          <button
            type="button"
            onClick={() => setAiOpen(!aiOpen)}
            className="w-full flex items-center justify-between px-5 py-4 hover:from-red-100 hover:to-orange-100 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-[#E1002A] rounded-lg flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div className="text-left">
                <h2 className="text-base font-semibold font-display text-[#0D2240]">
                  Wczytaj za pomocą AI
                </h2>
                <p className="text-sm text-gray-600">
                  Wklej treść ogłoszenia z innego portalu — AI
                  wypełni formularz automatycznie
                </p>
              </div>
            </div>
            {aiOpen ? (
              <ChevronUp className="w-5 h-5 text-gray-500 flex-shrink-0 ml-3" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500 flex-shrink-0 ml-3" />
            )}
          </button>

          {aiOpen && (
            <div className="px-5 pb-5 space-y-4">
              <div className="flex items-start gap-2 bg-white/60 rounded-lg p-3 text-sm text-gray-600">
                <ClipboardPaste className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                <span>
                  Skopiuj treść ogłoszenia ze strony
                  internetowej lub innego portalu i wklej ją poniżej.
                  AI przeanalizuje tekst i wypełni wszystkie pola
                  formularza.
                </span>
              </div>

              <textarea
                rows={10}
                value={aiText}
                onChange={(e) => setAiText(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-[#E1002A]/20 focus:border-[#E1002A] resize-y bg-white placeholder:text-gray-400"
                placeholder="Wklej tutaj pełną treść ogłoszenia o pracę..."
              />

              {aiError && (
                <div className="flex items-start gap-2 bg-[#FFF0F3] text-[#B8001F] px-4 py-3 rounded-lg text-sm">
                  <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span>{aiError}</span>
                </div>
              )}

              {aiMutation.isPending ? (
                <AIProgressBar />
              ) : (
                <button
                  type="button"
                  onClick={handleAiParse}
                  disabled={aiText.trim().length < 50}
                  className="bg-[#E1002A] text-white px-5 py-2.5 rounded-lg hover:bg-[#B8001F] font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
                >
                  <Sparkles className="w-4 h-4" />
                  Analizuj i wypełnij formularz
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* AI filled notification */}
      {aiFilled && (
        <div className="flex items-start gap-3 bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-xl mb-6 text-sm">
          <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-green-600" />
          <div>
            <p className="font-medium">
              Formularz został wypełniony przez AI
            </p>
            <p className="text-green-700 mt-0.5">
              Sprawdź i popraw dane poniżej przed opublikowaniem
              ogłoszenia.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setAiFilled(false)}
            className="ml-auto text-green-600 hover:text-green-800 flex-shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 bg-[#FFF0F3] border border-[#FFC2CD] text-[#B8001F] px-4 py-3 rounded-xl mb-6 text-sm">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Basic Info */}
        <SectionCard icon={FileText} title="Podstawowe informacje">
          <div>
            <label className={labelClass}>Tytuł stanowiska *</label>
            <input
              type="text"
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className={inputClass}
              placeholder="np. Monter instalacji sanitarnych"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-sm font-medium text-gray-700">
                Opis stanowiska *
              </label>
              {hasHtml && (
                <div className="flex gap-1 bg-gray-100 rounded-lg p-0.5">
                  <button
                    type="button"
                    onClick={() => setDescPreview(false)}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                      !descPreview
                        ? "bg-white text-gray-900 shadow-sm"
                        : "text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    <Pencil className="w-3 h-3" />
                    Edytuj
                  </button>
                  <button
                    type="button"
                    onClick={() => setDescPreview(true)}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                      descPreview
                        ? "bg-white text-gray-900 shadow-sm"
                        : "text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    <Eye className="w-3 h-3" />
                    Podgląd
                  </button>
                </div>
              )}
            </div>

            {descPreview && hasHtml ? (
              <div
                className="w-full min-h-[200px] px-3.5 py-2.5 border border-gray-300 rounded-lg text-sm bg-white prose prose-sm prose-gray max-w-none cursor-pointer hover:border-gray-400 transition-colors"
                onClick={() => setDescPreview(false)}
                dangerouslySetInnerHTML={{ __html: form.description }}
              />
            ) : (
              <textarea
                rows={8}
                required
                value={form.description}
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
                className={`${inputClass} resize-y`}
                placeholder="Opisz zakres obowiązków, wymagania, oferowane warunki..."
              />
            )}
            <p className="text-xs text-gray-400 mt-1">
              {descPreview
                ? "Kliknij w treść, aby przejść do edycji."
                : "Obsługiwane formatowanie: pogrubienie, listy, nagłówki."}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Kategoria</label>
              <select
                value={form.category_id}
                onChange={(e) =>
                  setForm({ ...form, category_id: e.target.value })
                }
                className={selectClass}
              >
                <option value="">Wybierz kategorię...</option>
                {categories?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass}>Typ umowy *</label>
              <select
                value={form.contract_type}
                onChange={(e) =>
                  setForm({ ...form, contract_type: e.target.value })
                }
                className={selectClass}
              >
                {Object.entries(CONTRACT_TYPES).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </SectionCard>

        {/* Location */}
        <SectionCard icon={MapPin} title="Lokalizacja">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Kanton *</label>
              <select
                required
                value={form.canton}
                onChange={(e) => setForm({ ...form, canton: e.target.value })}
                className={selectClass}
              >
                <option value="">Wybierz kanton...</option>
                {cantons?.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass}>Miasto</label>
              <input
                type="text"
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
                className={inputClass}
                placeholder="np. Zurych"
              />
            </div>
          </div>
        </SectionCard>

        {/* Salary */}
        <SectionCard icon={Banknote} title="Wynagrodzenie">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className={labelClass}>Wynagrodzenie od (CHF)</label>
              <input
                type="number"
                min={0}
                value={form.salary_min}
                onChange={(e) =>
                  setForm({ ...form, salary_min: e.target.value })
                }
                className={inputClass}
                placeholder="np. 5000"
              />
            </div>
            <div>
              <label className={labelClass}>Wynagrodzenie do (CHF)</label>
              <input
                type="number"
                min={0}
                value={form.salary_max}
                onChange={(e) =>
                  setForm({ ...form, salary_max: e.target.value })
                }
                className={inputClass}
                placeholder="np. 7000"
              />
            </div>
            <div>
              <label className={labelClass}>Okres</label>
              <select
                value={form.salary_type}
                onChange={(e) =>
                  setForm({ ...form, salary_type: e.target.value })
                }
                className={selectClass}
              >
                <option value="monthly">Miesięcznie</option>
                <option value="yearly">Rocznie</option>
                <option value="hourly">Za godzinę</option>
                <option value="negotiable">Do uzgodnienia</option>
              </select>
            </div>
          </div>
        </SectionCard>

        {/* Experience & Requirements */}
        <SectionCard icon={Briefcase} title="Wymagania">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className={labelClass}>
                Min. doświadczenie (lata)
              </label>
              <input
                type="number"
                min={0}
                max={50}
                value={form.experience_min}
                onChange={(e) =>
                  setForm({
                    ...form,
                    experience_min: parseInt(e.target.value) || 0,
                  })
                }
                className={inputClass}
              />
            </div>
            <div className="flex items-end pb-1">
              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.driving_license_required}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      driving_license_required: e.target.checked,
                    })
                  }
                  className="w-4 h-4 rounded border-gray-300 text-[#E1002A] focus:ring-[#E1002A]/20"
                />
                <span className="text-sm text-gray-700">
                  Wymagane prawo jazdy
                </span>
              </label>
            </div>
            <div className="flex items-end pb-1">
              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.car_required}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      car_required: e.target.checked,
                    })
                  }
                  className="w-4 h-4 rounded border-gray-300 text-[#E1002A] focus:ring-[#E1002A]/20"
                />
                <span className="text-sm text-gray-700">
                  Wymagany samochód
                </span>
              </label>
            </div>
          </div>
        </SectionCard>

        {/* Languages */}
        <SectionCard icon={Languages} title="Wymagane języki">
          <div>
            {form.languages_required.length === 0 && (
              <p className="text-sm text-gray-500 mb-3">
                Nie dodano jeszcze wymagań językowych.
              </p>
            )}
            {form.languages_required.map((lr, i) => (
              <div key={i} className="flex items-center gap-2 mb-2">
                <select
                  value={lr.lang}
                  onChange={(e) => {
                    const updated = [...form.languages_required];
                    updated[i] = { ...updated[i], lang: e.target.value };
                    setForm({ ...form, languages_required: updated });
                  }}
                  className={`${selectClass} flex-1`}
                >
                  {LANGUAGES.map((l) => (
                    <option key={l} value={l}>
                      {LANG_NAMES[l]}
                    </option>
                  ))}
                </select>
                <select
                  value={lr.level}
                  onChange={(e) => {
                    const updated = [...form.languages_required];
                    updated[i] = { ...updated[i], level: e.target.value };
                    setForm({ ...form, languages_required: updated });
                  }}
                  className={`${selectClass} w-24`}
                >
                  {LANG_LEVELS.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => removeLanguage(i)}
                  className="p-2 text-gray-400 hover:text-[#E1002A] hover:bg-[#FFF0F3] rounded-lg transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={addLanguage}
              className="text-sm text-[#E1002A] hover:text-[#B8001F] flex items-center gap-1.5 mt-2 font-medium transition-colors"
            >
              <Plus className="w-4 h-4" /> Dodaj język
            </button>
          </div>
        </SectionCard>

        {/* Application Method */}
        <SectionCard icon={Send} title="Sposób aplikowania">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Metoda aplikowania</label>
              <select
                value={form.apply_via}
                onChange={(e) =>
                  setForm({ ...form, apply_via: e.target.value })
                }
                className={selectClass}
              >
                <option value="portal">Przez portal</option>
                <option value="email">Email</option>
                <option value="external_url">Zewnętrzny link</option>
              </select>
            </div>
            {form.apply_via === "email" && (
              <div>
                <label className={labelClass}>Email kontaktowy</label>
                <input
                  type="email"
                  value={form.contact_email}
                  onChange={(e) =>
                    setForm({ ...form, contact_email: e.target.value })
                  }
                  className={inputClass}
                  placeholder="hr@firma.ch"
                />
              </div>
            )}
            {form.apply_via === "external_url" && (
              <div>
                <label className={labelClass}>Link do aplikowania</label>
                <input
                  type="url"
                  value={form.external_url}
                  onChange={(e) =>
                    setForm({ ...form, external_url: e.target.value })
                  }
                  className={inputClass}
                  placeholder="https://..."
                />
              </div>
            )}
          </div>
        </SectionCard>

        {/* Submit buttons */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              type="submit"
              disabled={mutation.isPending}
              className="bg-[#E1002A] text-white px-6 py-2.5 rounded-lg hover:bg-[#B8001F] font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors w-full sm:w-auto"
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Publikowanie...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Opublikuj ogłoszenie
                </>
              )}
            </button>
            <Link
              href="/panel/pracodawca/ogloszenia"
              className="px-6 py-2.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 text-center w-full sm:w-auto transition-colors"
            >
              Anuluj
            </Link>
          </div>
          <p className="text-xs text-gray-400 mt-3">
            Ogłoszenie zostanie opublikowane natychmiast.
          </p>
        </div>
      </form>
    </div>
  );
}
