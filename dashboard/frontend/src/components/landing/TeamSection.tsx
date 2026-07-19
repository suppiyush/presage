import { revealDelay } from "../../hooks/useReveal";

const GRADS = [
  "linear-gradient(135deg,#2b49c4,#5a4bc2)",
  "linear-gradient(135deg,#5a4bc2,#a850a0)",
  "linear-gradient(135deg,#a850a0,#e8560f)",
  "linear-gradient(135deg,#e8560f,#f0925f)",
];

const TEAM = [
  {
    name: "Sahil Vaswani", role: "Team lead · Forecast models",
    email: "24ucc158@lnmiit.ac.in",
  },
  {
    name: "Shivika Bansal", role: "Frontend & design",
    email: "24ucc055@lnmiit.ac.in",
  },
  {
    name: "Piyush Agarwal", role: "Data engineering",
    email: "24ucc006@lnmiit.ac.in",
  },
  
];

const initials = (name: string) => name.split(" ").map((w) => w[0]).join("");

export default function TeamSection() {
  return (
    <section id="contact" className="bg-navy px-10 py-18 text-paper">
      <div className="mx-auto max-w-[1080px]">
        <div data-reveal className="font-mono text-[12.5px] font-medium uppercase tracking-[0.1em] text-peach">
          Contact us
        </div>
        <div className="flex flex-wrap items-end justify-between gap-10">
          <h2 data-reveal style={revealDelay(90)} className="mt-3 text-[34px] font-bold tracking-[-0.02em]">
            Team Parity Check
          </h2>
          <a
            data-reveal
            style={revealDelay(150)}
            href="mailto:sahilvaswani1111@gmail.com"
            className="rounded-[10px] border border-navyline2 px-5.5 py-3 text-sm font-semibold text-paper transition-colors hover:border-peach hover:text-peach"
          >
            Team Parity Check
          </a>
        </div>
        <p data-reveal style={revealDelay(180)} className="mt-3.5 max-w-[520px] text-[15px] leading-relaxed text-mist">
          Three of us built Presage over one hackathon weekend. Questions,
          feedback, or want a demo? Reach any of us.
        </p>
        <div className="mt-10 grid grid-cols-3 gap-5">
          {TEAM.map((m, i) => (
            <div
              key={m.email}
              data-reveal
              style={revealDelay(i * 110)}
              className="flex flex-col gap-1 rounded-xl border border-navyline bg-navy2 p-6 transition-all duration-200 hover:-translate-y-1 hover:border-navyline2"
            >
              <div
                className="mb-3 flex h-11 w-11 items-center justify-center rounded-full text-[15px] font-bold text-paper"
                style={{ background: GRADS[i] }}
              >
                {initials(m.name)}
              </div>
              <div className="text-base font-semibold">{m.name}</div>
              <div className="mb-2.5 text-[13px] font-medium text-peach">{m.role}</div>
              <a
                href={`mailto:${m.email}`}
                className="mt-auto font-mono text-[12.5px] text-periwinkle hover:text-peach"
              >
                {m.email}
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
