"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { MapPin, Clock, Briefcase, Car, ArrowLeft, Send, Zap, ExternalLink, Mail } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import api from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { formatSalary, formatDate, formatJobLocation, CONTRACT_TYPES } from "@/lib/utils";
import { trackJobView } from "@/lib/viewHistory";
import SimilarJobs from "@/components/jobs/SimilarJobs";
import SaveJobButton from "@/components/jobs/SaveJobButton";
import QuickApplyModal from "@/components/jobs/QuickApplyModal";
import ExternalApplyModal from "@/components/jobs/ExternalApplyModal";
import type { JobOffer, Canton, WorkerProfile } from "@/types/api";

const LANG_NAMES: Record<string, string> = {
  de: "Niemiecki", fr: "Francuski", it: "Włoski", en: "Angielski",
  pl: "Polski", pt: "Portugalski", es: "Hiszpański",
};

interface Props {
  initialJob: JobOffer;
}

export default function JobDetailClient({ initialJob }: Props) {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [showApply, setShowApply] = useState(false);
  const [coverLetter, setCoverLetter] = useState("");
  const [applying, setApplying] = useState(false);
  const [applied, setApplied] = useState(false);
  const [error, setError] = useState("");
  const [showQuickApply, setShowQuickApply] = useState(false);
  const [quickApplySuccess, setQuickApplySuccess] = useState(false);
  const [showExternalApply, setShowExternalApply] = useState(false);

  const isWorker = isAuthenticated && user?.role === "worker";

  const { data: job } = useQuery({
    queryKey: ["job", initialJob.id],
    queryFn: () => api.get<JobOffer>(`/jobs/${initialJob.id}`).then((r) => r.data),
    initialData: initialJob,
  });

  const { data: cantons } = useQuery({
    queryKey: ["cantons"],
    queryFn: () => api.get<Canton[]>("/jobs/cantons").then((r) => r.data),
    staleTime: 24 * 60 * 60 * 1000,
  });

  // Fetch worker profile only if logged in as worker (for quick apply)
  const { data: workerProfile } = useQuery({
    queryKey: ["worker-profile"],
    queryFn: () => api.get<WorkerProfile>("/worker/profile").then((r) => r.data),
    enabled: isWorker,
    staleTime: 5 * 60 * 1000,
  });

  const cantonMap = cantons
    ? Object.fromEntries(cantons.map((c) => [c.value, c.label]))
    : {};

  // Track view (localStorage + API for logged-in users)
  const viewTracked = useRef(false);
  useEffect(() => {
    if (viewTracked.current) return;
    viewTracked.current = true;
    trackJobView(job.id, isAuthenticated);
  }, [job.id, isAuthenticated]);

  const hasCompleteCv = workerProfile?.has_cv ?? false;
  const alreadyApplied = applied || quickApplySuccess;

  const trackClick = (type: "portal" | "external" | "email") => {
    api.post(`/jobs/${job.id}/apply-click?click_type=${type}`).catch(() => {});
  };

  const handleApply = async () => {
    if (!isAuthenticated) {
      router.push(`/login?redirect=/oferty/${job.id}`);
      return;
    }
    if (user?.role !== "worker") {
      setError("Tylko pracownicy mogą aplikować na oferty");
      return;
    }

    setApplying(true);
    setError("");
    try {
      await api.post(`/worker/jobs/${job.id}/apply`, {
        cover_letter: coverLetter || null,
      });
      trackClick("portal");
      setApplied(true);
      setShowApply(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Wystąpił błąd");
    } finally {
      setApplying(false);
    }
  };

  const handleQuickApplyClick = () => {
    if (!isAuthenticated) {
      router.push(`/login?redirect=/oferty/${job.id}`);
      return;
    }
    setShowQuickApply(true);
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8 pb-36 lg:pb-8">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1.5 text-gray-500 hover:text-gray-700 mb-5 text-sm font-medium transition-colors group"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" /> Powrót do ofert
      </button>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Main content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              {job.is_featured && (
                <span className="inline-block bg-gradient-to-r from-yellow-100 to-yellow-50 text-yellow-800 text-xs font-semibold px-2.5 py-1 rounded-lg mb-3 border border-yellow-200">
                  Wyróżnione
                </span>
              )}

              <h1 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-[#0D2240] mb-2 leading-snug">
                {job.title}
              </h1>
            </div>
            <SaveJobButton jobId={job.id} size="md" className="mt-1 flex-shrink-0" />
          </div>

          {job.employer && (
            <Link
              href={`/firmy/${job.employer.company_slug}`}
              className="text-[#E1002A] hover:underline font-medium text-sm sm:text-base"
            >
              {job.employer.company_name}
              {job.employer.is_verified && " \u2713"}
            </Link>
          )}

          {/* Salary — prominently shown on mobile below company name */}
          {(job.salary_min || job.salary_max) && (
            <p className="lg:hidden mt-3 text-xl font-bold text-gray-900">
              {formatSalary(job.salary_min, job.salary_max, job.salary_type)}
            </p>
          )}

          <div className="flex flex-wrap gap-2 sm:gap-3 mt-3 sm:mt-4 text-sm text-gray-500">
            <span className="flex items-center gap-1 bg-gray-50 px-2.5 py-1.5 rounded-lg text-xs sm:text-sm">
              <MapPin className="w-4 h-4 flex-shrink-0" />
              {formatJobLocation(job.canton, job.city, cantonMap)}
            </span>
            <span className="flex items-center gap-1 bg-blue-50 text-blue-700 px-2.5 py-1.5 rounded-lg text-xs sm:text-sm font-medium">
              <Briefcase className="w-4 h-4 flex-shrink-0" />
              {CONTRACT_TYPES[job.contract_type] || job.contract_type}
            </span>
            {job.published_at && (
              <span className="flex items-center gap-1 bg-gray-50 px-2.5 py-1.5 rounded-lg text-xs sm:text-sm">
                <Clock className="w-4 h-4 flex-shrink-0" />
                {formatDate(job.published_at)}
              </span>
            )}
          </div>

          <hr className="my-5 sm:my-6" />

          <div
            className="prose prose-gray max-w-none text-gray-700"
            dangerouslySetInnerHTML={{ __html: job.description }}
          />

          {/* Company info */}
          {job.employer && (
            <>
              <hr className="my-6" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">O firmie</h3>
                <Link
                  href={`/firmy/${job.employer.company_slug}`}
                  className="text-[#E1002A] hover:underline"
                >
                  Zobacz profil firmy &rarr;
                </Link>
              </div>
            </>
          )}
        </div>

        {/* Sidebar — desktop only (mobile uses sticky bottom CTA bar) */}
        <aside className="hidden lg:block lg:w-80 flex-shrink-0">
          <div className="bg-white border border-gray-200 rounded-xl p-6 lg:sticky lg:top-24 space-y-5">
            {/* Salary — top of sidebar, most prominent */}
            <div className="pb-4 border-b border-gray-100">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Wynagrodzenie</p>
              <p className="text-2xl font-bold text-[#0D2240]">
                {formatSalary(job.salary_min, job.salary_max, job.salary_type)}
              </p>
              <p className="text-sm text-gray-500 mt-0.5">{CONTRACT_TYPES[job.contract_type]}</p>
            </div>

            {/* Apply buttons */}
            {job.apply_via === "email" && job.contact_email ? (
              <button
                onClick={() => { trackClick("email"); setShowExternalApply(true); }}
                className="w-full bg-[#E1002A] text-white py-3 rounded hover:bg-[#B8001F] font-medium flex items-center justify-center gap-2 transition-colors"
              >
                <Mail className="w-4 h-4" />
                Aplikuj — wyślij CV
              </button>
            ) : job.apply_via === "external_url" && job.external_url ? (
              <a
                href={job.external_url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => trackClick("external")}
                className="w-full bg-[#E1002A] text-white py-3 rounded hover:bg-[#B8001F] font-medium flex items-center justify-center gap-2 transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                Aplikuj na stronie pracodawcy
              </a>
            ) : alreadyApplied ? (
              <div className="bg-green-50 text-green-700 px-4 py-3 rounded-xl text-center text-sm font-medium">
                Aplikacja wysłana!
              </div>
            ) : (
              <div className="space-y-3">
                <button
                  onClick={() =>
                    isAuthenticated ? setShowApply(!showApply) : router.push(`/login?redirect=/oferty/${job.id}`)
                  }
                  className="w-full bg-[#E1002A] text-white py-3 rounded-xl hover:bg-[#B8001F] font-semibold flex items-center justify-center gap-2 transition-colors"
                >
                  <Send className="w-4 h-4" />
                  Aplikuj
                </button>

                {/* Quick Apply button - only for workers with CV */}
                {isWorker && hasCompleteCv && (
                  <button
                    onClick={handleQuickApplyClick}
                    className="w-full bg-green-600 text-white py-3 rounded-xl hover:bg-green-700 font-semibold flex items-center justify-center gap-2 transition-colors"
                  >
                    <Zap className="w-4 h-4" />
                    Aplikuj szybko
                  </button>
                )}
              </div>
            )}

            {error && (
              <div className="bg-[#FFF0F3] border border-[#FFC2CD] text-[#B8001F] px-3 py-2.5 rounded-lg text-sm flex items-start gap-2" role="alert">
                <span className="flex-shrink-0 mt-0.5">⚠</span>
                <span>{error}</span>
              </div>
            )}

            {/* Apply form */}
            {showApply && (
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">List motywacyjny</label>
                <textarea
                  value={coverLetter}
                  onChange={(e) => setCoverLetter(e.target.value)}
                  placeholder="Napisz kilka słów o sobie (opcjonalnie)..."
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-xl text-sm outline-none focus:ring-2 focus:ring-[#E1002A]/20 resize-none"
                />
                <button
                  onClick={handleApply}
                  disabled={applying}
                  className="w-full bg-[#E1002A] text-white py-2 rounded-xl hover:bg-[#B8001F] text-sm font-medium disabled:opacity-50"
                >
                  {applying ? "Wysyłanie..." : "Wyślij aplikację"}
                </button>
              </div>
            )}

            {/* Job details (secondary info) */}
            <div className="space-y-4 text-sm pt-1 border-t border-gray-100">
              {(job.driving_license_required || job.car_required) && (
                <div>
                  <p className="text-gray-500">Wymagania dodatkowe</p>
                  {job.driving_license_required && (
                    <p className="font-medium flex items-center gap-1">
                      <Car className="w-4 h-4" /> Prawo jazdy
                    </p>
                  )}
                  {job.car_required && (
                    <p className="font-medium flex items-center gap-1">
                      <Car className="w-4 h-4" /> Własny samochód
                    </p>
                  )}
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
            </div>
          </div>
        </aside>
      </div>

      {/* Similar jobs */}
      <SimilarJobs jobId={job.id} />

      {/* Mobile fixed CTA bar */}
      {!alreadyApplied && (
        <div
          className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg px-4 pt-3 z-10"
          style={{ paddingBottom: "calc(0.75rem + env(safe-area-inset-bottom, 0px))" }}
        >
          {/* Salary hint row */}
          <div className="flex items-center justify-between mb-2.5">
            <span className="text-xs text-gray-500 font-medium">Wynagrodzenie</span>
            <span className="text-sm font-bold text-gray-900">
              {formatSalary(job.salary_min, job.salary_max, job.salary_type)}
            </span>
          </div>
          {job.apply_via === "external_url" && job.external_url ? (
            <a
              href={job.external_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => trackClick("external")}
              className="w-full bg-[#E1002A] text-white py-3 rounded-xl hover:bg-[#B8001F] font-semibold flex items-center justify-center gap-2 transition-colors text-sm"
            >
              <ExternalLink className="w-4 h-4" />
              Aplikuj na stronie pracodawcy
            </a>
          ) : (
            <div className="flex gap-2">
              <button
                onClick={() =>
                  isAuthenticated ? setShowApply(!showApply) : router.push(`/login?redirect=/oferty/${job.id}`)
                }
                className="flex-1 bg-[#E1002A] text-white py-3 rounded-xl hover:bg-[#B8001F] font-semibold flex items-center justify-center gap-2 transition-colors text-sm"
              >
                <Send className="w-4 h-4" />
                Aplikuj
              </button>
              {isWorker && hasCompleteCv && (
                <button
                  onClick={handleQuickApplyClick}
                  aria-label="Aplikuj szybko"
                  className="bg-green-600 text-white py-3 px-4 rounded-xl hover:bg-green-700 font-semibold flex items-center justify-center gap-1.5 transition-colors text-sm"
                >
                  <Zap className="w-4 h-4" />
                  <span>Szybko</span>
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Quick Apply Modal */}
      {showQuickApply && workerProfile && (
        <QuickApplyModal
          jobId={job.id}
          jobTitle={job.title}
          companyName={job.employer?.company_name || ""}
          profile={workerProfile}
          onClose={() => setShowQuickApply(false)}
          onSuccess={() => {
            setShowQuickApply(false);
            setQuickApplySuccess(true);
          }}
        />
      )}

      {/* External Apply Modal — dla ofert z apply_via='email' */}
      {job.contact_email && (
        <ExternalApplyModal
          jobId={job.id}
          jobTitle={job.title}
          contactEmail={job.contact_email}
          open={showExternalApply}
          onClose={() => setShowExternalApply(false)}
        />
      )}
    </div>
  );
}
