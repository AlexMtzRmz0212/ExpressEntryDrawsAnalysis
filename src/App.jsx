import React from "react";
import { AnalysisDataProvider } from "./context/AnalysisDataContext";
import Header from "./components/Header";
import DashboardGrid from "./components/DashboardGrid";

function Footer() {
  return (
    <footer
      style={{
        borderTop: "1px solid var(--border)",
        padding: "18px 32px",
        marginTop: "16px",
      }}
    >
      <div
        style={{
          maxWidth: "1280px",
          margin: "0 auto",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "16px",
          flexWrap: "wrap",
        }}
      >
        <span
          style={{
            fontFamily: '"IBM Plex Mono"',
            fontSize: "0.58rem",
            color: "var(--text-muted)",
            letterSpacing: "0.1em",
          }}
        >
          DATA SOURCE: IRCC CANADA — AUTOMATED DAILY PIPELINE
        </span>
        <span
          style={{
            fontFamily: '"IBM Plex Mono"',
            fontSize: "0.55rem",
            color: "var(--border-bright)",
            letterSpacing: "0.1em",
          }}
        >
          EXPRESS ENTRY INTELLIGENCE DASHBOARD
        </span>
      </div>
    </footer>
  );
}

export default function App() {
  return (
    <AnalysisDataProvider>
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <Header />
        <DashboardGrid />
        <Footer />
      </div>
    </AnalysisDataProvider>
  );
}