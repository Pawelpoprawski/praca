"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
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
    api
      .get(`/auth/verify-email/${token}`)
      .then((res) => {
        setStatus("success");
        setMessage(res.data.message || "Email został zweryfikowany.");
      })
      .catch((err) => {
        setStatus("error");
        setMessage(
          err.response?.data?.detail || "Nieprawidłowy lub wygasły link weryfikacyjny."
        );
      });
  }, [token]);

  if (status === "loading") {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <div className="bg-white rounded-xl shadow-sm border p-8 max-w-md text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-red-600 mx-auto mb-4" />
          <p className="text-gray-600">Weryfikacja adresu email...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="bg-white rounded-xl shadow-sm border p-8 max-w-md text-center">
        <h2 className="text-xl font-bold text-gray-900 mb-3">
          {status === "success" ? "Gotowe!" : "Błąd weryfikacji"}
        </h2>
        <p className="text-gray-600 mb-6">{message}</p>
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
