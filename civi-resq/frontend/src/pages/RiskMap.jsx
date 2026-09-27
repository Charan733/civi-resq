import { useEffect, useState, useMemo } from "react";
import { MapContainer, TileLayer, Polygon, Tooltip as LeafletTooltip, useMap } from "react-leaflet";
import { useNavigate } from "react-router-dom";
import { Search, Filter } from "lucide-react";
import "leaflet/dist/leaflet.css";
import { zonesApi } from "../api/client";

const RISK_COLORS = { low: "#4C9A6B", moderate: "#D9A441", high: "#D97D34", critical: "#C1443A" };
const RISK_TYPES = [
  { key: "overall_risk_category", label: "Overall" },
  { key: "flood_risk_score", label: "Flood" },
  { key: "heat_risk_score", label: "Heat" },
  { key: "accessibility_risk_score", label: "Accessibility" },
];

function FitBounds({ zones }) {
  const map = useMap();
  useEffect(() => {
    if (!zones.length) return;
    const bounds = zones.map((z) => [z.centroid_lat, z.centroid_lng]);
    map.fitBounds(bounds, { padding: [40, 40] });
  }, [zones, map]);
  return null;
}

export default function RiskMap() {
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    zonesApi
      .list()
      .then(setZones)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const filteredZones = useMemo(() => {
    return zones.filter((z) => {
      if (categoryFilter !== "all" && z.overall_risk_category !== categoryFilter) return false;
      if (search && !`${z.zone_name} ${z.zone_code}`.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [zones, categoryFilter, search]);

  if (loading) {
    return <div className="p-8 flex items-center justify-center h-96 text-ink-400 font-mono text-sm">Loading zone map…</div>;
  }
  if (error) {
    return (
      <div className="p-8">
        <div className="bg-risk-critical/10 border border-risk-critical text-risk-critical rounded-lg p-4 text-sm">
          Couldn't reach the CIVI-RESQ API ({error}).
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Filter bar */}
      <div className="bg-white border-b border-ink-100 px-5 py-3 flex flex-wrap items-center gap-3 z-10">
        <h1 className="font-display font-semibold text-ink-800 mr-2">Risk Map</h1>
        <div className="flex items-center gap-1.5 bg-paper-100 rounded-md px-2.5 py-1.5 flex-1 min-w-[180px] max-w-xs">
          <Search size={14} className="text-ink-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search zone name or code…"
            className="bg-transparent text-sm outline-none w-full placeholder:text-ink-400"
          />
        </div>
        <div className="flex items-center gap-1.5 text-sm">
          <Filter size={14} className="text-ink-400" />
          {["all", "low", "moderate", "high", "critical"].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-2.5 py-1 rounded-full text-xs font-medium capitalize transition-colors ${
                categoryFilter === cat
                  ? "bg-ink-700 text-white"
                  : "bg-paper-100 text-ink-500 hover:bg-paper-300"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
        <span className="text-xs text-ink-400 font-mono ml-auto">{filteredZones.length} zones shown</span>
      </div>

      {/* Map + legend */}
      <div className="flex-1 relative">
        <MapContainer center={[16.4, 80.5]} zoom={11} className="w-full h-full" scrollWheelZoom>
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <FitBounds zones={zones} />
          {filteredZones.map((z) => (
            <Polygon
              key={z.id}
              positions={z.geometry.map(([lng, lat]) => [lat, lng])}
              pathOptions={{
                color: RISK_COLORS[z.overall_risk_category] || "#999",
                fillColor: RISK_COLORS[z.overall_risk_category] || "#999",
                fillOpacity: 0.45,
                weight: 2,
              }}
              eventHandlers={{ click: () => navigate(`/zones/${z.id}`) }}
            >
              <LeafletTooltip sticky>
                <div className="font-body">
                  <div className="font-semibold text-sm">{z.zone_name}</div>
                  <div className="text-xs text-ink-500">
                    Overall: {z.overall_vulnerability_score?.toFixed(1)} · {z.overall_risk_category}
                  </div>
                </div>
              </LeafletTooltip>
            </Polygon>
          ))}
        </MapContainer>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur rounded-lg border border-ink-100 p-3 shadow-sm z-[1000]">
          <div className="text-[10px] font-mono uppercase tracking-wider text-ink-400 mb-1.5">Risk Category</div>
          <div className="flex flex-col gap-1">
            {Object.entries(RISK_COLORS).map(([k, color]) => (
              <div key={k} className="flex items-center gap-2 text-xs text-ink-600 capitalize">
                <span className="w-3 h-3 rounded-sm" style={{ background: color }} />
                {k}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
