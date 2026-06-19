import { SkeletonBlock } from "@/components/UIBits";

export function ChartCard({ title, subtitle, right, children, testid, tall = false }) {
  return (
    <div className="uh-card p-5 h-full flex flex-col" data-testid={testid}>
      <div className="flex items-start justify-between mb-4 gap-3">
        <div>
          <div className="font-display text-base font-medium">{title}</div>
          {subtitle && <div className="text-[11px] text-[#9CA3AF] mt-0.5">{subtitle}</div>}
        </div>
        {right}
      </div>
      <div className={`flex-1 min-h-0 ${tall ? "min-h-[320px]" : "min-h-[220px]"}`}>{children}</div>
    </div>
  );
}

export function LoadingChart() {
  return (
    <div className="space-y-3">
      <div className="flex justify-between">
        <SkeletonBlock className="h-4 w-32" />
        <SkeletonBlock className="h-4 w-16" />
      </div>
      <SkeletonBlock className="h-44 w-full" />
    </div>
  );
}

export const chartTheme = {
  axis: "rgba(255,255,255,0.5)",
  grid: "rgba(255,255,255,0.08)",
  tooltipBg: "#1C2B3A",
  tooltipBorder: "rgba(255,255,255,0.1)",
  cyan: "#00D4FF",
  green: "#00E676",
  warn: "#F5A623",
  crit: "#FF4D4F",
};

export const tooltipStyle = {
  backgroundColor: chartTheme.tooltipBg,
  border: `1px solid ${chartTheme.tooltipBorder}`,
  borderRadius: "6px",
  fontSize: "12px",
  fontFamily: "IBM Plex Sans, sans-serif",
};
