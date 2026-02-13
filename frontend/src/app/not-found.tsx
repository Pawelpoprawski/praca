import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-24 text-center">
      <h1 className="text-6xl font-bold text-red-600 mb-4">404</h1>
      <p className="text-xl text-gray-700 mb-2">Strona nie została znaleziona</p>
      <p className="text-gray-500 mb-8">
        Strona, której szukasz, nie istnieje lub została przeniesiona.
      </p>
      <div className="flex justify-center gap-4">
        <Link
          href="/"
          className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 font-medium"
        >
          Strona główna
        </Link>
        <Link
          href="/oferty"
          className="border border-gray-300 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-50 font-medium"
        >
          Przeglądaj oferty
        </Link>
      </div>
    </div>
  );
}
