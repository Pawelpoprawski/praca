"use client";

import { useEffect, useRef, useState } from "react";
import { X, Upload, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import api from "@/services/api";
import { getRecaptchaToken } from "@/lib/recaptcha";

interface Props {
  jobId: string;
  jobTitle: string;
  contactEmail: string;
  open: boolean;
  onClose: () => void;
}

const ALLOWED_EXT = /\.(pdf|docx?|odt|txt|rtf)$/i;
const MAX_SIZE_MB = 5;
const PHONE_RE = /^\+?[\d\s\-()]{7,30}$/;
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export default function ExternalApplyModal({ jobId, jobTitle, contactEmail, open, onClose }: Props) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [cv, setCv] = useState<File | null>(null);
  const [rodoConsent, setRodoConsent] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  // Reset stanu przy otwarciu
  useEffect(() => {
    if (open) {
      setError(null);
      setSuccess(false);
    }
  }, [open]);

  // Esc zamyka
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const validateFile = (file: File): string | null => {
    if (!ALLOWED_EXT.test(file.name)) return "Dozwolone formaty: PDF, DOC, DOCX, ODT, TXT, RTF";
    if (file.size === 0) return "Plik jest pusty";
    if (file.size > MAX_SIZE_MB * 1024 * 1024) return `Plik przekracza ${MAX_SIZE_MB} MB`;
    return null;
  };

  const handleFile = (file: File) => {
    const err = validateFile(file);
    if (err) {
      setError(err);
      setCv(null);
      return;
    }
    setError(null);
    setCv(file);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!firstName.trim() || !lastName.trim()) { setError("Imię i nazwisko są wymagane"); return; }
    if (!EMAIL_RE.test(email.trim())) { setError("Nieprawidłowy format email"); return; }
    if (!PHONE_RE.test(phone.trim())) { setError("Nieprawidłowy format telefonu"); return; }
    if (!cv) { setError("Załącz plik CV"); return; }
    if (!rodoConsent) { setError("Wymagana zgoda na przetwarzanie danych osobowych (RODO)"); return; }

    setSubmitting(true);
    try {
      const recaptchaToken = await getRecaptchaToken("apply_external");
      const fd = new FormData();
      fd.append("first_name", firstName.trim());
      fd.append("last_name", lastName.trim());
      fd.append("email", email.trim());
      fd.append("phone", phone.trim());
      fd.append("rodo_consent", "true");
      fd.append("cv", cv);

      await api.post(`/jobs/${jobId}/apply-external`, fd, {
        headers: {
          "Content-Type": "multipart/form-data",
          "X-Recaptcha-Token": recaptchaToken,
        },
      });
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Nie udało się wysłać aplikacji. Spróbuj ponownie.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[100] bg-black/60 flex items-center justify-center px-4 py-6 overflow-y-auto"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="apply-modal-title"
    >
      <div
        className="bg-white rounded-lg w-full max-w-[560px] max-h-[90vh] overflow-y-auto shadow-2xl border border-[#E0E3E8]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header navy + red accent */}
        <div className="bg-[#0D2240] text-white p-6 sm:p-8 relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 w-8 h-8 rounded hover:bg-white/10 flex items-center justify-center transition-colors"
            aria-label="Zamknij"
          >
            <X className="w-5 h-5" />
          </button>
          <span className="hays-red-line" />
          <h2 id="apply-modal-title" className="font-display text-[1.4rem] font-extrabold leading-tight">
            Aplikuj na ofertę
          </h2>
          <p className="text-white/70 text-[0.9rem] mt-1">{jobTitle}</p>
        </div>

        {/* Content */}
        <div className="p-6 sm:p-8">
          {success ? (
            <SuccessView onClose={onClose} />
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="bg-[#FFF0F3] border border-[#E1002A]/30 text-[#E1002A] px-4 py-3 rounded text-sm flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <FormField label="Imię" required>
                  <input
                    type="text" required value={firstName} onChange={(e) => setFirstName(e.target.value)}
                    autoComplete="given-name"
                    className="w-full px-3 py-2.5 border border-[#E0E3E8] rounded focus:outline-none focus:border-[#E1002A] focus:ring-2 focus:ring-[#E1002A]/20"
                  />
                </FormField>
                <FormField label="Nazwisko" required>
                  <input
                    type="text" required value={lastName} onChange={(e) => setLastName(e.target.value)}
                    autoComplete="family-name"
                    className="w-full px-3 py-2.5 border border-[#E0E3E8] rounded focus:outline-none focus:border-[#E1002A] focus:ring-2 focus:ring-[#E1002A]/20"
                  />
                </FormField>
              </div>

              <FormField label="Email" required>
                <input
                  type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  placeholder="jan@example.com"
                  className="w-full px-3 py-2.5 border border-[#E0E3E8] rounded focus:outline-none focus:border-[#E1002A] focus:ring-2 focus:ring-[#E1002A]/20"
                />
              </FormField>

              <FormField label="Telefon" required>
                <input
                  type="tel" required value={phone} onChange={(e) => setPhone(e.target.value)}
                  autoComplete="tel"
                  placeholder="+41 79 123 45 67"
                  className="w-full px-3 py-2.5 border border-[#E0E3E8] rounded focus:outline-none focus:border-[#E1002A] focus:ring-2 focus:ring-[#E1002A]/20"
                />
              </FormField>

              <FormField label="CV" required>
                <div className="mb-2 bg-[#FFF7E6] border-l-4 border-[#D97706] px-3 py-2 rounded-r">
                  <p className="text-[#92400E] font-bold tracking-wide text-[0.95rem] uppercase leading-tight">
                    BITTE LEBENSLAUF AUF DEUTSCH HOCHLADEN
                  </p>
                  <p className="text-xs text-[#92400E]/80 mt-0.5">
                    Prześlij CV po niemiecku — szwajcarscy pracodawcy oczekują CV w języku regionu pracy.
                  </p>
                </div>
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={onDrop}
                  className={`border-2 border-dashed rounded p-5 text-center transition-colors ${
                    dragOver ? "border-[#E1002A] bg-[#FFF0F3]" : "border-[#E0E3E8] bg-[#F5F6F8]"
                  }`}
                >
                  {cv ? (
                    <div className="flex items-center justify-between gap-3 text-left">
                      <div className="flex items-center gap-3 min-w-0">
                        <FileText className="w-7 h-7 text-[#E1002A] flex-shrink-0" />
                        <div className="min-w-0">
                          <div className="text-sm font-medium text-[#0D2240] truncate">{cv.name}</div>
                          <div className="text-xs text-[#888]">{(cv.size / 1024).toFixed(0)} KB</div>
                        </div>
                      </div>
                      <button
                        type="button" onClick={() => { setCv(null); if (fileRef.current) fileRef.current.value = ""; }}
                        className="text-[#888] hover:text-[#E1002A] flex-shrink-0"
                        aria-label="Usuń plik"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  ) : (
                    <>
                      <Upload className="w-8 h-8 text-[#888] mx-auto mb-2" />
                      <p className="text-sm text-[#555] mb-1">Przeciągnij plik tutaj lub</p>
                      <button
                        type="button" onClick={() => fileRef.current?.click()}
                        className="text-[#E1002A] hover:underline text-sm font-medium"
                      >
                        wybierz z dysku
                      </button>
                      <p className="text-xs text-[#888] mt-2">PDF, DOC, DOCX, ODT, TXT, RTF (max {MAX_SIZE_MB} MB)</p>
                    </>
                  )}
                  <input
                    ref={fileRef} type="file" required hidden
                    accept=".pdf,.doc,.docx,.odt,.txt,.rtf"
                    onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
                  />
                </div>
              </FormField>

              <label className="flex items-start gap-2.5 cursor-pointer group select-none">
                <input
                  type="checkbox"
                  required
                  checked={rodoConsent}
                  onChange={(e) => setRodoConsent(e.target.checked)}
                  className="mt-0.5 w-4 h-4 rounded border-gray-300 text-[#E1002A] focus:ring-2 focus:ring-[#E1002A]/30 cursor-pointer accent-[#E1002A] flex-shrink-0"
                />
                <span className="text-xs text-[#555] leading-relaxed">
                  Wyrażam zgodę na przetwarzanie moich danych osobowych (imię, nazwisko, email, telefon, CV)
                  przez Praca w Szwajcarii oraz przekazanie ich pracodawcy w celu rozpatrzenia aplikacji.
                  Dane mogę w każdej chwili usunąć kontaktując się na{" "}
                  <a href="mailto:kontakt@polacyszwajcaria.com" className="text-[#E1002A] hover:underline">
                    kontakt@polacyszwajcaria.com
                  </a>
                  . Więcej w <a href="/polityka-prywatnosci" target="_blank" className="text-[#E1002A] hover:underline">Polityce prywatności</a>.
                </span>
              </label>

              <div className="flex gap-3 pt-2">
                <button
                  type="button" onClick={onClose}
                  className="flex-1 border border-[#0D2240] text-[#0D2240] py-3 rounded font-medium hover:bg-[#0D2240] hover:text-white transition-all"
                >
                  Anuluj
                </button>
                <button
                  type="submit" disabled={submitting}
                  className="flex-1 bg-[#E1002A] hover:bg-[#B8001F] text-white py-3 rounded font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {submitting ? (
                    <span className="inline-flex items-center gap-2">
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Wysyłanie…
                    </span>
                  ) : "Wyślij aplikację"}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

function FormField({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-[#0D2240] mb-1.5">
        {label} {required && <span className="text-[#E1002A]">*</span>}
      </span>
      {children}
    </label>
  );
}

function SuccessView({ onClose }: { onClose: () => void }) {
  return (
    <div className="text-center py-4">
      <div className="w-14 h-14 mx-auto bg-[#FFF0F3] rounded-full flex items-center justify-center mb-4">
        <CheckCircle2 className="w-7 h-7 text-[#E1002A]" />
      </div>
      <h3 className="font-display text-[1.3rem] font-bold text-[#0D2240] mb-2">Aplikacja wysłana</h3>
      <p className="text-[#555] mb-6">
        Pracodawca otrzymał Twoje dane oraz CV.<br />
        Odpisze bezpośrednio na podany przez Ciebie adres email.
      </p>
      <button
        type="button" onClick={onClose}
        className="bg-[#0D2240] hover:bg-[#1A3A5C] text-white px-7 py-2.5 rounded font-medium transition-colors"
      >
        Zamknij
      </button>
    </div>
  );
}
