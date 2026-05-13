"use client";

import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Upload, FileText, X, Mail, Users, Briefcase, ShieldCheck } from "lucide-react";
import api from "@/services/api";
import type { CVReviewResponse } from "@/types/api";

export default function WorkerCVSubmitPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [email, setEmail] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) validateAndSetFile(f);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      if (email) formData.append("email", email);
      // Hint dla strony wyników, żeby od razu otworzyć krok "Zostaw CV w bazie"
      formData.append("intent", "submit_to_db");

      const response = await api.post<CVReviewResponse>("/cv-review/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
      });

      router.push(`/sprawdz-cv/wyniki/${response.data.id}?step=submit`);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(
        axiosErr.response?.data?.detail ||
          "Wystąpił błąd podczas wysyłki CV. Spróbuj ponownie.",
      );
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-2xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#FFF0F3] rounded-full mb-4">
            <Briefcase className="w-8 h-8 text-[#E1002A]" />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold font-display text-[#0D2240] mb-3">
            Wyślij nam swoje CV
          </h1>
          <p className="text-lg text-gray-600 max-w-lg mx-auto">
            Zostaw swoje CV w naszej bazie. Jeśli rekruterzy uznają je za pasujące do
            otwartych pozycji w Szwajcarii — sami się do Ciebie odezwą.
          </p>
        </div>

        {/* How it works strip */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
            <div className="w-9 h-9 bg-[#F0F4FA] rounded-full flex items-center justify-center mx-auto mb-2">
              <Upload className="w-4 h-4 text-[#0D2240]" />
            </div>
            <p className="text-sm font-semibold text-[#0D2240] mb-0.5">1. Wyślij CV</p>
            <p className="text-xs text-gray-500 leading-relaxed">
              Wgraj plik PDF lub DOCX — bez zakładania konta
            </p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
            <div className="w-9 h-9 bg-[#F0F4FA] rounded-full flex items-center justify-center mx-auto mb-2">
              <Users className="w-4 h-4 text-[#0D2240]" />
            </div>
            <p className="text-sm font-semibold text-[#0D2240] mb-0.5">2. Rekruterzy oceniają</p>
            <p className="text-xs text-gray-500 leading-relaxed">
              Twoje CV trafia do bazy zweryfikowanych pracodawców
            </p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
            <div className="w-9 h-9 bg-[#F0F4FA] rounded-full flex items-center justify-center mx-auto mb-2">
              <Mail className="w-4 h-4 text-[#0D2240]" />
            </div>
            <p className="text-sm font-semibold text-[#0D2240] mb-0.5">3. Kontakt</p>
            <p className="text-xs text-gray-500 leading-relaxed">
              Rekruter pisze bezpośrednio do Ciebie, jeśli pasujesz
            </p>
          </div>
        </div>

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
            ${
              dragOver
                ? "border-[#E1002A] bg-[#FFF0F3] scale-[1.01]"
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
            placeholder="twoj@email.com — żebyśmy mogli Ci odpowiedzieć"
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#E1002A] focus:border-transparent transition-all"
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
            ${
              !file || uploading
                ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                : "bg-[#0D2240] text-white hover:shadow-xl hover:scale-[1.01] active:scale-[0.99]"
            }
          `}
        >
          {uploading ? "Wysyłanie..." : "Wyślij CV"}
        </button>

        {/* Privacy strip */}
        <div className="mt-6 flex items-start gap-3 bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600">
          <ShieldCheck className="w-5 h-5 text-gray-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-gray-900 mb-0.5">Twoje CV jest bezpieczne</p>
            <p>
              Plik trafia tylko do zweryfikowanych rekruterów. Nie udostępniamy Twoich danych
              osobowych publicznie ani nie sprzedajemy ich firmom trzecim. Możesz w każdej chwili
              poprosić o usunięcie swojego CV z bazy.
            </p>
          </div>
        </div>

        <p className="text-center text-sm text-gray-500 mt-8">
          Masz już konto?{" "}
          <Link href="/login" className="text-[#E1002A] hover:underline font-semibold">
            Zaloguj się
          </Link>
        </p>
      </div>
    </div>
  );
}
