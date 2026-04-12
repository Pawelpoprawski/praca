"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";
import { Eye, EyeOff, Shield, Briefcase, ArrowRight } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { getRecaptchaToken } from "@/lib/recaptcha";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const login = useAuthStore((s) => s.login);
  const user = useAuthStore((s) => s.user);
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
        const store = useAuthStore.getState();
        const role = store.user?.role;
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
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-5xl grid md:grid-cols-2 gap-0 md:gap-0">
        {/* Left side - Branding */}
        <div className="hidden md:flex flex-col justify-center bg-gradient-to-br from-red-600 via-red-700 to-red-900 rounded-l-2xl p-10 text-white relative overflow-hidden noise-overlay">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS1vcGFjaXR5PSIwLjA1IiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-40"></div>
          {/* Swiss cross */}
          <div className="absolute bottom-8 right-8 opacity-10">
            <svg width="80" height="80" viewBox="0 0 32 32" fill="currentColor">
              <rect x="13" y="6" width="6" height="20" rx="1" />
              <rect x="6" y="13" width="20" height="6" rx="1" />
            </svg>
          </div>
          <div className="relative z-10">
            <h2 className="text-3xl font-bold mb-4 tracking-tight">Witaj z powrotem!</h2>
            <p className="text-red-100 text-lg leading-relaxed mb-8">
              Zaloguj się, aby przeglądać oferty, aplikować na stanowiska i zarządzać swoim profilem.
            </p>
            <div className="space-y-4">
              <div className="flex items-center gap-3 text-red-100/90">
                <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Briefcase className="w-4 h-4" />
                </div>
                <span className="text-sm">Tysiące ofert pracy w Szwajcarii</span>
              </div>
              <div className="flex items-center gap-3 text-red-100/90">
                <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Shield className="w-4 h-4" />
                </div>
                <span className="text-sm">Bezpieczne i bezpłatne konto</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right side - Form */}
        <div className="bg-white rounded-2xl md:rounded-l-none md:rounded-r-2xl shadow-xl border border-gray-200 md:border-l-0 p-8 md:p-10 flex flex-col justify-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-1 tracking-tight">
            Zaloguj się
          </h1>
          <p className="text-gray-500 mb-8">Wprowadź swoje dane logowania</p>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-6 text-sm animate-scale-in" role="alert" aria-live="assertive">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all bg-gray-50 focus:bg-white"
                placeholder="jan@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Haslo
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  className="w-full px-4 py-3 pr-11 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all bg-gray-50 focus:bg-white"
                  placeholder="Min. 8 znaków"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  aria-label={showPassword ? "Ukryj hasło" : "Pokaż hasło"}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-end">
              <Link href="/reset-password" className="text-sm text-gray-500 hover:text-red-600 font-medium transition-colors">
                Zapomniałeś hasła?
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-red-600 to-red-700 text-white py-3.5 rounded-xl hover:shadow-lg hover:shadow-red-500/20 font-bold disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95 flex items-center justify-center gap-2"
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

          <div className="mt-8 text-center text-sm text-gray-600">
            Nie masz konta?{" "}
            <Link href="/register" className="text-red-600 hover:text-red-700 hover:underline font-bold transition-colors">
              Zarejestruj się
            </Link>
          </div>
        </div>
      </div>

      {/* Demo accounts - below the card on mobile */}
      <div className="fixed bottom-4 left-4 right-4 md:static md:mt-6 md:max-w-5xl md:w-full">
        <div className="bg-white/90 backdrop-blur-sm border border-gray-200 rounded-xl p-4 shadow-lg md:shadow-sm">
          <p className="text-xs font-semibold text-gray-500 mb-2">Konta demo (haslo: demo123):</p>
          <div className="flex flex-wrap gap-2 text-xs">
            <button type="button" onClick={() => { setEmail("jan.kowalski@gmail.com"); setPassword("demo123"); }}
              className="bg-gray-50 hover:bg-red-50 hover:text-red-600 px-3 py-1.5 rounded-lg transition-all border border-gray-200 hover:border-red-200">
              Pracownik
            </button>
            <button type="button" onClick={() => { setEmail("hr@swissbau.ch"); setPassword("demo123"); }}
              className="bg-gray-50 hover:bg-red-50 hover:text-red-600 px-3 py-1.5 rounded-lg transition-all border border-gray-200 hover:border-red-200">
              Pracodawca
            </button>
            <button type="button" onClick={() => { setEmail("admin@polacyszwajcaria.ch"); setPassword("admin-zmien-po-pierwszym-logowaniu"); }}
              className="bg-gray-50 hover:bg-red-50 hover:text-red-600 px-3 py-1.5 rounded-lg transition-all border border-gray-200 hover:border-red-200">
              Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Ładowanie...</div>}>
      <LoginForm />
    </Suspense>
  );
}
