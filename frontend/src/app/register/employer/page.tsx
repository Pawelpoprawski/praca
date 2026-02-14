"use client";

import Link from "next/link";
import { useState } from "react";
import { useAuthStore } from "@/store/authStore";
import { getRecaptchaToken } from "@/lib/recaptcha";

export default function RegisterEmployerPage() {
  const register = useAuthStore((s) => s.register);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    password2: "",
    company_name: "",
  });
  const [fieldErrors, setFieldErrors] = useState({ password: "", password2: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const validatePassword = (value: string) => {
    if (value.length > 0 && value.length < 8) {
      setFieldErrors((prev) => ({ ...prev, password: "Hasło musi mieć min. 8 znaków" }));
    } else {
      setFieldErrors((prev) => ({ ...prev, password: "" }));
    }
  };

  const validatePassword2 = (value: string, password: string) => {
    if (value.length > 0 && value !== password) {
      setFieldErrors((prev) => ({ ...prev, password2: "Hasła nie są identyczne" }));
    } else {
      setFieldErrors((prev) => ({ ...prev, password2: "" }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (form.password !== form.password2) {
      setError("Hasła nie są identyczne");
      return;
    }
    if (form.password.length < 8) {
      setError("Hasło musi mieć min. 8 znaków");
      return;
    }

    setLoading(true);
    try {
      const recaptchaToken = await getRecaptchaToken("register");
      await register({
        email: form.email,
        password: form.password,
        role: "employer",
        first_name: form.first_name,
        last_name: form.last_name,
        company_name: form.company_name,
      }, recaptchaToken);
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Wystąpił błąd rejestracji");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <div className="bg-white rounded-xl shadow-sm border p-8 max-w-md text-center">
          <h2 className="text-xl font-bold text-gray-900 mb-3">Konto firmy utworzone!</h2>
          <p className="text-gray-600 mb-6">
            Sprawdź email, aby zweryfikować konto. Po weryfikacji będziesz mógł dodawać ogłoszenia.
          </p>
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

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-xl shadow-sm border p-8">
          <h1 className="text-2xl font-bold text-gray-900 text-center mb-6">
            Rejestracja - Pracodawca
          </h1>

          {error && (
            <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nazwa firmy</label>
              <input
                type="text" required value={form.company_name}
                onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                placeholder="np. SwissBau GmbH"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Imię</label>
                <input
                  type="text" required value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nazwisko</label>
                <input
                  type="text" required value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email firmowy</label>
              <input
                type="email" required value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Hasło</label>
              <input
                type="password" required value={form.password}
                onChange={(e) => {
                  setForm({ ...form, password: e.target.value });
                  validatePassword(e.target.value);
                  if (form.password2) validatePassword2(form.password2, e.target.value);
                }}
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 ${
                  fieldErrors.password ? "border-red-300" : "border-gray-300"
                }`}
                placeholder="Min. 8 znaków"
              />
              {fieldErrors.password && (
                <p className="text-xs text-red-600 mt-1">{fieldErrors.password}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Powtórz hasło</label>
              <input
                type="password" required value={form.password2}
                onChange={(e) => {
                  setForm({ ...form, password2: e.target.value });
                  validatePassword2(e.target.value, form.password);
                }}
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 ${
                  fieldErrors.password2 ? "border-red-300" : "border-gray-300"
                }`}
              />
              {fieldErrors.password2 && (
                <p className="text-xs text-red-600 mt-1">{fieldErrors.password2}</p>
              )}
            </div>

            <button
              type="submit" disabled={loading}
              className="w-full bg-red-600 text-white py-3 rounded-lg hover:bg-red-700 font-semibold disabled:opacity-50 transition-colors"
            >
              {loading ? "Rejestracja..." : "Zarejestruj firmę"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-4">
            Masz już konto? <Link href="/login" className="text-red-600 hover:underline">Zaloguj się</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
