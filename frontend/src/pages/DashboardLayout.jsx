import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "@/components/Sidebar";
import Topbar from "@/components/Topbar";

export default function DashboardLayout() {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <div className="min-h-screen bg-[#0B1F3B] text-white flex" data-testid="dashboard-layout">
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      <div className="flex-1 min-w-0 flex flex-col">
        <Topbar />
        <main className="flex-1 p-6 overflow-x-hidden uh-grid-bg-sm">
          <div className="max-w-[1600px] mx-auto uh-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
