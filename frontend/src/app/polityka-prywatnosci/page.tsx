import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Polityka prywatności - Praca w Szwajcarii",
  description: "Polityka prywatności portalu PolacySzwajcaria.com",
};

export default function PolitykaPrywatnosciPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 md:py-16">
      <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">Polityka prywatności</h1>

      <div className="prose prose-gray max-w-none text-gray-700 space-y-6">
        <p className="text-sm text-gray-500">Ostatnia aktualizacja: 17 lutego 2026 r.</p>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">1. Administrator danych</h2>
        <p>
          Administratorem danych osobowych jest portal <strong>PolacySzwajcaria.com</strong>.
          Kontakt z administratorem możliwy jest pod adresem e-mail:{" "}
          <a href="mailto:kontakt@polacyszwajcaria.com" className="text-red-600 hover:underline">kontakt@polacyszwajcaria.com</a>.
        </p>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">2. Jakie dane zbieramy</h2>
        <p>W ramach korzystania z Portalu możemy zbierać następujące dane:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li><strong>Dane rejestracyjne:</strong> imię, nazwisko, adres e-mail, numer telefonu.</li>
          <li><strong>Dane profilowe pracownika:</strong> doświadczenie zawodowe, umiejętności, języki, CV, preferencje dotyczące pracy.</li>
          <li><strong>Dane profilowe pracodawcy:</strong> nazwa firmy, opis, strona internetowa, logo.</li>
          <li><strong>Dane techniczne:</strong> adres IP, typ przeglądarki, system operacyjny, czas wizyty.</li>
          <li><strong>Pliki cookies:</strong> w celu zapewnienia prawidłowego działania Portalu i analizy ruchu.</li>
        </ul>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">3. Cele przetwarzania danych</h2>
        <p>Dane osobowe przetwarzamy w celu:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li>Świadczenia usług dostępnych w Portalu (rejestracja, publikacja ogłoszeń, aplikowanie na oferty).</li>
          <li>Komunikacji z Użytkownikami (odpowiedzi na zapytania, powiadomienia).</li>
          <li>Zapewnienia bezpieczeństwa i zapobiegania nadużyciom.</li>
          <li>Analizy statystycznej i doskonalenia usług Portalu.</li>
          <li>Wypełnienia obowiązków prawnych.</li>
        </ul>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">4. Podstawa prawna przetwarzania</h2>
        <p>Przetwarzanie danych odbywa się na podstawie:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li>Zgody Użytkownika (art. 6 ust. 1 lit. a RODO).</li>
          <li>Wykonania umowy lub podjęcia działań przed jej zawarciem (art. 6 ust. 1 lit. b RODO).</li>
          <li>Prawnie uzasadnionego interesu administratora (art. 6 ust. 1 lit. f RODO).</li>
        </ul>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">5. Udostępnianie danych</h2>
        <p>Dane osobowe mogą być udostępniane:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li><strong>Pracodawcom</strong> &ndash; w przypadku aplikowania na ofertę pracy (imię, nazwisko, CV, list motywacyjny).</li>
          <li><strong>Dostawcom usług</strong> &ndash; podmiotom świadczącym usługi hostingowe, analityczne i e-mail na rzecz Portalu.</li>
          <li><strong>Organom publicznym</strong> &ndash; w przypadkach wymaganych przez prawo.</li>
        </ul>
        <p>Dane nie są sprzedawane ani udostępniane podmiotom trzecim w celach marketingowych.</p>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">6. Okres przechowywania danych</h2>
        <p>
          Dane osobowe przechowujemy przez okres niezbędny do realizacji celów, dla których zostały zebrane,
          lub do momentu wycofania zgody przez Użytkownika. Po usunięciu konta dane są usuwane w ciągu 30 dni,
          z wyjątkiem danych, które jesteśmy zobowiązani przechowywać na podstawie przepisów prawa.
        </p>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">7. Prawa Użytkownika</h2>
        <p>Każdy Użytkownik ma prawo do:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li>Dostępu do swoich danych osobowych.</li>
          <li>Sprostowania nieprawidłowych danych.</li>
          <li>Usunięcia danych (&quot;prawo do bycia zapomnianym&quot;).</li>
          <li>Ograniczenia przetwarzania danych.</li>
          <li>Przenoszenia danych.</li>
          <li>Wniesienia sprzeciwu wobec przetwarzania.</li>
          <li>Wycofania zgody w dowolnym momencie.</li>
        </ul>
        <p>
          W celu skorzystania z powyższych praw prosimy o kontakt pod adresem:{" "}
          <a href="mailto:kontakt@polacyszwajcaria.com" className="text-red-600 hover:underline">kontakt@polacyszwajcaria.com</a>.
        </p>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">8. Pliki cookies</h2>
        <p>
          Portal wykorzystuje pliki cookies w celu zapewnienia prawidłowego działania serwisu,
          zapamiętywania preferencji Użytkownika oraz analizy statystycznej. Użytkownik może zarządzać
          plikami cookies za pomocą ustawień swojej przeglądarki internetowej.
        </p>
        <p>Stosujemy następujące rodzaje cookies:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li><strong>Niezbędne</strong> &ndash; wymagane do działania Portalu (autoryzacja, sesja).</li>
          <li><strong>Funkcjonalne</strong> &ndash; zapamiętywanie preferencji Użytkownika.</li>
          <li><strong>Analityczne</strong> &ndash; zbieranie danych o sposobie korzystania z Portalu.</li>
        </ul>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">9. Bezpieczeństwo danych</h2>
        <p>
          Stosujemy odpowiednie środki techniczne i organizacyjne w celu ochrony danych osobowych
          przed nieuprawnionym dostępem, utratą, zniszczeniem lub modyfikacją, w tym szyfrowanie
          połączenia (SSL/TLS) oraz bezpieczne przechowywanie haseł.
        </p>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">10. Zmiany polityki prywatności</h2>
        <p>
          Zastrzegamy sobie prawo do zmiany niniejszej polityki prywatności. O istotnych zmianach
          Użytkownicy zostaną poinformowani za pośrednictwem Portalu. Aktualna wersja polityki
          prywatności jest zawsze dostępna pod adresem{" "}
          <a href="/polityka-prywatnosci" className="text-red-600 hover:underline">PolacySzwajcaria.com/polityka-prywatnosci</a>.
        </p>

        <h2 className="text-xl font-semibold text-gray-900 mt-8">11. Kontakt</h2>
        <p>
          W sprawach związanych z ochroną danych osobowych prosimy o kontakt:{" "}
          <a href="mailto:kontakt@polacyszwajcaria.com" className="text-red-600 hover:underline">kontakt@polacyszwajcaria.com</a>.
        </p>
      </div>
    </div>
  );
}
