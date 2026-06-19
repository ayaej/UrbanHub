import { useEffect, useState } from "react";

export function StatusBadge({ status, children, testid }) {
  const map = {
    good: "bg-[#00E676]/15 text-[#00E676] border-[#00E676]/30",
    moderate: "bg-[#F5A623]/15 text-[#F5A623] border-[#F5A623]/30",
    warning: "bg-[#F5A623]/15 text-[#F5A623] border-[#F5A623]/30",
    critical: "bg-[#FF4D4F]/15 text-[#FF4D4F] border-[#FF4D4F]/30",
    info: "bg-[#00D4FF]/15 text-[#00D4FF] border-[#00D4FF]/30",
  };
  return (
    <span
      data-testid={testid}
      className={`inline-flex items-center gap-1.5 text-[10px] uppercase tracking-[0.18em] font-semibold px-2 py-0.5 rounded border ${map[status] || map.info}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current uh-pulse" />
      {children || status}
    </span>
  );
}

export function FlowTag({ flow }) {
  const map = {
    Batch: "bg-[#00D4FF]/15 text-[#00D4FF]",
    Streaming: "bg-[#00E676]/15 text-[#00E676]",
    IoT: "bg-[#F5A623]/15 text-[#F5A623]",
    Cross: "bg-white/10 text-white",
  };
  return (
    <span className={`text-[9px] uppercase tracking-[0.18em] font-semibold px-1.5 py-0.5 rounded ${map[flow] || map.Cross}`}>
      {flow}
    </span>
  );
}

export function CountUp({ value, duration = 900, suffix = "", decimals = 0 }) {
  const [v, setV] = useState(0);
  useEffect(() => {
    const num = typeof value === "number" ? value : parseFloat(value) || 0;
    if (!isFinite(num)) return;
    const start = performance.now();
    let raf;
    const tick = (t) => {
      const p = Math.min(1, (t - start) / duration);
      setV(num * (0.2 + 0.8 * (1 - Math.pow(1 - p, 3))));
      if (p < 1) raf = requestAnimationFrame(tick);
      else setV(num);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, duration]);
  const formatted = v.toLocaleString("fr-FR", { maximumFractionDigits: decimals });
  return <span className="uh-counter">{formatted}{suffix}</span>;
}

export function SkeletonBlock({ className = "" }) {
  return <div className={`animate-pulse bg-[#263B4F] rounded-md ${className}`} />;
}

export function SectionHeader({ eyebrow, title, right, testid }) {
  return (
    <div className="flex items-end justify-between gap-4 flex-wrap mb-5" data-testid={testid}>
      <div>
        {eyebrow && (
          <div className="text-[10px] uppercase tracking-[0.25em] text-[#00D4FF] mb-1.5">{eyebrow}</div>
        )}
        <h1 className="font-display text-2xl sm:text-3xl font-medium tracking-tight">{title}</h1>
      </div>
      {right}
    </div>
  );
}
