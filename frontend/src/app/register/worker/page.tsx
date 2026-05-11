"use client";

import Link from "next/link";
import { useState } from "react";
import { useAuthStore } from "@/store/authStore";
import { getRecaptchaToken } from "@/lib/recaptcha";
import { AuthShell, Field, Input, PasswordInput, SubmitBtn, ErrorAlert, SuccessCard } from "@/components/auth/AuthUI";
import { SocialButtons, SocialDivider } from "@/components/auth/SocialButtons";

export default function RegisterWorkerPage() {
  const register = useAuthStore((s) => s.register);
  const [form, setForm] = useState({ first_name: "", last_name: "", email: "", password: "", password2: "" });
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
      await register({ email: form.email, password: form.password, role: "worker", first_name: form.first_name, last_name: form.last_name }, recaptchaToken);
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Wystąpił błąd rejestracji");
    } finally {
      setLoading(false);
    }
  };

  if (success) return <SuccessCard title="Konto utworzone" message="Sprawdź swoją skrzynkę email, aby zweryfikować konto." />;

  return (
    <AuthShell title="Rejestracja — pracownik" subtitle="Załóż konto i aplikuj na oferty">
      <SocialButtons mode="register" />
      <SocialDivider />
      {error && <ErrorAlert>{error}</ErrorAlert>}
      <form onSubmit={handleSubmit} className="space-y-4">
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
        <Field label="Email">
          <Input type="email" required value={form.email} autoComplete="email"
            onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="jan@example.com" />
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
        <SubmitBtn loading={loading} loadingLabel="Rejestracja…">Zarejestruj się</SubmitBtn>
      </form>
      <p className="text-center text-sm text-[#555] mt-6">
        Masz już konto?{" "}
        <Link href="/login" className="text-[#E1002A] hover:underline font-semibold">Zaloguj się</Link>
      </p>
    </AuthShell>
  );
}
