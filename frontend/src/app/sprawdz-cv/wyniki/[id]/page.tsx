"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import Link from "next/link";
import {
  CheckCircle2, AlertTriangle, XCircle, Lightbulb, Mail,
  ArrowLeft, Upload, ArrowRight, Loader2, ChevronDown, ChevronUp,
  TrendingUp, User, Briefcase, Calendar, Globe,
  FileText, Clock, LayoutList, Flag, PlusCircle, MinusCircle, Sparkles,
} from "lucide-react";
import api from "@/services/api";
import type { CVReviewResponse, MessageResponse } from "@/types/api";

function ScoreGauge({ score, previousScore }: { score: number; previousScore?: number | null }) {
  const getColor = (s: number) => {
    if (s <= 3) return { stroke: "#dc2626", bg: "#fef2f2", text: "text-[#E1002A]" };
    if (s <= 6) return { stroke: "#d97706", bg: "#fffbeb", text: "text-yellow-600" };
    return { stroke: "#16a34a", bg: "#f0fdf4", text: "text-green-600" };
  };
  const color = getColor(score);
  const circumference = 2 * Math.PI * 54;
  const progress = (score / 10) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-40 h-40">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="54" fill="none" stroke="#e5e7eb" strokeWidth="8" />
          <circle
            cx="60"
            cy="60"
            r="54"
            fill="none"
            stroke={color.stroke}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-4xl font-bold ${color.text}`}>{score}</span>
          <span className="text-gray-400 text-sm">/10</span>
        </div>
      </div>
      {previousScore != null && previousScore !== score && (
        <div className={`mt-3 flex items-center gap-1 text-sm font-semibold ${
          score > previousScore ? "text-green-600" : score < previousScore ? "text-[#E1002A]" : "text-gray-500"
        }`}>
          <TrendingUp className="w-4 h-4" />
          {score > previousScore
            ? `Wzrost z ${previousScore}/10 na ${score}/10!`
            : `Zmiana z ${previousScore}/10 na ${score}/10`
          }
        </div>
      )}
    </div>
  );
}

function CategoryBlock({
  icon: Icon,
  title,
  subtitle,
  score,
  children,
}: {
  icon: React.ElementType;
  title: string;
  subtitle: string;
  score: number;
  children: React.ReactNode;
}) {
  const scoreColor =
    score <= 3 ? "text-[#E1002A]" : score <= 6 ? "text-yellow-600" : "text-green-600";
  const scoreBg =
    score <= 3 ? "bg-[#FFF0F3] border-[#FFC2CD]" : score <= 6 ? "bg-yellow-50 border-yellow-200" : "bg-green-50 border-green-200";

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="flex items-start gap-4 p-5 border-b border-gray-100">
        <div className="w-10 h-10 bg-[#0D2240] rounded flex items-center justify-center flex-shrink-0">
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-display text-[1.1rem] font-bold text-[#0D2240] leading-tight">
            {title}
          </h3>
          <p className="text-[0.85rem] text-gray-500 mt-0.5">{subtitle}</p>
        </div>
        <div className={`flex items-baseline gap-1 px-3 py-1.5 rounded border ${scoreBg} flex-shrink-0`}>
          <span className={`font-display font-extrabold text-[1.25rem] leading-none ${scoreColor}`}>
            {score}
          </span>
          <span className="text-gray-400 text-xs">/10</span>
        </div>
      </div>
      <div className="p-5 space-y-3">{children}</div>
    </div>
  );
}

function AnalysisSection({
  title,
  items,
  icon: Icon,
  iconColor,
  bgColor,
  borderColor,
  defaultOpen = true,
}: {
  title: string;
  items: string[];
  icon: React.ElementType;
  iconColor: string;
  bgColor: string;
  borderColor: string;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  if (!items || items.length === 0) return null;

  return (
    <div className={`${bgColor} border ${borderColor} rounded-xl overflow-hidden`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-5 text-left"
      >
        <div className="flex items-center gap-3">
          <Icon className={`w-5 h-5 ${iconColor}`} />
          <h3 className="font-bold text-gray-900">{title}</h3>
          <span className="text-sm text-gray-500">({items.length})</span>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
      </button>
      {open && (
        <ul className="px-5 pb-5 space-y-3">
          {items.map((item, i) => (
            <li key={i} className="flex items-start gap-3">
              <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${iconColor}`} />
              <span className="text-gray-700">{item}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

type FunnelStep = 1 | 3 | "loading" | 4;

export default function CVReviewResultPage({ params }: { params: { id: string } }) {
  const [funnelStep, setFunnelStep] = useState<FunnelStep>(1);
  const [emailInput, setEmailInput] = useState("");
  const [emailSent, setEmailSent] = useState(false);
  const [showEmailForm, setShowEmailForm] = useState(false);

  // Step 3 form data
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    phone: "",
    job_preferences: "",
    available_from: "",
    preferred_cantons: [] as string[],
    expected_salary_min: "",
    expected_salary_max: "",
    work_mode: "onsite",
    languages: [{ language: "", level: "" }],
    driving_license: "",
    has_car: false,
    additional_notes: "",
    consent_given: false,
  });

  // Loading state for step 3 -> 4
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingStep, setLoadingStep] = useState(0);
  const [referenceNumber, setReferenceNumber] = useState("");

  const { data: review, isLoading, error } = useQuery({
    queryKey: ["cv-review", params.id],
    queryFn: () =>
      api.get<CVReviewResponse>(`/cv-review/${params.id}`).then((r) => r.data),
  });

  const emailMutation = useMutation({
    mutationFn: (email: string) =>
      api.post<MessageResponse>(`/cv-review/${params.id}/send-email`, { email }),
    onSuccess: () => {
      setEmailSent(true);
      setShowEmailForm(false);
    },
  });

  const submitMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post<MessageResponse>(`/cv-review/${params.id}/submit-to-database`, data),
  });

  // Auto-fill form from CV review data
  useEffect(() => {
    if (review && funnelStep === 3) {
      setFormData((prev) => ({
        ...prev,
        email: review.email || prev.email,
      }));
    }
  }, [review, funnelStep]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Ładowanie wyników...</p>
        </div>
      </div>
    );
  }

  if (error || !review || !review.analysis) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md mx-auto px-4">
          <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold font-display text-[#0D2240] mb-2">Nie znaleziono analizy</h2>
          <p className="text-gray-600 mb-6">
            Podana analiza CV nie istnieje lub wystąpił błąd.
          </p>
          <Link
            href="/sprawdz-cv"
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Wróć do analizy CV
          </Link>
        </div>
      </div>
    );
  }

  const { analysis } = review;

  // Funnel progress bar component
  const FunnelProgressBar = ({ currentStep }: { currentStep: FunnelStep }) => {
    const steps = [
      { num: 1, label: "Analiza" },
      { num: 2, label: "Popraw CV" },
      { num: 3, label: "Zostaw CV" },
      { num: 4, label: "Gotowe!" },
    ];

    const getStepStatus = (stepNum: number) => {
      if (currentStep === "loading" && stepNum <= 3) return "active";
      if (currentStep === 4 && stepNum <= 4) return "completed";
      if (typeof currentStep === "number" && stepNum < currentStep) return "completed";
      if (typeof currentStep === "number" && stepNum === currentStep) return "active";
      return "upcoming";
    };

    return (
      <div className="mb-8">
        <div className="flex items-center justify-between max-w-2xl mx-auto">
          {steps.map((step, i) => {
            const status = getStepStatus(step.num);
            return (
              <div key={step.num} className="flex items-center flex-1">
                <div className="flex flex-col items-center relative">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all ${
                      status === "completed"
                        ? "bg-green-500 text-white"
                        : status === "active"
                        ? "bg-blue-600 text-white ring-4 ring-blue-100"
                        : "bg-gray-200 text-gray-400"
                    }`}
                  >
                    {status === "completed" ? (
                      <CheckCircle2 className="w-5 h-5" />
                    ) : (
                      step.num
                    )}
                  </div>
                  <span
                    className={`text-xs mt-2 font-medium ${
                      status === "completed" || status === "active"
                        ? "text-gray-900"
                        : "text-gray-400"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
                {i < steps.length - 1 && (
                  <div className="flex-1 h-1 mx-2 -mt-6 relative">
                    <div className="absolute inset-0 bg-gray-200 rounded" />
                    <div
                      className={`absolute inset-0 rounded transition-all duration-500 ${
                        getStepStatus(step.num + 1) === "completed" ||
                        getStepStatus(step.num + 1) === "active"
                          ? "bg-green-500"
                          : "bg-gray-200"
                      }`}
                      style={{
                        width:
                          getStepStatus(step.num + 1) === "completed" ||
                          getStepStatus(step.num + 1) === "active"
                            ? "100%"
                            : "0%",
                      }}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Step 1: Results
  if (funnelStep === 1) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-3xl mx-auto px-4 py-12">
          <Link
            href="/sprawdz-cv"
            className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-8 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Nowa analiza
          </Link>

          <FunnelProgressBar currentStep={1} />

          {/* Critical issues — shown PROMINENTLY above everything */}
          {analysis.critical_issues && analysis.critical_issues.length > 0 && (
            <div className="bg-[#FFF0F3] border-2 border-[#E1002A] rounded-lg p-6 mb-6 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1.5 h-full bg-[#E1002A]" />
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-[#E1002A] rounded-full flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="w-5 h-5 text-white" strokeWidth={2.5} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[0.7rem] font-bold uppercase tracking-[0.15em] text-[#E1002A] mb-1.5">
                    Krytyczny problem — najpilniejsze
                  </div>
                  <h2 className="font-display text-[1.15rem] font-bold text-[#0D2240] mb-3">
                    To musisz naprawić zanim wyślesz CV
                  </h2>
                  <div className="space-y-3">
                    {analysis.critical_issues.map((issue, i) => (
                      <p
                        key={i}
                        className="text-[0.95rem] text-[#0D2240] leading-relaxed whitespace-pre-line"
                      >
                        {issue}
                      </p>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Score */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-8 mb-6 text-center">
            <h1 className="text-2xl font-bold font-display text-[#0D2240] mb-6">
              Wynik analizy Twojego CV
            </h1>
            <ScoreGauge score={analysis.overall_score} previousScore={review.previous_score} />
            <p className="mt-6 text-gray-600 max-w-lg mx-auto leading-relaxed">
              {analysis.summary}
            </p>
          </div>

          {/* Analysis sections */}
          <div className="space-y-6 mb-8">
            {analysis.structure || analysis.swiss_fit ? (
              <>
                {/* Category 1: CV structure */}
                {analysis.structure && (
                  <CategoryBlock
                    icon={LayoutList}
                    title="Struktura i zawartość CV"
                    subtitle="Forma, sekcje, dobór informacji, gramatyka"
                    score={analysis.structure.score}
                  >
                    <AnalysisSection
                      title="Co działa dobrze — zostaw"
                      items={analysis.structure.works_well}
                      icon={CheckCircle2}
                      iconColor="text-green-600"
                      bgColor="bg-green-50/50"
                      borderColor="border-green-200"
                    />
                    <AnalysisSection
                      title="Co poprawić lub usunąć"
                      items={analysis.structure.needs_fixing}
                      icon={MinusCircle}
                      iconColor="text-[#E1002A]"
                      bgColor="bg-[#FFF0F3]/50"
                      borderColor="border-[#FFC2CD]"
                    />
                    <AnalysisSection
                      title="Co dodać"
                      items={analysis.structure.to_add}
                      icon={PlusCircle}
                      iconColor="text-[#0D2240]"
                      bgColor="bg-[#F0F4FA]"
                      borderColor="border-[#C5D2E5]"
                    />
                  </CategoryBlock>
                )}

                {/* Category 2: Swiss market fit */}
                {analysis.swiss_fit && (
                  <CategoryBlock
                    icon={Flag}
                    title="Dopasowanie do rynku szwajcarskiego"
                    subtitle="Języki, doświadczenie, branże, pozwolenia"
                    score={analysis.swiss_fit.score}
                  >
                    <AnalysisSection
                      title="Twoje atuty"
                      items={analysis.swiss_fit.advantages}
                      icon={CheckCircle2}
                      iconColor="text-green-600"
                      bgColor="bg-green-50/50"
                      borderColor="border-green-200"
                    />
                    <AnalysisSection
                      title="Na co zwrócić uwagę"
                      items={analysis.swiss_fit.concerns}
                      icon={AlertTriangle}
                      iconColor="text-yellow-700"
                      bgColor="bg-yellow-50/50"
                      borderColor="border-yellow-200"
                    />
                    <AnalysisSection
                      title="Konkretne kroki"
                      items={analysis.swiss_fit.actions}
                      icon={Sparkles}
                      iconColor="text-[#0D2240]"
                      bgColor="bg-[#F0F4FA]"
                      borderColor="border-[#C5D2E5]"
                    />
                  </CategoryBlock>
                )}

                {analysis.tips && analysis.tips.length > 0 && (
                  <AnalysisSection
                    title="Dodatkowe porady"
                    items={analysis.tips}
                    icon={Lightbulb}
                    iconColor="text-[#0D2240]"
                    bgColor="bg-white"
                    borderColor="border-gray-200"
                  />
                )}
              </>
            ) : (
              <>
                {/* Legacy display for old reviews */}
                <AnalysisSection
                  title="Mocne strony"
                  items={analysis.strengths}
                  icon={CheckCircle2}
                  iconColor="text-green-600"
                  bgColor="bg-green-50/50"
                  borderColor="border-green-200"
                />
                <AnalysisSection
                  title="Do poprawienia"
                  items={analysis.improvements}
                  icon={AlertTriangle}
                  iconColor="text-yellow-600"
                  bgColor="bg-yellow-50/50"
                  borderColor="border-yellow-200"
                />
                <AnalysisSection
                  title="Brakujące elementy"
                  items={analysis.missing}
                  icon={XCircle}
                  iconColor="text-[#E1002A]"
                  bgColor="bg-[#FFF0F3]/50"
                  borderColor="border-[#FFC2CD]"
                />
                <AnalysisSection
                  title="Porady na rynek szwajcarski"
                  items={analysis.tips}
                  icon={Lightbulb}
                  iconColor="text-[#0D2240]"
                  bgColor="bg-[#F0F4FA]"
                  borderColor="border-[#C5D2E5]"
                />
              </>
            )}
          </div>

          {/* Email notification */}
          {emailSent ? (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-6 text-center">
              <CheckCircle2 className="w-5 h-5 text-green-600 mx-auto mb-2" />
              <p className="text-green-800 font-medium">
                Wyniki zostały wysłane na podany email!
              </p>
            </div>
          ) : showEmailForm ? (
            <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Mail className="w-5 h-5 text-blue-600" />
                Wyślij wyniki na email
              </h3>
              <div className="flex gap-3">
                <input
                  type="email"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  placeholder="twoj@email.com"
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={() => emailMutation.mutate(emailInput)}
                  disabled={!emailInput || emailMutation.isPending}
                  className="bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {emailMutation.isPending ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    "Wyślij"
                  )}
                </button>
              </div>
              {emailMutation.isError && (
                <p className="text-[#E1002A] text-sm mt-2">
                  Nie udało się wysłać emaila. Spróbuj ponownie.
                </p>
              )}
            </div>
          ) : null}

          {/* Action buttons */}
          <div className="flex gap-4 mb-8">
            <div className="flex-1">
              {!emailSent && !showEmailForm && (
                <button
                  onClick={() => setShowEmailForm(true)}
                  className="w-full flex items-center justify-center gap-2 bg-white border border-gray-200 text-gray-700 px-4 py-3 rounded-xl font-semibold hover:bg-gray-50 transition-colors"
                >
                  <Mail className="w-4 h-4" />
                  Wyślij na email
                </button>
              )}
            </div>
            <div className="flex-1">
              <Link
                href={`/sprawdz-cv?previous=${review.id}`}
                className="w-full flex items-center justify-center gap-2 bg-white border border-blue-200 text-blue-700 px-4 py-3 rounded-xl font-semibold hover:bg-blue-50 transition-colors"
              >
                <Upload className="w-4 h-4" />
                Wrzuć poprawione CV
              </Link>
            </div>
          </div>

          <button
            onClick={() => setFunnelStep(3)}
            className="w-full flex items-center justify-center gap-2 bg-[#0D2240] text-white px-6 py-4 rounded-xl font-bold text-lg hover:shadow-xl transition-all"
          >
            Dalej
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    );
  }

  // Step 3: Submit to recruiters
  if (funnelStep === 3) {
    const addLanguage = () => {
      setFormData((prev) => ({
        ...prev,
        languages: [...prev.languages, { language: "", level: "" }],
      }));
    };

    const updateLanguage = (index: number, field: string, value: string) => {
      setFormData((prev) => ({
        ...prev,
        languages: prev.languages.map((l, i) =>
          i === index ? { ...l, [field]: value } : l
        ),
      }));
    };

    const removeLanguage = (index: number) => {
      setFormData((prev) => ({
        ...prev,
        languages: prev.languages.filter((_, i) => i !== index),
      }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!formData.consent_given) return;

      setFunnelStep("loading");
      setLoadingProgress(0);
      setLoadingStep(0);

      // Start API call immediately
      const apiPromise = submitMutation.mutateAsync({
        full_name: formData.full_name || null,
        email: formData.email || null,
        phone: formData.phone || null,
        job_preferences: formData.job_preferences,
        available_from: formData.available_from || null,
        preferred_cantons: formData.preferred_cantons,
        expected_salary_min: formData.expected_salary_min
          ? parseInt(formData.expected_salary_min)
          : null,
        expected_salary_max: formData.expected_salary_max
          ? parseInt(formData.expected_salary_max)
          : null,
        work_mode: formData.work_mode || null,
        languages: formData.languages.filter((l) => l.language && l.level),
        driving_license: formData.driving_license ? [formData.driving_license] : null,
        has_car: formData.has_car,
        additional_notes: formData.additional_notes || null,
        consent_given: formData.consent_given,
      });

      // Minimum animation: 4 steps x 1.5s = 6 seconds
      const minAnimationPromise = new Promise<void>((resolve) => {
        let step = 0;
        const stepInterval = setInterval(() => {
          step++;
          setLoadingStep(step);
          if (step >= 4) {
            clearInterval(stepInterval);
            resolve();
          }
        }, 1500);
      });

      // Progress bar: smooth fill to 85% over 5.5 seconds
      const progressInterval = setInterval(() => {
        setLoadingProgress((prev) => {
          if (prev >= 85) {
            clearInterval(progressInterval);
            return 85;
          }
          return prev + 3;
        });
      }, 200);

      try {
        // Wait for BOTH: API response AND minimum animation time
        await Promise.all([apiPromise, minAnimationPromise]);

        clearInterval(progressInterval);
        setLoadingProgress(100);
        setLoadingStep(4);

        // Show 100% for a moment before transitioning
        const refNum = `CV-${params.id.substring(0, 8).toUpperCase()}`;
        setTimeout(() => {
          setReferenceNumber(refNum);
          setFunnelStep(4);
        }, 1000);
      } catch {
        clearInterval(progressInterval);
        setFunnelStep(3);
      }
    };

    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-3xl mx-auto px-4 py-12">
          <FunnelProgressBar currentStep={3} />

          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-8">
            <h2 className="text-2xl font-bold font-display text-[#0D2240] mb-2 text-center">
              Zostaw nam swoje CV
            </h2>
            <p className="text-gray-600 mb-8 text-center max-w-xl mx-auto">
              Wypełnij krótki formularz, a jeśli spełniasz kryteria, pracodawcy sami
              się z Tobą skontaktują
            </p>

            <form onSubmit={handleSubmit} className="space-y-8">
              {/* Sekcja: O Tobie */}
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <User className="w-5 h-5 text-blue-600" />
                  O Tobie
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Imię i nazwisko *
                    </label>
                    <input
                      type="text"
                      value={formData.full_name}
                      onChange={(e) =>
                        setFormData({ ...formData, full_name: e.target.value })
                      }
                      placeholder="Jan Kowalski"
                      required
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Email *
                      </label>
                      <input
                        type="email"
                        value={formData.email}
                        onChange={(e) =>
                          setFormData({ ...formData, email: e.target.value })
                        }
                        placeholder="twoj@email.com"
                        required
                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Telefon *
                      </label>
                      <input
                        type="tel"
                        value={formData.phone}
                        onChange={(e) =>
                          setFormData({ ...formData, phone: e.target.value })
                        }
                        placeholder="+48 123 456 789"
                        required
                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Sekcja: Czego szukasz */}
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-blue-600" />
                  Czego szukasz?
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Jakiej pracy szukasz? *
                    </label>
                    <textarea
                      value={formData.job_preferences}
                      onChange={(e) =>
                        setFormData({ ...formData, job_preferences: e.target.value })
                      }
                      placeholder="np. Praca w budownictwie, spawacz, kelner, opiekunka..."
                      rows={3}
                      required
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      <Calendar className="w-4 h-4 inline mr-1" />
                      Od kiedy jesteś dostępny/a?
                    </label>
                    <input
                      type="date"
                      value={formData.available_from}
                      onChange={(e) =>
                        setFormData({ ...formData, available_from: e.target.value })
                      }
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Sekcja: Kompetencje */}
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Globe className="w-5 h-5 text-blue-600" />
                  Twoje kompetencje
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Języki
                    </label>
                    {formData.languages.map((lang, i) => (
                      <div key={i} className="flex gap-3 mb-2">
                        <select
                          value={lang.language}
                          onChange={(e) =>
                            updateLanguage(i, "language", e.target.value)
                          }
                          className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                        >
                          <option value="">Wybierz język</option>
                          {LANGUAGE_OPTIONS.map((l) => (
                            <option key={l} value={l}>
                              {l}
                            </option>
                          ))}
                        </select>
                        <select
                          value={lang.level}
                          onChange={(e) => updateLanguage(i, "level", e.target.value)}
                          className="w-28 px-3 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                        >
                          <option value="">Poziom</option>
                          {LEVEL_OPTIONS.map((l) => (
                            <option key={l} value={l}>
                              {l}
                            </option>
                          ))}
                        </select>
                        {formData.languages.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeLanguage(i)}
                            className="px-3 py-3 text-red-500 hover:bg-[#FFF0F3] rounded-xl transition-colors"
                          >
                            <XCircle className="w-5 h-5" />
                          </button>
                        )}
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={addLanguage}
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                    >
                      + Dodaj język
                    </button>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Prawo jazdy
                      </label>
                      <select
                        value={formData.driving_license}
                        onChange={(e) =>
                          setFormData({ ...formData, driving_license: e.target.value })
                        }
                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                      >
                        <option value="">Brak / nie dotyczy</option>
                        <option value="B">Kat. B</option>
                        <option value="C">Kat. C</option>
                        <option value="D">Kat. D</option>
                        <option value="E">Kat. E</option>
                        <option value="B+C">Kat. B+C</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Czy posiadasz samochód?
                      </label>
                      <div className="grid grid-cols-2 gap-3">
                        {[
                          { value: true, label: "Tak" },
                          { value: false, label: "Nie" },
                        ].map((opt) => (
                          <button
                            key={String(opt.value)}
                            type="button"
                            onClick={() =>
                              setFormData({ ...formData, has_car: opt.value })
                            }
                            className={`px-4 py-3 rounded-xl text-sm font-medium transition-all border ${
                              formData.has_car === opt.value
                                ? "bg-blue-600 text-white border-blue-600"
                                : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
                            }`}
                          >
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Sekcja: Dodatkowe */}
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-600" />
                  Dodatkowe
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Dodatkowe uwagi
                    </label>
                    <textarea
                      value={formData.additional_notes}
                      onChange={(e) =>
                        setFormData({ ...formData, additional_notes: e.target.value })
                      }
                      placeholder="Dodatkowe informacje, które mogą być ważne..."
                      rows={2}
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    />
                  </div>
                  <div className="flex items-start gap-3 bg-gray-50 p-4 rounded-xl border border-gray-200">
                    <input
                      type="checkbox"
                      id="consent"
                      checked={formData.consent_given}
                      onChange={(e) =>
                        setFormData({ ...formData, consent_given: e.target.checked })
                      }
                      className="mt-1 w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <label htmlFor="consent" className="text-sm text-gray-700">
                      Wyrażam zgodę na przetwarzanie moich danych osobowych zawartych w
                      CV w celu prezentacji mojego profilu potencjalnym pracodawcom. *
                    </label>
                  </div>
                </div>
              </div>

              {submitMutation.isError && (
                <div className="bg-[#FFF0F3] border border-[#FFC2CD] rounded-xl p-4">
                  <p className="text-[#B8001F] text-sm">
                    {(() => {
                      const detail = (
                        submitMutation.error as {
                          response?: { data?: { detail?: string | Array<{ msg?: string }> } };
                        }
                      )?.response?.data?.detail;
                      if (typeof detail === "string") return detail;
                      if (Array.isArray(detail)) return detail.map((e) => e.msg || "").join(", ");
                      return "Wystąpił błąd. Spróbuj ponownie.";
                    })()}
                  </p>
                </div>
              )}

              <button
                type="submit"
                disabled={
                  !formData.consent_given ||
                  !formData.job_preferences ||
                  !formData.full_name ||
                  !formData.email ||
                  !formData.phone ||
                  submitMutation.isPending
                }
                className={`
                  w-full py-4 rounded-xl font-bold text-lg transition-all
                  ${
                    !formData.consent_given ||
                    !formData.job_preferences ||
                    !formData.full_name ||
                    !formData.email ||
                    !formData.phone ||
                    submitMutation.isPending
                      ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                      : "bg-[#0D2240] text-white hover:shadow-xl"
                  }
                `}
              >
                Prześlij CV do rekruterów
              </button>

              <div className="text-center">
                <Link
                  href="/"
                  className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
                >
                  Pomiń ten krok
                </Link>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // Loading screen (between step 3 and 4)
  if (funnelStep === "loading") {
    const loadingSteps = [
      "Zapisujemy Twoje CV...",
      "Analizujemy Twoje kompetencje...",
      "Dopasowujemy do ofert pracy...",
      "Finalizujemy profil...",
    ];

    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center">
        <div className="max-w-lg mx-auto px-4 w-full">
          <FunnelProgressBar currentStep="loading" />

          <div className="bg-white rounded-lg shadow-xl border border-gray-100 p-8 md:p-10">
            <div className="flex justify-center mb-8">
              <div className="relative">
                <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center animate-pulse">
                  <Clock className="w-10 h-10 text-blue-600" />
                </div>
                <div
                  className="absolute -inset-2 border-2 border-blue-200 rounded-full animate-spin"
                  style={{ borderTopColor: "transparent", animationDuration: "3s" }}
                />
              </div>
            </div>

            <h2 className="text-xl font-bold font-display text-[#0D2240] text-center mb-2">
              Przetwarzamy Twoje dane
            </h2>
            <p className="text-gray-500 text-center text-sm mb-8">
              To zajmie tylko chwilę...
            </p>

            <div className="mb-6">
              <div className="flex justify-between text-xs text-gray-400 mb-2">
                <span>Postęp</span>
                <span>{Math.round(loadingProgress)}%</span>
              </div>
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out"
                  style={{
                    width: `${loadingProgress}%`,
                    background:
                      loadingProgress < 100
                        ? "linear-gradient(90deg, #3b82f6, #6366f1)"
                        : "linear-gradient(90deg, #22c55e, #16a34a)",
                  }}
                />
              </div>
            </div>

            <div className="space-y-3">
              {loadingSteps.map((step, i) => {
                const isDone = i < loadingStep;
                const isCurrent = i === loadingStep;
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
                    <div
                      className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
                        isDone
                          ? "bg-green-500"
                          : isCurrent
                          ? "bg-blue-500"
                          : "bg-gray-300"
                      }`}
                    >
                      {isDone ? (
                        <CheckCircle2 className="w-4 h-4 text-white" />
                      ) : (
                        <div
                          className={`w-3 h-3 rounded-full bg-white ${
                            isCurrent ? "animate-pulse" : ""
                          }`}
                        />
                      )}
                    </div>
                    <span
                      className={`text-sm ${
                        isDone
                          ? "text-green-700 font-medium"
                          : isCurrent
                          ? "text-blue-700 font-medium"
                          : "text-gray-400"
                      }`}
                    >
                      {isDone ? step.replace("...", " - gotowe!") : step}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Step 4: Success
  if (funnelStep === 4) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-3xl mx-auto px-4 py-12">
          <FunnelProgressBar currentStep={4} />

          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-8 text-center">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6 animate-bounce">
              <CheckCircle2 className="w-10 h-10 text-green-600" />
            </div>

            <h1 className="text-3xl font-bold font-display text-[#0D2240] mb-3">
              Twoje CV zostało zapisane!
            </h1>
            <p className="text-lg text-gray-600 mb-2">
              Twój unikalny numer referencyjny:
            </p>
            <p className="text-2xl font-mono font-bold text-blue-600 mb-8">
              {referenceNumber}
            </p>

            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-8 text-left">
              <p className="text-gray-700 mb-4">
                Jeśli Twój profil spełni kryteria pracodawców, skontaktujemy się z
                Tobą na podany adres email.
              </p>
              <h3 className="font-bold text-gray-900 mb-3">
                Podsumowanie Twojego profilu:
              </h3>
              <div className="space-y-2 text-sm text-gray-600">
                <p>
                  <span className="font-semibold">Imię i nazwisko:</span>{" "}
                  {formData.full_name}
                </p>
                <p>
                  <span className="font-semibold">Email:</span>{" "}
                  {formData.email}
                </p>
                <p>
                  <span className="font-semibold">Szukana praca:</span>{" "}
                  {formData.job_preferences}
                </p>
                {formData.available_from && (
                  <p>
                    <span className="font-semibold">Dostępność od:</span>{" "}
                    {formData.available_from}
                  </p>
                )}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Link
                href="/oferty"
                className="flex-1 flex items-center justify-center gap-2 bg-[#0D2240] text-white px-6 py-4 rounded-xl font-bold hover:shadow-xl transition-all"
              >
                Przeglądaj oferty pracy
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                href="/"
                className="flex-1 flex items-center justify-center gap-2 bg-white border border-gray-300 text-gray-700 px-6 py-4 rounded-xl font-bold hover:bg-gray-50 transition-all"
              >
                Wróć na stronę główną
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
// Constants
const LANGUAGE_OPTIONS = [
  "Polski", "Niemiecki", "Angielski", "Włoski", "Francuski",
];

const LEVEL_OPTIONS = ["A1", "A2", "B1", "B2", "C1", "C2", "Native"];
