"use client";

import Link from "next/link";
import Image from "next/image";
import { useAuthStore } from "@/store/authStore";
import { Menu, X, User, LogOut, LayoutDashboard, ChevronRight } from "lucide-react";
import { useState, useEffect } from "react";
import NotificationBell from "@/components/layout/NotificationBell";

export default function Header() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Track scroll for glass effect
  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  // Close mobile menu on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && mobileOpen) setMobileOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [mobileOpen]);

  const dashboardLink =
    user?.role === "admin"
      ? "/panel/admin"
      : user?.role === "employer"
        ? "/panel/pracodawca"
        : "/panel/pracownik";

  return (
    <header
      className={`sticky top-0 z-50 transition-all duration-300 ${
        scrolled
          ? "glass border-b border-gray-200/60 shadow-sm"
          : "bg-white border-b border-gray-200"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <Image src="/logo.svg" alt="Praca w Szwajcarii" width={36} height={36} className="group-hover:shadow-md transition-shadow rounded-lg" />
            <span className="text-xl font-bold text-gray-900 hidden sm:block group-hover:text-red-600 transition-colors tracking-tight">
              Praca w Szwajcarii
            </span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-1">
            <Link
              href="/oferty"
              className="px-4 py-2 text-gray-600 hover:text-gray-900 font-medium transition-colors rounded-lg hover:bg-gray-50 relative after:absolute after:bottom-1 after:left-4 after:right-4 after:h-0.5 after:w-0 after:bg-red-600 after:transition-all hover:after:w-[calc(100%-2rem)]"
            >
              Oferty pracy
            </Link>
            <Link
              href="/sprawdz-cv"
              className="px-4 py-2 text-gray-600 hover:text-gray-900 font-medium transition-colors rounded-lg hover:bg-gray-50"
            >
              Sprawdź CV
            </Link>

            <div className="w-px h-6 bg-gray-200 mx-2" />

            {isAuthenticated ? (
              <div className="flex items-center gap-2">
                <Link
                  href={dashboardLink}
                  className="flex items-center gap-1.5 px-3 py-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <LayoutDashboard className="w-4 h-4" />
                  <span className="text-sm font-medium">Panel</span>
                </Link>
                <NotificationBell />
                <div className="flex items-center gap-2 text-sm text-gray-600 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                  <div className="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-bold text-red-600">
                      {(user?.first_name || user?.email || "U")[0].toUpperCase()}
                    </span>
                  </div>
                  <span className="font-medium">{user?.first_name || user?.email}</span>
                </div>
                <button
                  onClick={logout}
                  className="flex items-center gap-1.5 px-3 py-2 text-gray-400 hover:text-red-600 text-sm transition-colors rounded-lg hover:bg-red-50"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="px-4 py-2 text-gray-600 hover:text-gray-900 font-medium transition-colors rounded-lg hover:bg-gray-50"
                >
                  Zaloguj się
                </Link>
                <Link
                  href="/register"
                  className="bg-gradient-to-r from-red-600 to-red-700 text-white px-5 py-2.5 rounded-xl hover:shadow-lg hover:shadow-red-500/20 font-semibold text-sm transition-all active:scale-95"
                >
                  Zarejestruj się
                </Link>
              </div>
            )}
          </nav>

          {/* Mobile hamburger */}
          <button
            className="md:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label={mobileOpen ? "Zamknij menu" : "Otwórz menu"}
            aria-expanded={mobileOpen}
            aria-controls="mobile-menu"
          >
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div id="mobile-menu" className="md:hidden border-t border-gray-200/60 bg-white/95 backdrop-blur-lg pb-4 shadow-xl animate-fade-in">
          <div className="px-4 pt-4 space-y-1">
            <Link
              href="/oferty"
              className="flex items-center justify-between text-gray-700 font-semibold py-3 px-4 rounded-xl hover:bg-gray-50 transition-colors"
              onClick={() => setMobileOpen(false)}
            >
              Oferty pracy
              <ChevronRight className="w-4 h-4 text-gray-400" />
            </Link>
            <Link
              href="/sprawdz-cv"
              className="flex items-center justify-between text-gray-700 font-semibold py-3 px-4 rounded-xl hover:bg-gray-50 transition-colors"
              onClick={() => setMobileOpen(false)}
            >
              Sprawdź CV
              <ChevronRight className="w-4 h-4 text-gray-400" />
            </Link>
            {isAuthenticated ? (
              <>
                <div className="h-px bg-gray-100 my-2" />
                <Link
                  href={dashboardLink}
                  className="flex items-center gap-3 text-gray-700 font-semibold py-3 px-4 rounded-xl hover:bg-gray-50 transition-colors"
                  onClick={() => setMobileOpen(false)}
                >
                  <LayoutDashboard className="w-5 h-5 text-gray-500" />
                  Panel
                </Link>
                <Link
                  href="/panel/powiadomienia"
                  className="flex items-center gap-3 text-gray-700 font-semibold py-3 px-4 rounded-xl hover:bg-gray-50 transition-colors"
                  onClick={() => setMobileOpen(false)}
                >
                  Powiadomienia
                </Link>
                <div className="h-px bg-gray-100 my-2" />
                <div className="bg-gray-50 px-4 py-3 rounded-xl text-sm text-gray-600 flex items-center gap-3">
                  <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-bold text-red-600">
                      {(user?.first_name || user?.email || "U")[0].toUpperCase()}
                    </span>
                  </div>
                  <span className="font-medium">{user?.first_name || user?.email}</span>
                </div>
                <button
                  onClick={() => { logout(); setMobileOpen(false); }}
                  className="w-full text-left text-red-600 font-semibold py-3 px-4 rounded-xl hover:bg-red-50 transition-colors flex items-center gap-3"
                >
                  <LogOut className="w-5 h-5" />
                  Wyloguj się
                </button>
              </>
            ) : (
              <>
                <div className="h-px bg-gray-100 my-2" />
                <Link
                  href="/login"
                  className="block text-gray-700 font-semibold py-3 px-4 rounded-xl hover:bg-gray-50 transition-colors"
                  onClick={() => setMobileOpen(false)}
                >
                  Zaloguj się
                </Link>
                <Link
                  href="/register"
                  className="block bg-gradient-to-r from-red-600 to-red-700 text-white text-center px-4 py-3.5 rounded-xl font-bold shadow-lg shadow-red-500/20 active:scale-95 transition-all"
                  onClick={() => setMobileOpen(false)}
                >
                  Zarejestruj się
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
