"use client";

import Link from "next/link";
import { useAuthStore } from "@/store/authStore";
import { Menu, X, LogOut, LayoutDashboard, ChevronRight } from "lucide-react";
import { useState, useEffect } from "react";
import NotificationBell from "@/components/layout/NotificationBell";

export default function Header() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const [mobileOpen, setMobileOpen] = useState(false);

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
    <>
      {/* Main header */}
      <header className="sticky top-0 z-50 bg-white border-b border-[#E0E3E8]">
        <div className="max-w-[1200px] mx-auto px-6">
          <div className="flex justify-between items-center h-[72px]">
            {/* Logo */}
            <div className="flex items-center gap-2 sm:gap-3 min-w-0">
              <Link href="/" aria-label="Strona główna" className="relative w-9 h-9 sm:w-10 sm:h-10 bg-[#E1002A] rounded-md flex items-center justify-center flex-shrink-0 group">
                <svg viewBox="0 0 32 32" className="w-[22px] h-[22px] sm:w-[25px] sm:h-[25px]">
                  <path
                    fill="white"
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M10 6.5h8.2c3.59 0 6.3 2.78 6.3 6.4s-2.71 6.4-6.3 6.4H13.4v5.7c0 0.28-0.22 0.5-0.5 0.5h-2.9c-0.28 0-0.5-0.22-0.5-0.5V7c0-0.28 0.22-0.5 0.5-0.5zM13.4 10v6h4.6c1.7 0 3-1.34 3-3s-1.3-3-3-3h-4.6z"
                  />
                  <circle cx="24.5" cy="9.5" r="2" fill="white" opacity="0.95" />
                </svg>
              </Link>
              <div className="leading-tight min-w-0">
                <Link
                  href="/"
                  className="block font-display font-extrabold text-[1.05rem] sm:text-[1.4rem] text-[#0D2240] whitespace-nowrap no-underline"
                >
                  Praca <span className="text-[#E1002A]">w Szwajcarii</span>
                </Link>
                <a
                  href="https://polacyszwajcaria.com"
                  target="_blank"
                  rel="noopener"
                  className="hidden sm:block text-[0.65rem] text-[#888] tracking-[0.05em] -mt-0.5 no-underline hover:text-[#E1002A] transition-colors"
                >
                  część portalu <span className="font-semibold">PolacySzwajcaria.com</span>
                </a>
              </div>
            </div>

            {/* Desktop nav */}
            <nav className="hidden lg:flex items-center gap-7">
              <Link href="/oferty" className="hays-nav-link">Oferty pracy</Link>
              <Link href="/register/employer" className="hays-nav-link">Dla pracodawców</Link>
              <Link href="/sprawdz-cv" className="hays-nav-link">Sprawdź CV</Link>
            </nav>

            {/* Actions */}
            <div className="hidden md:flex items-center gap-3">
              {isAuthenticated ? (
                <>
                  <Link
                    href={dashboardLink}
                    className="flex items-center gap-1.5 px-3 py-2 text-[#555] hover:text-[#0D2240] text-sm font-medium transition-colors"
                  >
                    <LayoutDashboard className="w-4 h-4" />
                    Panel
                  </Link>
                  <NotificationBell />
                  <div className="flex items-center gap-2 text-sm text-[#555] bg-[#F5F6F8] px-3 py-1.5 rounded border border-[#E0E3E8]">
                    <div className="w-6 h-6 bg-[#FFF0F3] rounded-full flex items-center justify-center">
                      <span className="text-xs font-bold text-[#E1002A]">
                        {(user?.first_name || user?.email || "U")[0].toUpperCase()}
                      </span>
                    </div>
                    <span className="font-medium">{user?.first_name || user?.email}</span>
                  </div>
                  <button
                    onClick={logout}
                    className="p-2 text-[#888] hover:text-[#E1002A] transition-colors"
                    aria-label="Wyloguj"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="px-5 py-2.5 text-[#0D2240] border border-[#0D2240] rounded text-[0.88rem] font-medium hover:bg-[#0D2240] hover:text-white transition-all no-underline"
                  >
                    Zaloguj się
                  </Link>
                  <Link
                    href="/register"
                    className="px-5 py-2.5 bg-[#E1002A] text-white rounded text-[0.88rem] font-medium hover:bg-[#B8001F] transition-all no-underline"
                  >
                    Wyślij CV
                  </Link>
                </>
              )}
            </div>

            {/* Mobile hamburger */}
            <button
              className="lg:hidden p-2 hover:bg-[#F5F6F8] rounded transition-colors"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label={mobileOpen ? "Zamknij menu" : "Otwórz menu"}
              aria-expanded={mobileOpen}
              aria-controls="mobile-menu"
            >
              {mobileOpen ? <X className="w-6 h-6 text-[#0D2240]" /> : <Menu className="w-6 h-6 text-[#0D2240]" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div id="mobile-menu" className="lg:hidden border-t border-[#E0E3E8] bg-white shadow-xl animate-fade-in">
            <div className="px-4 py-4 space-y-1">
              <Link
                href="/oferty"
                className="flex items-center justify-between text-[#0D2240] font-semibold py-3 px-4 rounded hover:bg-[#F5F6F8] transition-colors no-underline"
                onClick={() => setMobileOpen(false)}
              >
                Oferty pracy
                <ChevronRight className="w-4 h-4 text-[#888]" />
              </Link>
              <Link
                href="/sprawdz-cv"
                className="flex items-center justify-between text-[#0D2240] font-semibold py-3 px-4 rounded hover:bg-[#F5F6F8] transition-colors no-underline"
                onClick={() => setMobileOpen(false)}
              >
                Sprawdź CV
                <ChevronRight className="w-4 h-4 text-[#888]" />
              </Link>
              <Link
                href="/register/employer"
                className="flex items-center justify-between text-[#0D2240] font-semibold py-3 px-4 rounded hover:bg-[#F5F6F8] transition-colors no-underline"
                onClick={() => setMobileOpen(false)}
              >
                Dla pracodawców
                <ChevronRight className="w-4 h-4 text-[#888]" />
              </Link>

              {isAuthenticated ? (
                <>
                  <div className="h-px bg-[#E0E3E8] my-2" />
                  <Link
                    href={dashboardLink}
                    className="flex items-center gap-3 text-[#0D2240] font-semibold py-3 px-4 rounded hover:bg-[#F5F6F8] transition-colors no-underline"
                    onClick={() => setMobileOpen(false)}
                  >
                    <LayoutDashboard className="w-5 h-5 text-[#888]" />
                    Panel
                  </Link>
                  <Link
                    href="/panel/powiadomienia"
                    className="block text-[#0D2240] font-semibold py-3 px-4 rounded hover:bg-[#F5F6F8] transition-colors no-underline"
                    onClick={() => setMobileOpen(false)}
                  >
                    Powiadomienia
                  </Link>
                  <button
                    onClick={() => { logout(); setMobileOpen(false); }}
                    className="w-full text-left text-[#E1002A] font-semibold py-3 px-4 rounded hover:bg-[#FFF0F3] transition-colors flex items-center gap-3"
                  >
                    <LogOut className="w-5 h-5" />
                    Wyloguj się
                  </button>
                </>
              ) : (
                <>
                  <div className="h-px bg-[#E0E3E8] my-2" />
                  <Link
                    href="/login"
                    className="block text-[#0D2240] font-semibold py-3 px-4 rounded hover:bg-[#F5F6F8] transition-colors no-underline border border-[#0D2240] text-center"
                    onClick={() => setMobileOpen(false)}
                  >
                    Zaloguj się
                  </Link>
                  <Link
                    href="/register"
                    className="block bg-[#E1002A] text-white text-center px-4 py-3 rounded font-bold transition-all no-underline"
                    onClick={() => setMobileOpen(false)}
                  >
                    Wyślij CV
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </header>
    </>
  );
}
