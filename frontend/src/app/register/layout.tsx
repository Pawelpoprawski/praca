import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Rejestracja",
  description: "Utwórz konto w portalu Praca w Szwajcarii - jako pracownik lub pracodawca.",
};

export default function RegisterLayout({ children }: { children: React.ReactNode }) {
  return children;
}
