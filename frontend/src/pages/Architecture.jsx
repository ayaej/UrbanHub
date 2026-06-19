import { useEffect, useState } from "react";
import { endpoints } from "@/lib/api";
import { SectionHeader, FlowTag, StatusBadge, SkeletonBlock } from "@/components/UIBits";
import { Database, Workflow, Cpu, Cloud, Bike, Radio, Boxes, BarChart3, Server, ArrowRight } from "lucide-react";

const iconFor = {
  source: Cloud,
  compute: Cpu,
  stream: Server,
  orchestrator: Workflow,
  storage: Database,
  warehouse: Boxes,
  consumer: BarChart3,
};

const flowColor = {
  batch: "#00D4FF",
  streaming: "#00E676",
  iot: "#F5A623",
};

export default function Architecture() {
  const [data, setData] = useState(null);

  useEffect(() => {
    endpoints.architecture.flows().then(setData);
  }, []);

  if (!data) {
    return (
      <div className="space-y-6">
        <SectionHeader eyebrow="Workspace · Architecture" title="Big Data Stack" />
        <SkeletonBlock className="h-[480px]" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="page-architecture">
      <SectionHeader
        eyebrow="Workspace · Architecture"
        title="UrbanHub Big Data Stack"
        right={<div className="flex items-center gap-2"><StatusBadge status="good">All flows OK</StatusBadge></div>}
        testid="architecture-header"
      />

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-3" data-testid="architecture-legend">
        {Object.entries(flowColor).map(([k, c]) => (
          <div key={k} className="inline-flex items-center gap-2 uh-card px-3 py-1.5">
            <span className="w-2 h-2 rounded-full" style={{ background: c }} />
            <span className="text-[10px] uppercase tracking-[0.2em] text-[#9CA3AF]">{k}</span>
          </div>
        ))}
      </div>

      {/* Diagram */}
      <div className="uh-card p-6 lg:p-8 overflow-x-auto uh-grid-bg" data-testid="architecture-diagram">
        <div className="min-w-[1100px] relative">
          <ArchitectureSVG />
        </div>
      </div>

      {/* Data quality */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" data-testid="architecture-dq">
        <DQCard label="Complétude" value={`${data.data_quality.completeness}%`} status="good" />
        <DQCard label="Fraîcheur" value={`${data.data_quality.freshness_seconds}s`} status="good" />
        <DQCard label="Schema drift" value={`${data.data_quality.schema_drift}`} status="good" />
        <DQCard label="Doublons" value={`${data.data_quality.duplicates_pct}%`} status="good" />
      </div>

      {/* Component reference */}
      <div className="uh-card p-5" data-testid="architecture-components">
        <div className="font-display text-base font-medium mb-1">Composants de la stack</div>
        <div className="text-[11px] text-[#9CA3AF] mb-4">Branchement avec Docker · n8n · MinIO · PostgreSQL · Metabase</div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {data.nodes.map((n) => {
            const Icon = iconFor[n.type] || Server;
            return (
              <div key={n.id} className="bg-[#0B1F3B]/60 border border-white/10 rounded-md p-3 hover:border-[#00D4FF]/30 transition">
                <div className="flex items-center gap-2 mb-1">
                  <Icon size={14} className="text-[#00D4FF]" />
                  <div className="text-sm font-medium">{n.label}</div>
                </div>
                <div className="text-[10px] uppercase tracking-[0.18em] text-[#9CA3AF]">{n.type}{n.flow ? ` · ${n.flow}` : ""}</div>
                {n.layers && (
                  <div className="flex gap-1 mt-2">
                    {n.layers.map((l) => (
                      <span key={l} className="text-[9px] uppercase tracking-[0.15em] px-1.5 py-0.5 rounded bg-[#00D4FF]/10 text-[#00D4FF]">{l}</span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Integration guide */}
      <div className="uh-card p-6" data-testid="architecture-integration-guide">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="font-display text-lg font-medium">Brancher la stack en local (Docker)</div>
            <div className="text-[11px] text-[#9CA3AF]">Guide rapide pour connecter UrbanHub à votre stack data engineering</div>
          </div>
          <StatusBadge status="info">Setup</StatusBadge>
        </div>
        <div className="grid lg:grid-cols-2 gap-4 text-sm">
          <CodeBlock title="docker-compose · services clés">
{`# UrbanHub stack
services:
  postgres:
    image: postgres:16
    environment: { POSTGRES_DB: urbanhub }
    ports: ["5432:5432"]
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]
  kafka:
    image: bitnami/kafka:3.7
    ports: ["9092:9092"]
  mosquitto:
    image: eclipse-mosquitto:2
    ports: ["1883:1883"]
  n8n:
    image: n8nio/n8n
    ports: ["5678:5678"]
  metabase:
    image: metabase/metabase
    ports: ["3001:3000"]`}
          </CodeBlock>
          <CodeBlock title="Bind UrbanHub backend">
{`# backend/.env
MONGO_URL=mongodb://localhost:27017
DB_NAME=urbanhub
POSTGRES_URL=postgresql://postgres@localhost/urbanhub
MINIO_ENDPOINT=http://localhost:9000
KAFKA_BROKER=localhost:9092
MQTT_BROKER=mqtt://localhost:1883
N8N_WEBHOOK=http://localhost:5678/webhook/urbanhub

# Replace mock endpoints by real connectors
# - /api/weather/timeseries  ← PostgreSQL (Gold)
# - /api/mobility/stations   ← Kafka topic "velib.live"
# - /api/pollution/sensors   ← MQTT topic "iot/air/+"`}
          </CodeBlock>
        </div>
      </div>
    </div>
  );
}

function DQCard({ label, value, status }) {
  return (
    <div className="uh-card p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="text-[10px] uppercase tracking-[0.22em] text-[#9CA3AF]">{label}</div>
        <StatusBadge status={status}>{status}</StatusBadge>
      </div>
      <div className="font-display text-2xl font-semibold uh-counter">{value}</div>
    </div>
  );
}

function CodeBlock({ title, children }) {
  return (
    <div className="bg-[#0B1F3B] border border-white/10 rounded-md overflow-hidden">
      <div className="px-3 py-2 border-b border-white/10 text-[11px] uppercase tracking-[0.18em] text-[#9CA3AF]">{title}</div>
      <pre className="text-[11.5px] leading-relaxed p-3 font-mono text-[#E5E7EB] overflow-x-auto">
        {children}
      </pre>
    </div>
  );
}

// SVG diagram - 3 flows converging into n8n → MinIO → Postgres → consumers
function ArchitectureSVG() {
  const nodes = [
    // Sources (left)
    { id: "weather", label: "NOAA / Météo APIs", icon: Cloud, x: 60, y: 60, flow: "batch" },
    { id: "bikes", label: "CityBikes / Vélib", icon: Bike, x: 60, y: 200, flow: "streaming" },
    { id: "iot", label: "Capteurs IoT", icon: Radio, x: 60, y: 340, flow: "iot" },

    // Middle compute
    { id: "python", label: "Python · Pandas / PyArrow", icon: Cpu, x: 320, y: 60, flow: "batch" },
    { id: "kafka", label: "Kafka Broker", icon: Server, x: 320, y: 200, flow: "streaming" },
    { id: "mqtt", label: "MQTT Broker", icon: Server, x: 320, y: 340, flow: "iot" },

    // n8n hub
    { id: "n8n", label: "n8n Orchestrator", icon: Workflow, x: 580, y: 200, wide: true },

    // Storage
    { id: "minio", label: "MinIO Data Lake", icon: Database, x: 820, y: 130, wide: true, layers: ["Bronze", "Silver", "Gold"] },
    { id: "postgres", label: "PostgreSQL", icon: Boxes, x: 820, y: 290, wide: true },

    // Consumers
    { id: "metabase", label: "Metabase", icon: BarChart3, x: 1060, y: 130 },
    { id: "urbanhub", label: "UrbanHub UI", icon: BarChart3, x: 1060, y: 290 },
  ];

  const edges = [
    ["weather", "python", "batch"],
    ["bikes", "kafka", "streaming"],
    ["iot", "mqtt", "iot"],
    ["python", "n8n", "batch"],
    ["kafka", "n8n", "streaming"],
    ["mqtt", "n8n", "iot"],
    ["n8n", "minio", "batch"],
    ["minio", "postgres", null],
    ["postgres", "metabase", null],
    ["postgres", "urbanhub", null],
  ];

  const getNode = (id) => nodes.find((n) => n.id === id);

  return (
    <svg viewBox="0 0 1180 480" className="w-full h-[480px]">
      {/* Edges */}
      {edges.map(([from, to, flow], i) => {
        const a = getNode(from);
        const b = getNode(to);
        const aw = a.wide ? 200 : 170;
        const bw = b.wide ? 200 : 170;
        const x1 = a.x + aw;
        const y1 = a.y + 30;
        const x2 = b.x;
        const y2 = b.y + 30;
        const mx = (x1 + x2) / 2;
        const path = `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
        const color = flow ? flowColor[flow] : "#9CA3AF";
        return (
          <g key={i}>
            <path d={path} fill="none" stroke={color} strokeOpacity="0.25" strokeWidth="2" />
            <path d={path} fill="none" stroke={color} strokeWidth="2"
              className={flow ? "uh-flow-line" : "uh-flow-line-slow"} />
          </g>
        );
      })}

      {/* Nodes */}
      {nodes.map((n) => {
        const w = n.wide ? 200 : 170;
        const color = n.flow ? flowColor[n.flow] : "#00D4FF";
        return (
          <g key={n.id} transform={`translate(${n.x}, ${n.y})`}>
            <rect width={w} height={60} rx="8" fill="#1C2B3A" stroke={color} strokeOpacity="0.45" />
            <rect x="0" y="0" width="3" height="60" fill={color} />
            <foreignObject x="14" y="10" width={w - 16} height="44">
              <div xmlns="http://www.w3.org/1999/xhtml" style={{ color: "#fff", fontFamily: "IBM Plex Sans" }}>
                <div style={{ fontSize: 9, letterSpacing: "0.18em", textTransform: "uppercase", color: "#9CA3AF" }}>
                  {n.flow || "core"}
                </div>
                <div style={{ fontSize: 13, fontWeight: 500, marginTop: 1 }}>{n.label}</div>
              </div>
            </foreignObject>
          </g>
        );
      })}
    </svg>
  );
}
