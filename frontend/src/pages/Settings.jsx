import { useState } from "react";
import { SectionHeader, StatusBadge, FlowTag } from "@/components/UIBits";
import { toast } from "sonner";
import { Save } from "lucide-react";

export default function Settings() {
  const [refresh, setRefresh] = useState(30);
  const [theme, setTheme] = useState("Dark");
  const [alerts, setAlerts] = useState(true);

  return (
    <div className="space-y-6" data-testid="page-settings">
      <SectionHeader eyebrow="Workspace · Settings" title="Préférences plateforme" testid="settings-header" />

      <div className="grid lg:grid-cols-2 gap-4">
        <div className="uh-card p-5">
          <div className="font-display text-base font-medium mb-1">Apparence</div>
          <div className="text-[11px] text-[#9CA3AF] mb-4">Thème de la console UrbanHub</div>
          <div className="flex gap-2">
            {["Dark", "Light (soon)"].map((t) => (
              <button
                key={t}
                disabled={t.includes("soon")}
                onClick={() => setTheme(t)}
                data-testid={`settings-theme-${t.toLowerCase().split(" ")[0]}`}
                className={`px-4 py-2 rounded-md text-sm border transition ${
                  theme === t ? "border-[#00D4FF]/60 bg-[#00D4FF]/10 text-white" : "border-white/10 bg-[#0B1F3B]/40 text-[#9CA3AF] hover:bg-white/5"
                } disabled:opacity-40 disabled:cursor-not-allowed`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        <div className="uh-card p-5">
          <div className="font-display text-base font-medium mb-1">Rafraîchissement données</div>
          <div className="text-[11px] text-[#9CA3AF] mb-4">Intervalle de polling streaming / IoT</div>
          <div className="flex items-center gap-3">
            <input
              type="range" min="5" max="120" value={refresh}
              onChange={(e) => setRefresh(parseInt(e.target.value))}
              className="flex-1 accent-[#00D4FF]"
              data-testid="settings-refresh-slider"
            />
            <div className="font-display text-2xl uh-counter w-16 text-right">{refresh}s</div>
          </div>
        </div>

        <div className="uh-card p-5">
          <div className="font-display text-base font-medium mb-1">Alertes anomalies</div>
          <div className="text-[11px] text-[#9CA3AF] mb-4">Notifications IoT + Météo</div>
          <label className="inline-flex items-center gap-3 cursor-pointer">
            <span className="text-sm">{alerts ? "Activées" : "Désactivées"}</span>
            <button
              data-testid="settings-alerts-toggle"
              onClick={() => setAlerts(!alerts)}
              className={`w-12 h-6 rounded-full border transition ${alerts ? "bg-[#00D4FF]/30 border-[#00D4FF]/60" : "bg-white/5 border-white/10"}`}
            >
              <span className={`block w-5 h-5 rounded-full bg-white transition-transform ${alerts ? "translate-x-6" : "translate-x-0.5"}`} />
            </button>
          </label>
        </div>

        <div className="uh-card p-5">
          <div className="font-display text-base font-medium mb-1">Sources</div>
          <div className="text-[11px] text-[#9CA3AF] mb-4">État des connecteurs de données</div>
          <div className="space-y-2">
            {[
              { name: "PostgreSQL · Gold", tag: "Batch", status: "good" },
              { name: "Kafka · velib.live", tag: "Streaming", status: "good" },
              { name: "MQTT · iot/air/+", tag: "IoT", status: "warning" },
              { name: "MinIO · Bronze", tag: "Batch", status: "good" },
            ].map((s) => (
              <div key={s.name} className="flex items-center justify-between bg-[#0B1F3B]/60 border border-white/10 rounded-md px-3 py-2 text-sm">
                <div className="flex items-center gap-2"><FlowTag flow={s.tag} /><span>{s.name}</span></div>
                <StatusBadge status={s.status}>{s.status}</StatusBadge>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          data-testid="settings-save"
          onClick={() => toast.success("Préférences enregistrées", { description: "Profil utilisateur mis à jour." })}
          className="inline-flex items-center gap-2 bg-[#00D4FF] text-[#0B1F3B] font-medium px-5 py-2.5 rounded-md hover:brightness-110 transition"
        >
          <Save size={16} /> Enregistrer
        </button>
      </div>
    </div>
  );
}
