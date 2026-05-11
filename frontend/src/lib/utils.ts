import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatSalary(min?: number | null, max?: number | null, type?: string): string {
  if (!min && !max) return "Do uzgodnienia";
  const fmt = (n: number) => n.toLocaleString("pl-PL");
  const suffix = type === "hourly" ? "CHF/h" : type === "yearly" ? "CHF/rok" : "CHF/mies.";
  if (min && max) return `${fmt(min)} - ${fmt(max)} ${suffix}`;
  if (min) return `od ${fmt(min)} ${suffix}`;
  return `do ${fmt(max!)} ${suffix}`;
}

export function formatDate(date: string): string {
  const d = new Date(date);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const hours = Math.floor(diff / (1000 * 60 * 60));
  if (hours < 1) return "Przed chwilą";
  if (hours < 24) return `${hours} godz. temu`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "Wczoraj";
  if (days < 7) return `${days} dni temu`;
  return d.toLocaleDateString("pl-PL");
}

/**
 * Sformatuj lokalizację jako "Miasto, Kanton" z deduplikacją:
 *  - jeśli brak kantonu i miasta → "Cała Szwajcaria" (fallback dla ofert bez precyzji geo)
 *  - jeśli city pusty/None → tylko nazwa kantonu
 *  - jeśli city to fragment "Cała" / "całej" / "Inne" → tylko nazwa kantonu
 *  - jeśli city == nazwa kantonu (po normalizacji case-insensitive) → tylko kanton
 *  - inaczej "City, Canton"
 */
export function formatJobLocation(
  canton: string | null | undefined,
  city: string | null | undefined,
  cantonMap: Record<string, string> = {},
): string {
  const cantonName = canton ? (cantonMap[canton] || canton) : "";
  const cleanCity = (city || "").trim();

  // Brak danych geo → fallback dla ofert dotyczących całego kraju
  if (!cantonName && !cleanCity) return "Cała Szwajcaria";

  // Brak miasta → tylko kanton
  if (!cleanCity) return cantonName;

  // Fragmenty błędnie wyciągnięte przez AI ("Cała Szwajcaria" rozbite na "Cała")
  const cityLower = cleanCity.toLowerCase();
  const FRAGMENTS = ["cała", "cala", "całej", "calej", "inne lokalizacje", "inne", "ck"];
  if (FRAGMENTS.includes(cityLower) || cityLower.length < 3) {
    return cantonName;
  }

  // "okolice X" — zostaw samo "okolice X" (już niesie info regionu, kanton zbędny)
  if (cityLower.startsWith("okolic")) {
    return cleanCity;
  }

  // City pokrywa się z kantonem (różne pisownia: "Berno" vs "bern", "Zug" vs "zug")
  const cantonLower = cantonName.toLowerCase();
  if (cityLower === cantonLower) return cantonName;
  // "Berno" zawiera "bern" -> duplikat
  if (cantonLower.length >= 3 && cityLower.includes(cantonLower)) return cantonName;
  if (cityLower.length >= 3 && cantonLower.includes(cityLower)) return cantonName;

  return cantonName ? `${cleanCity}, ${cantonName}` : cleanCity;
}

export const CONTRACT_TYPES: Record<string, string> = {
  full_time: "Pełny etat",
  part_time: "Część etatu",
  temporary: "Tymczasowa",
  contract: "Zlecenie",
  internship: "Praktyka",
  freelance: "Freelance",
};

export const WORK_PERMITS: Record<string, string> = {
  permit_b: "Pozwolenie B",
  permit_c: "Pozwolenie C",
  permit_g: "Pozwolenie G (cross-border)",
  permit_l: "Pozwolenie L",
  eu_efta: "EU/EFTA",
  swiss_citizen: "Obywatel CH",
  none: "Brak",
  other: "Inne",
};

export const APPLICATION_STATUSES: Record<string, { label: string; color: string }> = {
  sent: { label: "Wysłana", color: "bg-blue-100 text-blue-800" },
  viewed: { label: "Przeglądana", color: "bg-yellow-100 text-yellow-800" },
  shortlisted: { label: "Na krótkiej liście", color: "bg-green-100 text-green-800" },
  rejected: { label: "Odrzucona", color: "bg-red-100 text-red-800" },
  accepted: { label: "Zaakceptowana", color: "bg-emerald-100 text-emerald-800" },
};
