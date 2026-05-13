"use client";

import { useState, KeyboardEvent } from "react";
import { Bell, Check, Mail, X, Plus } from "lucide-react";
import api from "@/services/api";
import { getRecaptchaToken } from "@/lib/recaptcha";

interface Props {
  /** Current search query (frazę). The widget is only useful for a non-empty query. */
  query: string;
}

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const MAX_KEYWORDS = 5;

export default function AlertSubscribeWidget({ query }: Props) {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [consent, setConsent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  // Multi-keyword chip input: seed with the current search query
  const [keywords, setKeywords] = useState<string[]>(() =>
    query.trim() ? [query.trim()] : [],
  );
  const [pending, setPending] = useState("");

  if (!query.trim()) return null;

  const addKeyword = (raw: string) => {
    const norm = raw.trim();
    if (norm.length < 2) return;
    const exists = keywords.some((k) => k.toLowerCase() === norm.toLowerCase());
    if (exists) {
      setPending("");
      return;
    }
    if (keywords.length >= MAX_KEYWORDS) {
      setError(`Maksymalnie ${MAX_KEYWORDS} fraz na powiadomienie.`);
      return;
    }
    setError(null);
    setKeywords([...keywords, norm]);
    setPending("");
  };

  const removeKeyword = (idx: number) => {
    setKeywords(keywords.filter((_, i) => i !== idx));
  };

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addKeyword(pending);
    } else if (e.key === "Backspace" && !pending && keywords.length) {
      removeKeyword(keywords.length - 1);
    }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    // Auto-commit any pending text in the chip input
    const finalKeywords = pending.trim()
      ? Array.from(
          new Set(
            [...keywords, pending.trim()].map((k) => k.trim()).filter((k) => k.length >= 2),
          ),
        )
      : keywords;
    if (finalKeywords.length === 0) {
      setError("Dodaj przynajmniej jedną frazę.");
      return;
    }
    if (!EMAIL_RE.test(email.trim())) {
      setError("Nieprawidłowy format email");
      return;
    }
    if (!consent) {
      setError("Wymagana zgoda na przetwarzanie danych");
      return;
    }
    setSubmitting(true);
    try {
      const recaptchaToken = await getRecaptchaToken("subscribe_alert");
      const { data } = await api.post<{ message: string }>(
        "/public-alerts/subscribe",
        { email: email.trim(), queries: finalKeywords },
        { headers: { "X-Recaptcha-Token": recaptchaToken } },
      );
      setDone(data?.message || "Zapisano. Sprawdź skrzynkę za tydzień.");
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Nie udało się zapisać. Spróbuj ponownie.");
    } finally {
      setSubmitting(false);
    }
  };

  if (done) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4 flex items-start gap-3" role="status">
        <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="font-semibold text-green-900 text-sm mb-0.5">Zapisano</p>
          <p className="text-green-800 text-sm">{done}</p>
        </div>
      </div>
    );
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="w-full bg-[#FFF7E6] border border-[#FBBF24]/40 rounded-lg p-4 mb-4 flex items-center gap-3 hover:bg-[#FFEFC6] transition-colors text-left"
      >
        <div className="w-10 h-10 bg-[#E1002A] rounded-full flex items-center justify-center flex-shrink-0">
          <Bell className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-[#0D2240] text-sm">
            Powiadom mnie o nowych ofertach dla &quot;<span className="font-bold">{query}</span>&quot;
          </p>
          <p className="text-xs text-[#92400E] mt-0.5">
            Co tydzień email z nowymi ofertami. Możesz dodać kilka fraz na raz.
          </p>
        </div>
        <span className="text-xs text-[#0D2240] font-semibold whitespace-nowrap">Zapisz się →</span>
      </button>
    );
  }

  return (
    <div className="bg-white border border-[#E0E3E8] rounded-lg p-5 mb-4 shadow-sm relative">
      <button
        onClick={() => setOpen(false)}
        aria-label="Zamknij"
        className="absolute top-3 right-3 text-gray-400 hover:text-gray-700"
      >
        <X className="w-4 h-4" />
      </button>
      <div className="flex items-start gap-3 mb-4">
        <div className="w-10 h-10 bg-[#E1002A] rounded-full flex items-center justify-center flex-shrink-0">
          <Bell className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <h3 className="font-display font-bold text-[#0D2240] text-base leading-tight">
            Powiadomienia o nowych ofertach
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Co tydzień otrzymasz email z nowymi ofertami pasującymi do Twoich fraz.
          </p>
        </div>
      </div>

      <form onSubmit={submit} className="space-y-3">
        {/* Frazy (chip input) */}
        <div>
          <label htmlFor="alert-keyword" className="block text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wide">
            Frazy do śledzenia
          </label>
          <div className="flex flex-wrap gap-1.5 p-2 border border-gray-300 rounded-lg bg-white focus-within:ring-2 focus-within:ring-[#E1002A]/30 focus-within:border-[#E1002A] min-h-[48px]">
            {keywords.map((kw, i) => (
              <span
                key={`${kw}-${i}`}
                className="inline-flex items-center gap-1 px-2.5 py-1 bg-[#0D2240] text-white rounded-full text-xs font-semibold"
              >
                {kw}
                <button
                  type="button"
                  onClick={() => removeKeyword(i)}
                  aria-label={`Usuń frazę ${kw}`}
                  className="hover:text-red-200 transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
            <input
              id="alert-keyword"
              type="text"
              value={pending}
              onChange={(e) => setPending(e.target.value)}
              onKeyDown={handleKey}
              onBlur={() => pending.trim() && addKeyword(pending)}
              placeholder={keywords.length === 0 ? "np. monter, hydraulik..." : keywords.length < MAX_KEYWORDS ? "+ dodaj kolejną" : ""}
              disabled={keywords.length >= MAX_KEYWORDS}
              className="flex-1 min-w-[120px] px-1 text-sm border-0 outline-none bg-transparent disabled:bg-transparent"
            />
          </div>
          <p className="text-[11px] text-gray-500 mt-1.5 flex items-center gap-1">
            <Plus className="w-3 h-3" />
            Naciśnij <strong className="font-semibold">Enter</strong> po każdej frazie ({keywords.length}/{MAX_KEYWORDS})
          </p>
        </div>

        {/* Email */}
        <div>
          <label htmlFor="alert-email" className="block text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wide">
            Twój email
          </label>
          <div className="relative">
            <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              id="alert-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="jan@example.com"
              required
              autoComplete="email"
              className="w-full pl-9 pr-3 py-2.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-[#E1002A]/30 focus:border-[#E1002A]"
            />
          </div>
        </div>

        <label className="flex items-start gap-2 text-xs text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            className="mt-0.5 w-4 h-4 text-[#E1002A] border-gray-300 rounded focus:ring-[#E1002A]/30"
          />
          <span>
            Wyrażam zgodę na przetwarzanie mojego adresu email w celu otrzymywania powiadomień
            o ofertach pracy. Mogę wypisać się w dowolnej chwili klikając link w mailu.
          </span>
        </label>

        {error && (
          <div className="bg-[#FFF0F3] border border-[#FFC2CD] text-[#B8001F] px-3 py-2 rounded text-sm" role="alert">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || !email || !consent || keywords.length === 0}
          className="w-full bg-[#0D2240] text-white py-2.5 rounded font-semibold text-sm hover:bg-[#1B3157] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {submitting ? "Zapisuję..." : "Powiadom mnie"}
        </button>
      </form>
    </div>
  );
}
