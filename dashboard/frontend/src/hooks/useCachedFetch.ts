import { useEffect, useState } from "react";

const cache = new Map<string, unknown>();

/** Fetch-once-per-key hook: tab data is cached so switching tabs is instant. */
export function useCachedFetch<T>(key: string, fetcher: () => Promise<T>) {
  const [data, setData] = useState<T | null>((cache.get(key) as T) ?? null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (cache.has(key)) {
      setData(cache.get(key) as T);
      return;
    }
    let alive = true;
    setData(null);
    setError(null);
    fetcher()
      .then((d) => {
        cache.set(key, d);
        if (alive) setData(d);
      })
      .catch((e) => alive && setError(String(e)));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return { data, error };
}
