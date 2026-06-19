import { Link } from "react-router-dom";
import { ArrowRight, Activity, Cloud, Bike, Radio, Database, BarChart3, Workflow } from "lucide-react";

const stats = [
  { label: "Sources connectées", value: "12+" },
  { label: "Capteurs IoT", value: "1 842" },
  { label: "Volume/h", value: "124 Go" },
  { label: "Disponibilité", value: "99.97%" },
];

const features = [
  { icon: Cloud, title: "Météo Batch", desc: "Historique 5 ans + alertes." },
  { icon: Bike, title: "Mobilité Streaming", desc: "Vélib temps réel via Kafka." },
  { icon: Radio, title: "Pollution IoT", desc: "PM2.5, NO₂, O₃ via MQTT." },
  { icon: BarChart3, title: "Cross Analytics", desc: "Corrélations multi-sources." },
  { icon: Database, title: "Data Lake MinIO", desc: "Bronze · Silver · Gold." },
  { icon: Workflow, title: "Orchestration n8n", desc: "Cron, webhooks, retry." },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-[#0B1F3B] text-white relative overflow-hidden">
      {/* Animated grid */}
      <div className="absolute inset-0 uh-hero-bg opacity-60 pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#0B1F3B]/40 to-[#0B1F3B] pointer-events-none" />

      {/* Topbar */}
      <header className="relative z-10 border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5" data-testid="brand-logo">
            <div className="w-8 h-8 rounded-md bg-[#00D4FF]/15 border border-[#00D4FF]/40 flex items-center justify-center">
              <Activity size={18} className="text-[#00D4FF]" strokeWidth={2} />
            </div>
            <div className="leading-tight">
              <div className="font-display font-semibold tracking-tight text-base">UrbanHub</div>
              <div className="text-[10px] uppercase tracking-[0.25em] text-[#9CA3AF]">Smart City · Data Platform</div>
            </div>
          </div>
          <nav className="hidden md:flex items-center gap-7 text-sm text-[#9CA3AF]">
            <a href="#features" className="hover:text-white transition-colors">Plateforme</a>
            <a href="#architecture" className="hover:text-white transition-colors">Architecture</a>
            <Link to="/dashboard/architecture" className="hover:text-white transition-colors">Stack</Link>
          </nav>
          <Link
            to="/dashboard"
            data-testid="cta-launch-app"
            className="text-sm bg-[#00D4FF] text-[#0B1F3B] font-medium px-4 py-2 rounded-md hover:brightness-110 transition"
          >
            Lancer l'app
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 pt-24 pb-20">
        <div className="grid lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-7 uh-fade-in">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#1C2B3A] border border-white/10 text-xs uppercase tracking-[0.2em] text-[#00D4FF] mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00E676] uh-pulse" />
              Live · Batch · IoT
            </div>
            <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-semibold tracking-tight leading-[1.02]">
              UrbanHub
              <span className="block text-[#00D4FF] text-3xl sm:text-4xl lg:text-5xl mt-3 font-medium">
                Smart City Big Data Platform
              </span>
            </h1>
            <p className="mt-6 text-base sm:text-lg text-[#9CA3AF] max-w-xl leading-relaxed">
              Visualisez la météo, la mobilité urbaine et la pollution en temps réel.
              Une console enterprise inspirée d'Azure / AWS / GCP, branchée sur votre
              stack <span className="text-white">Kafka · MQTT · MinIO · n8n · PostgreSQL · Metabase</span>.
            </p>

            <div className="mt-9 flex flex-wrap gap-3">
              <Link
                to="/dashboard"
                data-testid="cta-explore-dashboard"
                className="group inline-flex items-center gap-2 bg-[#00D4FF] text-[#0B1F3B] font-medium px-5 py-3 rounded-md hover:brightness-110 transition"
              >
                Explorer le Dashboard
                <ArrowRight size={18} className="group-hover:translate-x-0.5 transition" />
              </Link>
              <Link
                to="/dashboard/architecture"
                data-testid="cta-view-architecture"
                className="inline-flex items-center gap-2 border border-white/15 text-white px-5 py-3 rounded-md hover:bg-white/5 transition"
              >
                Voir l'architecture
              </Link>
            </div>

            <div className="mt-12 grid grid-cols-2 sm:grid-cols-4 gap-px bg-white/5 rounded-lg overflow-hidden border border-white/10">
              {stats.map((s) => (
                <div key={s.label} className="bg-[#0B1F3B] p-4">
                  <div className="text-[10px] uppercase tracking-[0.2em] text-[#9CA3AF] mb-1.5">{s.label}</div>
                  <div className="font-display text-2xl font-semibold uh-counter">{s.value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Right visual */}
          <div className="lg:col-span-5 uh-fade-in" style={{ animationDelay: "0.15s" }}>
            <HeroVisual />
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative z-10 max-w-7xl mx-auto px-6 pb-24">
        <div className="flex items-end justify-between mb-8 gap-4 flex-wrap">
          <div>
            <div className="text-[10px] uppercase tracking-[0.25em] text-[#00D4FF] mb-2">Plateforme</div>
            <h2 className="font-display text-3xl sm:text-4xl font-medium">Une vue d'ensemble unifiée</h2>
          </div>
          <p className="text-sm text-[#9CA3AF] max-w-md">
            6 dashboards spécialisés, conçus pour les data engineers et les décideurs urbains.
          </p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div key={f.title} className="uh-card p-6 group">
                <div className="w-10 h-10 rounded-md bg-[#00D4FF]/10 border border-[#00D4FF]/30 flex items-center justify-center mb-4 group-hover:bg-[#00D4FF]/20 transition">
                  <Icon size={20} className="text-[#00D4FF]" strokeWidth={1.7} />
                </div>
                <div className="font-display text-lg font-medium mb-1">{f.title}</div>
                <div className="text-sm text-[#9CA3AF]">{f.desc}</div>
              </div>
            );
          })}
        </div>
      </section>

      <footer className="relative z-10 border-t border-white/5 py-6 text-center text-xs text-[#6B7280]">
        UrbanHub · Smart City Data Platform · Built for Master Data &amp; IA
      </footer>
    </div>
  );
}

function HeroVisual() {
  return (
    <div className="relative">
      <div className="uh-card p-5 relative overflow-hidden">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#00E676] uh-pulse" />
            <span className="text-xs uppercase tracking-[0.2em] text-[#9CA3AF]">Live preview</span>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded bg-[#00D4FF]/15 text-[#00D4FF] uppercase tracking-[0.15em]">streaming</span>
        </div>

        {/* Mini chart */}
        <svg viewBox="0 0 320 140" className="w-full h-32">
          <defs>
            <linearGradient id="hg" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#00D4FF" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#00D4FF" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d="M0,90 C40,70 70,100 100,75 C130,55 160,85 200,60 C235,40 270,65 320,40 L320,140 L0,140 Z" fill="url(#hg)" />
          <path d="M0,90 C40,70 70,100 100,75 C130,55 160,85 200,60 C235,40 270,65 320,40" stroke="#00D4FF" strokeWidth="1.6" fill="none" />
        </svg>

        <div className="grid grid-cols-3 gap-3 mt-4">
          <MiniStat label="Trips/h" value="3 421" />
          <MiniStat label="AQI moy." value="62" />
          <MiniStat label="Temp." value="14.2°" />
        </div>
      </div>

      {/* Floating sub-card */}
      <div className="uh-card p-4 absolute -bottom-6 -left-6 w-56 hidden sm:block">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] uppercase tracking-[0.2em] text-[#9CA3AF]">IoT Alert</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#F5A623]/15 text-[#F5A623]">Warning</span>
        </div>
        <div className="font-display text-sm">PM2.5 Marseille‑Sud</div>
        <div className="text-xs text-[#9CA3AF] mt-1">Variance anormale détectée</div>
      </div>
    </div>
  );
}

function MiniStat({ label, value }) {
  return (
    <div className="bg-[#0B1F3B]/60 border border-white/5 rounded-md p-2.5">
      <div className="text-[10px] uppercase tracking-[0.15em] text-[#9CA3AF]">{label}</div>
      <div className="font-display text-base font-medium mt-0.5 uh-counter">{value}</div>
    </div>
  );
}
