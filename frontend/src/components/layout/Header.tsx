"use client";

import Link from "next/link";
import { useAuthStore } from "@/store/authStore";
import { Menu, X, User, LogOut, LayoutDashboard } from "lucide-react";
import { useState } from "react";

export default function Header() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const [mobileOpen, setMobileOpen] = useState(false);

  const dashboardLink =
    user?.role === "admin"
      ? "/panel/admin"
      : user?.role === "employer"
        ? "/panel/pracodawca"
        : "/panel/pracownik";

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">PS</span>
            </div>
            <span className="text-xl font-bold text-gray-900 hidden sm:block">
              PolacySzwajcaria
            </span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="/oferty"
              className="text-gray-600 hover:text-gray-900 font-medium"
            >
              Oferty pracy
            </Link>

            {isAuthenticated ? (
              <div className="flex items-center gap-4">
                <Link
                  href={dashboardLink}
                  className="flex items-center gap-1 text-gray-600 hover:text-gray-900"
                >
                  <LayoutDashboard className="w-4 h-4" />
                  Panel
                </Link>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <User className="w-4 h-4" />
                  {user?.first_name || user?.email}
                </div>
                <button
                  onClick={logout}
                  className="flex items-center gap-1 text-gray-500 hover:text-red-600 text-sm"
                >
                  <LogOut className="w-4 h-4" />
                  Wyloguj
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  href="/login"
                  className="text-gray-600 hover:text-gray-900 font-medium"
                >
                  Zaloguj się
                </Link>
                <Link
                  href="/register"
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 font-medium text-sm"
                >
                  Zarejestruj się
                </Link>
              </div>
            )}
          </nav>

          {/* Mobile hamburger */}
          <button
            className="md:hidden p-2"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white pb-4">
          <div className="px-4 pt-3 space-y-3">
            <Link
              href="/oferty"
              className="block text-gray-700 font-medium py-2"
              onClick={() => setMobileOpen(false)}
            >
              Oferty pracy
            </Link>
            {isAuthenticated ? (
              <>
                <Link
                  href={dashboardLink}
                  className="block text-gray-700 font-medium py-2"
                  onClick={() => setMobileOpen(false)}
                >
                  Panel
                </Link>
                <button
                  onClick={() => { logout(); setMobileOpen(false); }}
                  className="block text-red-600 font-medium py-2"
                >
                  Wyloguj się
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="block text-gray-700 font-medium py-2"
                  onClick={() => setMobileOpen(false)}
                >
                  Zaloguj się
                </Link>
                <Link
                  href="/register"
                  className="block bg-red-600 text-white text-center px-4 py-2 rounded-lg font-medium"
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
