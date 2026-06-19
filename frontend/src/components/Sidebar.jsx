import { NavLink, Link } from "react-router-dom";
import {
  LayoutGrid, Cloud, Bike, Radio, GitMerge, Workflow, Settings as SettingsIcon, Activity, ChevronsLeft, ChevronsRight
} from "lucide-react";

const items = [
  { to: "/dashboard", label: "Overview", icon: LayoutGrid, end: true, testid: "sidebar-overview-link" },
  { to: "/dashboard/weather", label: "Weather", icon: Cloud, tag: "Batch", testid: "sidebar-weather-link" },
  { to: "/dashboard/mobility", label: "Mobility", icon: Bike, tag: "Streaming", testid: "sidebar-mobility-link" },
  { to: "/dashboard/pollution", label: "Pollution", icon: Radio, tag: "IoT", testid: "sidebar-pollution-link" },
  { to: "/dashboard/analytics", label: "Cross Analytics", icon: GitMerge, testid: "sidebar-analytics-link" },
  { to: "/dashboard/architecture", label: "Architecture", icon: Workflow, testid: "sidebar-architecture-link" },
  { to: "/dashboard/settings", label: "Settings", icon: SettingsIcon, testid: "sidebar-settings-link" },
];

const tagColors = {
  Batch: "bg-[#00D4FF]/15 text-[#00D4FF]",
  Streaming: "bg-[#00E676]/15 text-[#00E676]",
  IoT: "bg-[#F5A623]/15 text-[#F5A623]",
};

export default function Sidebar({ collapsed, setCollapsed }) {
  return (
    <aside
      data-testid="sidebar"
      className={`${collapsed ? "w-[72px]" : "w-64"} shrink-0 border-r border-white/10 bg-[#0B1F3B] flex flex-col transition-all duration-200 h-screen sticky top-0`}
    >
      <div className="h-16 flex items-center gap-2.5 px-4 border-b border-white/10">
        <Link to="/" className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-md bg-[#00D4FF]/15 border border-[#00D4FF]/40 flex items-center justify-center shrink-0">
            <Activity size={18} className="text-[#00D4FF]" strokeWidth={2} />
          </div>
          {!collapsed && (
            <div className="leading-tight min-w-0">
              <div className="font-display font-semibold tracking-tight truncate">UrbanHub</div>
              <div className="text-[9px] uppercase tracking-[0.25em] text-[#9CA3AF] truncate">Smart City</div>
            </div>
          )}
        </Link>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {!collapsed && (
          <div className="text-[10px] uppercase tracking-[0.25em] text-[#6B7280] px-2 mb-2">Workspace</div>
        )}
        {items.map((it) => {
          const Icon = it.icon;
          return (
            <NavLink
              key={it.to}
              to={it.to}
              end={it.end}
              data-testid={it.testid}
              className={({ isActive }) =>
                `group flex items-center gap-3 px-2.5 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? "bg-[#00D4FF]/12 text-white border border-[#00D4FF]/30"
                    : "text-[#9CA3AF] hover:bg-white/5 hover:text-white border border-transparent"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={18} strokeWidth={1.7} className={isActive ? "text-[#00D4FF]" : ""} />
                  {!collapsed && <span className="flex-1 truncate">{it.label}</span>}
                  {!collapsed && it.tag && (
                    <span className={`text-[9px] uppercase tracking-[0.15em] px-1.5 py-0.5 rounded ${tagColors[it.tag]}`}>
                      {it.tag}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="p-3 border-t border-white/10">
        {!collapsed && (
          <div className="uh-card p-3 mb-2">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00E676] uh-pulse" />
              <span className="text-[10px] uppercase tracking-[0.2em] text-[#9CA3AF]">Pipeline</span>
            </div>
            <div className="text-xs">All systems operational</div>
            <div className="text-[10px] text-[#6B7280] mt-1">Last sync · 12s ago</div>
          </div>
        )}
        <button
          data-testid="sidebar-toggle"
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center gap-2 text-xs text-[#9CA3AF] py-2 rounded-md hover:bg-white/5 hover:text-white transition"
        >
          {collapsed ? <ChevronsRight size={16} /> : <><ChevronsLeft size={16} /> Réduire</>}
        </button>
      </div>
    </aside>
  );
}
