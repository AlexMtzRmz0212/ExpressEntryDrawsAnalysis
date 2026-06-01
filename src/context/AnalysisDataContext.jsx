import React, { createContext, useContext, useState, useEffect } from "react";

const AnalysisDataContext = createContext(null);

/**
 * AnalysisDataProvider
 * --------------------
 * Fetches module_manifest.json once on mount and exposes it to all children.
 * The manifest is a plain object: { "Label": "/data/path.json", ... }
 * Any number of modules can be registered; the DashboardGrid auto-renders them.
 */
export function AnalysisDataProvider({ children }) {
  const [manifest, setManifest]       = useState(null);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState(null);
  const [lastModified, setLastModified] = useState(null);

  const resolvePublicUrl = (path) => new URL(path.replace(/^\//, ""), window.location.origin + import.meta.env.BASE_URL).href;

  useEffect(() => {
    const url = resolvePublicUrl("data/analyses/module_manifest.json");

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status} — could not load manifest`);
        setLastModified(res.headers.get("last-modified"));
        return res.json();
      })
      .then((data) => {
        setManifest(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <AnalysisDataContext.Provider value={{ manifest, loading, error, lastModified }}>
      {children}
    </AnalysisDataContext.Provider>
  );
}

export function useAnalysisData() {
  const ctx = useContext(AnalysisDataContext);
  if (!ctx) throw new Error("useAnalysisData must be used inside <AnalysisDataProvider>");
  return ctx;
}

export default AnalysisDataContext;