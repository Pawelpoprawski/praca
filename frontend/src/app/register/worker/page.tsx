"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuthStore } from "@/store/authStore";

export default function RegisterWorkerPage() {
  const router = useRouter();
  const register = useAuthStore((s) => s.register);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    password2: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

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
      await register({
        email: form.email,
        password: form.password,
        role: "worker",
        first_name: form.first_name,
        last_name: form.last_name,
      });
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
          <h2 className="text-xl font-bold text-gray-900 mb-3">Konto utworzone!</h2>
          <p className="text-gray-600 mb-6">
            Sprawdź swoją skrzynkę email, aby zweryfikować konto.
          </p>
          <Link
            href="/login"
            className="inline-block bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 font-medium"
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
            Rejestracja - Pracownik
          </h1>

          {error && (
            <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Imię</label>
                <input
                  type="text" required value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nazwisko</label>
                <input
                  type="text" required value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email" required value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Hasło</label>
              <input
                type="password" required value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
                placeholder="Min. 8 znaków"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Powtórz hasło</label>
              <input
                type="password" required value={form.password2}
                onChange={(e) => setForm({ ...form, password2: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
              />
            </div>

            <button
              type="submit" disabled={loading}
              className="w-full bg-red-600 text-white py-3 rounded-lg hover:bg-red-700 font-semibold disabled:opacity-50"
            >
              {loading ? "Rejestracja..." : "Zarejestruj się"}
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
