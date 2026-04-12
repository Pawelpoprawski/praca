"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";
import { Eye, EyeOff } from "lucide-react";
import api from "@/services/api";
import { getRecaptchaToken } from "@/lib/recaptcha";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showPassword2, setShowPassword2] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Step 1: request reset link
  const handleForgot = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const recaptchaToken = await getRecaptchaToken("forgot_password");
      const headers: Record<string, string> = {};
      if (recaptchaToken) headers["X-Recaptcha-Token"] = recaptchaToken;

      await api.post("/auth/forgot-password", { email }, { headers });
      setSuccess("Jeśli konto istnieje, wysłaliśmy link do resetowania hasła na podany adres email.");
    } catch {
      setError("Wystąpił błąd. Spróbuj ponownie.");
    } finally {
      setLoading(false);
    }
  };

  // Step 2: set new password
  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== password2) {
      setError("Hasła nie są identyczne");
      return;
    }
    if (password.length < 8) {
      setError("Hasło musi mieć min. 8 znaków");
      return;
    }

    setLoading(true);
    try {
      await api.post("/auth/reset-password", {
        token,
        new_password: password,
      });
      setSuccess("Hasło zostało zmienione. Możesz się zalogować.");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Nieprawidłowy lub wygasły link");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <div className="bg-white rounded-xl shadow-sm border p-8 max-w-md text-center">
          <h2 className="text-xl font-bold text-gray-900 mb-3">Gotowe!</h2>
          <p className="text-gray-600 mb-6">{success}</p>
          <Link
            href="/login"
            className="inline-block bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 font-medium transition-colors"
          >
            Przejdź do logowania
          </Link>
        </div>
      </div>
    );
  }

  // If token is present, show new password form
  if (token) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-xl shadow-sm border p-8">
            <h1 className="text-2xl font-bold text-gray-900 text-center mb-6">
              Nowe hasło
            </h1>

            {error && (
              <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">{error}</div>
            )}

            <form onSubmit={handleReset} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nowe hasło</label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="new-password"
                    className="w-full px-4 py-2 pr-11 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder="Min. 8 znaków"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                    aria-label={showPassword ? "Ukryj hasło" : "Pokaż hasło"}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Powtórz hasło</label>
                <div className="relative">
                  <input
                    type={showPassword2 ? "text" : "password"}
                    required
                    value={password2}
                    onChange={(e) => setPassword2(e.target.value)}
                    autoComplete="new-password"
                    className="w-full px-4 py-2 pr-11 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword2(!showPassword2)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                    aria-label={showPassword2 ? "Ukryj hasło" : "Pokaż hasło"}
                  >
                    {showPassword2 ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-red-600 text-white py-3 rounded-lg hover:bg-red-700 font-semibold disabled:opacity-50 transition-colors"
              >
                {loading ? "Zmieniam..." : "Zmień hasło"}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // No token: show forgot password form
  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-xl shadow-sm border p-8">
          <h1 className="text-2xl font-bold text-gray-900 text-center mb-6">
            Resetuj hasło
          </h1>

          {error && (
            <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">{error}</div>
          )}

          <p className="text-gray-600 text-sm mb-4">
            Podaj adres email powiązany z Twoim kontem. Wyślemy Ci link do zmiany hasła.
          </p>

          <form onSubmit={handleForgot} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                placeholder="jan@example.com"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-red-600 text-white py-3 rounded-lg hover:bg-red-700 font-semibold disabled:opacity-50 transition-colors"
            >
              {loading ? "Wysyłanie..." : "Wyślij link resetujący"}
            </button>
          </form>

          <div className="mt-4 text-center text-sm text-gray-500">
            <Link href="/login" className="text-red-600 hover:underline">Wróć do logowania</Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Ładowanie...</div>}>
      <ResetPasswordForm />
    </Suspense>
  );
}
