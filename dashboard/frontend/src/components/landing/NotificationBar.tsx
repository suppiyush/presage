import { useState } from "react";

const NOTIF_TEXT = "Presage is live — built in 48 hours for the 2026 hackathon.";

export default function NotificationBar() {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed) return null;

  return (
    <div
      className="animate-spectrum relative flex items-center justify-center gap-3.5 px-5 py-[9px] text-[13px] text-paper"
      style={{
        background: "linear-gradient(90deg,#2b49c4,#7a4fc0,#e8560f,#7a4fc0,#2b49c4)",
        backgroundSize: "300% 100%",
      }}
    >
      <span className="font-semibold">{NOTIF_TEXT}</span>
      <a
        href="#contact"
        className="font-medium text-paper underline underline-offset-[3px] hover:text-paper"
      >
        Meet the team →
      </a>
      <button
        aria-label="Dismiss"
        onClick={() => setDismissed(true)}
        className="absolute right-3.5 top-1/2 -translate-y-1/2 cursor-pointer border-0 bg-transparent p-1 text-base leading-none text-paper"
      >
        ×
      </button>
    </div>
  );
}
