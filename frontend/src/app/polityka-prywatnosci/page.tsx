import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Polityka prywatności - Praca w Szwajcarii",
  description: "Polityka prywatności portalu Praca w Szwajcarii.com",
};

export default function PolitykaPrywatnosciPage() {
  return (
    <div className="bg-white">
      {/* Hero strip — navy */}
      <section className="bg-[#0D2240] text-white py-12 md:py-16 relative overflow-hidden">
        <div className="absolute inset-0 hays-pattern" />
        <div className="relative z-10 max-w-[1200px] mx-auto px-6">
          <span className="hays-red-line" />
          <h1 className="font-display text-[2rem] md:text-[2.5rem] font-extrabold leading-tight">
            Polityka prywatności
          </h1>
          <p className="text-white/70 mt-2 text-[0.95rem]">
            Ostatnia aktualizacja: 17 lutego 2026 r.
          </p>
        </div>
      </section>

      {/* Content */}
      <article className="max-w-[800px] mx-auto px-6 py-12 md:py-16 text-[#1A1A1A] leading-[1.75]">
        <PolicySection number={1} title="Administrator danych">
          <p>
            Administratorem danych osobowych jest portal <strong>Praca w Szwajcarii.com</strong>.
            Kontakt z administratorem możliwy jest pod adresem e-mail:{" "}
            <a href="mailto:kontakt@praca-w-szwajcarii.ch" className="text-[#E1002A] hover:underline">
              kontakt@praca-w-szwajcarii.ch
            </a>.
          </p>
        </PolicySection>

        <PolicySection number={2} title="Jakie dane zbieramy">
          <p>W ramach korzystania z Portalu możemy zbierać następujące dane:</p>
          <PolicyList items={[
            <><strong>Dane rejestracyjne:</strong> imię, nazwisko, adres e-mail, numer telefonu.</>,
            <><strong>Dane profilowe pracownika:</strong> doświadczenie zawodowe, umiejętności, języki, CV, preferencje dotyczące pracy.</>,
            <><strong>Dane profilowe pracodawcy:</strong> nazwa firmy, opis, strona internetowa, logo.</>,
            <><strong>Dane techniczne:</strong> adres IP, typ przeglądarki, system operacyjny, czas wizyty.</>,
            <><strong>Pliki cookies:</strong> w celu zapewnienia prawidłowego działania Portalu i analizy ruchu.</>,
          ]} />
        </PolicySection>

        <PolicySection number={3} title="Cele przetwarzania danych">
          <p>Dane osobowe przetwarzamy w celu:</p>
          <PolicyList items={[
            "Świadczenia usług dostępnych w Portalu (rejestracja, publikacja ogłoszeń, aplikowanie na oferty).",
            "Komunikacji z Użytkownikami (odpowiedzi na zapytania, powiadomienia).",
            "Zapewnienia bezpieczeństwa i zapobiegania nadużyciom.",
            "Analizy statystycznej i doskonalenia usług Portalu.",
            "Wypełnienia obowiązków prawnych.",
          ]} />
        </PolicySection>

        <PolicySection number={4} title="Podstawa prawna przetwarzania">
          <p>Przetwarzanie danych odbywa się na podstawie:</p>
          <PolicyList items={[
            "Zgody Użytkownika (art. 6 ust. 1 lit. a RODO).",
            "Wykonania umowy lub podjęcia działań przed jej zawarciem (art. 6 ust. 1 lit. b RODO).",
            "Prawnie uzasadnionego interesu administratora (art. 6 ust. 1 lit. f RODO).",
          ]} />
        </PolicySection>

        <PolicySection number={5} title="Udostępnianie danych">
          <p>Dane osobowe mogą być udostępniane:</p>
          <PolicyList items={[
            <><strong>Pracodawcom</strong> &ndash; w przypadku aplikowania na ofertę pracy (imię, nazwisko, CV, list motywacyjny).</>,
            <><strong>Dostawcom usług</strong> &ndash; podmiotom świadczącym usługi hostingowe, analityczne i e-mail na rzecz Portalu.</>,
            <><strong>Organom publicznym</strong> &ndash; w przypadkach wymaganych przez prawo.</>,
          ]} />
          <p className="mt-4">Dane nie są sprzedawane ani udostępniane podmiotom trzecim w celach marketingowych.</p>
        </PolicySection>

        <PolicySection number={6} title="Okres przechowywania danych">
          <p>
            Dane osobowe przechowujemy przez okres niezbędny do realizacji celów, dla których zostały zebrane,
            lub do momentu wycofania zgody przez Użytkownika. Po usunięciu konta dane są usuwane w ciągu 30 dni,
            z wyjątkiem danych, które jesteśmy zobowiązani przechowywać na podstawie przepisów prawa.
          </p>
        </PolicySection>

        <PolicySection number={7} title="Prawa Użytkownika">
          <p>Każdy Użytkownik ma prawo do:</p>
          <PolicyList items={[
            "Dostępu do swoich danych osobowych.",
            "Sprostowania nieprawidłowych danych.",
            <>Usunięcia danych (&quot;prawo do bycia zapomnianym&quot;).</>,
            "Ograniczenia przetwarzania danych.",
            "Przenoszenia danych.",
            "Wniesienia sprzeciwu wobec przetwarzania.",
            "Wycofania zgody w dowolnym momencie.",
          ]} />
          <p className="mt-4">
            W celu skorzystania z powyższych praw prosimy o kontakt pod adresem:{" "}
            <a href="mailto:kontakt@praca-w-szwajcarii.ch" className="text-[#E1002A] hover:underline">
              kontakt@praca-w-szwajcarii.ch
            </a>.
          </p>
        </PolicySection>

        <PolicySection number={8} title="Pliki cookies">
          <p>
            Portal wykorzystuje pliki cookies w celu zapewnienia prawidłowego działania serwisu,
            zapamiętywania preferencji Użytkownika oraz analizy statystycznej. Użytkownik może zarządzać
            plikami cookies za pomocą ustawień swojej przeglądarki internetowej.
          </p>
          <p className="mt-4">Stosujemy następujące rodzaje cookies:</p>
          <PolicyList items={[
            <><strong>Niezbędne</strong> &ndash; wymagane do działania Portalu (autoryzacja, sesja).</>,
            <><strong>Funkcjonalne</strong> &ndash; zapamiętywanie preferencji Użytkownika.</>,
            <><strong>Analityczne</strong> &ndash; zbieranie danych o sposobie korzystania z Portalu.</>,
          ]} />
        </PolicySection>

        <PolicySection number={9} title="Bezpieczeństwo danych">
          <p>
            Stosujemy odpowiednie środki techniczne i organizacyjne w celu ochrony danych osobowych
            przed nieuprawnionym dostępem, utratą, zniszczeniem lub modyfikacją, w tym szyfrowanie
            połączenia (SSL/TLS) oraz bezpieczne przechowywanie haseł.
          </p>
        </PolicySection>

        <PolicySection number={10} title="Zmiany polityki prywatności">
          <p>
            Zastrzegamy sobie prawo do zmiany niniejszej polityki prywatności. O istotnych zmianach
            Użytkownicy zostaną poinformowani za pośrednictwem Portalu. Aktualna wersja polityki
            prywatności jest zawsze dostępna pod adresem{" "}
            <a href="/polityka-prywatnosci" className="text-[#E1002A] hover:underline">
              Praca w Szwajcarii.com/polityka-prywatnosci
            </a>.
          </p>
        </PolicySection>

        <PolicySection number={11} title="Kontakt">
          <p>
            W sprawach związanych z ochroną danych osobowych prosimy o kontakt:{" "}
            <a href="mailto:kontakt@praca-w-szwajcarii.ch" className="text-[#E1002A] hover:underline">
              kontakt@praca-w-szwajcarii.ch
            </a>.
          </p>
        </PolicySection>
      </article>
    </div>
  );
}

function PolicySection({ number, title, children }: { number: number; title: string; children: React.ReactNode }) {
  return (
    <section className="mt-10 first:mt-0">
      <h2 className="font-display text-[1.25rem] md:text-[1.4rem] font-bold text-[#0D2240] mb-3">
        <span className="text-[#E1002A] mr-2">{number}.</span>
        {title}
      </h2>
      <div className="text-[#555] space-y-3">{children}</div>
    </section>
  );
}

function PolicyList({ items }: { items: React.ReactNode[] }) {
  return (
    <ul className="space-y-2 mt-3">
      {items.map((item, i) => (
        <li key={i} className="flex gap-3">
          <span className="text-[#E1002A] flex-shrink-0 mt-1.5 w-1.5 h-1.5 bg-[#E1002A] rounded-full" />
          <span className="flex-1">{item}</span>
        </li>
      ))}
    </ul>
  );
}
