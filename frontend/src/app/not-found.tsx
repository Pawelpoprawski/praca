import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-32 text-center">
      <h1 className="text-8xl font-bold font-display bg-[#E1002A] bg-clip-text text-transparent mb-6">404</h1>
      <p className="text-2xl font-bold text-[#0D2240] mb-3">Strona nie została znaleziona</p>
      <p className="text-gray-600 mb-10 leading-relaxed">
        Strona, której szukasz, nie istnieje lub została przeniesiona.
      </p>
      <div className="flex flex-col sm:flex-row justify-center gap-4">
        <Link
          href="/"
          className="bg-[#E1002A] text-white px-8 py-3.5 rounded-xl hover:shadow-lg font-bold transition-all active:scale-95"
        >
          Strona główna
        </Link>
        <Link
          href="/oferty"
          className="border-2 border-gray-300 text-gray-700 px-8 py-3.5 rounded-xl hover:bg-gray-50 hover:border-gray-400 font-semibold transition-all"
        >
          Przeglądaj oferty
        </Link>
      </div>
    </div>
  );
}
