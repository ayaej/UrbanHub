import { CountUp, FlowTag } from "@/components/UIBits";
import { TrendingUp, TrendingDown } from "lucide-react";

export default function KPICard({ label, value, delta, icon: Icon, tag, suffix = "", decimals = 0, testid }) {
  const positive = delta >= 0;
  return (
    <div className="uh-card p-5 h-full flex flex-col justify-between min-h-[126px]" data-testid={testid}>
      <div className="flex items-start justify-between gap-2">
        <div className="text-[10px] uppercase tracking-[0.22em] text-[#9CA3AF]">{label}</div>
        <div className="flex items-center gap-2">
          {tag && <FlowTag flow={tag} />}
          {Icon && (
            <div className="w-7 h-7 rounded-md bg-[#00D4FF]/10 border border-[#00D4FF]/30 flex items-center justify-center">
              <Icon size={14} className="text-[#00D4FF]" strokeWidth={1.8} />
            </div>
          )}
        </div>
      </div>
      <div className="mt-2">
        <div className="font-display text-3xl font-semibold tracking-tight">
          <CountUp value={value} decimals={decimals} suffix={suffix} />
        </div>
        {typeof delta === "number" && (
          <div className={`mt-1.5 inline-flex items-center gap-1 text-xs ${positive ? "text-[#00E676]" : "text-[#FF4D4F]"}`}>
            {positive ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
            {positive ? "+" : ""}{delta.toFixed(1)}%
            <span className="text-[#6B7280] ml-1">vs 7j</span>
          </div>
        )}
      </div>
    </div>
  );
}
