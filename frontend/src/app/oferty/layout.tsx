import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Oferty pracy w Szwajcarii",
  description:
    "Przeglądaj aktualne oferty pracy w Szwajcarii dla polskojęzycznych pracowników. Filtruj po kantonie, branży i wynagrodzeniu.",
};

export default function OfertyLayout({ children }: { children: React.ReactNode }) {
  return children;
}
