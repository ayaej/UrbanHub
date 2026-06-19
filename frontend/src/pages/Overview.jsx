import { useEffect, useState } from "react";
import { endpoints } from "@/lib/api";
import { SectionHeader, FlowTag, StatusBadge, SkeletonBlock } from "@/components/UIBits";
import { ChartCard, tooltipStyle, chartTheme, LoadingChart } from "@/components/ChartCard";
import KPICard from "@/components/KPICard";
import MapFrance from "@/components/MapFrance";
import {
  Bike, Cloud, Radio, Database, Activity, AlertTriangle, ArrowUpRight, Sparkles,
} from "lucide-react";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
  BarChart, Bar, Legend,
} from "recharts";

const iconForKey = {
  bike_trips: Bike, avg_pollution: Radio, active_sensors: Activity,
  weather_alerts: Cloud, data_volume: Database, stations_critical: AlertTriangle,
};

const tagForKey = {
  bike_trips: "Streaming", avg_pollution: "IoT", active_sensors: "IoT",
  weather_alerts: "Batch", data_volume: "Batch", stations_critical: "Streaming",
};

export default function Overview() {
  const [kpis, setKpis] = useState(null);
  const [weatherTs, setWeatherTs] = useState(null);
  const [pollutionTl, setPollutionTl] = useState(null);
  const [mobilityTl, setMobilityTl] = useState(null);
  const [cities, setCities] = useState(null);
  const [insights, setInsights] = useState(null);

  useEffect(() => {
    endpoints.analytics.kpis().then((d) => setKpis(d.data));
    endpoints.weather.timeseries(2).then((d) => setWeatherTs(d.data.slice(-12)));
    endpoints.pollution.timeline(null, 24).then((d) => setPollutionTl(d.data));
    endpoints.mobility.timeline().then((d) => setMobilityTl(d.data));
    endpoints.pollution.sensors().then((d) => setCities(d.data));
    endpoints.analytics.insights().then((d) => setInsights(d.data));
  }, []);

  const mapPoints = (cities || []).map((c) => ({
    lat: c.lat, lng: c.lng,
    label: c.name, value: `AQI ${c.aqi}`, sub: c.status,
    color: c.status === "critical" ? chartTheme.crit : c.status === "moderate" ? chartTheme.warn : chartTheme.green,
    radius: 7 + c.aqi / 25,
  }));

  return (
    <div className="space-y-6" data-testid="page-overview">
      <SectionHeader
        eyebrow="Workspace · Overview"
        title="Pulse de la ville en temps réel"
        right={<div className="flex items-center gap-2"><StatusBadge status="good">Pipeline OK</StatusBadge><FlowTag flow="Cross" /></div>}
        testid="overview-header"
      />

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4" data-testid="kpi-grid">
        {!kpis && Array.from({ length: 6 }).map((_, i) => (
          <SkeletonBlock key={i} className="h-[126px] col-span-1" />
        ))}
        {kpis && kpis.map((k) => (
          <KPICard
            key={k.key}
            label={k.label}
            value={k.value}
            delta={k.delta}
            icon={iconForKey[k.key]}
            tag={tagForKey[k.key]}
            testid={`kpi-${k.key}`}
          />
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <ChartCard
            title="Température nationale"
            subtitle="Moyenne mensuelle · 12 derniers mois"
            right={<FlowTag flow="Batch" />}
            testid="overview-weather-chart"
            tall
          >
            {!weatherTs ? <LoadingChart /> : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={weatherTs} margin={{ top: 5, right: 12, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="ovTemp" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={chartTheme.cyan} stopOpacity={0.55} />
                      <stop offset="100%" stopColor={chartTheme.cyan} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fill: chartTheme.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: chartTheme.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} cursor={{ stroke: chartTheme.cyan, strokeWidth: 1 }} />
                  <Area type="monotone" dataKey="temp" stroke={chartTheme.cyan} strokeWidth={2} fill="url(#ovTemp)" name="Temp °C" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </div>
        <ChartCard
          title="Trajets vélo · 24h"
          subtitle="Streaming Kafka"
          right={<FlowTag flow="Streaming" />}
          testid="overview-mobility-chart"
          tall
        >
          {!mobilityTl ? <LoadingChart /> : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mobilityTl} margin={{ top: 5, right: 5, left: -16, bottom: 0 }}>
                <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="hour" tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} interval={2} />
                <YAxis tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(0,212,255,0.08)" }} />
                <Bar dataKey="trips" fill={chartTheme.green} radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      {/* Map + Pollution timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <ChartCard
          title="Qualité de l'air · France"
          subtitle="Carte temps réel par ville"
          right={<FlowTag flow="IoT" />}
          testid="overview-pollution-map"
          tall
        >
          <div className="lg:col-span-3"><MapFrance points={mapPoints} height={300} /></div>
        </ChartCard>
        <div className="lg:col-span-2">
          <ChartCard
            title="Pollution · 24 dernières heures"
            subtitle="PM2.5 · PM10 · NO₂"
            right={<FlowTag flow="IoT" />}
            testid="overview-pollution-chart"
            tall
          >
            {!pollutionTl ? <LoadingChart /> : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={pollutionTl} margin={{ top: 5, right: 8, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="ovP25" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={chartTheme.warn} stopOpacity={0.5} />
                      <stop offset="100%" stopColor={chartTheme.warn} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" />
                  <XAxis dataKey="ts" tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} interval={3} />
                  <YAxis tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend wrapperStyle={{ fontSize: 11, color: chartTheme.axis }} />
                  <Area type="monotone" dataKey="pm25" stroke={chartTheme.warn} strokeWidth={1.6} fill="url(#ovP25)" name="PM2.5" />
                  <Area type="monotone" dataKey="no2" stroke={chartTheme.cyan} strokeWidth={1.6} fill="transparent" name="NO₂" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </div>
      </div>

      {/* Insights */}
      <div className="uh-card p-5" data-testid="overview-insights">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-[#00D4FF]/10 border border-[#00D4FF]/30 flex items-center justify-center">
              <Sparkles size={14} className="text-[#00D4FF]" />
            </div>
            <div>
              <div className="font-display text-base font-medium">Insights automatiques</div>
              <div className="text-[11px] text-[#9CA3AF]">Détectés sur la couche Gold du Data Lake</div>
            </div>
          </div>
          <a href="/dashboard/analytics" className="text-xs text-[#00D4FF] hover:underline inline-flex items-center gap-1">
            Voir tout <ArrowUpRight size={13} />
          </a>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {!insights && Array.from({ length: 3 }).map((_, i) => <SkeletonBlock key={i} className="h-24" />)}
          {insights && insights.slice(0, 3).map((it, i) => (
            <div key={i} className="bg-[#0B1F3B]/60 border border-white/10 rounded-md p-4">
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
