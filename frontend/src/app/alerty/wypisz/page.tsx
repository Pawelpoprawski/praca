"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Bell, CheckCircle2, ArrowLeft, Loader2 } from "lucide-react";
import api from "@/services/api";

export const dynamic = "force-dynamic";

function UnsubscribeInner() {
  const params = useSearchParams();
  const token = params.get("token") || "";
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("Brak tokenu w linku.");
      return;
    }
    api
      .get<{ message: string }>(`/public-alerts/unsubscribe?token=${encodeURIComponent(token)}`)
      .then((r) => {
        setStatus("ok");
        setMessage(r.data?.message || "Powiadomienia zostały wyłączone.");
      })
      .catch((e: unknown) => {
        const d = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        setStatus("error");
        setMessage(typeof d === "string" ? d : "Coś poszło nie tak. Spróbuj ponownie później.");
      });
  }, [token]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full bg-white border border-[#E0E3E8] rounded-lg shadow-sm p-8 text-center">
        <div className="w-16 h-16 mx-auto mb-5 rounded-full flex items-center justify-center bg-[#FFF0F3]">
          {status === "loading" ? (
            <Loader2 className="w-7 h-7 text-[#E1002A] animate-spin" />
          ) : status === "ok" ? (
            <CheckCircle2 className="w-8 h-8 text-green-600" />
          ) : (
            <Bell className="w-7 h-7 text-[#E1002A]" />
          )}
        </div>

        <h1 className="font-display text-2xl font-bold text-[#0D2240] mb-2">
          {status === "loading"
            ? "Wyłączamy powiadomienia..."
            : status === "ok"
              ? "Powiadomienia wyłączone"
              : "Nie udało się wypisać"}
        </h1>

        <p className="text-gray-600 mb-7 text-sm leading-relaxed">
          {message ||
            (status === "loading"
              ? "Chwilę potrwa..."
              : "Spróbuj ponownie lub napisz do nas na kontakt@polacyszwajcaria.com.")}
        </p>

        <Link
          href="/oferty"
          className="inline-flex items-center gap-2 bg-[#0D2240] text-white px-6 py-3 rounded font-semibold text-sm hover:bg-[#1B3157] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Wróć do ofert pracy
        </Link>
      </div>
    </div>
  );
}

export default function UnsubscribePage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Ładowanie...</div>}>
      <UnsubscribeInner />
    </Suspense>
  );
}
