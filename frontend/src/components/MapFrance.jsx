import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";

/**
 * Generic Leaflet map (dark tiles) over France.
 * `points`: [{ lat, lng, color, value, label, sub }]
 */
export default function MapFrance({ points = [], center = [46.6, 2.5], zoom = 5.4, height = 360 }) {
  return (
    <div className="rounded-md overflow-hidden border border-white/10" style={{ height }}>
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={false}
        style={{ height: "100%", width: "100%", background: "#0B1F3B" }}
      >
        <TileLayer
          attribution='&copy; OpenStreetMap, &copy; CARTO'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        {points.map((p, i) => (
          <CircleMarker
            key={i}
            center={[p.lat, p.lng]}
            radius={p.radius || 9}
            pathOptions={{
              color: p.color || "#00D4FF",
              fillColor: p.color || "#00D4FF",
              fillOpacity: 0.65,
              weight: 1.5,
            }}
          >
            <Tooltip direction="top" offset={[0, -6]} opacity={1} className="!bg-[#1C2B3A] !text-white">
              <div className="font-display font-medium">{p.label}</div>
              {p.value !== undefined && <div className="text-xs">{p.value}</div>}
              {p.sub && <div className="text-[10px] text-[#9CA3AF]">{p.sub}</div>}
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
