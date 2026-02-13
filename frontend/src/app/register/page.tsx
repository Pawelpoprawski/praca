"use client";

import Link from "next/link";
import { Briefcase, User } from "lucide-react";

export default function RegisterPage() {
  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-lg">
        <h1 className="text-2xl font-bold text-gray-900 text-center mb-2">
          Utwórz konto
        </h1>
        <p className="text-gray-500 text-center mb-8">
          Wybierz typ konta, który Cię interesuje
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Link
            href="/register/worker"
            className="bg-white border-2 border-gray-200 rounded-xl p-6 hover:border-red-500 hover:shadow-md transition-all text-center group"
          >
            <User className="w-12 h-12 mx-auto mb-4 text-gray-400 group-hover:text-red-600" />
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Szukam pracy
            </h2>
            <p className="text-sm text-gray-500">
              Przeglądaj oferty, aplikuj, zarządzaj swoim CV
            </p>
          </Link>

          <Link
            href="/register/employer"
            className="bg-white border-2 border-gray-200 rounded-xl p-6 hover:border-red-500 hover:shadow-md transition-all text-center group"
          >
            <Briefcase className="w-12 h-12 mx-auto mb-4 text-gray-400 group-hover:text-red-600" />
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Szukam pracowników
            </h2>
            <p className="text-sm text-gray-500">
              Dodawaj ogłoszenia, przeglądaj kandydatów
            </p>
          </Link>
        </div>

        <p className="text-center text-sm text-gray-500 mt-6">
          Masz już konto?{" "}
          <Link href="/login" className="text-red-600 hover:underline font-medium">
            Zaloguj się
          </Link>
        </p>
      </div>
    </div>
  );
}
