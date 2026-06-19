import { useEffect, useState } from "react";
import { endpoints } from "@/lib/api";
import { SectionHeader, FlowTag, StatusBadge, SkeletonBlock } from "@/components/UIBits";
import { ChartCard, chartTheme, tooltipStyle, LoadingChart } from "@/components/ChartCard";
import MapFrance from "@/components/MapFrance";
import KPICard from "@/components/KPICard";
import { Bike, ParkingCircle, AlertOctagon, Activity } from "lucide-react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

export default function Mobility() {
  const [stations, setStations] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [critical, setCritical] = useState(null);

  useEffect(() => {
    endpoints.mobility.stations(240).then((d) => setStations(d.data));
    endpoints.mobility.timeline().then((d) => setTimeline(d.data));
    endpoints.mobility.critical().then((d) => setCritical(d.data));
  }, []);

  const totalBikes = stations ? stations.reduce((a, s) => a + s.bikes, 0) : 0;
  const totalSlots = stations ? stations.reduce((a, s) => a + s.slots, 0) : 0;
  const totalCap = stations ? stations.reduce((a, s) => a + s.capacity, 0) : 0;
  const occupation = totalCap ? ((totalBikes / totalCap) * 100) : 0;

  const points = (stations || []).map((s) => {
    const ratio = s.bikes / s.capacity;
    let color = chartTheme.green;
    if (ratio < 0.15 || ratio > 0.85) color = chartTheme.crit;
    else if (ratio < 0.3 || ratio > 0.7) color = chartTheme.warn;
    return {
      lat: s.lat, lng: s.lng,
      label: s.name, value: `${s.bikes}/${s.capacity} vélos`,
      sub: `${s.slots} places libres`,
      color, radius: 4 + s.capacity / 12,
    };
  });

  return (
    <div className="space-y-6" data-testid="page-mobility">
      <SectionHeader
        eyebrow="Workspace · Mobilité"
        title="Mobility Dashboard"
        right={<div className="flex items-center gap-2"><FlowTag flow="Streaming" /><StatusBadge status="good">Kafka OK</StatusBadge></div>}
        testid="mobility-header"
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Vélos disponibles" value={totalBikes} icon={Bike} tag="Streaming" testid="mobility-kpi-bikes" />
        <KPICard label="Places libres" value={totalSlots} icon={ParkingCircle} tag="Streaming" testid="mobility-kpi-slots" />
        <KPICard label="Stations actives" value={stations?.length || 0} icon={Activity} tag="Streaming" testid="mobility-kpi-stations" />
        <KPICard label="Occupation moyenne" value={occupation} suffix="%" decimals={1} delta={3.2} icon={AlertOctagon} tag="Streaming" testid="mobility-kpi-occupation" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3">
          <ChartCard title="Heatmap des stations" subtitle="Vélib temps réel · couleur = saturation" right={<FlowTag flow="Streaming" />} tall testid="mobility-map">
            <MapFrance points={points} center={[48.8566, 2.3522]} zoom={11} height={420} />
          </ChartCard>
        </div>
        <div className="lg:col-span-2">
          <ChartCard title="Pic d'utilisation · 24h" subtitle="Trajets / heure" right={<FlowTag flow="Streaming" />} tall testid="mobility-timeline">
            {!timeline ? <LoadingChart /> : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timeline} margin={{ top: 5, right: 8, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="mob1" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={chartTheme.green} stopOpacity={0.55} />
                      <stop offset="100%" stopColor={chartTheme.green} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" />
                  <XAxis dataKey="hour" tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} interval={2} />
                  <YAxis tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Area type="monotone" dataKey="trips" stroke={chartTheme.green} strokeWidth={2} fill="url(#mob1)" name="Trajets" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </div>
      </div>

      {/* Critical stations table */}
      <div className="uh-card p-5" data-testid="mobility-critical">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="font-display text-base font-medium">Stations critiques</div>
            <div className="text-[11px] text-[#9CA3AF] mt-0.5">Empty (0 vélo) ou Full (0 place) · Action requise</div>
          </div>
          <FlowTag flow="Streaming" />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[10px] uppercase tracking-[0.18em] text-[#9CA3AF] border-b border-white/10">
                <th className="text-left font-medium py-2 px-3">Station</th>
                <th className="text-left font-medium py-2 px-3">État</th>
                <th className="text-right font-medium py-2 px-3">Vélos</th>
                <th className="text-right font-medium py-2 px-3">Places</th>
                <th className="text-right font-medium py-2 px-3">Capacité</th>
              </tr>
            </thead>
            <tbody className="font-mono text-[13px]">
              {!critical && Array.from({ length: 6 }).map((_, i) => (
                <tr key={i}><td colSpan="5" className="p-2"><SkeletonBlock className="h-7 w-full" /></td></tr>
              ))}
              {critical?.data?.map((s) => (
                <tr key={s.id} className="border-b border-white/5 hover:bg-[#263B4F]/50 transition">
                  <td className="py-3 px-3 font-sans">{s.name} <span className="text-[10px] text-[#6B7280]">· {s.id}</span></td>
                  <td className="py-3 px-3"><StatusBadge status="critical">{s.status}</StatusBadge></td>
                  <td className="py-3 px-3 text-right">{s.bikes}</td>
                  <td className="py-3 px-3 text-right">{s.slots}</td>
                  <td className="py-3 px-3 text-right text-[#9CA3AF]">{s.capacity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
