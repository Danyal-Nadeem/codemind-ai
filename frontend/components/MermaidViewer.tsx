"use client";

import React, { useEffect, useRef, useState } from "react";

interface MermaidProps {
  chart: string;
}

declare global {
  interface Window {
    mermaid?: any;
  }
}

export default function MermaidViewer({ chart }: MermaidProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (window.mermaid) {
      setLoaded(true);
      return;
    }

    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js";
    script.async = true;
    script.onload = () => {
      if (window.mermaid) {
        window.mermaid.initialize({
          startOnLoad: false,
          theme: "dark",
          securityLevel: "loose",
          flowchart: {
            useMaxWidth: false,
            htmlLabels: true
          }
        });
        setLoaded(true);
      }
    };
    script.onerror = () => {
      setError("Failed to load diagram renderer from CDN.");
    };
    document.body.appendChild(script);
  }, []);

  useEffect(() => {
    if (!loaded || !containerRef.current || !chart || !window.mermaid) return;

    containerRef.current.innerHTML = "";
    setError(null);

    const id = `mermaid-diag-${Math.floor(Math.random() * 1000000)}`;

    try {
      window.mermaid.render(id, chart).then(({ svg }: any) => {
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      }).catch((err: any) => {
        console.error("Mermaid render error:", err);
        setError("Invalid diagram syntax. Showing code instead.");
      });
    } catch (e: any) {
      console.error(e);
      setError("Failed to render diagram.");
    }
  }, [chart, loaded]);

  const handleDownloadSVG = () => {
    if (!containerRef.current) return;
    const svgElement = containerRef.current.querySelector("svg");
    if (!svgElement) return;

    const svgString = new XMLSerializer().serializeToString(svgElement);
    const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const svgUrl = URL.createObjectURL(svgBlob);
    
    const downloadLink = document.createElement("a");
    downloadLink.href = svgUrl;
    downloadLink.download = "architecture_diagram.svg";
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    URL.revokeObjectURL(svgUrl);
  };

  const handleDownloadPNG = () => {
    if (!containerRef.current) return;
    const svgElement = containerRef.current.querySelector("svg");
    if (!svgElement) return;

    const svgString = new XMLSerializer().serializeToString(svgElement);
    const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const svgUrl = URL.createObjectURL(svgBlob);

    const image = new Image();
    image.onload = () => {
      const canvas = document.createElement("canvas");
      // Scale resolution
      canvas.width = 1600;
      canvas.height = 1200;
      
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.fillStyle = "#09090b"; // dark backdrop
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob((blob) => {
          if (blob) {
            const pngUrl = URL.createObjectURL(blob);
            const downloadLink = document.createElement("a");
            downloadLink.href = pngUrl;
            downloadLink.download = "architecture_diagram.png";
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
            URL.revokeObjectURL(pngUrl);
          }
        }, "image/png");
      }
    };
    image.src = svgUrl;
  };

  return (
    <div className="flex flex-col space-y-4">
      {loaded && !error && (
        <div className="flex gap-3 justify-end">
          <button
            onClick={handleDownloadSVG}
            className="flex items-center gap-2 px-3 py-1.5 bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer"
          >
            Download SVG
          </button>
          <button
            onClick={handleDownloadPNG}
            className="flex items-center gap-2 px-3 py-1.5 bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer"
          >
            Download PNG
          </button>
        </div>
      )}

      {error ? (
        <div className="p-4 border border-rose-500/20 bg-rose-500/5 text-rose-400 rounded-xl text-sm space-y-3">
          <p className="font-semibold">{error}</p>
          <pre className="p-3 bg-zinc-950 border border-zinc-800 rounded-lg text-xs font-mono text-zinc-300 max-h-60 overflow-y-auto whitespace-pre-wrap">
            {chart}
          </pre>
        </div>
      ) : !loaded ? (
        <div className="flex items-center justify-center p-12 bg-zinc-900/50 border border-zinc-800 rounded-xl text-zinc-500 text-sm">
          Loading diagram renderer...
        </div>
      ) : (
        <div className="relative flex justify-center items-center w-full overflow-auto bg-zinc-950/80 p-8 rounded-xl border border-zinc-800 shadow-inner">
          <div ref={containerRef} className="w-full flex justify-center max-w-full" />
        </div>
      )}
    </div>
  );
}
