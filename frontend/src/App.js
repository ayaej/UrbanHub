import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Landing from "@/pages/Landing";
import DashboardLayout from "@/pages/DashboardLayout";
import Overview from "@/pages/Overview";
import Weather from "@/pages/Weather";
import Mobility from "@/pages/Mobility";
import Pollution from "@/pages/Pollution";
import Analytics from "@/pages/Analytics";
import Architecture from "@/pages/Architecture";
import Settings from "@/pages/Settings";
import { Toaster } from "@/components/ui/sonner";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<Overview />} />
            <Route path="weather" element={<Weather />} />
            <Route path="mobility" element={<Mobility />} />
            <Route path="pollution" element={<Pollution />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="architecture" element={<Architecture />} />
            <Route path="settings" element={<Settings />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster theme="dark" position="top-right" />
    </div>
  );
}

export default App;
