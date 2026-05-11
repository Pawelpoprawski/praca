"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";
import api from "@/services/api";
import { getRecaptchaToken } from "@/lib/recaptcha";
import {
  AuthShell, Field, Input, PasswordInput, SubmitBtn, ErrorAlert, SuccessCard,
} from "@/components/auth/AuthUI";

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

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== password2) { setError("Hasła nie są identyczne"); return; }
    if (password.length < 8) { setError("Hasło musi mieć min. 8 znaków"); return; }
    setLoading(true);
    try {
      await api.post("/auth/reset-password", { token, new_password: password });
      setSuccess("Hasło zostało zmienione. Możesz się zalogować.");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Nieprawidłowy lub wygasły link");
    } finally {
      setLoading(false);
    }
  };

  if (success) return <SuccessCard title="Gotowe" message={success} />;

  if (token) {
    return (
      <AuthShell title="Nowe hasło" subtitle="Wpisz nowe hasło dla swojego konta">
        {error && <ErrorAlert>{error}</ErrorAlert>}
        <form onSubmit={handleReset} className="space-y-4">
          <Field label="Nowe hasło">
            <PasswordInput value={password} show={showPassword} onToggle={() => setShowPassword(!showPassword)}
              onChange={setPassword} placeholder="Min. 8 znaków" />
          </Field>
          <Field label="Powtórz hasło">
            <PasswordInput value={password2} show={showPassword2} onToggle={() => setShowPassword2(!showPassword2)}
              onChange={setPassword2} />
          </Field>
          <SubmitBtn loading={loading} loadingLabel="Zmieniam…">Zmień hasło</SubmitBtn>
        </form>
      </AuthShell>
    );
  }

  return (
    <AuthShell title="Resetuj hasło" subtitle="Wyślemy Ci link do zmiany hasła na email">
      {error && <ErrorAlert>{error}</ErrorAlert>}
      <form onSubmit={handleForgot} className="space-y-4">
        <Field label="Email">
          <Input type="email" required value={email}
            onChange={(e) => setEmail(e.target.value)} placeholder="jan@example.com" />
        </Field>
        <SubmitBtn loading={loading} loadingLabel="Wysyłanie…">Wyślij link resetujący</SubmitBtn>
      </form>
      <div className="mt-6 text-center text-sm">
        <Link href="/login" className="text-[#E1002A] hover:underline font-medium">Wróć do logowania</Link>
      </div>
    </AuthShell>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-[#555]">Ładowanie…</div>}>
      <ResetPasswordForm />
    </Suspense>
  );
}
