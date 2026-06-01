import React from "react";
import { useAnalysisData } from "../context/AnalysisDataContext";
import AnalysisContainer from "./AnalysisContainer";

function SkeletonCard() {
  return (
    <div
      className="skeleton"
      style={{
        borderRadius: "4px",
        height: "420px",
        border: "1px solid var(--border)",
      }}
    />
  );
}

function ErrorState({ message }) {
  return (
    <div
      style={{
        gridColumn: "1 / -1",
        padding: "64px 40px",
        textAlign: "center",
        border: "1px solid var(--accent-red)",
        borderRadius: "4px",
        backgroundColor: "rgba(192,57,43,0.04)",
      }}
    >
      <p
        style={{
          fontFamily: '"Playfair Display"',
          fontSize: "1.1rem",
          color: "var(--text-primary)",
          margin: "0 0 12px",
        }}
      >
        Manifest Unavailable
      </p>
      <p
        style={{
          fontFamily: '"IBM Plex Mono"',
          fontSize: "0.65rem",
          color: "var(--accent-red-lt)",
          margin: "0 0 20px",
          letterSpacing: "0.06em",
        }}
      >
        ERROR: {message}
      </p>
      <p
        style={{
          fontFamily: '"IBM Plex Mono"',
          fontSize: "0.6rem",
          color: "var(--text-muted)",
          lineHeight: 1.9,
          margin: 0,
        }}
      >
        Ensure the Python ETL script has run at least once
        <br />
        and that{" "}
        <code style={{ color: "var(--accent-gold)" }}>
          public/data/analyses/module_manifest.json
        </code>{" "}
        exists.
      </p>
    </div>
  );
}

function EmptyState() {
  return (
    <div
      style={{
        gridColumn: "1 / -1",
        padding: "64px 40px",
        textAlign: "center",
        border: "1px dashed var(--border)",
        borderRadius: "4px",
      }}
    >
      <p
        style={{
          fontFamily: '"IBM Plex Mono"',
          fontSize: "0.65rem",
          color: "var(--text-muted)",
          letterSpacing: "0.12em",
          margin: 0,
        }}
      >
        NO MODULES FOUND
        <br />
        <span style={{ opacity: 0.5, fontSize: "0.58rem" }}>
          ADD ENTRIES TO module_manifest.json TO REGISTER ANALYSIS MODULES
        </span>
      </p>
    </div>
  );
}

/**
 * DashboardGrid
 * -------------
 * Consumes the AnalysisDataContext manifest and maps each entry to an
 * AnalysisContainer. The grid auto-expands as new modules are registered —
 * no frontend changes required.
 */
export default function DashboardGrid() {
  const { manifest, loading, error } = useAnalysisData();
  const entries = manifest ? Object.entries(manifest) : [];

  return (
    <main
      style={{
        maxWidth: "1280px",
        margin: "0 auto",
        padding: "32px",
        flex: 1,
      }}
    >
      {/* Section header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "16px",
          marginBottom: "24px",
        }}
      >
        <span
          style={{
            fontFamily: '"IBM Plex Mono"',
            fontSize: "0.6rem",
            color: "var(--text-muted)",
            letterSpacing: "0.18em",
            whiteSpace: "nowrap",
          }}
        >
          ANALYTICAL MODULES
        </span>
        <div
          style={{
            flex: 1,
            height: "1px",
            backgroundColor: "var(--border)",
          }}
        />
        {!loading && !error && (
          <span
            style={{
              fontFamily: '"IBM Plex Mono"',
              fontSize: "0.58rem",
              color: "var(--border-bright)",
              letterSpacing: "0.1em",
              whiteSpace: "nowrap",
            }}
          >
            {entries.length} TOTAL
          </span>
        )}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Loading skeletons */}
        {loading && [0, 1, 2].map((i) => <SkeletonCard key={i} />)}

        {/* Error state */}
        {error && <ErrorState message={error} />}

        {/* Empty state */}
        {!loading && !error && entries.length === 0 && <EmptyState />}

        {/* Module cards — each mounts independently and fetches its own data */}
        {!loading &&
          !error &&
          entries.map(([title, path], index) => (
            <div
              key={title}
              style={{
                animationDelay: `${index * 0.08}s`,
                opacity: 0,
                animation: `fadeSlideUp 0.45s ease ${index * 0.08}s forwards`,
              }}
            >
              <AnalysisContainer title={title} dataPath={path} />
            </div>
          ))}
      </div>
    </main>
  );
}