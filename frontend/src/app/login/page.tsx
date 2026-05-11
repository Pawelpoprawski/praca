"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";
import { Eye, EyeOff, Shield, Briefcase, ArrowRight } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { getRecaptchaToken } from "@/lib/recaptcha";
import { SocialButtons, SocialDivider } from "@/components/auth/SocialButtons";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const login = useAuthStore((s) => s.login);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const recaptchaToken = await getRecaptchaToken("login");
      await login(email, password, recaptchaToken);
      const redirect = searchParams.get("redirect");
      if (redirect) {
        router.push(redirect);
      } else {
        const role = useAuthStore.getState().user?.role;
        if (role === "admin") router.push("/panel/admin");
        else if (role === "employer") router.push("/panel/pracodawca");
        else router.push("/panel/pracownik");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Wystąpił błąd logowania");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] bg-[#F5F6F8] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-5xl grid md:grid-cols-2 rounded-lg overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.08)]">
        {/* Left — branding navy */}
        <div className="hidden md:flex flex-col justify-center bg-[#0D2240] p-10 text-white relative overflow-hidden">
          <div className="absolute inset-0 hays-pattern" />
          <div className="absolute -right-[100px] -top-[100px] w-[400px] h-[400px] hays-red-glow" />
          <div className="relative z-10">
            <span className="hays-red-line" />
            <h2 className="font-display text-[1.8rem] font-extrabold mb-4 leading-tight">
              Witaj z powrotem
            </h2>
            <p className="text-white/85 text-[1rem] leading-[1.7] mb-8 max-w-[360px] font-light">
              Zaloguj się, aby przeglądać oferty, aplikować na stanowiska i zarządzać swoim profilem.
            </p>
            <ul className="space-y-3">
              <li className="flex items-center gap-3 text-white/80">
                <div className="w-9 h-9 bg-[#E1002A] rounded flex items-center justify-center flex-shrink-0">
                  <Briefcase className="w-4 h-4" />
                </div>
                <span className="text-[0.9rem]">Tysiące ofert pracy w Szwajcarii</span>
              </li>
              <li className="flex items-center gap-3 text-white/80">
                <div className="w-9 h-9 bg-[#E1002A] rounded flex items-center justify-center flex-shrink-0">
                  <Shield className="w-4 h-4" />
                </div>
                <span className="text-[0.9rem]">Bezpieczne i bezpłatne konto</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Right — form */}
        <div className="bg-white p-8 md:p-10 flex flex-col justify-center">
          <h1 className="font-display text-[2rem] font-extrabold text-[#0D2240] mb-1 leading-tight">
            Zaloguj się
          </h1>
          <p className="text-[#888] mb-8">Wprowadź swoje dane logowania</p>

          <SocialButtons mode="login" />
          <SocialDivider />

          {error && (
            <div className="bg-[#FFF0F3] border border-[#E1002A]/30 text-[#E1002A] px-4 py-3 rounded mb-6 text-sm" role="alert" aria-live="assertive">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <Field label="Email">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                className="w-full px-4 py-3 border border-[#E0E3E8] rounded focus:outline-none focus:border-[#E1002A] focus:ring-2 focus:ring-[#E1002A]/20 transition-all"
                placeholder="jan@example.com"
              />
            </Field>

            <Field label="Hasło">
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  className="w-full px-4 py-3 pr-11 border border-[#E0E3E8] rounded focus:outline-none focus:border-[#E1002A] focus:ring-2 focus:ring-[#E1002A]/20 transition-all"
                  placeholder="Min. 8 znaków"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#888] hover:text-[#0D2240] transition-colors"
                  aria-label={showPassword ? "Ukryj hasło" : "Pokaż hasło"}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </Field>

            <div className="flex items-center justify-end">
              <Link href="/reset-password" className="text-sm text-[#888] hover:text-[#E1002A] font-medium transition-colors">
                Zapomniałeś hasła?
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#E1002A] hover:bg-[#B8001F] text-white py-3.5 rounded font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Logowanie...
                </>
              ) : (
                <>
                  Zaloguj się
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 text-center text-sm text-[#555]">
            Nie masz konta?{" "}
            <Link href="/register" className="text-[#E1002A] hover:underline font-semibold transition-colors">
              Zarejestruj się
            </Link>
          </div>

          {/* Demo accounts */}
          <div className="mt-8 pt-6 border-t border-[#E0E3E8]">
            <p className="text-[0.72rem] font-semibold text-[#888] uppercase tracking-[0.1em] mb-3">
              Konta demo <span className="font-normal normal-case tracking-normal text-[#555]">(hasło: demo123)</span>
            </p>
            <div className="flex flex-wrap gap-2 text-xs">
              <DemoBtn onClick={() => { setEmail("jan.kowalski@gmail.com"); setPassword("demo123"); }}>Pracownik</DemoBtn>
              <DemoBtn onClick={() => { setEmail("hr@swissbau.ch"); setPassword("demo123"); }}>Pracodawca</DemoBtn>
              <DemoBtn onClick={() => { setEmail("admin@praca-w-szwajcarii.ch"); setPassword("admin-zmien-po-pierwszym-logowaniu"); }}>Admin</DemoBtn>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-[#0D2240] mb-2">{label}</span>
      {children}
    </label>
  );
}

function DemoBtn({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="bg-[#F5F6F8] hover:bg-[#FFF0F3] hover:text-[#E1002A] hover:border-[#E1002A] px-3 py-1.5 rounded transition-all border border-[#E0E3E8] text-[#555]"
    >
      {children}
    </button>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-[#555]">Ładowanie…</div>}>
      <LoginForm />
    </Suspense>
  );
}
