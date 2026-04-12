"use client";

import Link from "next/link";
import { Briefcase, User, ArrowRight, CheckCircle2 } from "lucide-react";

export default function RegisterPage() {
  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-12 animate-fade-in-up">
          <h1 className="text-4xl font-bold text-gray-900 mb-3 tracking-tight">
            Utwórz konto
          </h1>
          <p className="text-lg text-gray-500">
            Wybierz typ konta, który Cię interesuje
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <Link
            href="/register/worker"
            className="bg-white border-2 border-gray-100 rounded-2xl p-8 hover:border-red-400 hover:shadow-2xl hover:shadow-red-500/10 hover:-translate-y-1 transition-all text-center group animate-fade-in-up delay-100"
          >
            <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-red-50 to-red-100 rounded-2xl flex items-center justify-center group-hover:from-red-100 group-hover:to-red-200 group-hover:scale-110 transition-all">
              <User className="w-8 h-8 text-red-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-3 group-hover:text-red-600 transition-colors tracking-tight">
              Szukam pracy
            </h2>
            <p className="text-sm text-gray-500 leading-relaxed mb-5">
              Przeglądaj oferty, aplikuj, zarządzaj swoim CV
            </p>
            <ul className="text-xs text-gray-500 space-y-2 text-left">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                Szybka aplikacja jednym kliknięciem
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                Darmowa analiza CV z AI
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                Alerty o nowych ofertach
              </li>
            </ul>
            <div className="mt-6 inline-flex items-center gap-1 text-red-600 font-semibold text-sm group-hover:gap-2 transition-all">
              Załóż konto <ArrowRight className="w-4 h-4" />
            </div>
          </Link>

          <Link
            href="/register/employer"
            className="bg-white border-2 border-gray-100 rounded-2xl p-8 hover:border-red-400 hover:shadow-2xl hover:shadow-red-500/10 hover:-translate-y-1 transition-all text-center group animate-fade-in-up delay-200"
          >
            <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-red-50 to-red-100 rounded-2xl flex items-center justify-center group-hover:from-red-100 group-hover:to-red-200 group-hover:scale-110 transition-all">
              <Briefcase className="w-8 h-8 text-red-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-3 group-hover:text-red-600 transition-colors tracking-tight">
              Szukam pracowników
            </h2>
            <p className="text-sm text-gray-500 leading-relaxed mb-5">
              Dodawaj ogłoszenia, przeglądaj kandydatów
            </p>
            <ul className="text-xs text-gray-500 space-y-2 text-left">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                Publikuj ogłoszenia za darmo
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                Dostęp do bazy CV
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                Panel zarządzania kandydatami
              </li>
            </ul>
            <div className="mt-6 inline-flex items-center gap-1 text-red-600 font-semibold text-sm group-hover:gap-2 transition-all">
              Załóż konto <ArrowRight className="w-4 h-4" />
            </div>
          </Link>
        </div>

        <p className="text-center text-base text-gray-500 mt-10 animate-fade-in-up delay-400">
          Masz już konto?{" "}
          <Link href="/login" className="text-red-600 hover:text-red-700 hover:underline font-bold transition-colors">
            Zaloguj się
          </Link>
        </p>
      </div>
    </div>
  );
}
