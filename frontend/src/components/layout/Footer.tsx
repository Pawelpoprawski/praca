import Link from "next/link";
import Image from "next/image";

export default function Footer() {
  return (
    <footer className="bg-gray-950 text-gray-400 mt-auto relative overflow-hidden">
      {/* Swiss cross subtle watermark */}
      <div className="absolute right-8 top-8 opacity-[0.03]">
        <svg width="120" height="120" viewBox="0 0 32 32" fill="white">
          <rect x="13" y="6" width="6" height="20" rx="1" />
          <rect x="6" y="13" width="20" height="6" rx="1" />
        </svg>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 relative">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 md:gap-8">
          {/* Brand column */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5 mb-4">
              <Image src="/logo.svg" alt="Praca w Szwajcarii" width={36} height={36} className="rounded-lg" />
              <span className="text-lg font-bold text-white tracking-tight">
                Praca w Szwajcarii
              </span>
            </div>
            <p className="text-sm leading-relaxed max-w-sm mb-6">
              Portal pracy dla Polaków w Szwajcarii. Znajdź wymarzoną pracę lub
              najlepszych pracowników. Wszystko za darmo.
            </p>
            {/* PL + CH flags */}
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="inline-flex items-center gap-1.5 bg-gray-900 px-2.5 py-1 rounded-md border border-gray-800">
                <span>🇵🇱</span> Polska
              </span>
              <span className="text-gray-700">&rarr;</span>
              <span className="inline-flex items-center gap-1.5 bg-gray-900 px-2.5 py-1 rounded-md border border-gray-800">
                <span>🇨🇭</span> Szwajcaria
              </span>
            </div>
          </div>

          {/* Links - Workers */}
          <div>
            <h3 className="text-white font-bold mb-4 text-sm uppercase tracking-wider">Dla pracowników</h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/register/worker" className="hover:text-white transition-colors inline-flex items-center gap-1 group">
                  <span className="w-1 h-1 bg-red-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
                  Utwórz konto
                </Link>
              </li>
              <li>
                <Link href="/sprawdz-cv" className="hover:text-white transition-colors inline-flex items-center gap-1 group">
                  <span className="w-1 h-1 bg-red-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
                  Analizuj CV
                </Link>
              </li>
              <li>
                <Link href="/oferty" className="hover:text-white transition-colors inline-flex items-center gap-1 group">
                  <span className="w-1 h-1 bg-red-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
                  Przeglądaj oferty
                </Link>
              </li>
            </ul>
          </div>

          {/* Links - Employers */}
          <div>
            <h3 className="text-white font-bold mb-4 text-sm uppercase tracking-wider">Dla pracodawców</h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/register/employer" className="hover:text-white transition-colors inline-flex items-center gap-1 group">
                  <span className="w-1 h-1 bg-red-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
                  Dodaj ogłoszenie
                </Link>
              </li>
              <li>
                <Link href="/register/employer" className="hover:text-white transition-colors inline-flex items-center gap-1 group">
                  <span className="w-1 h-1 bg-red-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
                  Zarejestruj firmę
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800/80 mt-12 pt-8 flex flex-col sm:flex-row justify-between items-center gap-4 text-sm">
          <p className="text-gray-500">&copy; {new Date().getFullYear()} Praca w Szwajcarii. Wszelkie prawa zastrzeżone.</p>
          <div className="flex gap-6">
            <Link href="/regulamin" className="hover:text-white transition-colors">Regulamin</Link>
            <Link href="/polityka-prywatnosci" className="hover:text-white transition-colors">Polityka prywatności</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
