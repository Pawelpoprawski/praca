"use client";

import Link from "next/link";
import { Eye, EyeOff, CheckCircle2 } from "lucide-react";

export function AuthShell({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="min-h-[80vh] bg-[#F5F6F8] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-lg border border-[#E0E3E8] shadow-[0_8px_32px_rgba(0,0,0,0.08)] p-8 sm:p-10">
          <span className="hays-red-line" />
          <h1 className="font-display text-[1.6rem] font-extrabold text-[#0D2240] mb-1 leading-tight">{title}</h1>
          {subtitle ? <p className="text-[#888] text-sm mb-7">{subtitle}</p> : <div className="mb-6" />}
          {children}
        </div>
      </div>
    </div>
  );
}

export function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-[#0D2240] mb-2">{label}</span>
      {children}
      {error && <p className="text-xs text-[#E1002A] mt-1">{error}</p>}
    </label>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement> & { hasError?: boolean }) {
  const { hasError, className, ...rest } = props;
  return (
    <input
      {...rest}
      className={`w-full px-4 py-3 border rounded focus:outline-none focus:ring-2 focus:ring-[#E1002A]/20 transition-all ${
        hasError ? "border-[#E1002A] focus:border-[#E1002A]" : "border-[#E0E3E8] focus:border-[#E1002A]"
      } ${className || ""}`}
    />
  );
}

export function PasswordInput({ value, show, onToggle, onChange, error, placeholder }: {
  value: string; show: boolean; onToggle: () => void; onChange: (v: string) => void; error?: boolean; placeholder?: string;
}) {
  return (
    <div className="relative">
      <Input type={show ? "text" : "password"} required value={value} autoComplete="new-password" placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)} hasError={error} className="pr-11" />
      <button type="button" onClick={onToggle}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-[#888] hover:text-[#0D2240] transition-colors"
        aria-label={show ? "Ukryj hasło" : "Pokaż hasło"}>
        {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
      </button>
    </div>
  );
}

export function SubmitBtn({ loading, loadingLabel, children }: { loading: boolean; loadingLabel: string; children: React.ReactNode }) {
  return (
    <button type="submit" disabled={loading}
      className="w-full bg-[#E1002A] hover:bg-[#B8001F] text-white py-3.5 rounded font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all">
      {loading ? (
        <span className="inline-flex items-center gap-2">
          <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          {loadingLabel}
        </span>
      ) : children}
    </button>
  );
}

export function ErrorAlert({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-[#FFF0F3] border border-[#E1002A]/30 text-[#E1002A] px-4 py-3 rounded mb-5 text-sm" role="alert" aria-live="assertive">
      {children}
    </div>
  );
}

export function SuccessCard({ title, message }: { title: string; message: string }) {
  return (
    <div className="min-h-[80vh] bg-[#F5F6F8] flex items-center justify-center px-4">
      <div className="bg-white rounded-lg border border-[#E0E3E8] shadow-[0_8px_32px_rgba(0,0,0,0.08)] p-8 max-w-md text-center">
        <div className="w-14 h-14 mx-auto bg-[#FFF0F3] rounded-full flex items-center justify-center mb-4">
          <CheckCircle2 className="w-7 h-7 text-[#E1002A]" />
        </div>
        <h2 className="font-display text-[1.4rem] font-bold text-[#0D2240] mb-3">{title}</h2>
        <p className="text-[#555] mb-6">{message}</p>
        <Link href="/login"
          className="inline-block bg-[#E1002A] hover:bg-[#B8001F] text-white px-6 py-2.5 rounded font-medium transition-colors no-underline">
          Przejdź do logowania
        </Link>
      </div>
    </div>
  );
}
