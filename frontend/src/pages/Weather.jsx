import { useEffect, useState } from "react";
import { endpoints } from "@/lib/api";
import { SectionHeader, FlowTag, StatusBadge, SkeletonBlock } from "@/components/UIBits";
import { ChartCard, chartTheme, tooltipStyle, LoadingChart } from "@/components/ChartCard";
import MapFrance from "@/components/MapFrance";
import { AlertTriangle, Thermometer, Wind, Droplets, Gauge } from "lucide-react";
import KPICard from "@/components/KPICard";
import {
  ResponsiveContainer, LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, Tooltip, CartesianGrid, Legend,
} from "recharts";

export default function Weather() {
  const [ts, setTs] = useState(null);
  const [cities, setCities] = useState(null);
  const [alerts, setAlerts] = useState(null);

  useEffect(() => {
    endpoints.weather.timeseries(5).then((d) => setTs(d.data));
    endpoints.weather.cities().then((d) => setCities(d.data));
    endpoints.weather.alerts().then((d) => setAlerts(d.data));
  }, []);

  const last = ts ? ts[ts.length - 1] : null;
  const points = (cities || []).map((c) => ({
    lat: c.lat, lng: c.lng,
    label: c.name,
    value: `${c.temp}°C · ${c.condition}`,
    sub: `Vent ${c.wind} km/h · ${c.humidity}%`,
    color: c.anomaly ? chartTheme.crit : chartTheme.cyan,
    radius: 8 + Math.abs(c.temp) / 5,
  }));

  return (
    <div className="space-y-6" data-testid="page-weather">
      <SectionHeader
        eyebrow="Workspace · Météo"
        title="Weather Dashboard"
        right={<div className="flex items-center gap-2"><FlowTag flow="Batch" /><StatusBadge status="info">Source · NOAA</StatusBadge></div>}
        testid="weather-header"
      />

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Température" value={last?.temp || 0} suffix="°C" decimals={1} icon={Thermometer} tag="Batch" testid="weather-kpi-temp" />
        <KPICard label="Pression" value={last?.pressure || 0} suffix=" hPa" decimals={0} icon={Gauge} tag="Batch" testid="weather-kpi-pressure" />
        <KPICard label="Vent" value={last?.wind || 0} suffix=" km/h" decimals={1} icon={Wind} tag="Batch" testid="weather-kpi-wind" />
        <KPICard label="Précipitations" value={last?.precip || 0} suffix=" mm" decimals={1} icon={Droplets} tag="Batch" testid="weather-kpi-precip" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <ChartCard title="Température · 5 ans" subtitle="Moyenne mensuelle nationale" right={<FlowTag flow="Batch" />} tall testid="weather-chart-temp">
            {!ts ? <LoadingChart /> : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={ts} margin={{ top: 5, right: 12, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="wTemp" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={chartTheme.cyan} stopOpacity={0.6} />
                      <stop offset="100%" stopColor={chartTheme.cyan} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} interval={5} />
                  <YAxis tick={{ fill: chartTheme.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Area type="monotone" dataKey="temp" stroke={chartTheme.cyan} strokeWidth={2} fill="url(#wTemp)" name="Temp °C" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </div>
        <ChartCard title="Pression atmosphérique" subtitle="hPa · mensuel" right={<FlowTag flow="Batch" />} tall testid="weather-chart-pressure">
          {!ts ? <LoadingChart /> : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={ts.slice(-24)} margin={{ top: 5, right: 12, left: -10, bottom: 0 }}>
                <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} interval={3} />
                <YAxis tick={{ fill: chartTheme.axis, fontSize: 11 }} axisLine={false} tickLine={false} domain={["dataMin - 3", "dataMax + 3"]} />
                <Tooltip contentStyle={tooltipStyle} />
                <Line type="monotone" dataKey="pressure" stroke={chartTheme.green} strokeWidth={2} dot={false} name="hPa" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <ChartCard title="Vent" subtitle="km/h moyens" right={<FlowTag flow="Batch" />} testid="weather-chart-wind">
          {!ts ? <LoadingChart /> : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ts.slice(-12)} margin={{ top: 5, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(0,212,255,0.07)" }} />
                <Bar dataKey="wind" fill={chartTheme.cyan} radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
        <ChartCard title="Précipitations" subtitle="mm cumulés" right={<FlowTag flow="Batch" />} testid="weather-chart-precip">
          {!ts ? <LoadingChart /> : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ts.slice(-12)} margin={{ top: 5, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(0,230,118,0.07)" }} />
                <Bar dataKey="precip" fill={chartTheme.green} radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
        <div className="uh-card p-5" data-testid="weather-alerts">
          <div className="flex items-center justify-between mb-3">
            <div className="font-display text-base font-medium">Alertes anomalies</div>
            <div className="flex items-center gap-1.5 text-[#FF4D4F]"><AlertTriangle size={14} /><span className="text-xs">{alerts?.data?.length || 0}</span></div>
          </div>
          <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
            {!alerts && Array.from({ length: 4 }).map((_, i) => <SkeletonBlock key={i} className="h-14" />)}
            {alerts?.data?.map((a, i) => (
              <div key={i} className="bg-[#0B1F3B]/60 border border-white/10 rounded-md p-3 hover:border-[#00D4FF]/30 transition">
                <div className="flex justify-between items-start gap-2 mb-1">
                  <div className="text-sm font-medium">{a.title}</div>
                  <StatusBadge status={a.severity}>{a.severity}</StatusBadge>
                </div>
                <div className="text-[11px] text-[#9CA3AF]">{a.city} · {new Date(a.ts).toLocaleString("fr-FR", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit" })}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Map */}
      <ChartCard title="Carte météo France" subtitle="Anomalies surlignées en rouge" right={<FlowTag flow="Batch" />} tall testid="weather-map">
        <MapFrance points={points} height={420} />
      </ChartCard>
    </div>
  );
}
