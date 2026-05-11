"use client";

import Link from "next/link";
import { useState } from "react";
import {
  Building2, FilePlus2, Users, ShieldCheck, MailCheck, Sparkles, Check,
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { getRecaptchaToken } from "@/lib/recaptcha";
import {
  Field, Input, PasswordInput, SubmitBtn, ErrorAlert, SuccessCard,
} from "@/components/auth/AuthUI";
import { SocialButtons, SocialDivider } from "@/components/auth/SocialButtons";

export default function RegisterEmployerPage() {
  const register = useAuthStore((s) => s.register);
  const [form, setForm] = useState({ first_name: "", last_name: "", email: "", password: "", password2: "", company_name: "" });
  const [fieldErrors, setFieldErrors] = useState({ password: "", password2: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [showPassword2, setShowPassword2] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const validatePassword = (value: string) => {
    setFieldErrors((p) => ({ ...p, password: value.length > 0 && value.length < 8 ? "Hasło musi mieć min. 8 znaków" : "" }));
  };
  const validatePassword2 = (value: string, password: string) => {
    setFieldErrors((p) => ({ ...p, password2: value.length > 0 && value !== password ? "Hasła nie są identyczne" : "" }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.password2) { setError("Hasła nie są identyczne"); return; }
    if (form.password.length < 8) { setError("Hasło musi mieć min. 8 znaków"); return; }
    setLoading(true);
    try {
      const recaptchaToken = await getRecaptchaToken("register");
      await register({
        email: form.email, password: form.password, role: "employer",
        first_name: form.first_name, last_name: form.last_name, company_name: form.company_name,
      }, recaptchaToken);
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Wystąpił błąd rejestracji");
    } finally {
      setLoading(false);
    }
  };

  if (success) return <SuccessCard title="Konto firmy utworzone" message="Sprawdź email, aby zweryfikować konto. Po weryfikacji będziesz mógł dodawać ogłoszenia." />;

  const features = [
    { icon: FilePlus2, title: "Publikacja ogłoszeń za darmo", desc: "Dodawaj nieograniczoną liczbę ofert pracy. Brak prowizji od zatrudnienia." },
    { icon: Sparkles, title: "Asystent AI", desc: "Wklej ogłoszenie w dowolnym języku — system przetłumaczy i uzupełni dane automatycznie." },
    { icon: Users, title: "Dostęp do bazy kandydatów", desc: "Przeglądaj profile zarejestrowanych pracowników i ich CV." },
    { icon: MailCheck, title: "Aplikacje na maila", desc: "Otrzymuj zgłoszenia bezpośrednio na firmowy adres z plikiem CV w załączniku." },
    { icon: ShieldCheck, title: "Weryfikacja firm", desc: "Po weryfikacji NIP / numeru handlowego twoja firma zyskuje znaczek zaufania." },
    { icon: Building2, title: "Profil firmy", desc: "Własna strona z logo, opisem działalności i listą aktywnych ofert." },
  ];

  return (
    <div className="min-h-[80vh] bg-[#F5F6F8] py-12 px-4">
      <div className="max-w-[1100px] mx-auto grid lg:grid-cols-[1.1fr_1fr] gap-8 items-start">
        {/* LEFT: opis */}
        <div className="bg-gradient-to-br from-[#0D2240] to-[#1A3A5C] rounded-lg p-8 sm:p-10 text-white">
          <span className="inline-block text-[0.72rem] font-semibold uppercase tracking-[0.1em] px-3 py-1 rounded mb-5 bg-[#E1002A]/15 text-[#FFC2CD]">
            Dla pracodawców
          </span>
          <h1 className="font-display text-[1.8rem] sm:text-[2.1rem] font-extrabold leading-tight mb-4">
            Znajdź sprawdzonych polskich pracowników do swojej firmy w Szwajcarii
          </h1>
          <p className="text-white/70 leading-[1.7] mb-8">
            Załóż bezpłatne konto i opublikuj ogłoszenie w kilka minut. Docieraj do tysięcy
            polskojęzycznych specjalistów gotowych do pracy w Szwajcarii — od budownictwa
            i gastronomii po IT i opiekę.
          </p>

          <ul className="space-y-4 mb-8">
            {features.map(({ icon: Icon, title, desc }) => (
              <li key={title} className="flex gap-3">
                <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center">
                  <Icon className="w-[18px] h-[18px] text-[#FFC2CD]" />
                </div>
                <div className="min-w-0">
                  <div className="font-semibold text-[0.95rem] mb-0.5">{title}</div>
                  <div className="text-[0.85rem] text-white/60 leading-[1.55]">{desc}</div>
                </div>
              </li>
            ))}
          </ul>

          <div className="border-t border-white/10 pt-6">
            <div className="text-[0.72rem] uppercase tracking-[0.1em] font-semibold text-white/50 mb-3">Jak to działa</div>
            <ol className="space-y-2 text-[0.88rem] text-white/75">
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[#E1002A] text-white text-[0.7rem] font-bold flex items-center justify-center">1</span>
                <span>Załóż konto i potwierdź adres email firmy</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[#E1002A] text-white text-[0.7rem] font-bold flex items-center justify-center">2</span>
                <span>Dodaj ogłoszenie ręcznie lub wklej tekst w dowolnym języku</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[#E1002A] text-white text-[0.7rem] font-bold flex items-center justify-center">3</span>
                <span>Odbieraj aplikacje kandydatów wprost na swój email</span>
              </li>
            </ol>
          </div>
        </div>

        {/* RIGHT: formularz */}
        <div className="bg-white rounded-lg border border-[#E0E3E8] shadow-[0_8px_32px_rgba(0,0,0,0.08)] p-8 sm:p-10">
          <span className="hays-red-line" />
          <h2 className="font-display text-[1.6rem] font-extrabold text-[#0D2240] mb-1 leading-tight">
            Załóż konto firmy
          </h2>
          <p className="text-[#888] text-sm mb-7">Bezpłatnie. Bez zobowiązań.</p>

          <div className="grid grid-cols-3 gap-2 mb-7 text-[0.7rem] text-[#0D2240]">
            <div className="flex items-center gap-1.5">
              <Check className="w-3.5 h-3.5 text-[#E1002A]" /> Bez prowizji
            </div>
            <div className="flex items-center gap-1.5">
              <Check className="w-3.5 h-3.5 text-[#E1002A]" /> Bez limitów
            </div>
            <div className="flex items-center gap-1.5">
              <Check className="w-3.5 h-3.5 text-[#E1002A]" /> Asystent AI
            </div>
          </div>

          <SocialButtons mode="register" />
          <SocialDivider />

          {error && <ErrorAlert>{error}</ErrorAlert>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <Field label="Nazwa firmy">
              <Input type="text" required value={form.company_name} autoComplete="organization"
                onChange={(e) => setForm({ ...form, company_name: e.target.value })} placeholder="np. SwissBau GmbH" />
            </Field>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Imię">
                <Input type="text" required value={form.first_name} autoComplete="given-name"
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
              </Field>
              <Field label="Nazwisko">
                <Input type="text" required value={form.last_name} autoComplete="family-name"
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
              </Field>
            </div>
            <Field label="Email firmowy">
              <Input type="email" required value={form.email} autoComplete="email"
                onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </Field>
            <Field label="Hasło" error={fieldErrors.password}>
              <PasswordInput value={form.password} show={showPassword} onToggle={() => setShowPassword(!showPassword)}
                onChange={(v) => { setForm({ ...form, password: v }); validatePassword(v); if (form.password2) validatePassword2(form.password2, v); }}
                error={!!fieldErrors.password} placeholder="Min. 8 znaków" />
            </Field>
            <Field label="Powtórz hasło" error={fieldErrors.password2}>
              <PasswordInput value={form.password2} show={showPassword2} onToggle={() => setShowPassword2(!showPassword2)}
                onChange={(v) => { setForm({ ...form, password2: v }); validatePassword2(v, form.password); }}
                error={!!fieldErrors.password2} />
            </Field>
            <SubmitBtn loading={loading} loadingLabel="Rejestracja…">Zarejestruj firmę</SubmitBtn>
          </form>
          <p className="text-center text-sm text-[#555] mt-6">
            Masz już konto?{" "}
            <Link href="/login" className="text-[#E1002A] hover:underline font-semibold">Zaloguj się</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
