"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, X, Mail, CheckCircle2, Search, BookOpen, Languages, Award, FileCheck } from "lucide-react";
import api from "@/services/api";
import type { CVReviewResponse } from "@/types/api";

const ANALYSIS_STEPS = [
  { icon: Upload, label: "Wczytujemy dokument" },
  { icon: Search, label: "Sprawdzamy strukturę CV" },
  { icon: BookOpen, label: "Analizujemy doświadczenie zawodowe" },
  { icon: Languages, label: "Weryfikujemy kompetencje językowe" },
  { icon: FileCheck, label: "Sprawdzamy zgodność z rynkiem szwajcarskim" },
  { icon: Award, label: "Przygotowujemy rekomendacje" },
];

const SWISS_FACTS = [
  "Szwajcaria ma 4 oficjalne języki: niemiecki, francuski, włoski i romansz.",
  "Średnie wynagrodzenie w Szwajcarii to ok. 6500 CHF miesięcznie.",
  "W Szwajcarii jest ponad 7000 jezior, w tym słynne Jezioro Genewskie.",
  "Zurych jest najdroższym miastem w Europie, ale też oferuje najwyższe zarobki.",
  "Szwajcarzy pracują średnio 42,5 godziny tygodniowo.",
  "CV w Szwajcarii powinno zawierać zdjęcie - to standard na rynku DACH.",
  "Kanton Zug ma najniższe podatki w Szwajcarii - ok. 11,9%.",
  "Polacy to 4. największa grupa obcokrajowców w Szwajcarii.",
  "W Szwajcarii jest ponad 900 000 firm, z czego 99% to MŚP.",
  "Szwajcarski rynek pracy ceni punktualność - spóźnienie na rozmowę to duży minus.",
  "Znajomość niemieckiego otwiera drzwi do 65% ofert pracy w Szwajcarii.",
  "Pozwolenie typu B daje prawo do pracy i zamieszkania na 5 lat.",
  "Berno to stolica Szwajcarii, ale Zurych jest największym miastem.",
  "Szwajcaria nie jest w UE, ale ma bilateralne umowy o swobodzie przepływu osób.",
  "Branża farmaceutyczna (Basel) to jeden z najlepiej opłacanych sektorów.",
];

export default function SprawdzCVPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [email, setEmail] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previousReviewId, setPreviousReviewId] = useState<string | null>(null);

  // Analysis progress state
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [currentFact, setCurrentFact] = useState(0);
  const [apiDone, setApiDone] = useState(false);
  const [reviewId, setReviewId] = useState<string | null>(null);
  const stepTimerRef = useRef<NodeJS.Timeout | null>(null);
  const factTimerRef = useRef<NodeJS.Timeout | null>(null);
  const progressTimerRef = useRef<NodeJS.Timeout | null>(null);
  // Randomized minimum analysis duration (5-10s) — set once per submission
  const minDurationRef = useRef<number>(7000);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const prevId = params.get("previous");
    if (prevId) setPreviousReviewId(prevId);
  }, []);

  // Rotate Swiss facts every 4 seconds
  useEffect(() => {
    if (!uploading) return;
    setCurrentFact(Math.floor(Math.random() * SWISS_FACTS.length));
    factTimerRef.current = setInterval(() => {
      setCurrentFact((prev) => (prev + 1) % SWISS_FACTS.length);
    }, 4000);
    return () => { if (factTimerRef.current) clearInterval(factTimerRef.current); };
  }, [uploading]);

  // Step through analysis stages — distribute over min duration
  useEffect(() => {
    if (!uploading) return;
    setCurrentStep(0);
    let step = 0;
    const perStep = Math.max(700, Math.floor(minDurationRef.current / ANALYSIS_STEPS.length));

    const advanceStep = () => {
      step++;
      if (step < ANALYSIS_STEPS.length) {
        setCurrentStep(step);
        stepTimerRef.current = setTimeout(advanceStep, perStep);
      }
    };

    stepTimerRef.current = setTimeout(advanceStep, perStep);
    return () => { if (stepTimerRef.current) clearTimeout(stepTimerRef.current); };
  }, [uploading]);

  // Smooth progress bar (reaches ~90% during analysis, 100% when done)
  useEffect(() => {
    if (!uploading) {
      setProgress(0);
      return;
    }
    setProgress(0);
    const totalDuration = minDurationRef.current;
    const interval = 100;
    let elapsed = 0;

    progressTimerRef.current = setInterval(() => {
      elapsed += interval;
      const raw = elapsed / totalDuration;
      const eased = raw < 1 ? 90 * (1 - Math.pow(1 - raw, 3)) : 90;
      setProgress(Math.min(eased, 90));
    }, interval);

    return () => { if (progressTimerRef.current) clearInterval(progressTimerRef.current); };
  }, [uploading]);

  // When API is done, animate to 100% and redirect
  useEffect(() => {
    if (apiDone && reviewId) {
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);
      setProgress(100);
      setCurrentStep(ANALYSIS_STEPS.length - 1);
      const timeout = setTimeout(() => {
        router.push(`/sprawdz-cv/wyniki/${reviewId}`);
      }, 800);
      return () => clearTimeout(timeout);
    }
  }, [apiDone, reviewId, router]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) validateAndSetFile(droppedFile);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOver(false);
  }, []);

  const validateAndSetFile = (f: File) => {
    setError(null);
    const allowed = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    if (!allowed.includes(f.type)) {
      setError("Dozwolone formaty: PDF, DOCX");
      return;
    }
    if (f.size > 5 * 1024 * 1024) {
      setError("Maksymalny rozmiar pliku to 5 MB");
      return;
    }
    setFile(f);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) validateAndSetFile(f);
  };

  const handleSubmit = async () => {
    if (!file) return;
    // Randomize minimum analysis duration to 5-10 seconds
    minDurationRef.current = 5000 + Math.floor(Math.random() * 5000);
    setUploading(true);
    setApiDone(false);
    setReviewId(null);
    setError(null);

    const minDelay = new Promise<void>((resolve) =>
      setTimeout(resolve, minDurationRef.current),
    );

    try {
      const formData = new FormData();
      formData.append("file", file);
      if (email) formData.append("email", email);
      if (previousReviewId) formData.append("previous_review_id", previousReviewId);

      const apiCall = api.post<CVReviewResponse>("/cv-review/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
      });

      // Wait for BOTH the API response AND the minimum animation duration
      const [response] = await Promise.all([apiCall, minDelay]);

      setReviewId(response.data.id);
      setApiDone(true);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(
        axiosErr.response?.data?.detail ||
        "Wystąpił błąd podczas analizy CV. Spróbuj ponownie."
      );
      setUploading(false);
    }
  };

  // Loading screen
  if (uploading) {
    return (
      <div className="min-h-screen bg-[#F5F6F8] flex items-center justify-center py-12 px-4">
        <div className="max-w-[560px] w-full">
          <div className="bg-white border border-[#E0E3E8] rounded-lg overflow-hidden">
            {/* Top strip — navy */}
            <div className="bg-[#0D2240] px-8 py-7 text-white">
              <span className="hays-red-line" />
              <h2 className="font-display text-[1.5rem] font-extrabold leading-tight">
                Analizujemy Twoje CV
              </h2>
              <p className="text-white/70 text-[0.9rem] mt-1.5">
                Analizujemy dokument pod kątem rynku szwajcarskiego.
              </p>
            </div>

            {/* Body */}
            <div className="px-8 py-7">
              {/* Progress bar */}
              <div className="mb-7">
                <div className="flex justify-between text-[0.75rem] text-[#888] mb-2 font-medium tracking-wide uppercase">
                  <span>Postęp</span>
                  <span className="tabular-nums">{Math.round(progress)}%</span>
                </div>
                <div className="h-1 bg-[#E0E3E8] overflow-hidden">
                  <div
                    className="h-full transition-all duration-500 ease-out"
                    style={{
                      width: `${progress}%`,
                      backgroundColor: progress < 100 ? "#E1002A" : "#16a34a",
                    }}
                  />
                </div>
              </div>

              {/* Analysis steps — sparse, editorial */}
              <ul className="space-y-2.5 mb-7">
                {ANALYSIS_STEPS.map((step, i) => {
                  const isDone = i < currentStep;
                  const isCurrent = i === currentStep;
                  return (
                    <li
                      key={i}
                      className={`flex items-center gap-3 text-[0.92rem] transition-opacity ${
                        isDone || isCurrent ? "opacity-100" : "opacity-30"
                      }`}
                    >
                      <span
                        className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 border-2 ${
                          isDone
                            ? "bg-[#0D2240] border-[#0D2240]"
                            : isCurrent
                              ? "border-[#E1002A] bg-white"
                              : "border-[#E0E3E8] bg-white"
                        }`}
                      >
                        {isDone ? (
                          <CheckCircle2 className="w-3 h-3 text-white" strokeWidth={3} />
                        ) : isCurrent ? (
                          <span className="w-1.5 h-1.5 bg-[#E1002A] rounded-full" />
                        ) : null}
                      </span>
                      <span
                        className={`${
                          isDone
                            ? "text-[#0D2240] font-medium"
                            : isCurrent
                              ? "text-[#0D2240] font-semibold"
                              : "text-[#888]"
                        }`}
                      >
                        {step.label}
                      </span>
                    </li>
                  );
                })}
              </ul>

              {/* Swiss fact — bottom info strip */}
              <div className="border-t border-[#E0E3E8] pt-5">
                <p className="text-[0.7rem] font-semibold uppercase tracking-[0.1em] text-[#888] mb-1.5">
                  Warto wiedzieć
                </p>
                <p className="text-[0.9rem] text-[#555] leading-relaxed transition-opacity duration-500">
                  {SWISS_FACTS[currentFact]}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-2xl mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#FFF0F3] rounded-full mb-4">
            <FileText className="w-8 h-8 text-[#E1002A]" />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold font-display text-[#0D2240] mb-3">
            Sprawdź swoje CV za darmo
          </h1>
          <p className="text-lg text-gray-600 max-w-lg mx-auto">
            Wgraj swoje CV, a nasze narzędzie przeanalizuje je i poda konkretne
            wskazówki na rynek szwajcarski.
          </p>
        </div>

        {previousReviewId && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 text-center">
            <p className="text-blue-800 font-medium">
              Wrzuć poprawioną wersję CV, a porównamy wynik z poprzednią analizą.
            </p>
          </div>
        )}

        {/* Upload area */}
        <div
          role="button"
          tabIndex={file ? -1 : 0}
          aria-label="Wgraj CV"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => !file && fileInputRef.current?.click()}
          onKeyDown={(e) => {
            if (file) return;
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          className={`
            relative border-2 border-dashed rounded-lg p-10 text-center transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#E1002A]/40
            ${dragOver
              ? "border-[#E1002A] bg-[#FFF0F3] scale-[1.02]"
              : file
                ? "border-green-300 bg-green-50"
                : "border-gray-300 bg-white hover:border-[#E1002A] hover:bg-[#FFF0F3]/40"
            }
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={handleFileSelect}
            className="hidden"
          />

          {file ? (
            <div className="flex items-center justify-center gap-4">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <FileText className="w-6 h-6 text-green-600" />
              </div>
              <div className="text-left">
                <p className="font-semibold text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-500">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setFile(null);
                  if (fileInputRef.current) fileInputRef.current.value = "";
                }}
                className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center hover:bg-[#FFE0E6] hover:text-[#E1002A] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <>
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-lg font-semibold text-gray-700 mb-2">
                Przeciągnij i upuść CV tutaj
              </p>
              <p className="text-gray-500 mb-4">lub kliknij, aby wybrać plik</p>
              <p className="text-xs text-gray-400">
                Obsługiwane formaty: PDF, DOCX (max 5 MB)
              </p>
            </>
          )}
        </div>

        {/* Email (optional) */}
        <div className="mt-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Mail className="w-4 h-4 inline mr-1" />
            Email (opcjonalnie)
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="twoj@email.com - wyślemy Ci wyniki analizy"
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#E1002A]/40 focus:border-[#E1002A] transition-all"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 bg-[#FFF0F3] border border-[#FFC2CD] rounded-xl p-4">
            <p className="text-[#B8001F] text-sm">{error}</p>
          </div>
        )}

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={!file || uploading}
          className={`
            w-full mt-6 py-4 rounded-xl font-bold text-lg transition-all
            ${!file || uploading
              ? "bg-gray-200 text-gray-400 cursor-not-allowed"
              : "bg-[#0D2240] text-white hover:shadow-xl hover:scale-[1.01] active:scale-[0.99]"
            }
          `}
        >
          Analizuj CV
        </button>

        {/* Info */}
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4 text-center text-sm text-gray-500">
          <div className="bg-white border border-gray-100 rounded-xl p-4">
            <p className="font-semibold text-gray-700 mb-1">Bezpiecznie</p>
            <p>Twoje CV jest chronione i nie jest udostępniane</p>
          </div>
          <div className="bg-white border border-gray-100 rounded-xl p-4">
            <p className="font-semibold text-gray-700 mb-1">Za darmo</p>
            <p>Analiza CV jest całkowicie bezpłatna</p>
          </div>
          <div className="bg-white border border-gray-100 rounded-xl p-4">
            <p className="font-semibold text-gray-700 mb-1">Dla Szwajcarii</p>
            <p>Porady dostosowane do rynku szwajcarskiego</p>
          </div>
        </div>
      </div>
    </div>
  );
}
