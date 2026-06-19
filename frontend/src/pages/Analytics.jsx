import { useEffect, useState } from "react";
import { endpoints } from "@/lib/api";
import { SectionHeader, FlowTag, StatusBadge, SkeletonBlock } from "@/components/UIBits";
import { ChartCard, chartTheme, tooltipStyle, LoadingChart } from "@/components/ChartCard";
import { Sparkles } from "lucide-react";
import {
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ZAxis,
} from "recharts";

export default function Analytics() {
  const [corr, setCorr] = useState(null);
  const [insights, setInsights] = useState(null);

  useEffect(() => {
    endpoints.analytics.correlation().then(setCorr);
    endpoints.analytics.insights().then((d) => setInsights(d.data));
  }, []);

  return (
    <div className="space-y-6" data-testid="page-analytics">
      <SectionHeader
        eyebrow="Workspace · Cross Analytics"
        title="Corrélations multi-sources"
        right={<div className="flex items-center gap-2"><FlowTag flow="Cross" /><StatusBadge status="info">Gold Layer</StatusBadge></div>}
        testid="analytics-header"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard
          title="Météo ↔ Pollution"
          subtitle="Température (°C) vs Pollution (AQI)"
          right={<FlowTag flow="Cross" />}
          tall
          testid="analytics-corr-wp"
        >
          {!corr ? <LoadingChart /> : (
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 12, left: -10, bottom: 6 }}>
                <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" />
                <XAxis type="number" dataKey="temp" name="Temp" unit="°C" tick={{ fill: chartTheme.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis type="number" dataKey="pollution" name="Pollution" unit="" tick={{ fill: chartTheme.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
                <ZAxis range={[40, 120]} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ strokeDasharray: "3 3", stroke: chartTheme.cyan }} />
                <Scatter data={corr.weather_pollution} fill={chartTheme.cyan} fillOpacity={0.7} />
              </ScatterChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard
          title="Météo ↔ Mobilité"
          subtitle="Précipitations (mm) vs Trajets vélo"
          right={<FlowTag flow="Cross" />}
          tall
          testid="analytics-corr-wm"
        >
          {!corr ? <LoadingChart /> : (
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 12, left: -10, bottom: 6 }}>
                <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" />
                <XAxis type="number" dataKey="precip" name="Précip" unit=" mm" tick={{ fill: chartTheme.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis type="number" dataKey="trips" name="Trajets" tick={{ fill: chartTheme.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
                <ZAxis range={[40, 120]} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ strokeDasharray: "3 3", stroke: chartTheme.green }} />
                <Scatter data={corr.weather_mobility} fill={chartTheme.green} fillOpacity={0.7} />
              </ScatterChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      {/* Insights IA */}
      <div className="uh-card p-5" data-testid="analytics-insights">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-md bg-[#00D4FF]/10 border border-[#00D4FF]/30 flex items-center justify-center">
              <Sparkles size={16} className="text-[#00D4FF]" />
            </div>
            <div>
              <div className="font-display text-base font-medium">Insights automatiques</div>
              <div className="text-[11px] text-[#9CA3AF]">Précalculés sur PostgreSQL · Gold Layer</div>
            </div>
          </div>
          <FlowTag flow="Cross" />
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {!insights && Array.from({ length: 6 }).map((_, i) => <SkeletonBlock key={i} className="h-32" />)}
          {insights?.map((it, i) => (
            <div key={i} className="bg-[#0B1F3B]/60 border border-white/10 rounded-md p-4 hover:border-[#00D4FF]/30 transition">
              <div className="flex items-start justify-between gap-2 mb-2">
                <FlowTag flow={it.tag} />
                <StatusBadge status={it.severity}>{it.severity}</StatusBadge>
              </div>
              <div className="text-sm font-medium">{it.title}</div>
              <div className="text-xs text-[#9CA3AF] mt-1.5 leading-relaxed">{it.summary}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
