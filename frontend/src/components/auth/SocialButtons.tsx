"use client";

import { useState } from "react";

// Endpointy backendowe trafiaja przez rewrites (/api/* -> backend)
const OAUTH_BASE = "/api/v1/auth";

function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
  );
}

function FacebookIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#1877F2" d="M24 12c0-6.627-5.373-12-12-12S0 5.373 0 12c0 5.99 4.388 10.954 10.125 11.854V15.469H7.078V12h3.047V9.356c0-3.007 1.792-4.668 4.533-4.668 1.312 0 2.686.234 2.686.234v2.953H15.83c-1.491 0-1.956.925-1.956 1.875V12h3.328l-.532 3.469h-2.796v8.385C19.612 22.954 24 17.99 24 12z"/>
      <path fill="#fff" d="M16.671 15.469L17.203 12h-3.328V9.75c0-.949.465-1.875 1.956-1.875h1.513V4.922s-1.374-.234-2.686-.234c-2.741 0-4.533 1.661-4.533 4.668V12H7.078v3.469h3.047v8.385a12.13 12.13 0 003.75 0v-8.385h2.796z"/>
    </svg>
  );
}

type Mode = "login" | "register";

export function SocialButtons({ mode = "login" }: { mode?: Mode }) {
  const [pending, setPending] = useState<"google" | "facebook" | null>(null);

  const handleClick = (provider: "google" | "facebook") => {
    setPending(provider);
    // Backend zrobi 302 redirect do ekranu logowania providera.
    // Z dummy credentials provider pokaze blad "invalid client" — flow jest widoczny.
    window.location.href = `${OAUTH_BASE}/${provider}/login`;
  };

  const verb = mode === "register" ? "Zarejestruj" : "Zaloguj";

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={() => handleClick("google")}
        disabled={pending !== null}
        className="w-full flex items-center justify-center gap-3 py-3 rounded border border-[#E0E3E8] bg-white hover:bg-[#F5F6F8] hover:border-[#0D2240]/30 transition-all text-[#0D2240] font-medium disabled:opacity-60"
      >
        <GoogleIcon className="w-5 h-5" />
        <span>{verb} się przez Google</span>
      </button>
      <button
        type="button"
        onClick={() => handleClick("facebook")}
        disabled={pending !== null}
        className="w-full flex items-center justify-center gap-3 py-3 rounded border border-[#E0E3E8] bg-white hover:bg-[#F5F6F8] hover:border-[#0D2240]/30 transition-all text-[#0D2240] font-medium disabled:opacity-60"
      >
        <FacebookIcon className="w-5 h-5" />
        <span>{verb} się przez Facebook</span>
      </button>
    </div>
  );
}

export function SocialDivider({ label = "lub kontynuuj z emailem" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 my-5">
      <div className="flex-1 h-px bg-[#E0E3E8]" />
      <span className="text-[0.72rem] text-[#888] uppercase tracking-[0.1em]">{label}</span>
      <div className="flex-1 h-px bg-[#E0E3E8]" />
    </div>
  );
}
