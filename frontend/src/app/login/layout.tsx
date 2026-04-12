import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Logowanie",
  description: "Zaloguj się do portalu Praca w Szwajcarii.",
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return children;
}
