"""Rozdziela zbiorcze cv_01.txt i cv_22.txt na osobne pliki + renumeruje wszystkie."""
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).parent


def split_bundle(text: str) -> list[str]:
    """Dzieli długi tekst zawierający wiele CV na listę osobnych CV.
    Heurystyka: nowe CV zaczyna się od linii zawierającej CV/LEBENSLAUF/CURRICULUM lub
    od linii w stylu IMIĘ NAZWISKO (caps) poprzedzonej >=1 pustą linią.
    """
    # Najpewniejsza heurystyka: linia zaczynająca się od CV/LEBENSLAUF/CURRICULUM
    # albo wzorzec "NAZWISKO IMIĘ" caps na własnej linii
    lines = text.splitlines()
    starts: list[int] = []
    for i, line in enumerate(lines):
        s = line.strip()
        if re.match(r"^(CV|LEBENSLAUF|CURRICULUM VITAE|Curriculum Vitae)\s*$", s):
            starts.append(i)
        # caps name like "JAN KOWALSKI" preceded by empty line
        elif i > 0 and lines[i - 1].strip() == "" and re.match(r"^[A-ZŻŹĆĄŁĘÓŚŃ][A-ZŻŹĆĄŁĘÓŚŃ\s]{4,30}$", s):
            # only if not already included via header above
            if not starts or starts[-1] != i - 1:
                starts.append(i)
    cvs: list[str] = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        chunk = "\n".join(lines[start:end]).strip()
        if len(chunk) > 100:  # min sensowna długość CV
            cvs.append(chunk)
    return cvs


def main() -> None:
    # Zbierz wszystkie CV z aktualnych plików (zostały te które są poprawne)
    all_cvs: list[str] = []

    for txt_path in sorted(HERE.glob("cv_*.txt")):
        content = txt_path.read_text(encoding="utf-8")
        # Jeśli plik krótki (<3000 chars) — to jedno CV, zostaw
        if len(content) < 3000:
            if len(content.strip()) >= 50:  # min length
                all_cvs.append(content.strip())
        else:
            # Długi — rozdziel
            chunks = split_bundle(content)
            print(f"  {txt_path.name} → {len(chunks)} chunks")
            all_cvs.extend(chunks)
        txt_path.unlink()  # usuń stary

    print(f"\nTotal po rozdzieleniu: {len(all_cvs)} CV")
    # Zapisz wszystkie pod nowymi numerami
    for i, cv_text in enumerate(all_cvs, start=1):
        (HERE / f"cv_{i:02d}.txt").write_text(cv_text + "\n", encoding="utf-8")
    print(f"Zapisano cv_01.txt do cv_{len(all_cvs):02d}.txt")


if __name__ == "__main__":
    main()
