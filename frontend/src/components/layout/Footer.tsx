import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-400 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">PS</span>
              </div>
              <span className="text-lg font-bold text-white">
                PolacySzwajcaria
              </span>
            </div>
            <p className="text-sm">
              Portal pracy dla Polaków w Szwajcarii. Znajdź wymarzoną pracę lub
              najlepszych pracowników.
            </p>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-4">Dla pracowników</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/oferty" className="hover:text-white">Przeglądaj oferty</Link></li>
              <li><Link href="/register/worker" className="hover:text-white">Utwórz konto</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-4">Dla pracodawców</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/register/employer" className="hover:text-white">Dodaj ogłoszenie</Link></li>
              <li><Link href="/register/employer" className="hover:text-white">Zarejestruj firmę</Link></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 flex flex-col sm:flex-row justify-between items-center gap-4 text-sm">
          <p>&copy; {new Date().getFullYear()} PolacySzwajcaria. Wszelkie prawa zastrzeżone.</p>
          <div className="flex gap-4">
            <Link href="/regulamin" className="hover:text-white">Regulamin</Link>
            <Link href="/polityka-prywatnosci" className="hover:text-white">Polityka prywatności</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
