"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CheckCircle2, AlertCircle } from "lucide-react";
import api from "@/services/api";

export default function VerifyEmailPage({
  params,
}: {
  params: { token: string };
}) {
  const { token } = params;
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.get(`/auth/verify-email/${token}`)
      .then((res) => {
        setStatus("success");
        setMessage(res.data.message || "Email został zweryfikowany.");
      })
      .catch((err) => {
        setStatus("error");
        setMessage(err.response?.data?.detail || "Nieprawidłowy lub wygasły link weryfikacyjny.");
      });
  }, [token]);

  if (status === "loading") {
    return (
      <div className="min-h-[80vh] bg-[#F5F6F8] flex items-center justify-center px-4">
        <div className="bg-white rounded-lg border border-[#E0E3E8] shadow-[0_8px_32px_rgba(0,0,0,0.08)] p-8 max-w-md text-center">
          <div className="w-12 h-12 mx-auto mb-4 border-2 border-[#E0E3E8] border-t-[#E1002A] rounded-full animate-spin" />
          <p className="text-[#555]">Weryfikacja adresu email…</p>
        </div>
      </div>
    );
  }

  const isOk = status === "success";

  return (
    <div className="min-h-[80vh] bg-[#F5F6F8] flex items-center justify-center px-4">
      <div className="bg-white rounded-lg border border-[#E0E3E8] shadow-[0_8px_32px_rgba(0,0,0,0.08)] p-8 max-w-md text-center">
        <div className={`w-14 h-14 mx-auto rounded-full flex items-center justify-center mb-4 ${
          isOk ? "bg-[#FFF0F3]" : "bg-[#F5F6F8]"
        }`}>
          {isOk ? (
            <CheckCircle2 className="w-7 h-7 text-[#E1002A]" />
          ) : (
            <AlertCircle className="w-7 h-7 text-[#888]" />
          )}
        </div>
        <h2 className="font-display text-[1.4rem] font-bold text-[#0D2240] mb-3">
          {isOk ? "Email zweryfikowany" : "Błąd weryfikacji"}
        </h2>
        <p className="text-[#555] mb-6">{message}</p>
        <Link href="/login"
          className="inline-block bg-[#E1002A] hover:bg-[#B8001F] text-white px-6 py-2.5 rounded font-medium transition-colors no-underline">
          Przejdź do logowania
        </Link>
      </div>
    </div>
  );
}
