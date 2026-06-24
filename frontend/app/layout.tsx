import type { Metadata } from "next";
import localFont from "next/font/local";
import Link from "next/link";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "NC 2024 Voter Simulation",
  description:
    "Agent-based behavioral simulation predicting the 2024 North Carolina presidential election at the county level.",
};

function NavLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="rounded-md px-3 py-1.5 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900"
    >
      {children}
    </Link>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gray-50 text-gray-900`}
      >
        <nav className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
            <Link
              href="/"
              className="flex items-center gap-2 text-base font-extrabold tracking-tight text-gray-900"
            >
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-gradient-to-br from-blue-500 to-red-500" />
              NC&nbsp;2024
            </Link>
            <div className="flex gap-1 text-sm font-medium">
              <NavLink href="/">Dashboard</NavLink>
              <NavLink href="/counties">Counties</NavLink>
              <NavLink href="/results">Results</NavLink>
              <NavLink href="/about">About</NavLink>
            </div>
          </div>
        </nav>
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">{children}</main>
      </body>
    </html>
  );
}
