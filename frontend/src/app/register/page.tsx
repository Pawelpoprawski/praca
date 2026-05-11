"use client";

import Link from "next/link";
import { Briefcase, User, ArrowRight, Check } from "lucide-react";

export default function RegisterPage() {
  return (
    <div className="min-h-[80vh] bg-[#F5F6F8] flex items-center justify-center px-4 py-16">
      <div className="w-full max-w-3xl">
        <div className="text-center mb-12">
          <span className="hays-red-line mx-auto" />
          <h1 className="font-display text-[2.2rem] md:text-[2.8rem] font-extrabold text-[#0D2240] mb-3 leading-tight">
            Utwórz konto
          </h1>
          <p className="text-[1.05rem] text-[#555]">
            Wybierz typ konta, który Cię interesuje
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <RoleCard
            href="/register/worker"
            badge="Dla kandydatów"
            badgeStyle="red"
            icon={<User className="w-7 h-7 text-[#E1002A]" />}
            title="Szukam pracy"
            desc="Przeglądaj oferty, aplikuj, zarządzaj swoim CV."
            features={[
              "Szybka aplikacja jednym kliknięciem",
              "Darmowa analiza CV z AI",
              "Alerty o nowych ofertach",
            ]}
            cta="Załóż konto pracownika"
          />
          <RoleCard
            href="/register/employer"
            badge="Dla pracodawców"
            badgeStyle="navy"
            icon={<Briefcase className="w-7 h-7 text-[#0D2240]" />}
            title="Szukam pracowników"
            desc="Dodawaj ogłoszenia, przeglądaj kandydatów."
            features={[
              "Publikuj ogłoszenia za darmo",
              "Dostęp do bazy CV",
              "Panel zarządzania kandydatami",
            ]}
            cta="Załóż konto pracodawcy"
          />
        </div>

        <p className="text-center text-[#555] mt-10">
          Masz już konto?{" "}
          <Link href="/login" className="text-[#E1002A] hover:underline font-semibold">
            Zaloguj się
          </Link>
        </p>
      </div>
    </div>
  );
}

function RoleCard({
  href, badge, badgeStyle, icon, title, desc, features, cta,
}: {
  href: string;
  badge: string;
  badgeStyle: "red" | "navy";
  icon: React.ReactNode;
  title: string;
  desc: string;
  features: string[];
  cta: string;
}) {
  const badgeClass = badgeStyle === "red"
    ? "bg-[#FFF0F3] text-[#E1002A]"
    : "bg-[#E8EDF4] text-[#0D2240]";

  return (
    <Link
      href={href}
      className="bg-white border border-[#E0E3E8] rounded-lg p-8 hover:border-[#E1002A] hover:shadow-[0_8px_32px_rgba(0,0,0,0.08)] transition-all group no-underline block"
    >
      <span className={`inline-block text-[0.72rem] font-semibold uppercase tracking-[0.1em] px-3 py-1 rounded mb-4 ${badgeClass}`}>
        {badge}
      </span>
      <div className="w-14 h-14 rounded-lg bg-[#F5F6F8] flex items-center justify-center mb-5 group-hover:bg-[#FFF0F3] transition-colors">
        {icon}
      </div>
      <h2 className="font-display text-[1.3rem] font-bold text-[#0D2240] mb-2 group-hover:text-[#E1002A] transition-colors">
        {title}
      </h2>
      <p className="text-[#555] leading-[1.7] mb-5 text-[0.95rem]">{desc}</p>
      <ul className="space-y-2 mb-6">
        {features.map((f) => (
          <li key={f} className="flex items-start gap-3 text-[0.88rem] text-[#555]">
            <Check className="w-4 h-4 text-[#E1002A] flex-shrink-0 mt-0.5" />
            <span>{f}</span>
          </li>
        ))}
      </ul>
      <div className="inline-flex items-center gap-2 text-[#E1002A] font-medium text-[0.9rem] group-hover:gap-3 transition-all">
        {cta} <ArrowRight className="w-4 h-4" />
      </div>
    </Link>
  );
}
