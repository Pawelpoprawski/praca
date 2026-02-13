"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { MapPin, Clock, Briefcase, Globe, Shield, ArrowLeft, Send } from "lucide-react";
import { useState } from "react";
import api from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { formatSalary, formatDate, CONTRACT_TYPES, WORK_PERMITS } from "@/lib/utils";
import type { JobOffer, Canton } from "@/types/api";

const LANG_NAMES: Record<string, string> = {
  de: "Niemiecki", fr: "Francuski", it: "Włoski", en: "Angielski",
  pl: "Polski", pt: "Portugalski", es: "Hiszpański",
};

export default function JobDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [showApply, setShowApply] = useState(false);
  const [coverLetter, setCoverLetter] = useState("");
  const [applying, setApplying] = useState(false);
  const [applied, setApplied] = useState(false);
  const [error, setError] = useState("");

  const { data: job, isLoading } = useQuery({
    queryKey: ["job", id],
    queryFn: () => api.get<JobOffer>(`/jobs/${id}`).then((r) => r.data),
    enabled: !!id,
  });

  const { data: cantons } = useQuery({
    queryKey: ["cantons"],
    queryFn: () => api.get<Canton[]>("/jobs/cantons").then((r) => r.data),
    staleTime: 24 * 60 * 60 * 1000,
  });

  const cantonMap = cantons
    ? Object.fromEntries(cantons.map((c) => [c.value, c.label]))
    : {};

  const handleApply = async () => {
    if (!isAuthenticated) {
      router.push(`/login?redirect=/oferty/${id}`);
      return;
    }
    if (user?.role !== "worker") {
      setError("Tylko pracownicy mogą aplikować na oferty");
      return;
    }

    setApplying(true);
    setError("");
    try {
      await api.post(`/worker/jobs/${id}/apply`, {
        cover_letter: coverLetter || null,
      });
      setApplied(true);
      setShowApply(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Wystąpił błąd");
    } finally {
      setApplying(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-2/3 mb-4" />
          <div className="h-4 bg-gray-100 rounded w-1/3 mb-8" />
          <div className="h-64 bg-gray-100 rounded" />
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500 text-lg">Oferta nie została znaleziona</p>
        <Link href="/oferty" className="text-red-600 hover:underline mt-2 inline-block">
          Wróć do listy ofert
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1 text-gray-500 hover:text-gray-700 mb-6 text-sm"
      >
        <ArrowLeft className="w-4 h-4" /> Powrót
      </button>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Main content */}
        <div className="flex-1">
          {job.is_featured && (
            <span className="inline-block bg-yellow-100 text-yellow-800 text-xs font-semibold px-2 py-1 rounded mb-3">
              Wyróżnione
            </span>
          )}

          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
            {job.title}
          </h1>

          {job.employer && (
            <Link
              href={`/firmy/${job.employer.company_slug}`}
              className="text-red-600 hover:underline font-medium"
            >
              {job.employer.company_name}
              {job.employer.is_verified && " \u2713"}
            </Link>
          )}

          <div className="flex flex-wrap gap-3 mt-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <MapPin className="w-4 h-4" />
              {cantonMap[job.canton] || job.canton}{job.city ? `, ${job.city}` : ""}
            </span>
            <span className="flex items-center gap-1">
              <Briefcase className="w-4 h-4" />
              {CONTRACT_TYPES[job.contract_type] || job.contract_type}
            </span>
            {job.published_at && (
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {formatDate(job.published_at)}
              </span>
            )}
          </div>

          <hr className="my-6" />

          <div className="prose prose-gray max-w-none whitespace-pre-line text-gray-700">
            {job.description}
          </div>

          {/* Company info */}
          {job.employer && (
            <>
              <hr className="my-6" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">O firmie</h3>
                <Link
                  href={`/firmy/${job.employer.company_slug}`}
                  className="text-red-600 hover:underline"
                >
                  Zobacz profil firmy &rarr;
                </Link>
              </div>
            </>
          )}
        </div>

        {/* Sidebar */}
        <aside className="lg:w-80 flex-shrink-0">
          <div className="bg-white border border-gray-200 rounded-xl p-6 sticky top-24 space-y-5">
            {/* Apply button */}
            {applied ? (
              <div className="bg-green-50 text-green-700 px-4 py-3 rounded-lg text-center text-sm font-medium">
                Aplikacja wysłana!
              </div>
            ) : (
              <button
                onClick={() =>
                  isAuthenticated ? setShowApply(!showApply) : router.push(`/login?redirect=/oferty/${id}`)
                }
                className="w-full bg-red-600 text-white py-3 rounded-lg hover:bg-red-700 font-semibold flex items-center justify-center gap-2"
              >
                <Send className="w-4 h-4" />
                Aplikuj
              </button>
            )}

            {error && (
              <div className="bg-red-50 text-red-600 px-3 py-2 rounded text-sm">{error}</div>
            )}

            {/* Apply form */}
            {showApply && (
              <div className="space-y-3">
                <textarea
                  value={coverLetter}
                  onChange={(e) => setCoverLetter(e.target.value)}
                  placeholder="List motywacyjny (opcjonalnie)..."
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500 resize-none"
                />
                <button
                  onClick={handleApply}
                  disabled={applying}
                  className="w-full bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 text-sm font-medium disabled:opacity-50"
                >
                  {applying ? "Wysyłanie..." : "Wyślij aplikację"}
                </button>
              </div>
            )}

            {/* Job details */}
            <div className="space-y-4 text-sm">
              <div>
                <p className="text-gray-500">Wynagrodzenie</p>
                <p className="font-semibold text-gray-900">
                  {formatSalary(job.salary_min, job.salary_max, job.salary_type)}
                </p>
              </div>

              <div>
                <p className="text-gray-500">Typ umowy</p>
                <p className="font-medium">{CONTRACT_TYPES[job.contract_type]}</p>
              </div>

              {job.is_remote !== "no" && (
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-gray-400" />
                  <span>{job.is_remote === "yes" ? "Praca zdalna" : "Hybrydowo"}</span>
                </div>
              )}

              {job.work_permit_required && (
                <div>
                  <p className="text-gray-500">Wymagane pozwolenie</p>
                  <p className="font-medium">
                    {WORK_PERMITS[job.work_permit_required] || job.work_permit_required}
                  </p>
                </div>
              )}

              {job.work_permit_sponsored && (
                <div className="flex items-center gap-2 text-green-600">
                  <Shield className="w-4 h-4" />
                  <span className="text-sm font-medium">Sponsorujemy pozwolenie</span>
                </div>
              )}

              {job.languages_required && job.languages_required.length > 0 && (
                <div>
                  <p className="text-gray-500">Wymagane języki</p>
                  {job.languages_required.map((l, i) => (
                    <p key={i} className="font-medium">
                      {LANG_NAMES[l.lang] || l.lang.toUpperCase()} ({l.level})
                    </p>
                  ))}
                </div>
              )}

              {job.experience_min > 0 && (
                <div>
                  <p className="text-gray-500">Doświadczenie</p>
                  <p className="font-medium">Min. {job.experience_min} lat</p>
                </div>
              )}

              {job.expires_at && (
                <div>
                  <p className="text-gray-500">Wygasa</p>
                  <p className="font-medium">
                    {new Date(job.expires_at).toLocaleDateString("pl-PL")}
                  </p>
                </div>
              )}

              <div>
                <p className="text-gray-500">Wyświetlenia</p>
                <p className="font-medium">{job.views_count}</p>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
