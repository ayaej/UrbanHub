import { useEffect, useState } from "react";
import { endpoints } from "@/lib/api";
import { SectionHeader, FlowTag, StatusBadge, SkeletonBlock } from "@/components/UIBits";
import { ChartCard, chartTheme, tooltipStyle, LoadingChart } from "@/components/ChartCard";
import MapFrance from "@/components/MapFrance";
import KPICard from "@/components/KPICard";
import { Radio, AlertTriangle, Wind, Sparkles } from "lucide-react";
import {
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
  CartesianGrid, Legend,
} from "recharts";

export default function Pollution() {
  const [sensors, setSensors] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [comp, setComp] = useState(null);

  useEffect(() => {
    endpoints.pollution.sensors().then((d) => setSensors(d.data));
    endpoints.pollution.timeline(null, 48).then((d) => setTimeline(d.data));
    endpoints.pollution.comparison().then((d) => setComp(d.data));
  }, []);

  const avgAqi = sensors ? Math.round(sensors.reduce((a, c) => a + c.aqi, 0) / sensors.length) : 0;
  const critical = sensors ? sensors.filter((c) => c.status === "critical").length : 0;
  const points = (sensors || []).map((c) => ({
    lat: c.lat, lng: c.lng,
    label: c.name, value: `AQI ${c.aqi}`,
    sub: `PM2.5 ${c.pm25} · NO₂ ${c.no2}`,
    color: c.status === "critical" ? chartTheme.crit : c.status === "moderate" ? chartTheme.warn : chartTheme.green,
    radius: 7 + c.aqi / 18,
  }));

  // Latest reading for "pic anormaux" detection
  const peaks = timeline ? timeline.slice(-12).filter((t) => t.pm25 > 18 || t.no2 > 38).slice(0, 4) : [];

  return (
    <div className="space-y-6" data-testid="page-pollution">
      <SectionHeader
        eyebrow="Workspace · Pollution"
        title="Pollution Dashboard"
        right={<div className="flex items-center gap-2"><FlowTag flow="IoT" /><StatusBadge status="info">MQTT · OpenAQ</StatusBadge></div>}
        testid="pollution-header"
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="AQI moyen" value={avgAqi} delta={-1.4} icon={Wind} tag="IoT" testid="pollution-kpi-aqi" />
        <KPICard label="Capteurs critiques" value={critical} icon={AlertTriangle} tag="IoT" testid="pollution-kpi-critical" />
        <KPICard label="PM2.5 moy." value={timeline?.[timeline.length - 1]?.pm25 || 0} suffix=" μg/m³" decimals={1} icon={Radio} tag="IoT" testid="pollution-kpi-pm25" />
        <KPICard label="NO₂ moy." value={timeline?.[timeline.length - 1]?.no2 || 0} suffix=" μg/m³" decimals={1} icon={Radio} tag="IoT" testid="pollution-kpi-no2" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3">
          <ChartCard title="Carte pollution France" subtitle="AQI par ville · IoT temps réel" right={<FlowTag flow="IoT" />} tall testid="pollution-map">
            <MapFrance points={points} height={420} />
          </ChartCard>
        </div>
        <div className="lg:col-span-2">
          <ChartCard title="Timeline 48h" subtitle="PM2.5 · PM10 · NO₂ · O₃" right={<FlowTag flow="IoT" />} tall testid="pollution-timeline">
            {!timeline ? <LoadingChart /> : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timeline} margin={{ top: 5, right: 8, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="pollPM" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={chartTheme.warn} stopOpacity={0.55} />
                      <stop offset="100%" stopColor={chartTheme.warn} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" />
                  <XAxis dataKey="ts" tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} interval={5} />
                  <YAxis tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend wrapperStyle={{ fontSize: 11, color: chartTheme.axis }} />
                  <Area type="monotone" dataKey="pm25" stroke={chartTheme.warn} strokeWidth={1.6} fill="url(#pollPM)" name="PM2.5" />
                  <Area type="monotone" dataKey="no2" stroke={chartTheme.cyan} strokeWidth={1.6} fill="transparent" name="NO₂" />
                  <Area type="monotone" dataKey="o3" stroke={chartTheme.green} strokeWidth={1.6} fill="transparent" name="O₃" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <ChartCard title="Comparaison villes" subtitle="PM2.5 · PM10 · NO₂ (μg/m³)" right={<FlowTag flow="IoT" />} testid="pollution-comparison">
            {!comp ? <LoadingChart /> : (
              <ResponsiveContainer width="100%" height={290}>
                <BarChart data={comp.data} margin={{ top: 5, right: 12, left: -16, bottom: 0 }}>
                  <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="city" tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} angle={-15} dy={6} />
                  <YAxis tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(0,212,255,0.06)" }} />
                  <Legend wrapperStyle={{ fontSize: 11, color: chartTheme.axis }} />
                  <Bar dataKey="pm25" name="PM2.5" fill={chartTheme.warn} radius={[3, 3, 0, 0]} />
                  <Bar dataKey="pm10" name="PM10" fill={chartTheme.cyan} radius={[3, 3, 0, 0]} />
                  <Bar dataKey="no2" name="NO₂" fill={chartTheme.green} radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </div>
        <div className="uh-card p-5" data-testid="pollution-peaks">
          <div className="flex items-center justify-between mb-3">
            <div className="font-display text-base font-medium">Détection pics anormaux</div>
            <Sparkles size={14} className="text-[#00D4FF]" />
          </div>
          <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
            {!timeline && Array.from({ length: 3 }).map((_, i) => <SkeletonBlock key={i} className="h-14" />)}
            {peaks.length === 0 && timeline && (
              <div className="text-xs text-[#9CA3AF]">Aucun pic récent détecté.</div>
            )}
            {peaks.map((p, i) => (
              <div key={i} className="bg-[#0B1F3B]/60 border border-white/10 rounded-md p-3">
                <div className="flex items-center justify-between mb-1">
                  <div className="text-sm font-medium font-mono">{p.ts}</div>
                  <StatusBadge status="warning">peak</StatusBadge>
                </div>
                <div className="text-[11px] text-[#9CA3AF] font-mono">
                  PM2.5: {p.pm25} · NO₂: {p.no2} · O₃: {p.o3}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
