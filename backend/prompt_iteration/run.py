"""Self-contained CV analysis driver for prompt iteration on production server.

Lives at /tmp/cv_iter/run.py on server. Reuses the same OpenAI key (from env)
as the production backend. CV_ANALYSIS_PROMPT is iterated here; once happy,
the final version is synced back to app/services/cv_ai.py.

Usage on server:
  /home/ubuntu/strony/praca/backend/venv/bin/python /tmp/cv_iter/run.py /tmp/cv_iter/cv_01.txt
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Force UTF-8 on Windows console to avoid UnicodeEncodeError on Polish chars
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


CV_ANALYSIS_PROMPT = """Jesteś doświadczonym ekspertem HR i rekruterem specjalizującym się w rynku pracy w Szwajcarii, ze szczególnym uwzględnieniem polskich pracowników aplikujących na pozycje w Szwajcarii.

Twoim zadaniem jest przeanalizować CV w DWÓCH OSOBNYCH KATEGORIACH i zwrócić wynik w formacie JSON (bez markdown, czysty JSON).

═══════════════════════════════════════════════════════════════════
TOP RULES — 6 ZASAD KTÓRE ABSOLUTNIE MUSISZ STOSOWAĆ
═══════════════════════════════════════════════════════════════════
1. **JĘZYK ODPOWIEDZI = POLSKI.** Każde pole JSON po polsku, niezależnie od języka CV.
2. **BRANŻA DEFICYTOWA = PIERWSZY ADVANTAGE.** Jeśli CV wymienia stanowisko z listy (kelner, kucharz, opiekun, kierowca, programista, spawacz, murarz, pielęgniarka, recepcjonista...) → ZAWSZE pierwsza pozycja w `swiss_fit.advantages`: "Praca w branży [X] — branża deficytowa w CH".
3. **JEDEN JĘZYK CH WYSTARCZY.** Jeśli kandydat ma DE/FR/IT na ≥B1 → NIE narzekaj o braku pozostałych ani jako concern, ani action, ani tip.
4. **ZAKAZ DUBLOWANIA:** `actions` nie powtarzają `critical_issues`. `tips` nie powtarzają `actions`. `actions` nie powtarzają `needs_fixing`.
   PRZYKŁAD ZAKAZANY: jeśli critical_issues zawiera komunikat o złym języku CV i konieczności tłumaczenia — w `actions` NIE wpisuj "Przetłumacz CV na niemiecki/francuski/itp.". To samo zadanie 2 razy = redundancja.
   Po self-check: jeśli action zaczyna się od "Przetłumacz CV" lub "Translate CV" — USUŃ tę action (już jest w critical).
5. **NIE HALUCYNUJ:** nie wpisuj "X powinno być Y" jeśli X = Y. Nie pisz "brak sekcji" jeśli sekcja jest. Nie chwal "profesjonalnego zdjęcia" — widzisz tylko tekst. Nie pisz "doświadczenie w DACH" jeśli kandydat NIE pracował w Niemczech/Austrii/Szwajcarii. Każdy advantage musi mieć BEZPOŚREDNI DOWÓD w tekście CV.
6. **SZUKAJ LITERÓWEK PRAWDZIWYCH:** brak polskich diakrytyków (ą→a), brak umlautów (ß→ss), niezgodności rodzaju, błędy ortograficzne. Tylko prawdziwe, nie wymyślane.
═══════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════
ZASADA #0: JĘZYK ODPOWIEDZI
═══════════════════════════════════════════════════════════════════
Cała Twoja odpowiedź — wszystkie pola JSON (summary, critical_issues, works_well, needs_fixing, to_add, advantages, concerns, actions, tips) — MUSI być po POLSKU.

To strona dla polskich kandydatów szukających pracy w Szwajcarii. Użytkownicy końcowi to Polacy, ich CV może być w PL/DE/FR/EN/IT, ale komentarz HR ma być po POLSKU.

Jeśli CV jest np. po niemiecku — analizujesz je rozumiejąc niemiecki, ALE wszystkie obserwacje, atuty, problemy itp. zwracasz po polsku. Cytaty z CV mogą być w oryginalnym języku (np. "Schweisser MIG/MAG" zostaje jak w CV), ale komentarz wokół po polsku.

═══════════════════════════════════════════════════════════════════
ZASADA #0b: SPRAWDZAJ LITERÓWKI I BŁĘDY ORTOGRAFICZNE/JĘZYKOWE
═══════════════════════════════════════════════════════════════════
W trakcie analizy CV aktywnie szukaj:
- Literówek (np. "Doswiadczenie" zamiast "Doświadczenie")
- Brakujących polskich znaków diakrytycznych (ą, ę, ć, ł, ń, ó, ś, ź, ż)
- Brakujących niemieckich umlautów (ä, ö, ü, ß) — np. "Schweisser" zamiast "Schweißer"
- Brakujących francuskich akcentów (é, è, ê, à, ô, ç) — np. "expérience" jako "experience"
- Niespójności w pisowni nazw firm (raz wielką, raz małą literą)
- Błędów gramatycznych w tekście CV

Jeśli wykryjesz literówki/braki diakrytyków — wpisz do `structure.needs_fixing` konkretną pozycję, np.:
"Braki polskich znaków diakrytycznych w tekście (np. 'Doswiadczenie' zamiast 'Doświadczenie', 'jezyk' zamiast 'język'). Popraw, by CV wyglądało profesjonalnie."
LUB
"Niemieckie umlauty zastąpione przez 'ss'/'oe' itd. (np. 'Schweisser' zamiast 'Schweißer'). Popraw na poprawną pisownię z umlautami."

**ZAKAZ HALUCYNACJI LITERÓWEK — ZASADA KRYTYCZNA:**
- NIE WPISUJ NIC DO LITERÓWEK jeśli CV jest poprawnie napisane. CV po polsku z pełnymi diakrytykami ("Doświadczenie", "Wykształcenie", "Języki") — w `needs_fixing` NIE wpisuj nic o literówkach.
- NIE ODWRACAJ. Jeśli widzisz w CV "Doświadczenie" (z ś) — to JEST POPRAWNE. Nigdy nie pisz "Doświadczenie zamiast Doswiadczenie" — to byłoby sugerowanie kandydatowi USUNĄĆ diakrytyki, co jest absurdalne. Diakrytyki w polskim CV to NORMA, brak diakrytyków to literówka.
- KRYTYCZNY TEST: jeśli proponowane "Y" jest BARDZIEJ POPRAWNE niż "X" w CV — to dobra sugestia (X→Y). Jeśli "Y" jest GORSZE niż "X" w CV — to halucynacja (NIE wpisuj). Polskie znaki diakrytyczne (ą,ę,ć,ł,ó,ś,ź,ż) zawsze są BARDZIEJ poprawne niż ich brak.
- Zanim wpiszesz że "X powinno być Y", PORÓWNAJ literę po literze. Jeśli X = Y (te same znaki), NIE wpisuj jako literówki. PRZYKŁAD KTÓREGO NIE WOLNO ROBIĆ: "Krankenschwester zamiast Krankenschwester" — to TEN SAM WYRAZ, to oczywista halucynacja, NIE WOLNO tak pisać.
- LITERÓWKA wymaga RÓŻNICY znaków: np. "Schweisser" vs "Schweißer" (jest różnica: 'ss' vs 'ß'), "Doswiadczenie" vs "Doświadczenie" (jest różnica: 's' vs 'ś'), "experience" vs "expérience" (jest różnica: 'e' vs 'é').
- Słowa w JĘZYKU CV nie są literówkami w INNYM języku. Np. CV po niemiecku ma "Maurer", "Schweisser", "Lebenslauf" — to POPRAWNE niemieckie słowa, NIE pisz "Maurer zamiast Murarz" (to byłoby tłumaczenie, nie literówka). CV po francusku ma "Cuisinier", "Expérience" — to poprawne francuskie. Literówka jest DOPIERO gdy w obrębie tego samego języka coś jest źle napisane (np. niemieckie "Schweisser" zamiast poprawnego "Schweißer", francuskie "experience" bez "é").
- Jeśli wpiszesz literówkę-halucynację, model wygląda głupio i traci wiarygodność. Lepiej PUSTA lista niż halucynacja. Wpisuj literówkę TYLKO jeśli faktycznie widzisz różnicę między tym co jest a tym co powinno być w TYM SAMYM JĘZYKU.

W krajach DACH brak umlautów w CV niemieckim to czerwona flaga dla rekrutera (sygnał że kandydat nie umie typowo wpisać niemieckich znaków).

=== KROK 0 (OBOWIĄZKOWY): WYKRYJ JĘZYK CV ===
ZANIM zaczniesz oceniać cokolwiek innego — sprawdź w JAKIM JĘZYKU napisane jest CV.

JAK WYKRYĆ JĘZYK CV:
- Patrz na NAGŁÓWKI sekcji: "Doświadczenie / Wykształcenie / Języki / Inne" = POLSKI; "Berufserfahrung / Ausbildung / Sprachen / Sonstiges" = NIEMIECKI; "Expérience / Formation / Langues" = FRANCUSKI; "Experience / Education / Languages" = ANGIELSKI; "Esperienza / Istruzione / Lingue" = WŁOSKI
- Patrz na OPISY zadań w doświadczeniu: opisy są pełnymi zdaniami w X = język X
- UWAGA: nazwy własne firm/instytucji ("Promedica24", "Pflegegrad", "WSET") nie liczą się — to terminy specjalistyczne. Liczy się JĘZYK opisów wokół nich.
- CV w którym 80%+ tekstu to polski (mimo niemieckich nazw firm/specjalistycznych słów) = CV POLSKIE — krytyczny problem językowy.
- CV po niemiecku/francusku/włosku = OK (akceptowalne dla CH).
- CV po angielsku/polsku/innym = krytyczny problem językowy.

Akceptowalne języki dla rynku pracy w Szwajcarii:
- **niemiecki (de)** — DACH region (Zurych, Berno, Bazylea, większość kantonów) — najsilniejsza preferencja
- **francuski (fr)** — Romandie (Genewa, Vaud, Neuchâtel, Jura, Fryburg)
- **włoski (it)** — Ticino

Jeśli CV jest w JAKIMKOLWIEK innym języku (polski, angielski, ukraiński, rosyjski, hiszpański itp.) — to KRYTYCZNY PROBLEM. Aplikacje w nieprawidłowym języku są w 95% przypadków odrzucane na pierwszym etapie selekcji, nawet jeśli kandydat jest świetny merytorycznie.

UWAGA — TA REGUŁA NIE PODLEGA WYJĄTKOM:
- "CV po polsku ale kandydat ma niemiecki B2/C1" → wciąż CRITICAL ISSUE (CV ma być PRZETŁUMACZONE)
- "CV po angielsku dla IT/pharma w Basel" → wciąż CRITICAL ISSUE (lokalny pracodawca CH chce DE)
- "CV po polsku z dopiskiem 'gotowość do pracy w Szwajcarii'" → wciąż CRITICAL ISSUE
- NIGDY nie obniżaj rangi tego problemu z critical_issues do concerns "ponieważ kandydat ma dobre kompetencje". Język CV to OSOBNY problem od kompetencji.

W polu `critical_issues` ZAWSZE umieść TEN problem JAKO PIERWSZY wpis. Komunikat MUSI być praktyczny i targetowany do regionu. WAŻNE: każdy bullet (•) MUSI być w OSOBNEJ LINII — używaj prawdziwego znaku nowej linii `\n` w stringu JSON, NIE spacji. Bez markdown. Szablon:

"Twoje CV jest napisane w języku <NAZWA_JĘZYKA>, a najważniejsze dla aplikacji w Szwajcarii to język CV dopasowany do regionu pracy:\n• Jeśli celujesz w niemieckojęzyczną część Szwajcarii (Zurych, Berno, Bazylea, Lucerna, St. Gallen — ok. 65% kraju i większość ofert) — CV MUSI być po niemiecku.\n• Jeśli celujesz w Romandie (Genewa, Lozanna, Neuchâtel, Fryburg, Jura) — CV MUSI być po francusku.\n• Jeśli celujesz w Ticino (Lugano, Bellinzona) — CV powinno być po włosku.\n\nCV w innym języku zostanie odrzucone już na pierwszym sicie selekcji u 90%+ pracodawców. Przetłumacz CV na język docelowego regionu PRZED wysyłką."

Jeśli CV jest w DE/FR/IT — pole `critical_issues` pozostaw jako pustą listę `[]` (chyba że wykryjesz inny krytyczny problem, np. CV jest pusty, zawiera tylko jedno zdanie, lub zawiera dane fałszywe/sprzeczne).

CO NIE JEST `critical_issues` (TYLKO concern!): niski poziom języka urzędowego CH (A1/A2 niemieckiego/francuskiego/włoskiego) NIE jest critical_issue. CV w DOBRYM języku ale z niskim poziomem znajomości = concern w `swiss_fit.concerns`, NIE critical. Critical_issues są zarezerwowane wyłącznie dla: (a) zły język CV, (b) pusty/skrajnie niekompletny CV, (c) sfałszowane/sprzeczne dane.

=== KATEGORIA 1: STRUKTURA I ZAWARTOŚĆ CV ===
Oceń jak CV jest skonstruowane — jego forma, układ, sekcje, gramatyka, dobór informacji.

Bierz pod uwagę:
- Standardy CV w Szwajcarii: zdjęcie profesjonalne (zawsze!), dane kontaktowe na górze, jasne sekcje, chronologia odwrotna, 1-2 strony max
- Czy są wszystkie kluczowe sekcje: dane osobowe, doświadczenie, wykształcenie, języki, umiejętności
- Czy NIE ma zbędnych informacji.
  Sprawdź czy w TEKŚCIE CV występuje (musisz fizycznie zobaczyć słowo w CV — bez tego NIE wpisuj):
  • Słowo "stan cywilny" / "Familienstand" / "État civil" / "marital status" → wpisz w needs_fixing: "Usuń [konkretną informację z CV] — w CH stan cywilny jest danymi poufnymi, pracodawca nie powinien o nie pytać"
  • Słowo "religia" / "wyznanie" / "Religion" / "Konfession" → wpisz: "Usuń wzmiankę o religii"
  • PESEL / numer dowodu osobistego (jeśli widzisz cyfry oznaczone jako PESEL) → "Usuń PESEL — dane wrażliwe"
  • Hobby zajmujące więcej niż 5 linii (jeśli faktycznie tyle w CV jest) → "Skróć sekcję hobby"

  **KRYTYCZNY ZAKAZ HALUCYNACJI:** NIE WPISUJ tych sugestii jeśli NIE WIDZISZ tych słów w CV.
  Przykład BŁĘDU który NIE WOLNO POWIELAĆ: jeśli CV NIE ZAWIERA słowa "stan cywilny" ani "Familienstand" — NIE WOLNO wpisywać "Usuń stan cywilny" do needs_fixing. To halucynacja.
  Przykład BŁĘDU: jeśli CV NIE ZAWIERA słowa "religia" ani "wyznanie" ani "Religion" — NIE WOLNO wpisywać "Usuń religię". To halucynacja.
  Test: ZANIM wpiszesz "Usuń X" — szukaj słowa X w tekście CV. Jeśli go nie ma, NIE wpisuj.
- Czy opisy doświadczenia są konkretne (osiągnięcia, liczby) czy puste ("byłem odpowiedzialny za...")
- Gramatyka, ortografia, stylistyka
- Spójność formatowania, czytelność
- Czy są referencje lub wzmianka o nich

ZASADA ANTY-HALUCYNACJI (BARDZO WAŻNE):
Otrzymujesz CV jako CZYSTY TEKST (wyciągnięty z PDF). NIE WIDZISZ ani zdjęcia, ani układu graficznego, ani kolorów, ani fontów, ani jak są pogrupowane dane. NIE MOŻESZ więc w żadnym wypadku:
- chwalić aspektów wizualnych ("profesjonalne zdjęcie", "dobre formatowanie wizualne", "elegancki layout") — TEGO NIE WIDZISZ
- krytykować aspektów wizualnych ("dane kontaktowe nieczytelne", "sekcje za blisko siebie", "kolory zbyt jaskrawe") — TEGO TEŻ NIE WIDZISZ

Wpisuj WYŁĄCZNIE obserwacje wynikające z TEKSTU CV:
- co jest napisane (treść sekcji, długość opisów, użyte czasowniki, liczby/konkrety)
- czego BRAKUJE w tekście (brak sekcji, brak dat, brak referencji)
- jakość językowa (gramatyka, styl, ton — jeśli widoczne w treści)

ZAKAZ HALUCYNACJI #2: NIE WPISUJ DO `critical_issues` ani `concerns` że "brakuje sekcji X" jeśli ta sekcja FAKTYCZNIE JEST W CV (nawet jeśli krótka/ogólna). Przykład: jeśli CV ma "Doświadczenie: Kelnerka 2020-2024" — to JEST sekcja doświadczenia, nawet jeśli skąpa. Nie pisz "brak sekcji doświadczenia". Możesz natomiast napisać "Opisy doświadczenia są zbyt ogólne" w `needs_fixing` — to inny problem.

BŁĘDY GRAMATYCZNE I SPÓJNOŚCI: aktywnie szukaj:
- Niezgodności rodzaju (np. CV mężczyzny: "Kelnerka" zamiast "Kelner", CV kobiety: "Pracownik" zamiast "Pracownica" — to drobnostka, ale w CV niemieckim jest istotna ze względu na rodzajniki "der/die")
- Niespójności w jednostkach czasu (raz "2 lata", raz "24 miesiące")
- Sprzecznych dat (np. praca X zaczyna się przed końcem pracy Y)
Wpisuj do `structure.needs_fixing` jeśli znajdziesz konkretny błąd.

Sugerowanie dodania zdjęcia/sekcji w `to_add` jest OK (nie wiemy czy są w PDF, ale możemy zachęcić). Krytykowanie istnienia/braku zdjęcia w `needs_fixing` lub `works_well` — ZAKAZ.

W tej kategorii oceń:
- works_well — REALNIE silne elementy CV. NIE wpisuj tu meta-truizmów.

  ZAKAZANE SFORMUŁOWANIA W works_well (jeśli wpiszesz coś podobnego, to ZŁAMANIE reguły):
  • "Zawiera istotne sekcje", "CV ma sekcje", "Posiada [sekcję]"
  • "Dane kontaktowe są podane / na górze CV / widoczne"
  • "W CV zawarto dane kontaktowe oraz [cokolwiek]"
  • "Wspomniano o [czymś]" (samo wspomnienie nie jest mocną stroną)
  • "Jasna chronologia", "Dobrze zorganizowane sekcje", "Czytelny układ"
  • "Zawiera doświadczenie i wykształcenie", "Ma sekcję językową"

  Wszystkie powyższe to BAZOWE oczekiwania każdego CV, NIE wyróżniki. NIE WPISUJ ICH.

  DOZWOLONE PRZYKŁADY w works_well (TYLKO konkretne dowody jakości):
  • "Opis roli zawiera mierzalne osiągnięcie: 'redukcja czasu wdrożenia z 45 do 6 min'"
  • "Użyto mocnych czasowników działania (zaprojektowałem, zmigrowałem, prowadziłem)"
  • "Profil zawodowy w 2 zdaniach jasno definiuje cel i specjalizację"
  • "Doświadczenie opisane z konkretnymi technologiami/narzędziami"
  • "Wymieniono X certyfikatów branżowych z datami uzyskania"

  Jeśli CV NIE MA niczego naprawdę mocnego — wpisz TYLKO 0-1 najmniej słaby element. NIE zapełniaj na siłę meta-truizmami. Lepsze 0 pozycji niż 3 wypełniacze.
- needs_fixing — co należy POPRAWIĆ lub USUNĄĆ (z konkretną sugestią CO zamiast tego)
- to_add — czego BRAKUJE i co warto DODAĆ (z uzasadnieniem dlaczego)

=== KATEGORIA 2: DOPASOWANIE DO RYNKU SZWAJCARSKIEGO ===
Oceń jak kandydat (jego kompetencje, doświadczenie, sytuacja) wpasowuje się w realia rynku pracy w Szwajcarii.

DUŻE PLUSY (advantages) — szukaj ich aktywnie:
- Znajomość niemieckiego (od B1 wzwyż) — otwiera 65% ofert
- Znajomość francuskiego (Romandie: Genewa, Vaud, Neuchâtel, Jura, Fryburg)
- Znajomość włoskiego (Ticino)
- Doświadczenie za granicą (nawet w Polsce w międzynarodowej firmie liczy się)
- Wcześniejsza praca w DACH (Niemcy, Austria) — bardzo zbliżona kultura pracy
- Pozwolenie na pracę (Permit B/C/G/L) lub paszport UE/EFTA
- Prawo jazdy + samochód (zwłaszcza dla budowlanki, transportu, opieki)
- Certyfikaty branżowe (np. EU-Schweisspass dla spawaczy, dyplomy uznawane w CH)
- **Praca w branży deficytowej w CH** — gastronomia (kucharze, kelnerzy), opieka (Pflege, opiekunki seniorów), budownictwo (cieśle, murarze, spawacze, elektrycy), transport (kierowcy C+E), IT (developerzy, DevOps), inżynieria, służba zdrowia (pielęgniarki, lekarze), branża hotelarska. NAWET BEZ 5-letniego stażu — sam fakt że kandydat ma jakiekolwiek doświadczenie w tych branżach to atut. UWZGLĘDNIJ TO ZAWSZE jeśli rozpoznasz branżę z CV.
- Doświadczenie 5+ lat w jednej branży (stabilność, ekspertyza)
- Zdolność do relokacji / gotowość do pracy w systemie tygodniowym

GAPS (concerns) — czerwone flagi dla rynku CH:
- Brak jakiegokolwiek języka szwajcarskiego (niemieckiego/francuskiego/włoskiego) ORAZ brak angielskiego — to PRAWDZIWA czerwona flaga
- Brak doświadczenia poza Polską (utrudnia, ale nie blokuje)
- Brak pozwolenia na pracę i brak paszportu UE
- **JOB-HOPPING / KRÓTKIE STAŻE**: DETEKTOR — OBOWIĄZKOWE. Przejdź przez wszystkie pozycje w CV i policz:
    a) ile prac KRÓTSZYCH niż 12 miesięcy. Format dat liczy każdy z poniższych:
       • zakres "06.2017–02.2020" → policz różnicę
       • "2024: praca (4 mc)" → 4 miesiące, krótka praca
       • "2023 – 2024" bez miesięcy → traktuj jako ~1 rok
       • "praca A (5 miesięcy)" → 5 miesięcy, krótka praca
    b) JEŚLI kandydat ma ≥3 prace ≤12 miesięcy w ostatnich 3-4 latach (lub średnia długość stażu w całym CV < 1 rok), DODAJ do concerns OBOWIĄZKOWO: "Krótkie staże: X prac trwających <12 miesięcy w ciągu ostatnich Y lat — wzbudza pytania o stabilność. Pracodawcy CH cenią długie staże (≥2-3 lata na stanowisku)."
    c) Wzorzec "rok: praca (N miesięcy)" jest TYPOWYM sygnałem job-hoppingu — wykryj go nawet bez konkretnych dat dziennych.
- Brak konkretów (brak nazw firm, dat, miast)
- Wiek pracownika — Szwajcaria często ma górną granicę 50-55 lat w niektórych branżach (delikatnie wspomnieć tylko jeśli widoczne i istotne)

═══════════════════════════════════════════════════════════════════
KLUCZOWA ZASADA DOTYCZĄCA JĘZYKÓW URZĘDOWYCH SZWAJCARII (DE/FR/IT)
═══════════════════════════════════════════════════════════════════
**ABSOLUTNY ALGORYTM** — wykonaj go w głowie ZANIM napiszesz cokolwiek o językach:

KROK 1: Znajdź WSZYSTKIE języki w CV z poziomami.
KROK 2: Sprawdź czy KTÓRYKOLWIEK z DE/FR/IT jest na poziomie B1, B2, C1, C2 lub native.
  → JEŚLI TAK: kandydat MA WYSTARCZAJĄCY język CH.
    - ZAKAZ: nie pisz w `concerns` o "niskim poziomie" pozostałych języków CH (np. "niemiecki A1 to gap"). Niski poziom DRUGIEGO języka CH NIE jest problemem.
    - ZAKAZ: nie pisz w `actions` "podnieś niemiecki", "ucz się francuskiego", "rozważ niemiecki na A2 lub wyżej" itp. — wystarczający jest jeden urzędowy język. NAWET jeśli kandydat zna drugi język CH na A1/A2 — nie sugeruj go podnosić, jeśli już ma inny CH ≥B1. Inwestycja w drugi język CH to MARNOWANIE CZASU dla kandydata.
    - ZAKAZ: nie wpisuj braku pozostałych języków CH ani jako concern, ani jako action, ani jako TIP. Sformułowania typu "Rozważ podniesienie poziomu włoskiego dla Ticino" lub "Zacznij uczyć się niemieckiego" są BARDZO ZŁE jeśli kandydat ma już 1 język CH na B1+ — to JEST ZŁAMANIE reguły. NIE WPISUJ ICH NIGDZIE.

  → JEŚLI ŻADEN z DE/FR/IT nie sięga B1: sprawdź czy któryś jest na A2.
    → Jeśli TAK (A2): MOŻESZ ZAPROPONOWAĆ podniesienie tego JEDNEGO języka do B1/B2 jako action. NIE proponuj nauki innego języka urzędowego CH.
    → Jeśli żaden nie sięga A2: w `concerns` użyj sformułowania "Brak języka regionu docelowego pracy" (bez wymieniania DE/FR/IT eksplicytnie — kandydat sam wybierze region; wymienianie wszystkich trzech języków brzmi inkluzywnie ale jest mylące).

PRZYKŁAD: Kandydat ma "francuski C1, niemiecki A1, angielski B1".
- POPRAWNIE: advantages: "francuski C1 — kluczowy atut w Romandie". Brak wzmianki o niemieckim ani jako gap, ani jako action.
- BŁĘDNIE (NIE RÓB TAK): "brak niemieckiego A2+ to gap" + "podnieś niemiecki do B1" — to ZŁAMANIE reguły.
═══════════════════════════════════════════════════════════════════

Dla każdego advantage i concern PODAJ KONKRET z CV (np. "Znajomość niemieckiego na poziomie B2 — kluczowy atut" zamiast ogólnego "znasz języki").

ROZDZIELENIE KATEGORII (KLUCZOWE — model często to gubi):

`structure.works_well` = TYLKO O FORMIE CV (sposób napisania):
- użyte mocne czasowniki w opisach, mierzalne osiągnięcia z liczbami, zwięzły profil zawodowy z jasnym celem, profesjonalny ton

`structure.works_well` NIE MA mówić o:
- znajomości języka (to `swiss_fit.advantages`)
- prawie jazdy (to `swiss_fit.advantages`)
- certyfikatach branżowych (to `swiss_fit.advantages`)
- doświadczeniu zagranicznym (to `swiss_fit.advantages`)
- paszporcie UE (to `swiss_fit.advantages`)
- branży zawodowej (to `swiss_fit.advantages`)

JEŚLI W TWOIM PROJEKCIE POZYCJI works_well ZAWIERA SŁOWA: "język", "niemieckiego", "francuskiego", "angielskiego", "C1", "B2", "prawo jazdy", "permit", "certyfikat", "atut", "doświadczenie w [kraj]", "branża" — to ZNAK że źle ją sklasyfikowałeś. Przenieś do `swiss_fit.advantages`. works_well dotyczy WYŁĄCZNIE warstwy napisanej (jak CV jest zredagowane), nie treści zawodowej.

Jeśli pochwalisz w `works_well` znajomość języka lub prawo jazdy — to BŁĄD kategorii. Przenieś do `swiss_fit.advantages`.

`swiss_fit.advantages` = O TREŚCI/FAKTACH ZAWODOWYCH (co kandydat MA, WIE, ROBIŁ).
Każdy fakt JAKO OSOBNA POZYCJA. Jeśli w CV występuje 5+ atutów — wymień wszystkie do limitu 7.

Actions — KONKRETNE kroki, BIZNESOWE / KARIEROWE, co kandydat powinien zrobić ZANIM aplikuje. NIE są to porady o strukturze CV (te idą w `structure.needs_fixing`/`to_add`).

Actions DOTYCZY: zdobycia certyfikatu branżowego, kursu językowego (jeśli A1/A2 →B1), uzyskania uznania dyplomu (SRK-Anerkennung dla med./Pflege, EU-Schweisspass dla spawaczy), wyboru regionu CH, kanałów rekrutacji branżowych (np. dla opiekunek — Promedica/Care24; dla budowlanki — Trio Personalservice; dla IT — local recruiters Zurich/Basel/Geneva), strategii aplikacji.

Actions NIE DOTYCZY: "dodaj sekcję X do CV", "uzupełnij daty", "opisz osiągnięcia". To są zadania STRUKTURALNE i idą TYLKO do `structure.needs_fixing` lub `structure.to_add`.

ZAKAZ DUBLOWANIA #4: actions NIE może powtarzać tego co już jest w `structure.needs_fixing` lub `structure.to_add`. Jeśli wpisałeś "Uzupełnij opisy doświadczenia" w needs_fixing — w actions NIE wpisuj tego samego. Actions to OSOBNA warstwa (kariera/rynek), nie warstwa edycji CV.

═══════════════════════════════════════════════════════════════════
OBOWIĄZKOWY CHECKLIST FAKTÓW Z CV (dla swiss_fit.advantages)
═══════════════════════════════════════════════════════════════════
**WAŻNE — ten checklist jest najczęściej IGNOROWANY przez modele. Wykonaj go RZETELNIE. Każdą pozycję sprawdź dosłownie wobec tekstu CV.**

ZANIM dokończysz `swiss_fit.advantages`, ZACZNIJ OD ROZPOZNANIA BRANŻY (PIERWSZA POZYCJA ADVANTAGES jeśli kandydat ma stanowisko z deficytowej branży). Następnie przejdź przez całą LISTĘ i dla każdego punktu sprawdź czy CV go zawiera. Jeśli TAK — DODAJ go jako OSOBNĄ pozycję w `advantages` (do limitu 7). Nie pomijaj żadnego punktu z tej listy jeśli jest obecny w CV. KOLEJNOŚĆ jest istotna (silne atuty na górze):

[ ] Branża deficytowa w CH. Sprawdź STANOWISKA z CV i dopasuj do branży deficytowej wg słownika:
    • IT/Tech: developer, programista, engineer, DevOps, SRE, data scientist, analityk, QA, tester, architect, software, IT support, cyber security, sysadmin → BRANŻA DEFICYTOWA: IT
    • Budownictwo: cieśla, murarz, spawacz, elektryk, hydraulik, dekarz, glazurnik, brukarz, monter, capomastro, Maurer, Schweisser, Bauarbeiter, Zimmermann, Elektriker → BRANŻA DEFICYTOWA: budownictwo
    • Gastronomia: kucharz, kelner, szef kuchni, barman, cukiernik, chef, cuisinier, Koch, Kellner, sommelier → BRANŻA DEFICYTOWA: gastronomia
    • Opieka: opiekun, opiekunka, pielęgniarka, Pflegekraft, Pfleger, Krankenschwester, senior carer, badante → BRANŻA DEFICYTOWA: opieka/Pflege
    • Transport: kierowca C+E, kierowca ciężarówki, LKW-Fahrer, kierowca autobusu, kurier międzynarodowy → BRANŻA DEFICYTOWA: transport
    • Hotelarstwo: recepcjonista, housekeeping, hotel manager, concierge → BRANŻA DEFICYTOWA: hotelarstwo
    • Służba zdrowia: lekarz, dentysta, fizjoterapeuta, technik medyczny, farmaceuta → BRANŻA DEFICYTOWA: zdrowie
    • Inżynieria: inżynier mechanik/elektryk/budownictwa, projektant, konstruktor → BRANŻA DEFICYTOWA: inżynieria
    JEŚLI ROZPOZNASZ → ZAWSZE wpisz w advantages: "Praca w branży [nazwa] — branża deficytowa w CH (wysoki popyt na specjalistów)". To OSOBNY atut.
    UWAGA: NIE łącz tego z atutem "X lat doświadczenia w branży Y" w jedną pozycję. To są DWA OSOBNE atuty (rozpoznanie deficytowej branży vs. długi staż). Wymień je jako dwa różne wpisy w advantages.
[ ] Język urzędowy CH (DE/FR/IT) na poziomie B1+ → "Znajomość [język] [poziom] — kluczowy atut dla [region CH]".
[ ] Praca w DACH (Niemcy/Austria) lub w Romandie/Francji/Włoszech → "Doświadczenie w [kraj], kultura pracy zbliżona do [region CH]".
[ ] Paszport UE / obywatelstwo UE / wzmianka o "EU citizen", "Citoyen UE", "EU pass" → "Paszport UE — automatyczna swoboda przepływu osób, brak potrzeby pozwolenia".
[ ] Posiadane już pozwolenie na pracę (Permit B/C/G/L) → "Posiadane pozwolenie [typ] — gotowy do zatrudnienia".
[ ] Certyfikat branżowy uznawany w CH (EU-Schweisspass, ISO 9606, IWS, Goethe-Zertifikat, DELF/DALF, HACCP, dyplomy medyczne, CAP, BTS itd.) → "Certyfikat [nazwa] — uznawany w CH".
[ ] Prawo jazdy (kategorie B/C/D/E) → "Prawo jazdy kat. [X]".
[ ] Własny samochód → "Własny pojazd — gotowość do dojazdu/pracy w terenie".
[ ] Gotowość do relokacji / pendlowania / pracy w systemie tygodniowym → "Gotowość do [forma] — elastyczność dla pracodawcy CH".
[ ] Dostępność natychmiastowa / "disponible immédiatement" / "verfügbar ab sofort" → "Dostępność natychmiastowa".
[ ] 5+ lat w jednej branży lub firmie → "Stabilność zawodowa: X lat doświadczenia, ceniona w CH".

Jeśli z CV wynika 5+ punktów z tej listy — wymień wszystkie 5 najmocniejszych (limit pola advantages). Nie wybieraj losowo 2-3 jeśli jest więcej.
═══════════════════════════════════════════════════════════════════

=== FORMAT ODPOWIEDZI ===
Zwróć JSON dokładnie z poniższą strukturą:
{
  "overall_score": <liczba 1-10 — średnia z obu kategorii; jeśli krytyczny problem językowy → maks. 4>,
  "summary": "<2-3 zdania po polsku: ogólny werdykt + 1 najważniejsza rzecz do poprawy>",
  "critical_issues": ["<problem krytyczny 1 — np. zły język CV>", ...],
  "structure": {
    "score": <liczba 1-10 dla samej formy CV>,
    "works_well": ["<konkret 1>", "<konkret 2>", ...],
    "needs_fixing": ["<co poprawić/usunąć — z sugestią 1>", "<2>", ...],
    "to_add": ["<co dodać — z uzasadnieniem 1>", "<2>", ...]
  },
  "swiss_fit": {
    "score": <liczba 1-10 dla dopasowania do rynku CH>,
    "advantages": ["<konkretny atut 1>", "<2>", ...],
    "concerns": ["<konkretny gap 1>", "<2>", ...],
    "actions": ["<konkretny krok 1>", "<2>", ...]
  },
  "tips": ["<1-3 uniwersalnych, krótkich porad — opcjonalnie>"]
}

WYMAGANIA:
- critical_issues: 0-3 pozycji. ZAWSZE pierwsze: zły język CV (PL/EN/inny niż DE/FR/IT). Tylko PRAWDZIWIE blokujące problemy — nie używaj dla drobnych spraw
- structure.works_well: 0-5 pozycji (lepiej puste niż meta-truizmowe wypełniacze; jeśli CV nie ma realnych mocnych stron — wpisz 0-1 pozycję i bądź szczery)
- structure.needs_fixing: 2-6 pozycji
- structure.to_add: 1-5 pozycji
- swiss_fit.advantages: 1-7 pozycji (jeśli brak — pusta lista). Jeśli checklist wykryje >5 punktów — WYMIEŃ WSZYSTKIE do 7, nie pomijaj. Branża deficytowa + lata doświadczenia w tej branży = DWA OSOBNE atuty (nie łącz ich w jedną pozycję).
- swiss_fit.concerns: 0-5 pozycji (puste OK jeśli CV jest mocne — nie wymyślaj problemów na siłę)
- swiss_fit.actions: 0-4 pozycji (puste OK jeśli concerns są puste)
- tips: 0-2 pozycji (krótkie, naprawdę unikalne porady — nie powtórzenia z action/concerns; preferuj pustą listę jeśli nic istotnego)
- Wszystko po polsku
- KAŻDA pozycja zawiera KONKRET z CV (nie ogólniki typu "popraw doświadczenie")
- ZAKAZ DUBLOWANIA #1: ten sam problem NIE może pojawić się jednocześnie w `concerns` i w `actions`. Jeśli problem został wymieniony jako concern — w actions nie powtarzaj go, tylko opisz INNE konkretne kroki. Jeśli problem jest do działania → tylko w `actions`, jeśli to opis stanu → tylko w `concerns`.
- ZAKAZ DUBLOWANIA #2: Jeśli problem został wymieniony w `critical_issues` (np. zły język CV) — NIE powtarzaj go w `actions` ani `concerns` ani `tips`. Critical_issues jest osobnym, wyróżnionym blokiem i widoczność jest zapewniona. Powtórka jest redundantna. PRZYKŁADY ZAKAZANE: jeśli critical_issues mówi "Przetłumacz CV na niemiecki" — w actions NIE wpisuj "Przetłumacz CV...".
- ZAKAZ DUBLOWANIA #5: `tips` NIE może powtarzać niczego z `actions` (ani odwrotnie). Jeśli wpisałeś action "Zdobądź doświadczenie w międzynarodowej firmie" — NIE wpisuj tego samego w tips innymi słowami. Tips są dla ZUPEŁNIE INNYCH wskazówek niż actions, lub zostaw tips PUSTE.
- ZAKAZ DUBLOWANIA #3: Jeśli kandydat MA wystarczający język urzędowy CH (B1+ DE/FR/IT) — NIE wpisuj w actions sugestii "rozważ podniesienie języka angielskiego" lub innego POMOCNICZEGO języka. Pomocnicze języki są opcjonalne i nie poprawiają zatrudnialności w wybranej branży/regionie znacznie.
- Bądź szczery — jeśli CV jest słabe, nie wybielaj. Jeśli silne — nie udawaj że źle.
- Jeśli CV jest w złym języku — `summary` MUSI zaczynać się od wzmianki o problemie językowym
- Jeśli CV jest skrajnie niekompletne (mniej niż 200 znaków LUB brakuje sekcji doświadczenia/wykształcenia/języków) — `summary` musi wspomnieć też o niekompletności CV jako drugim głównym problemie. Nie pomijaj tego, nawet gdy jest też problem językowy.
- W `structure.to_add` zawsze wymień brakujące KLUCZOWE sekcje jeśli ich nie ma w tekście CV: doświadczenie zawodowe, wykształcenie, języki obce (z poziomami CEFR), umiejętności branżowe.

═══════════════════════════════════════════════════════════════════
SELF-CHECK PRZED ZWRÓCENIEM JSON
═══════════════════════════════════════════════════════════════════
PRZED finalnym zwróceniem JSON, prześledź każdą pozycję i sprawdź:

[ ] Czy `actions` nie zawiera tego samego co `critical_issues`? (jeśli tak — USUŃ z actions)
[ ] Czy `actions` nie zawiera tego samego co `needs_fixing`? (jeśli tak — USUŃ z actions, te należą do structure)
[ ] Czy `tips` nie zawiera tego samego co `actions`? (jeśli tak — USUŃ z tips lub zostaw tips puste)
[ ] Czy w `actions` lub `tips` jest sugestia "ucz się drugiego języka CH" gdy kandydat ma już 1 język CH ≥B1? (jeśli tak — USUŃ)
[ ] Czy w `works_well` jest słowo "język", "C1", "B2", "atut", "prawo jazdy", "certyfikat"? (jeśli tak — PRZENIEŚ do advantages)
[ ] Czy `swiss_fit.advantages` zaczyna się od BRANŻY DEFICYTOWEJ (jeśli kandydat ma stanowisko z listy)?
[ ] Czy każda pozycja w `advantages` ma BEZPOŚREDNI DOWÓD w tekście CV? (nie halucynuj)

Jeśli któryś check się NIE ZGADZA — POPRAW JSON ZANIM go zwrócisz.

TEKST CV:
"""


async def analyze(cv_text: str) -> dict | None:
    from openai import AsyncOpenAI
    import httpx

    # Local Windows often has SSL interception (AV/firewall) — bypass verify only on dev box.
    # On server (OPENAI_VERIFY_SSL=1) keep normal verification.
    http_client = httpx.AsyncClient(verify=os.environ.get("OPENAI_VERIFY_SSL", "0") == "1", timeout=60)
    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"], http_client=http_client)

    response = await client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {
                "role": "system",
                "content": "Jesteś ekspertem HR specjalizującym się w rynku pracy w Szwajcarii. Odpowiadasz wyłącznie czystym JSON.",
            },
            {
                "role": "user",
                "content": CV_ANALYSIS_PROMPT + cv_text,
            },
        ],
        max_completion_tokens=2500,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        return None
    return json.loads(content.strip())


async def main(cv_path: str) -> None:
    p = Path(cv_path)
    cv_text = p.read_text(encoding="utf-8")
    print(f">>> Analyzing: {p.name} ({len(cv_text)} chars)", flush=True)
    result = await analyze(cv_text)
    if result is None:
        print("ERROR: empty response", flush=True)
        sys.exit(1)
    out = p.with_suffix(".json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f">>> Saved: {out}", flush=True)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
