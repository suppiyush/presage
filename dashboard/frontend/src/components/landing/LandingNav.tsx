import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const LINKS = [
  { href: "#product", label: "Product" },
  { href: "#how", label: "How it works" },
  { href: "#contact", label: "Contact us" },
];

function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <div
        className="flex h-7 w-7 items-center justify-center rounded-full"
        style={{ background: "conic-gradient(from 210deg,#2b49c4,#7a4fc0,#e8560f,#2b49c4)" }}
      >
        <span className="h-3 w-3 rounded-full bg-cream" />
      </div>
      <span className="text-[17px] font-bold tracking-[-0.02em] text-ink">Presage</span>
      <span className="rounded-[20px] border border-sand2 px-2 py-0.5 font-mono text-xs text-dune">
        hackathon
      </span>
    </div>
  );
}

export default function LandingNav() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const toggle = () => setDrawerOpen((o) => !o);

  // Sarvam-style nav: condenses and lifts off the page once you scroll.
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <>
      <header
        className={`sticky top-0 z-30 flex items-center gap-6 border-b px-10 transition-all duration-300 ${
          scrolled
            ? "border-sand bg-paper/90 py-3 shadow-[0_4px_24px_rgba(20,27,51,0.07)] backdrop-blur-sm"
            : "border-sand bg-cream py-4"
        }`}
      >
        <button
          aria-label="Toggle menu"
          onClick={toggle}
          className="flex cursor-pointer flex-col gap-1 rounded-lg border border-sand2 bg-transparent px-2.5 py-2"
        >
          {[0, 1, 2].map((i) => (
            <span key={i} className="block h-0.5 w-4 rounded-[1px] bg-ink" />
          ))}
        </button>
        <Logo />
        <nav className="ml-auto flex items-center gap-6 text-sm font-medium">
          {LINKS.map((l) => (
            <a key={l.href} href={l.href} className="text-ink2 hover:text-flame">
              {l.label}
            </a>
          ))}
          <Link
            to="/dashboard"
            className="rounded-lg bg-ink px-4.5 py-2.5 font-semibold text-paper transition-colors hover:bg-blue"
          >
            Open dashboard
          </Link>
        </nav>
      </header>

      {drawerOpen && (
        <>
          <div
            className="animate-fade-in fixed inset-0 z-40 bg-ink/35"
            onClick={toggle}
          />
          <aside className="animate-drawer-in fixed bottom-0 left-0 top-0 z-50 flex w-[290px] flex-col gap-1.5 border-r border-sand bg-paper p-6 shadow-[8px_0_32px_rgba(20,27,51,0.12)]">
            <div className="mb-4 flex items-center justify-between">
              <span className="text-base font-bold text-ink">Menu</span>
              <button
                aria-label="Close menu"
                onClick={toggle}
                className="cursor-pointer border-0 bg-transparent p-1 text-xl text-ink"
              >
                ×
              </button>
            </div>
            {LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={toggle}
                className="rounded-lg px-3 py-[11px] font-medium text-ink hover:bg-[#f1ebdf]"
              >
                {l.label}
              </a>
            ))}
            <Link
              to="/dashboard"
              className="rounded-lg px-3 py-[11px] font-medium text-ink hover:bg-[#f1ebdf]"
            >
              Dashboard
            </Link>
            <div className="mt-auto border-t border-sand pt-4 text-[12.5px] leading-normal text-dune">
              Built for the 2026 hackathon by Team Parity Check.
            </div>
          </aside>
        </>
      )}
    </>
  );
}
