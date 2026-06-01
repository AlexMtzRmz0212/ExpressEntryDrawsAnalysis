import React from "react";
import { useAnalysisData } from "../context/AnalysisDataContext";

export default function Header() {
  const { manifest, lastModified, loading } = useAnalysisData();
  const moduleCount = manifest ? Object.keys(manifest).length : 0;

  const formattedDate = (() => {
    if (!lastModified) return null;
    try {
      return new Date(lastModified).toLocaleDateString("en-CA", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return null;
    }
  })();

  return (
    <header
      style={{
        borderBottom: "1px solid var(--border)",
        backgroundColor: "var(--bg-secondary)",
      }}
    >
      {/* Top stripe */}
      <div
        style={{
          borderBottom: "1px solid var(--border)",
          padding: "8px 32px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <span
          style={{
            fontFamily: '"IBM Plex Mono"',
            fontSize: "0.6rem",
            letterSpacing: "0.22em",
            color: "var(--accent-red)",
            textTransform: "uppercase",
          }}
        >
          IRCC / Express Entry Draws
        </span>

        <span
          style={{
            fontFamily: '"IBM Plex Mono"',
            fontSize: "0.6rem",
            letterSpacing: "0.12em",
            color: "var(--text-muted)",
          }}
        >
          {loading ? (
            <span className="skeleton" style={{ display: "inline-block", width: "120px", height: "10px" }} />
          ) : formattedDate ? (
            `DATA AS OF ${formattedDate.toUpperCase()}`
          ) : (
            "AUTOMATED PIPELINE ACTIVE"
          )}
        </span>
      </div>

      {/* Main header content */}
      <div
        style={{
          maxWidth: "1280px",
          margin: "0 auto",
          padding: "28px 32px 24px",
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          gap: "24px",
          flexWrap: "wrap",
        }}
      >
        {/* Title block */}
        <div style={{ display: "flex", alignItems: "flex-start", gap: "16px" }}>
          {/* Red accent bar */}
          <div
            style={{
              width: "3px",
              height: "72px",
              backgroundColor: "var(--accent-red)",
              borderRadius: "2px",
              flexShrink: 0,
              marginTop: "4px",
            }}
          />
          <div>
            <h1
              style={{
                fontFamily: '"Playfair Display"',
                fontSize: "clamp(1.75rem, 3vw, 2.5rem)",
                fontWeight: 700,
                color: "var(--text-primary)",
                lineHeight: 1.1,
                margin: 0,
              }}
            >
              Draws Intelligence
            </h1>
            <p
              style={{
                fontFamily: '"DM Sans"',
                fontSize: "0.85rem",
                color: "var(--text-muted)",
                margin: "6px 0 0",
                fontWeight: 300,
                letterSpacing: "0.04em",
              }}
            >
              Historical Analysis Dashboard — Canada Express Entry
            </p>
          </div>
        </div>

        {/* Status panel */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            alignItems: "flex-end",
          }}
        >
          {/* Live indicator */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "6px 12px",
              border: "1px solid var(--border)",
              borderRadius: "3px",
              backgroundColor: "var(--bg-card)",
            }}
          >
            <div
              style={{
                width: "7px",
                height: "7px",
                borderRadius: "50%",
                backgroundColor: loading ? "var(--text-muted)" : "#22C55E",
                boxShadow: loading ? "none" : "0 0 6px #22C55E88",
              }}
            />
            <span
              style={{
                fontFamily: '"IBM Plex Mono"',
                fontSize: "0.62rem",
                color: loading ? "var(--text-muted)" : "#22C55E",
                letterSpacing: "0.1em",
              }}
            >
              {loading ? "LOADING" : "PIPELINE ACTIVE"}
            </span>
          </div>

          {/* Module count */}
          {!loading && (
            <span
              style={{
                fontFamily: '"IBM Plex Mono"',
                fontSize: "0.6rem",
                color: "var(--text-muted)",
                letterSpacing: "0.1em",
              }}
            >
              {moduleCount} MODULE{moduleCount !== 1 ? "S" : ""} REGISTERED
            </span>
          )}
        </div>
      </div>
    </header>
  );
}