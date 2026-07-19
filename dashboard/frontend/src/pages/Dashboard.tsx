import { useCallback, useEffect, useRef, useState } from "react";
import Header from "../components/Header";
import Sidebar from "../components/Sidebar";
import TabNav, { TabKey } from "../components/TabNav";
import { getMeta, postForecast } from "../lib/api";
import AllocationTab from "../tabs/AllocationTab";
import AnomaliesTab from "../tabs/AnomaliesTab";
import ForecastTab from "../tabs/ForecastTab";
import SimulatorTab from "../tabs/SimulatorTab";
import SummaryTab from "../tabs/SummaryTab";
import type { Budgets, Forecast, Meta } from "../types";

const FORECAST_DEBOUNCE_MS = 300;

export default function Dashboard() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [horizon, setHorizon] = useState(30);
  const [budgets, setBudgets] = useState<Budgets>({});
  // Budgets after the debounce settles — what the data tabs actually query with.
  const [settledBudgets, setSettledBudgets] = useState<Budgets>({});
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabKey>("forecast");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const debounceRef = useRef<number>();

  // Bootstrap: meta + default budgets for the initial horizon.
  useEffect(() => {
    getMeta()
      .then((m) => {
        setMeta(m);
        setBudgets({ ...m.default_plans[String(30)] });
      })
      .catch((e) => setError(String(e)));
  }, []);

  const runForecast = useCallback((h: number, b: Budgets) => {
    setLoading(true);
    postForecast(h, b)
      .then((f) => {
        setForecast(f);
        setError(null);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  // Refetch (debounced) whenever the scenario changes.
  useEffect(() => {
    if (!meta) return;
    window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(() => {
      setSettledBudgets(budgets);
      runForecast(horizon, budgets);
    }, FORECAST_DEBOUNCE_MS);
    return () => window.clearTimeout(debounceRef.current);
  }, [meta, horizon, budgets, runForecast]);

  const changeHorizon = (h: number) => {
    if (!meta) return;
    setHorizon(h);
    setBudgets({ ...meta.default_plans[String(h)] });
  };

  if (error && !meta) {
    return (
      <div className="p-12 font-instrument bg-dbg text-dtext min-h-screen">
        <h2 className="text-lg font-semibold">Could not reach the forecast API</h2>
        <p className="text-dtext2 mt-2">{error}</p>
      </div>
    );
  }

  return (
    <div className="min-w-[1440px] max-w-[1600px] mx-auto flex min-h-screen bg-dbg text-dtext font-instrument">
      <Sidebar
        open={sidebarOpen}
        meta={meta}
        horizon={horizon}
        budgets={budgets}
        onHorizonChange={changeHorizon}
        onBudgetChange={(ch, v) => setBudgets((b) => ({ ...b, [ch]: v }))}
      />
      <main className="flex-1 min-w-0 flex flex-col">
        <Header
          meta={meta}
          horizon={horizon}
          budgets={budgets}
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen((o) => !o)}
          onRerun={() => runForecast(horizon, budgets)}
        />
        <TabNav active={tab} onChange={setTab} />
        {/* key remounts on tab switch so the content gets a subtle fade-up */}
        <div key={tab} className="animate-fade-up px-8 pt-7 pb-12 flex flex-col gap-6">
          {tab === "forecast" && (
            <ForecastTab meta={meta} forecast={forecast} loading={loading} horizon={horizon} />
          )}
          {tab === "simulator" && (
            <SimulatorTab horizon={horizon} budgets={settledBudgets} />
          )}
          {tab === "allocation" && (
            <AllocationTab horizon={horizon} budgets={settledBudgets} />
          )}
          {tab === "anomalies" && <AnomaliesTab />}
          {tab === "summary" && <SummaryTab horizon={horizon} budgets={budgets} />}
        </div>
      </main>
    </div>
  );
}
