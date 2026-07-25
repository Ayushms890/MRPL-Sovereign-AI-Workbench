"use client";

import React, { useEffect, useRef, useState } from "react";

interface MermaidDiagramProps {
  chart: string;
}

export function MermaidDiagram({ chart }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function renderDiagram() {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "neutral",
          securityLevel: "loose",
          fontFamily: "monospace",
        });

        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
        const { svg } = await mermaid.render(id, chart);
        
        if (isMounted) {
          setSvgContent(svg);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          console.error("Mermaid rendering error:", err);
          setError("Could not render diagram.");
        }
      }
    }

    if (chart) {
      void renderDiagram();
    }

    return () => {
      isMounted = false;
    };
  }, [chart]);

  if (error) {
    return (
      <div style={{ padding: "12px", background: "#fef2f2", color: "#991b1b", borderRadius: "6px", fontSize: "12px" }}>
        <code>{chart}</code>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="mermaid-diagram-container"
      style={{
        margin: "12px 0",
        padding: "16px",
        background: "#ffffff",
        borderRadius: "8px",
        border: "1px solid #e2e8f0",
        overflowX: "auto",
        display: "flex",
        justifyContent: "center",
      }}
      dangerouslySetInnerHTML={{ __html: svgContent || `<div style="color: #94a3b8; font-size: 12px;">Rendering diagram...</div>` }}
    />
  );
}
