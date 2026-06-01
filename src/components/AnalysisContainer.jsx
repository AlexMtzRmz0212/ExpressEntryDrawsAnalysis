import React, { useState, useEffect } from "react";

/* ── Sub-components ──────────────────────────────────────────────────────────── */

/** Corner-mark decoration for the canvas area */
function CornerMark({ top, left }) {
  return (
    <div
      style={{
        position: "absolute",
        top: top ? "8px" : "auto",
        bottom: top ? "auto" : "8px",
        left: left ? "8px" : "auto",
        right: left ? "auto" : "8px",
        width: "10px",
        height: "10px",
        borderTop:    top  ? "1px solid var(--accent-red)" : "none",
        borderBottom: !top ? "1px solid var(--accent-red)" : "none",
        borderLeft:   left ? "1px solid var(--accent-red)" : "none",
        borderRight: !left ? "1px solid var(--accent-red)" : "none",
        opacity: 0.7,
      }}
    />
  );
}

/** Tabular view for array payloads */
function DataTable({ data }) {
  if (!data?.length) return null;
  const headers = Object.keys(data[0]);

  return (
    <div style={{ overflowX: "auto" }}>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontFamily: '"IBM Plex Mono"',
          fontSize: "0.62rem",
        }}
      >
        <thead>
          <tr>
            {headers.map((h) => (
              <th
                key={h}
                style={{
                  textAlign: "left",
                  padding: "6px 10px",
                  borderBottom: "1px solid var(--border)",
                  color: "var(--accent-gold)",
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  whiteSpace: "nowrap",
                  fontWeight: 500,
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.slice(0, 8).map((row, i) => (
            <tr
              key={i}
              style={{
                backgroundColor:
                  i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.018)",
              }}
            >
              {headers.map((h) => (
                <td
                  key={h}
                  style={{
                    padding: "5px 10px",
                    borderBottom: "1px solid rgba(31,45,72,0.5)",
                    color: "var(--text-muted)",
                    whiteSpace: "nowrap",
                  }}
                >
                  {String(row[h] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length > 8 && (
        <p
          style={{
            fontFamily: '"IBM Plex Mono"',
            fontSize: "0.58rem",
            color: "var(--text-muted)",
            padding: "6px 10px",
            margin: 0,
            letterSpacing: "0.06em",
          }}
        >
          ↓ {data.length - 8} MORE RECORDS
        </p>
      )}
    </div>
  );
}

/** Skeleton rows while loading */
function SkeletonRows({ n = 4 }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "6px", padding: "4px 0" }}>
      {Array.from({ length: n }).map((_, i) => (
        <div
          key={i}
          className="skeleton"
          style={{ height: "18px", opacity: 0.5, borderRadius: "2px" }}
        />
      ))}
    </div>
  );
}

/* ── Main component ──────────────────────────────────────────────────────────── */

/**
 * AnalysisContainer
 * -----------------
 * Props:
 *   title    {string} — displayed in the card header
 *   dataPath {string} — JSON endpoint relative to PUBLIC_URL (e.g. "/data/analyses/draw_summary.json")
 *
 * On mount, fetches `dataPath` and renders:
 *   1. A reserved visualization canvas (dashed border, corner marks, placeholder text)
 *   2. The raw JSON payload — table view for arrays, pretty-printed JSON for objects
 */
export default function AnalysisContainer({ title, dataPath }) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  const resolvePublicUrl = (path) => new URL(path.replace(/^\//, ""), window.location.origin + import.meta.env.BASE_URL).href;

  useEffect(() => {
    const url = resolvePublicUrl(dataPath);
    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [dataPath]);

  const statusColor = loading
    ? "var(--text-muted)"
    : error
    ? "var(--accent-red-lt)"
    : "#22C55E";

  const statusLabel = loading ? "FETCHING" : error ? "ERROR" : "LOADED";

  return (
    <article
      className="animate-fade-in"
      style={{
        backgroundColor: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "4px",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* ── Card header ── */}
      <div
        style={{
          padding: "14px 18px",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          backgroundColor: "rgba(7,11,20,0.4)",
        }}
      >
        <h3
          style={{
            fontFamily: '"Playfair Display"',
            fontSize: "0.95rem",
            fontWeight: 600,
            color: "var(--text-primary)",
            margin: 0,
          }}
        >
          {title}
        </h3>

        {/* Status badge */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            fontFamily: '"IBM Plex Mono"',
            fontSize: "0.58rem",
            letterSpacing: "0.1em",
            color: statusColor,
          }}
        >
          <span
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              backgroundColor: statusColor,
              boxShadow: error || loading ? "none" : `0 0 5px ${statusColor}`,
              flexShrink: 0,
            }}
          />
          {statusLabel}
        </div>
      </div>

      {/* ── Visualization canvas (reserved for future chart) ── */}
      <div
        style={{
          margin: "16px 18px",
          border: "1px dashed var(--border-bright)",
          borderRadius: "3px",
          aspectRatio: "16 / 7",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
          gap: "10px",
          backgroundColor: "rgba(7,11,20,0.55)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Corner marks */}
        <CornerMark top left />
        <CornerMark top={false} left />
        <CornerMark top left={false} />
        <CornerMark top={false} left={false} />

        {/* Placeholder content */}
        <div
          style={{
            fontSize: "1.4rem",
            color: "var(--border-bright)",
            lineHeight: 1,
            userSelect: "none",
          }}
        >
          ◈
        </div>
        <div
          style={{
            fontFamily: '"IBM Plex Mono"',
            fontSize: "0.6rem",
            color: "var(--text-muted)",
            letterSpacing: "0.14em",
            textAlign: "center",
            opacity: 0.55,
            lineHeight: 1.7,
          }}
        >
          VISUALIZATION CANVAS
          <br />
          <span style={{ opacity: 0.6 }}>AWAITING IMPLEMENTATION</span>
        </div>

        {/* Subtle diagonal lines for depth */}
        <svg
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            opacity: 0.04,
            pointerEvents: "none",
          }}
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <pattern id={`hatch-${title}`} width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <line x1="0" y1="0" x2="0" y2="12" stroke="#E8EAF0" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill={`url(#hatch-${title})`} />
        </svg>
      </div>

      {/* ── Data payload section ── */}
      <div style={{ padding: "0 18px 18px", flex: 1, minHeight: 0 }}>
        {/* Section label */}
        <div
          style={{
            fontFamily: '"IBM Plex Mono"',
            fontSize: "0.58rem",
            color: "var(--accent-gold)",
            letterSpacing: "0.14em",
            marginBottom: "10px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>◆</span>
          DATA PAYLOAD
          {!loading && !error && data && (
            <span style={{ color: "var(--text-muted)", marginLeft: "auto" }}>
              {Array.isArray(data)
                ? `${data.length} RECORDS`
                : `${Object.keys(data).length} KEYS`}
            </span>
          )}
        </div>

        {/* States */}
        {loading && <SkeletonRows />}

        {error && (
          <div
            style={{
              fontFamily: '"IBM Plex Mono"',
              fontSize: "0.62rem",
              color: "var(--accent-red-lt)",
              padding: "12px 14px",
              border: "1px solid var(--accent-red)",
              borderRadius: "3px",
              backgroundColor: "rgba(192,57,43,0.06)",
              lineHeight: 1.7,
            }}
          >
            ERROR: {error}
            <br />
            <span style={{ color: "var(--text-muted)", fontSize: "0.56rem" }}>
              PATH: {dataPath}
            </span>
          </div>
        )}

        {!loading && !error && data !== null && (
          Array.isArray(data) ? (
            data.length === 0 ? (
              <p
                style={{
                  fontFamily: '"IBM Plex Mono"',
                  fontSize: "0.62rem",
                  color: "var(--text-muted)",
                  letterSpacing: "0.08em",
                  margin: 0,
                  padding: "8px 0",
                }}
              >
                NO RECORDS YET — RUN THE ETL SCRIPT TO POPULATE
              </p>
            ) : (
              <DataTable data={data} />
            )
          ) : (
            <pre
              style={{
                fontFamily: '"IBM Plex Mono"',
                fontSize: "0.6rem",
                color: "var(--text-muted)",
                backgroundColor: "rgba(7,11,20,0.6)",
                padding: "12px",
                borderRadius: "3px",
                border: "1px solid var(--border)",
                overflow: "auto",
                maxHeight: "160px",
                margin: 0,
                lineHeight: 1.6,
              }}
            >
              {JSON.stringify(data, null, 2)}
            </pre>
          )
        )}
      </div>
    </article>
  );
}