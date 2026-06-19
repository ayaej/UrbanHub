import { Search, Bell, CircleUser } from "lucide-react";

export default function Topbar() {
  return (
    <header
      data-testid="topbar"
      className="h-16 sticky top-0 z-20 backdrop-blur-xl bg-[#0B1F3B]/80 border-b border-white/10 px-6 flex items-center gap-4"
    >
      <div className="flex-1 max-w-xl">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6B7280]" />
          <input
            data-testid="topbar-search"
            type="text"
            placeholder="Rechercher capteurs, stations, villes…"
            className="w-full bg-[#1C2B3A] border border-white/10 rounded-md pl-9 pr-3 py-2 text-sm placeholder:text-[#6B7280] focus:outline-none focus:border-[#00D4FF]/60 transition"
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="hidden md:inline-flex items-center gap-1.5 text-[10px] uppercase tracking-[0.2em] text-[#9CA3AF] px-2.5 py-1.5 rounded border border-white/10 bg-[#1C2B3A]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#00E676] uh-pulse" />
          Pipeline · Live
        </span>
        <button
          data-testid="topbar-notifications"
          className="relative w-9 h-9 rounded-md border border-white/10 bg-[#1C2B3A] hover:bg-[#263B4F] flex items-center justify-center text-[#9CA3AF] hover:text-white transition"
        >
          <Bell size={16} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-[#FF4D4F]" />
        </button>
        <div className="h-9 pl-2 pr-3 rounded-md border border-white/10 bg-[#1C2B3A] flex items-center gap-2 text-sm">
          <CircleUser size={18} className="text-[#00D4FF]" />
          <span className="hidden sm:inline text-xs">data.engineer@urbanhub</span>
        </div>
      </div>
    </header>
  );
}
