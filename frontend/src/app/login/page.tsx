"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";
import { useAuthStore } from "@/store/authStore";
import { getRecaptchaToken } from "@/lib/recaptcha";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const login = useAuthStore((s) => s.login);
  const user = useAuthStore((s) => s.user);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
        // Redirect based on role
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
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <h1 className="text-2xl font-bold text-gray-900 text-center mb-6">
            Zaloguj się
          </h1>

          {error && (
            <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                placeholder="jan@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Hasło
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                placeholder="Min. 8 znaków"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-red-600 text-white py-3 rounded-lg hover:bg-red-700 font-semibold disabled:opacity-50 transition-colors"
            >
              {loading ? "Logowanie..." : "Zaloguj się"}
            </button>
          </form>

          <div className="mt-4 text-center">
            <Link href="/reset-password" className="text-sm text-gray-500 hover:text-red-600 hover:underline">
              Zapomniałeś hasła?
            </Link>
          </div>

          <div className="mt-4 text-center text-sm text-gray-500">
            Nie masz konta?{" "}
            <Link href="/register" className="text-red-600 hover:underline font-medium">
              Zarejestruj się
            </Link>
          </div>
        </div>

        {/* Demo accounts */}
        <div className="mt-4 bg-gray-50 border rounded-lg p-4">
          <p className="text-xs font-medium text-gray-500 mb-2">Konta demo (hasło: demo123):</p>
          <div className="grid grid-cols-1 gap-1 text-xs text-gray-600">
            <button type="button" onClick={() => { setEmail("jan.kowalski@gmail.com"); setPassword("demo123"); }}
              className="text-left hover:text-red-600">Pracownik: jan.kowalski@gmail.com</button>
            <button type="button" onClick={() => { setEmail("hr@swissbau.ch"); setPassword("demo123"); }}
              className="text-left hover:text-red-600">Pracodawca: hr@swissbau.ch</button>
            <button type="button" onClick={() => { setEmail("admin@polacyszwajcaria.ch"); setPassword("admin-zmien-po-pierwszym-logowaniu"); }}
              className="text-left hover:text-red-600">Admin: admin@polacyszwajcaria.ch</button>
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
