import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-[#0D2240] text-white/85 mt-auto">
      <div className="max-w-[1200px] mx-auto px-6 pt-12 pb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-[2fr_1fr_1fr_1fr] gap-10 mb-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-[#E1002A] rounded flex items-center justify-center">
                <svg viewBox="0 0 32 32" fill="white" className="w-5 h-5">
                  <rect x="13" y="6" width="6" height="20" rx="1" />
                  <rect x="6" y="13" width="20" height="6" rx="1" />
                </svg>
              </div>
              <div className="leading-tight">
                <span className="font-display font-extrabold text-[1.25rem] text-white">
                  Praca <span className="text-[#E1002A]">w Szwajcarii</span>
                </span>
                <div className="text-[0.7rem] text-white/40 mt-0.5">
                  część portalu <span className="font-semibold text-white/60">PolacySzwajcaria.com</span>
                </div>
              </div>
            </div>
            <p className="text-[0.85rem] text-white/50 leading-[1.7] max-w-[320px]">
              Specjaliści dla specjalistów. Profesjonalna rekrutacja polskich pracowników do firm w Szwajcarii — od 2015 roku.
            </p>
          </div>

          {/* Dla kandydatów */}
          <div>
            <h4 className="font-display text-[0.8rem] font-semibold uppercase tracking-[0.1em] text-white mb-4">
              Dla kandydatów
            </h4>
            <ul className="flex flex-col gap-2.5 list-none">
              <li><Link href="/oferty" className="text-white/50 hover:text-white text-[0.88rem] transition-colors no-underline">Oferty pracy</Link></li>
              <li><Link href="/register/worker" className="text-white/50 hover:text-white text-[0.88rem] transition-colors no-underline">Wyślij CV</Link></li>
              <li><Link href="/sprawdz-cv" className="text-white/50 hover:text-white text-[0.88rem] transition-colors no-underline">Sprawdź CV</Link></li>
            </ul>
          </div>

          {/* Dla pracodawców */}
          <div>
            <h4 className="font-display text-[0.8rem] font-semibold uppercase tracking-[0.1em] text-white mb-4">
              Dla pracodawców
            </h4>
            <ul className="flex flex-col gap-2.5 list-none">
              <li><Link href="/register/employer" className="text-white/50 hover:text-white text-[0.88rem] transition-colors no-underline">Dodaj ogłoszenie</Link></li>
              <li><Link href="/register/employer" className="text-white/50 hover:text-white text-[0.88rem] transition-colors no-underline">Zarejestruj firmę</Link></li>
              <li><Link href="/login" className="text-white/50 hover:text-white text-[0.88rem] transition-colors no-underline">Panel pracodawcy</Link></li>
            </ul>
          </div>

          {/* O firmie */}
          <div>
            <h4 className="font-display text-[0.8rem] font-semibold uppercase tracking-[0.1em] text-white mb-4">
              O firmie
            </h4>
            <ul className="flex flex-col gap-2.5 list-none">
              <li><Link href="/regulamin" className="text-white/50 hover:text-white text-[0.88rem] transition-colors no-underline">Regulamin</Link></li>
              <li><Link href="/polityka-prywatnosci" className="text-white/50 hover:text-white text-[0.88rem] transition-colors no-underline">Polityka prywatności</Link></li>
              <li><a href="mailto:kontakt@praca-w-szwajcarii.ch" className="text-white/50 hover:text-white text-[0.88rem] transition-colors no-underline">Kontakt</a></li>
            </ul>
          </div>
        </div>

        <div className="pt-5 border-t border-white/10 flex flex-col sm:flex-row justify-between items-center gap-3 text-[0.78rem] text-white/40">
          <span>© {new Date().getFullYear()} Praca w Szwajcarii. Wszystkie prawa zastrzeżone.</span>
          <div className="flex gap-5">
            <Link href="/regulamin" className="text-white/40 hover:text-white transition-colors no-underline">Regulamin</Link>
            <Link href="/polityka-prywatnosci" className="text-white/40 hover:text-white transition-colors no-underline">Polityka prywatności</Link>
            <Link href="/polityka-prywatnosci#rodo" className="text-white/40 hover:text-white transition-colors no-underline">RODO</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
