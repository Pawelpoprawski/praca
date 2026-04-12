import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Regulamin - Praca w Szwajcarii",
  description: "Regulamin korzystania z portalu PolacySzwajcaria.com",
};

export default function RegulaminPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 md:py-16">
      <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">Regulamin</h1>

      <div className="prose prose-gray max-w-none text-gray-700 space-y-6">
        <p className="text-sm text-gray-500">Ostatnia aktualizacja: 17 lutego 2026 r.</p>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">1. Postanowienia ogólne</h2>
        <p>
          Niniejszy regulamin określa zasady korzystania z portalu internetowego dostępnego pod adresem{" "}
          <strong>PolacySzwajcaria.com</strong> (dalej: &quot;Portal&quot;), którego właścicielem i operatorem jest portal
          PolacySzwajcaria.com. Kontakt z administratorem możliwy jest pod adresem e-mail:{" "}
          <a href="mailto:kontakt@polacyszwajcaria.com" className="text-red-600 hover:underline">kontakt@polacyszwajcaria.com</a>.
        </p>
        <p>
          Korzystanie z Portalu oznacza akceptację niniejszego regulaminu w całej jego treści.
        </p>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">2. Definicje</h2>
        <ul className="list-disc pl-6 space-y-2">
          <li><strong>Portal</strong> &ndash; serwis internetowy PolacySzwajcaria.com umożliwiający publikowanie i przeglądanie ofert pracy w Szwajcarii.</li>
          <li><strong>Użytkownik</strong> &ndash; każda osoba korzystająca z Portalu, w tym Pracownik i Pracodawca.</li>
          <li><strong>Pracownik</strong> &ndash; osoba fizyczna poszukująca pracy, która zarejestruje konto w roli pracownika.</li>
          <li><strong>Pracodawca</strong> &ndash; osoba fizyczna, prawna lub jednostka organizacyjna publikująca oferty pracy.</li>
          <li><strong>Ogłoszenie</strong> &ndash; oferta pracy opublikowana na Portalu przez Pracodawcę.</li>
        </ul>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">3. Zasady korzystania z Portalu</h2>
        <p>Użytkownik zobowiązuje się do:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li>Podawania prawdziwych i aktualnych danych podczas rejestracji oraz publikacji ogłoszeń.</li>
          <li>Korzystania z Portalu zgodnie z obowiązującym prawem oraz dobrymi obyczajami.</li>
          <li>Niepodejmowania działań mogących zakłócić działanie Portalu lub naruszać prawa innych Użytkowników.</li>
          <li>Nieumieszczania treści o charakterze bezprawnym, oszukańczym, dyskryminującym lub wprowadzającym w błąd.</li>
        </ul>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">4. Rejestracja i konto</h2>
        <p>
          Rejestracja konta jest dobrowolna i bezpłatna. Użytkownik może zarejestrować się jako Pracownik lub Pracodawca.
          Każdy Użytkownik może posiadać jedno konto. Administrator zastrzega sobie prawo do zablokowania lub
          usunięcia konta w przypadku naruszenia regulaminu.
        </p>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">5. Publikacja ogłoszeń</h2>
        <p>
          Pracodawca może publikować ogłoszenia o pracę w ramach przydzielonego limitu. Ogłoszenia podlegają moderacji
          i mogą zostać odrzucone w przypadku naruszenia regulaminu. Portal zastrzega sobie prawo do edycji lub
          usunięcia ogłoszeń niezgodnych z regulaminem.
        </p>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">6. Odpowiedzialność</h2>
        <p>
          Portal pełni rolę pośrednika między Pracownikami a Pracodawcami. Nie ponosimy odpowiedzialności za:
        </p>
        <ul className="list-disc pl-6 space-y-2">
          <li>Treść ogłoszeń publikowanych przez Pracodawców.</li>
          <li>Przebieg i wynik procesów rekrutacyjnych.</li>
          <li>Działania Użytkowników podejmowane poza Portalem.</li>
          <li>Przerwy w działaniu Portalu wynikające z przyczyn technicznych lub siły wyższej.</li>
        </ul>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">7. Prawa własności intelektualnej</h2>
        <p>
          Wszelkie treści zamieszczone na Portalu, w tym teksty, grafiki, logo i oprogramowanie, stanowią
          własność portalu PolacySzwajcaria.com lub ich autoryzowanych dostawców i są chronione prawem autorskim.
          Kopiowanie, rozpowszechnianie lub wykorzystywanie tych treści bez zgody jest zabronione.
        </p>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">8. Zmiany regulaminu</h2>
        <p>
          Portal zastrzega sobie prawo do zmiany niniejszego regulaminu. O istotnych zmianach Użytkownicy
          zostaną poinformowani za pośrednictwem Portalu. Dalsze korzystanie z Portalu po wprowadzeniu zmian
          oznacza ich akceptację.
        </p>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">9. Kontakt</h2>
        <p>
          W sprawach związanych z regulaminem prosimy o kontakt pod adresem:{" "}
          <a href="mailto:kontakt@polacyszwajcaria.com" className="text-red-600 hover:underline">kontakt@polacyszwajcaria.com</a>.
        </p>
      </div>
    </div>
  );
}
