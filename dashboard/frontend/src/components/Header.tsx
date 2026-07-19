import { exportCsvUrl } from "../lib/api";
import { longDate } from "../lib/format";
import { btnGhost, btnPrimary, iconBtn } from "../lib/tw";
import type { Budgets, Meta } from "../types";

interface Props {
  meta: Meta | null;
  horizon: number;
  budgets: Budgets;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
  onRerun: () => void;
}

export default function Header({ meta, horizon, budgets, sidebarOpen, onToggleSidebar, onRerun }: Props) {
  return (
    <header className="flex items-center justify-between border-b border-dline px-8 py-5">
      <div className="flex items-center gap-3.5">
        <button
          className={iconBtn}
          title={sidebarOpen ? "Hide scenario panel" : "Show scenario panel"}
          aria-label={sidebarOpen ? "Hide scenario panel" : "Show scenario panel"}
          onClick={onToggleSidebar}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="1" y="2" width="14" height="12" rx="2" stroke="currentColor" strokeWidth="1.4" />
            <line x1="5.6" y1="2.6" x2="5.6" y2="13.4" stroke="currentColor" strokeWidth="1.4" />
          </svg>
        </button>
        <div>
          <h1 className="m-0 text-lg font-semibold tracking-[-0.01em]">Revenue forecast</h1>
          <div className="mt-0.5 text-xs text-dmuted">
            Google · Meta · Microsoft
            {meta ? ` — data through ${longDate(meta.last_data_date)}` : ""}
          </div>
        </div>
      </div>
      <div className="flex gap-2.5">
        <a className={`${btnGhost} inline-block`} href={exportCsvUrl(horizon, budgets)}>
          Export CSV
        </a>
        <button className={btnPrimary} onClick={onRerun}>
          Re-run forecast
        </button>
      </div>
    </header>
  );
}
