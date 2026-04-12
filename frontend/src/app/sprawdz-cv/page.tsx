"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, X, Mail, CheckCircle2, Search, BookOpen, Languages, Award, FileCheck } from "lucide-react";
import api from "@/services/api";
import type { CVReviewResponse } from "@/types/api";

const ANALYSIS_STEPS = [
  { icon: Upload, label: "Wczytywanie dokumentu...", duration: 1500 },
  { icon: Search, label: "Sprawdzamy strukturę CV...", duration: 2000 },
  { icon: BookOpen, label: "Analizujemy doświadczenie zawodowe...", duration: 2000 },
  { icon: Languages, label: "Weryfikujemy kompetencje językowe...", duration: 1500 },
  { icon: FileCheck, label: "Sprawdzamy gramatykę i stylizację...", duration: 1500 },
  { icon: Award, label: "Przygotowujemy rekomendacje...", duration: 1500 },
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

  // Step through analysis stages
  useEffect(() => {
    if (!uploading) return;
    setCurrentStep(0);
    let step = 0;

    const advanceStep = () => {
      step++;
      if (step < ANALYSIS_STEPS.length) {
        setCurrentStep(step);
        stepTimerRef.current = setTimeout(advanceStep, ANALYSIS_STEPS[step].duration);
      }
    };

    stepTimerRef.current = setTimeout(advanceStep, ANALYSIS_STEPS[0].duration);
    return () => { if (stepTimerRef.current) clearTimeout(stepTimerRef.current); };
  }, [uploading]);

  // Smooth progress bar (reaches ~90% during analysis, 100% when done)
  useEffect(() => {
    if (!uploading) {
      setProgress(0);
      return;
    }
    setProgress(0);
    const totalDuration = 10000; // 10 seconds to reach ~90%
    const interval = 100;
    let elapsed = 0;

    progressTimerRef.current = setInterval(() => {
      elapsed += interval;
      // Easing: fast start, slows down near 90%
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
    setUploading(true);
    setApiDone(false);
    setReviewId(null);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      if (email) formData.append("email", email);
      if (previousReviewId) formData.append("previous_review_id", previousReviewId);

      const response = await api.post<CVReviewResponse>("/cv-review/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
      });

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
    const StepIcon = ANALYSIS_STEPS[currentStep]?.icon || FileCheck;
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center">
        <div className="max-w-lg mx-auto px-4 w-full">
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8 md:p-10">
            {/* Animated icon */}
            <div className="flex justify-center mb-8">
              <div className="relative">
                <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center animate-pulse">
                  <StepIcon className="w-10 h-10 text-blue-600" />
                </div>
                <div className="absolute -inset-2 border-2 border-blue-200 rounded-full animate-spin" style={{ borderTopColor: 'transparent', animationDuration: '3s' }} />
              </div>
            </div>

            <h2 className="text-xl font-bold text-gray-900 text-center mb-2">
              Analizujemy Twoje CV
            </h2>
            <p className="text-gray-500 text-center text-sm mb-8">
              To zajmie tylko chwilę...
            </p>

            {/* Progress bar */}
            <div className="mb-6">
              <div className="flex justify-between text-xs text-gray-400 mb-2">
                <span>Postęp analizy</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out"
                  style={{
                    width: `${progress}%`,
                    background: progress < 100
                      ? 'linear-gradient(90deg, #3b82f6, #6366f1)'
                      : 'linear-gradient(90deg, #22c55e, #16a34a)',
                  }}
                />
              </div>
            </div>

            {/* Analysis steps */}
            <div className="space-y-3 mb-8">
              {ANALYSIS_STEPS.map((step, i) => {
                const Icon = step.icon;
                const isDone = i < currentStep;
                const isCurrent = i === currentStep;
                return (
                  <div
                    key={i}
                    className={`flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-300 ${
                      isCurrent
                        ? "bg-blue-50 border border-blue-200"
                        : isDone
                          ? "bg-green-50 border border-green-200"
                          : "bg-gray-50 border border-transparent opacity-40"
                    }`}
                  >
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
                      isDone ? "bg-green-500" : isCurrent ? "bg-blue-500" : "bg-gray-300"
                    }`}>
                      {isDone ? (
                        <CheckCircle2 className="w-4 h-4 text-white" />
                      ) : (
                        <Icon className={`w-3.5 h-3.5 text-white ${isCurrent ? "animate-pulse" : ""}`} />
                      )}
                    </div>
                    <span className={`text-sm ${
                      isDone ? "text-green-700 font-medium" : isCurrent ? "text-blue-700 font-medium" : "text-gray-400"
                    }`}>
                      {isDone ? step.label.replace("...", " - gotowe!") : step.label}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Swiss fun fact */}
            <div className="bg-gradient-to-r from-red-50 to-red-100/50 border border-red-200 rounded-xl p-4">
              <p className="text-xs font-semibold text-red-800 mb-1 flex items-center gap-1.5">
                <span className="text-base">🇨🇭</span> Czy wiesz, że...
              </p>
              <p className="text-sm text-red-700 leading-relaxed transition-opacity duration-500">
                {SWISS_FACTS[currentFact]}
              </p>
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
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
            <FileText className="w-8 h-8 text-blue-600" />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
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
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => !file && fileInputRef.current?.click()}
          className={`
            relative border-2 border-dashed rounded-2xl p-10 text-center transition-all cursor-pointer
            ${dragOver
              ? "border-blue-500 bg-blue-50 scale-[1.02]"
              : file
                ? "border-green-300 bg-green-50"
                : "border-gray-300 bg-white hover:border-blue-400 hover:bg-blue-50/50"
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
                className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center hover:bg-red-100 hover:text-red-600 transition-colors"
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
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-xl p-4">
            <p className="text-red-700 text-sm">{error}</p>
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
              : "bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:shadow-xl hover:scale-[1.01] active:scale-[0.99]"
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
