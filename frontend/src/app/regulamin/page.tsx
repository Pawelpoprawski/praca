import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Regulamin - Praca w Szwajcarii",
  description: "Regulamin korzystania z portalu Praca w Szwajcarii.com",
};

export default function RegulaminPage() {
  return (
    <div className="bg-white">
      {/* Hero strip — navy */}
      <section className="bg-[#0D2240] text-white py-12 md:py-16 relative overflow-hidden">
        <div className="absolute inset-0 hays-pattern" />
        <div className="relative z-10 max-w-[1200px] mx-auto px-6">
          <span className="hays-red-line" />
          <h1 className="font-display text-[2rem] md:text-[2.5rem] font-extrabold leading-tight">
            Regulamin
          </h1>
          <p className="text-white/70 mt-2 text-[0.95rem]">
            Ostatnia aktualizacja: 17 lutego 2026 r.
          </p>
        </div>
      </section>

      {/* Content */}
      <article className="max-w-[800px] mx-auto px-6 py-12 md:py-16 text-[#1A1A1A] leading-[1.75]">
        <Section number={1} title="Postanowienia ogólne">
          <p>
            Niniejszy regulamin określa zasady korzystania z portalu internetowego dostępnego pod adresem{" "}
            <strong>Praca w Szwajcarii.com</strong> (dalej: &quot;Portal&quot;), którego właścicielem i operatorem jest portal
            Praca w Szwajcarii.com. Kontakt z administratorem możliwy jest pod adresem e-mail:{" "}
            <a href="mailto:kontakt@polacyszwajcaria.com" className="text-[#E1002A] hover:underline">
              kontakt@polacyszwajcaria.com
            </a>.
          </p>
          <p>Korzystanie z Portalu oznacza akceptację niniejszego regulaminu w całej jego treści.</p>
        </Section>

        <Section number={2} title="Definicje">
          <List items={[
            <><strong>Portal</strong> &ndash; serwis internetowy Praca w Szwajcarii.com umożliwiający publikowanie i przeglądanie ofert pracy w Szwajcarii.</>,
            <><strong>Użytkownik</strong> &ndash; każda osoba korzystająca z Portalu, w tym Pracownik i Pracodawca.</>,
            <><strong>Pracownik</strong> &ndash; osoba fizyczna poszukująca pracy, która zarejestruje konto w roli pracownika.</>,
            <><strong>Pracodawca</strong> &ndash; osoba fizyczna, prawna lub jednostka organizacyjna publikująca oferty pracy.</>,
            <><strong>Ogłoszenie</strong> &ndash; oferta pracy opublikowana na Portalu przez Pracodawcę.</>,
          ]} />
        </Section>

        <Section number={3} title="Zasady korzystania z Portalu">
          <p>Użytkownik zobowiązuje się do:</p>
          <List items={[
            "Podawania prawdziwych i aktualnych danych podczas rejestracji oraz publikacji ogłoszeń.",
            "Korzystania z Portalu zgodnie z obowiązującym prawem oraz dobrymi obyczajami.",
            "Niepodejmowania działań mogących zakłócić działanie Portalu lub naruszać prawa innych Użytkowników.",
            "Nieumieszczania treści o charakterze bezprawnym, oszukańczym, dyskryminującym lub wprowadzającym w błąd.",
          ]} />
        </Section>

        <Section number={4} title="Rejestracja i konto">
          <p>
            Rejestracja konta jest dobrowolna i bezpłatna. Użytkownik może zarejestrować się jako Pracownik lub Pracodawca.
            Każdy Użytkownik może posiadać jedno konto. Administrator zastrzega sobie prawo do zablokowania lub
            usunięcia konta w przypadku naruszenia regulaminu.
          </p>
        </Section>

        <Section number={5} title="Publikacja ogłoszeń">
          <p>
            Pracodawca może publikować ogłoszenia o pracę w ramach przydzielonego limitu. Ogłoszenia podlegają moderacji
            i mogą zostać odrzucone w przypadku naruszenia regulaminu. Portal zastrzega sobie prawo do edycji lub
            usunięcia ogłoszeń niezgodnych z regulaminem.
          </p>
        </Section>

        <Section number={6} title="Odpowiedzialność">
          <p>Portal pełni rolę pośrednika między Pracownikami a Pracodawcami. Nie ponosimy odpowiedzialności za:</p>
          <List items={[
            "Treść ogłoszeń publikowanych przez Pracodawców.",
            "Przebieg i wynik procesów rekrutacyjnych.",
            "Działania Użytkowników podejmowane poza Portalem.",
            "Przerwy w działaniu Portalu wynikające z przyczyn technicznych lub siły wyższej.",
          ]} />
        </Section>

        <Section number={7} title="Prawa własności intelektualnej">
          <p>
            Wszelkie treści zamieszczone na Portalu, w tym teksty, grafiki, logo i oprogramowanie, stanowią
            własność portalu Praca w Szwajcarii.com lub ich autoryzowanych dostawców i są chronione prawem autorskim.
            Kopiowanie, rozpowszechnianie lub wykorzystywanie tych treści bez zgody jest zabronione.
          </p>
        </Section>

        <Section number={8} title="Zmiany regulaminu">
          <p>
            Portal zastrzega sobie prawo do zmiany niniejszego regulaminu. O istotnych zmianach Użytkownicy
            zostaną poinformowani za pośrednictwem Portalu. Dalsze korzystanie z Portalu po wprowadzeniu zmian
            oznacza ich akceptację.
          </p>
        </Section>

        <Section number={9} title="Kontakt">
          <p>
            W sprawach związanych z regulaminem prosimy o kontakt pod adresem:{" "}
            <a href="mailto:kontakt@polacyszwajcaria.com" className="text-[#E1002A] hover:underline">
              kontakt@polacyszwajcaria.com
            </a>.
          </p>
        </Section>
      </article>
    </div>
  );
}

function Section({ number, title, children }: { number: number; title: string; children: React.ReactNode }) {
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

function List({ items }: { items: React.ReactNode[] }) {
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
