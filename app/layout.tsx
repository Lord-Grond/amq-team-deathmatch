import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Chungus AMQ Team Deathmatch",
  description: "A host-first anime music quiz game board.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
