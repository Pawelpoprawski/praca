"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { useEffect } from "react";
import {
  LayoutDashboard, User, FileText, Send, Building2,
  PlusCircle, Users, Settings, Shield, List, FolderOpen, Bell, Star, BellRing, Clock, Heart, FileSearch,
  Activity, Cpu, Briefcase,
} from "lucide-react";
import { cn } from "@/lib/utils";

const workerLinks = [
  { href: "/panel/pracownik", label: "Dashboard", icon: LayoutDashboard },
  { href: "/panel/pracownik/profil", label: "Mój profil", icon: User },
  { href: "/panel/pracownik/cv", label: "Moje CV", icon: FileText },
  { href: "/panel/pracownik/aplikacje", label: "Moje aplikacje", icon: Send },
  { href: "/panel/pracownik/zapisane", label: "Zapisane oferty", icon: Heart },
  { href: "/panel/pracownik/historia", label: "Ostatnio oglądane", icon: Clock },
  { href: "/panel/pracownik/alerty", label: "Alerty o pracy", icon: BellRing },
];

const employerLinks = [
  { href: "/panel/pracodawca", label: "Dashboard", icon: LayoutDashboard },
  { href: "/panel/pracodawca/profil", label: "Profil firmy", icon: Building2 },
  { href: "/panel/pracodawca/ogloszenia", label: "Moje ogłoszenia", icon: List },
  { href: "/panel/pracodawca/ogloszenia/nowe", label: "Dodaj ogłoszenie", icon: PlusCircle },
];

const adminLinks = [
  { href: "/panel/admin", label: "Dashboard", icon: LayoutDashboard },
  { href: "/panel/admin/moderacja", label: "Moderacja", icon: Shield },
  { href: "/panel/admin/recenzje", label: "Recenzje", icon: Star },
  { href: "/panel/admin/uzytkownicy", label: "Użytkownicy", icon: Users },
  { href: "/panel/admin/firmy", label: "Firmy", icon: Building2 },
  { href: "/panel/admin/cv", label: "CV pracowników", icon: FileText },
  { href: "/panel/admin/baza-cv", label: "Baza CV", icon: FileSearch },
  { href: "/panel/admin/oferty", label: "Oferty AI", icon: Briefcase },
  { href: "/panel/admin/ekstrakcja", label: "Ekstrakcja AI", icon: Cpu },
  { href: "/panel/admin/logi", label: "Logi", icon: Activity },
  { href: "/panel/admin/kategorie", label: "Kategorie", icon: FolderOpen },
  { href: "/panel/admin/ustawienia", label: "Ustawienia", icon: Settings },
];

export default function PanelLayout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-200 border-t-red-600" />
          <p className="text-sm text-gray-400">Ładowanie...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  const commonLinks = [
    { href: "/panel/powiadomienia", label: "Powiadomienia", icon: Bell },
  ];

  const links =
    user?.role === "admin"
      ? [...adminLinks, ...commonLinks]
      : user?.role === "employer"
        ? [...employerLinks, ...commonLinks]
        : [...workerLinks, ...commonLinks];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
      <div className="flex flex-col md:flex-row gap-4 md:gap-8">
        {/* Sidebar */}
        <aside className="md:w-56 flex-shrink-0">
          <nav className="flex md:flex-col gap-1 overflow-x-auto md:overflow-x-visible pb-2 md:pb-0 -mx-4 px-4 sm:mx-0 sm:px-0 md:bg-white md:border md:border-gray-100 md:rounded-2xl md:p-2 md:shadow-sm">
            {links.map((link) => {
              const isActive =
                pathname === link.href ||
                (link.href !== `/panel/${user?.role === "admin" ? "admin" : user?.role === "employer" ? "pracodawca" : "pracownik"}` &&
                  pathname.startsWith(link.href));
              const Icon = link.icon;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "flex flex-col md:flex-row items-center md:items-center gap-1 md:gap-3 px-2 md:px-3 py-2 md:py-2.5 rounded-lg md:rounded-xl text-xs md:text-sm font-medium transition-all whitespace-nowrap md:whitespace-normal min-w-[52px] md:min-w-0",
                    isActive
                      ? "bg-red-50 text-red-700 md:shadow-sm"
                      : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
                  )}
                >
                  <Icon className={cn("w-4 h-4 flex-shrink-0", isActive && "text-red-600")} />
                  <span className="leading-tight text-center md:text-left">{link.label}</span>
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Content */}
        <div className="flex-1 min-w-0">{children}</div>
      </div>
    </div>
  );
}
