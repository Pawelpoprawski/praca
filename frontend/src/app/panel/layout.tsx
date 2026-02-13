"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { useEffect } from "react";
import {
  LayoutDashboard, User, FileText, Send, Building2,
  PlusCircle, Users, Settings, Shield, List, FolderOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";

const workerLinks = [
  { href: "/panel/pracownik", label: "Dashboard", icon: LayoutDashboard },
  { href: "/panel/pracownik/profil", label: "Mój profil", icon: User },
  { href: "/panel/pracownik/cv", label: "Moje CV", icon: FileText },
  { href: "/panel/pracownik/aplikacje", label: "Moje aplikacje", icon: Send },
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
  { href: "/panel/admin/uzytkownicy", label: "Użytkownicy", icon: Users },
  { href: "/panel/admin/cv", label: "Baza CV", icon: FileText },
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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  const links =
    user?.role === "admin"
      ? adminLinks
      : user?.role === "employer"
        ? employerLinks
        : workerLinks;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col md:flex-row gap-8">
        {/* Sidebar */}
        <aside className="md:w-56 flex-shrink-0">
          <nav className="space-y-1">
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
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-red-50 text-red-700"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {link.label}
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
