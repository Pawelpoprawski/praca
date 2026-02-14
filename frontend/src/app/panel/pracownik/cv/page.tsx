"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useRef } from "react";
import {
  Upload, FileText, Trash2, CheckCircle, User, Mail, Phone, Globe,
  ChevronRight, RotateCcw, ShieldCheck, Lightbulb, AlertTriangle,
  CircleCheck,
} from "lucide-react";
import api from "@/services/api";
import type { WorkerProfile, CVInfo, CVAnalysis } from "@/types/api";

const ALLOWED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

const STEPS = [
  { num: 1, label: "CV" },
  { num: 2, label: "Analiza" },
  { num: 3, label: "Decyzja" },
  { num: 4, label: "Zgoda" },
  { num: 5, label: "Gotowe" },
];

function ProgressBar({ step }: { step: number }) {
  return (
    <div className="flex items-center gap-1 mb-8">
      {STEPS.map((s, i) => (
        <div key={s.num} className="flex items-center flex-1">
          <div className="flex flex-col items-center flex-1">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                step > s.num
                  ? "bg-green-500 text-white"
                  : step === s.num
                  ? "bg-red-600 text-white"
                  : "bg-gray-200 text-gray-500"
              }`}
            >
              {step > s.num ? <CheckCircle className="w-4 h-4" /> : s.num}
            </div>
            <span className={`text-[10px] mt-1 ${step >= s.num ? "text-gray-700 font-medium" : "text-gray-400"}`}>
              {s.label}
            </span>
          </div>
          {i < STEPS.length - 1 && (
            <div className={`h-0.5 flex-1 -mt-4 mx-1 transition-colors duration-500 ${step > s.num ? "bg-green-500" : "bg-gray-200"}`} />
          )}
        </div>
      ))}
    </div>
  );
}

function ScoreCircle({ score }: { score: number }) {
  const color = score >= 70 ? "text-green-500" : score >= 40 ? "text-yellow-500" : "text-red-500";
  const bg = score >= 70 ? "border-green-200 bg-green-50" : score >= 40 ? "border-yellow-200 bg-yellow-50" : "border-red-200 bg-red-50";
  return (
    <div className={`w-24 h-24 rounded-full border-4 ${bg} flex flex-col items-center justify-center mx-auto mb-4`}>
      <span className={`text-2xl font-bold ${color}`}>{score}</span>
      <span className="text-[10px] text-gray-500">/ 100</span>
    </div>
  );
}

export default function CVPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [message, setMessage] = useState({ type: "", text: "" });
  const [step, setStep] = useState(1);
  const [analysis, setAnalysis] = useState<CVAnalysis | null>(null);
  const [consent, setConsent] = useState(false);
  const [jobPreferences, setJobPreferences] = useState("");

  const { data: profile, isLoading } = useQuery({
    queryKey: ["worker-profile"],
    queryFn: () => api.get<WorkerProfile>("/worker/profile").then((r) => r.data),
  });

  const { data: cvInfo } = useQuery({
    queryKey: ["cv-info"],
    queryFn: () => api.get<CVInfo>("/worker/cv-info").then((r) => r.data),
    enabled: !!profile?.has_cv,
    retry: false,
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return api.post("/worker/cv", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    },
    onSuccess: () => {
      setMessage({ type: "success", text: "CV zostało przesłane" });
      queryClient.invalidateQueries({ queryKey: ["worker-profile"] });
      queryClient.invalidateQueries({ queryKey: ["cv-info"] });
      setTimeout(() => {
        setMessage({ type: "", text: "" });
        setStep(2);
        analyzeMutation.mutate();
      }, 500);
    },
    onError: (err: any) => {
      setMessage({
        type: "error",
        text: err.response?.data?.detail || "Błąd przesyłania pliku",
      });
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: () => api.post<CVAnalysis>("/worker/cv-analyze").then((r) => r.data),
    onSuccess: (data) => {
      setAnalysis(data);
    },
    onError: (err: any) => {
      setMessage({
        type: "error",
        text: err.response?.data?.detail || "Błąd analizy CV",
      });
    },
  });

  const consentMutation = useMutation({
    mutationFn: () =>
      api.post("/worker/cv-consent", {
        consent: true,
        job_preferences: jobPreferences || null,
      }),
    onSuccess: () => {
      setStep(5);
      queryClient.invalidateQueries({ queryKey: ["cv-info"] });
    },
    onError: (err: any) => {
      setMessage({
        type: "error",
        text: err.response?.data?.detail || "Błąd zapisu zgody",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.delete("/worker/cv"),
    onSuccess: () => {
      setMessage({ type: "success", text: "CV zostało usunięte" });
      queryClient.invalidateQueries({ queryKey: ["worker-profile"] });
      queryClient.invalidateQueries({ queryKey: ["cv-info"] });
      setStep(1);
      setAnalysis(null);
      setConsent(false);
      setJobPreferences("");
      setTimeout(() => setMessage({ type: "", text: "" }), 3000);
    },
    onError: (err: any) => {
      setMessage({
        type: "error",
        text: err.response?.data?.detail || "Błąd usuwania CV",
      });
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (e.target) e.target.value = "";

    if (!ALLOWED_TYPES.includes(file.type)) {
      setMessage({ type: "error", text: "Dozwolony format: PDF lub DOCX" });
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setMessage({ type: "error", text: "Maksymalny rozmiar pliku: 5 MB" });
      return;
    }

    setMessage({ type: "", text: "" });
    uploadMutation.mutate(file);
  };

  if (isLoading) {
    return <div className="animate-pulse h-64 bg-gray-100 rounded-lg" />;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Moje CV</h1>

      {message.text && (
        <div
          className={`px-4 py-3 rounded-lg mb-4 text-sm ${
            message.type === "success"
              ? "bg-green-50 text-green-700"
              : "bg-red-50 text-red-600"
          }`}
        >
          {message.text}
        </div>
      )}

      <div className="bg-white border rounded-lg p-6">
        <ProgressBar step={step} />

        {/* STEP 1: Upload */}
        {step === 1 && (
          <div>
            {profile?.has_cv ? (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center">
                      <FileText className="w-5 h-5 text-red-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{profile.cv_filename}</p>
                      <div className="flex items-center gap-1 text-xs text-green-600">
                        <CheckCircle className="w-3 h-3" />
                        <span>Aktywne CV</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploadMutation.isPending}
                      className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 font-medium disabled:opacity-50"
                    >
                      Zmień
                    </button>
                    <button
                      onClick={() => deleteMutation.mutate()}
                      disabled={deleteMutation.isPending}
                      className="px-4 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 font-medium disabled:opacity-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Extracted data preview */}
                {cvInfo && cvInfo.extraction_status === "completed" && (
                  <div className="mb-4 pt-3 border-t">
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Dane odczytane z CV</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {cvInfo.extracted_name && (
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <User className="w-4 h-4 text-gray-400" />
                          <span>{cvInfo.extracted_name}</span>
                        </div>
                      )}
                      {cvInfo.extracted_email && (
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Mail className="w-4 h-4 text-gray-400" />
                          <span>{cvInfo.extracted_email}</span>
                        </div>
                      )}
                      {cvInfo.extracted_phone && (
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Phone className="w-4 h-4 text-gray-400" />
                          <span>{cvInfo.extracted_phone}</span>
                        </div>
                      )}
                      {cvInfo.extracted_languages && cvInfo.extracted_languages.length > 0 && (
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Globe className="w-4 h-4 text-gray-400" />
                          <span>
                            {cvInfo.extracted_languages
                              .map((l) => `${l.lang.toUpperCase()} (${l.level})`)
                              .join(", ")}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <button
                  onClick={() => {
                    setStep(2);
                    analyzeMutation.mutate();
                  }}
                  className="w-full mt-2 px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium flex items-center justify-center gap-2"
                >
                  Kontynuuj <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-red-300 hover:bg-red-50/30 transition-colors"
              >
                {uploadMutation.isPending ? (
                  <div className="animate-pulse">
                    <div className="w-8 h-8 bg-gray-300 rounded-full mx-auto mb-3" />
                    <p className="text-gray-500">Przesyłanie...</p>
                  </div>
                ) : (
                  <>
                    <Upload className="w-8 h-8 text-gray-400 mx-auto mb-3" />
                    <p className="font-medium text-gray-700 mb-1">Kliknij, aby przesłać CV</p>
                    <p className="text-sm text-gray-500">PDF lub DOCX, maksymalnie 5 MB</p>
                  </>
                )}
              </div>
            )}
          </div>
        )}

        {/* STEP 2: Analysis */}
        {step === 2 && (
          <div>
            {analyzeMutation.isPending ? (
              <div className="text-center py-8">
                <div className="animate-spin w-12 h-12 border-4 border-red-200 border-t-red-600 rounded-full mx-auto mb-4" />
                <p className="text-gray-700 font-semibold text-lg mb-2">Analizujemy Twoje CV...</p>
                <p className="text-sm text-gray-500">AI sprawdza Twoje doświadczenie, umiejętności i formatowanie</p>
                <div className="mt-4 flex items-center justify-center gap-2">
                  <div className="w-2 h-2 bg-red-600 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-2 h-2 bg-red-600 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="w-2 h-2 bg-red-600 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            ) : analysis ? (
              <div>
                <ScoreCircle score={analysis.score} />

                {analysis.strengths.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-green-700 mb-2 flex items-center gap-1">
                      <CircleCheck className="w-4 h-4" /> Mocne strony
                    </h3>
                    <ul className="space-y-1">
                      {analysis.strengths.map((s, i) => (
                        <li key={i} className="text-sm text-green-700 bg-green-50 px-3 py-2 rounded-lg">{s}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {analysis.weaknesses.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-red-700 mb-2 flex items-center gap-1">
                      <AlertTriangle className="w-4 h-4" /> Do poprawy
                    </h3>
                    <ul className="space-y-1">
                      {analysis.weaknesses.map((w, i) => (
                        <li key={i} className="text-sm text-red-700 bg-red-50 px-3 py-2 rounded-lg">{w}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {analysis.tips.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-yellow-700 mb-2 flex items-center gap-1">
                      <Lightbulb className="w-4 h-4" /> Wskazówki
                    </h3>
                    <ul className="space-y-1">
                      {analysis.tips.map((t, i) => (
                        <li key={i} className="text-sm text-yellow-700 bg-yellow-50 px-3 py-2 rounded-lg">{t}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <button
                  onClick={() => setStep(3)}
                  className="w-full mt-4 px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium flex items-center justify-center gap-2"
                >
                  Dalej <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="text-center py-8">
                <AlertTriangle className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
                <p className="text-gray-600">Nie udało się przeanalizować CV</p>
                <button
                  onClick={() => { setStep(1); }}
                  className="mt-4 text-sm text-red-600 hover:underline"
                >
                  Wróć do przesyłania
                </button>
              </div>
            )}
          </div>
        )}

        {/* STEP 3: Decision */}
        {step === 3 && (
          <div className="text-center py-4">
            <h2 className="text-lg font-bold text-gray-900 mb-2">Co chcesz zrobić?</h2>
            <p className="text-sm text-gray-500 mb-6">
              Możesz przesłać nowe CV lub kontynuować z obecnym
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => {
                  setStep(1);
                  setAnalysis(null);
                }}
                className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-lg hover:bg-gray-50 font-medium flex items-center justify-center gap-2 text-gray-700"
              >
                <RotateCcw className="w-4 h-4" /> Prześlij nowe CV
              </button>
              <button
                onClick={() => setStep(4)}
                className="flex-1 px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium flex items-center justify-center gap-2"
              >
                Kontynuuj <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: Consent */}
        {step === 4 && (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <ShieldCheck className="w-5 h-5 text-red-600" />
              <h2 className="text-lg font-bold text-gray-900">Udostępnij CV rekruterom</h2>
            </div>
            <p className="text-sm text-gray-500 mb-6">
              Twoje CV trafi do bazy dostępnej dla zweryfikowanych rekruterów w Szwajcarii.
              Mogą oni wyszukiwać kandydatów i kontaktować się z Tobą bezpośrednio.
            </p>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Preferencje dotyczące pracy (opcjonalnie)
              </label>
              <textarea
                value={jobPreferences}
                onChange={(e) => setJobPreferences(e.target.value)}
                placeholder="Np. szukam pracy w IT, najchętniej zdalnie, kanton Zurych lub Berno..."
                className="w-full border rounded-lg px-3 py-2 text-sm h-24 resize-none focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                maxLength={2000}
              />
            </div>

            <label className="flex items-start gap-3 mb-6 cursor-pointer">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500"
              />
              <span className="text-sm text-gray-700">
                Wyrażam zgodę na udostępnienie mojego CV rekruterom na platformie PolacySzwajcaria.
                Moje dane kontaktowe oraz treść CV będą widoczne dla zweryfikowanych pracodawców.
              </span>
            </label>

            <div className="flex gap-3">
              <button
                onClick={() => setStep(3)}
                className="px-4 py-3 border rounded-lg hover:bg-gray-50 font-medium text-gray-700"
              >
                Wstecz
              </button>
              <button
                onClick={() => consentMutation.mutate()}
                disabled={!consent || consentMutation.isPending}
                className="flex-1 px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {consentMutation.isPending ? "Zapisywanie..." : "Udostępnij CV"}
                {!consentMutation.isPending && <ShieldCheck className="w-4 h-4" />}
              </button>
            </div>
          </div>
        )}

        {/* STEP 5: Confirmation */}
        {step === 5 && (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-lg font-bold text-gray-900 mb-2">CV udostępnione!</h2>
            <p className="text-sm text-gray-500 mb-6">
              Twoje CV jest teraz dostępne dla rekruterów. Możesz w każdej chwili
              zaktualizować swoje CV lub cofnąć zgodę.
            </p>
            <button
              onClick={() => {
                setStep(1);
                setAnalysis(null);
                setConsent(false);
                setJobPreferences("");
              }}
              className="px-6 py-2 border rounded-lg hover:bg-gray-50 font-medium text-sm"
            >
              Wróć do CV
            </button>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={handleFileSelect}
          className="hidden"
        />

        {/* Tips (only on step 1) */}
        {step === 1 && (
          <div className="mt-6 pt-4 border-t">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Wskazówki</h3>
            <ul className="text-sm text-gray-500 space-y-1 list-disc list-inside">
              <li>Prześlij CV w formacie PDF lub DOCX</li>
              <li>Maksymalny rozmiar pliku: 5 MB</li>
              <li>Dane z CV zostaną automatycznie odczytane</li>
              <li>CV jest automatycznie dołączane do aplikacji</li>
              <li>Możesz w każdej chwili zaktualizować swoje CV</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
