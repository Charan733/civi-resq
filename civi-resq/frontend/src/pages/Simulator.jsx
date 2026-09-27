import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Sliders as SlidersIcon, Play } from "lucide-react";
import { zonesApi, simulateApi } from "../api/client";
import RiskStamp from "../components/RiskStamp";

const SLIDER_PARAMS = [
  { key: "drainage_capacity_index", label: "Drainage Capacity Index", min: 0, max: 100 },
  { key: "green_cover_pct", label: "Green Cover %", min: 0, max: 60 },
  { key: "road_accessibility_index", label: "Road Accessibility Index", min: 0, max: 100 },
  { key: "impervious_surface_pct", label: "Impervious Surface %", min: 0, max: 100 },
];

export default function Simulator() {
  const [zones, setZones] = useState([]);
  const [selectedZoneId, setSelectedZoneId] = useState("");
  const [zoneParams, setZoneParams] = useState(null);
  const [modified, setModified] = useState({});
  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    zonesApi.list().then((zs) => {
      setZones(zs);
      if (zs.length) setSelectedZoneId(zs[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedZoneId) return;
    zonesApi.detail(selectedZoneId).then((d) => {
      setZoneParams(d.zone);
      setModified({});
      setResult(null);
    });
  }, [selectedZoneId]);

  const runSimulation = async () => {
    setRunning(true);
    try {
      const res = await simulateApi.run(selectedZoneId, modified);
      setResult(res);
    } catch (e) {
      alert("Simulation failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setRunning(false);
    }
  };

  const chartData = result
    ? [
        { name: "Flood", before: result.deltas.flood_risk_score.before, after: result.deltas.flood_risk_score.after },
        { name: "Heat", before: result.deltas.heat_risk_score.before, after: result.deltas.heat_risk_score.after },
        { name: "Accessibility", before: result.deltas.accessibility_risk_score.before, after: result.deltas.accessibility_risk_score.after },
        { name: "Overall", before: result.deltas.overall_vulnerability_score.before, after: result.deltas.overall_vulnerability_score.after },
      ]
    : [];

  return (
    <div className="p-5 md:p-8 max-w-[1100px]">
      <header className="mb-6">
        <h1 className="font-display text-2xl font-semibold text-ink-800 flex items-center gap-2">
          <SlidersIcon size={22} className="text-monsoon-500" /> What-If Civil Planning Simulator
        </h1>
        <p className="text-sm text-ink-500 mt-1">
          Hypothetically adjust intervention parameters and see the predicted change in risk — powered by the same ML models as live assessments.
        </p>
      </header>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Controls */}
        <div className="bg-white rounded-lg border border-ink-100 p-5">
          <label className="block text-xs font-semibold text-ink-500 uppercase tracking-wide mb-1.5">Select Zone</label>
          <select
            value={selectedZoneId}
            onChange={(e) => setSelectedZoneId(e.target.value)}
            className="w-full border border-ink-200 rounded-md px-3 py-2 text-sm mb-5 bg-paper-50"
          >
            {zones.map((z) => (
              <option key={z.id} value={z.id}>{z.zone_name} ({z.zone_code})</option>
            ))}
          </select>

          {zoneParams && (
            <div className="space-y-5">
              {SLIDER_PARAMS.map((p) => {
                const current = modified[p.key] ?? zoneParams[p.key];
                return (
                  <div key={p.key}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-medium text-ink-600">{p.label}</span>
                      <span className="font-mono text-ink-500">
                        {zoneParams[p.key]?.toFixed(0)} → <b className="text-monsoon-600">{current?.toFixed(0)}</b>
                      </span>
                    </div>
                    <input
                      type="range"
                      min={p.min}
                      max={p.max}
                      value={current}
                      onChange={(e) => setModified({ ...modified, [p.key]: Number(e.target.value) })}
                      className="w-full accent-monsoon-500"
                    />
                  </div>
                );
              })}

              <button
                onClick={runSimulation}
                disabled={running || Object.keys(modified).length === 0}
                className="w-full flex items-center justify-center gap-2 bg-monsoon-500 hover:bg-monsoon-600 text-white font-medium text-sm py-2.5 rounded-md disabled:opacity-40 transition-colors"
              >
                <Play size={15} /> {running ? "Running simulation…" : "Run Simulation"}
              </button>
              {Object.keys(modified).length === 0 && (
                <p className="text-xs text-ink-400 text-center">Move a slider to enable simulation</p>
              )}
            </div>
          )}
        </div>

        {/* Results */}
        <div className="bg-white rounded-lg border border-ink-100 p-5">
          <h2 className="font-display font-semibold text-ink-700 mb-3">Before vs. After</h2>
          {!result ? (
            <div className="h-64 flex items-center justify-center text-sm text-ink-400 text-center px-6">
              Adjust parameters and run a simulation to see predicted risk changes here.
            </div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#DCE4E7" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 11, fontFamily: "IBM Plex Mono" }} domain={[0, 100]} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="before" fill="#B7C7CE" name="Before" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="after" fill="#1F6F63" name="After" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
              <div className="grid grid-cols-2 gap-2 mt-4">
                {Object.entries(result.deltas).map(([key, d]) => (
                  <div key={key} className="bg-paper-100 rounded-md p-2.5">
                    <div className="text-[10px] text-ink-400 uppercase tracking-wide">{key.replace(/_/g, " ")}</div>
                    <div className="font-mono text-sm text-ink-700 mt-0.5">
                      {d.before.toFixed(1)} → {d.after.toFixed(1)}{" "}
                      <span className={d.change_pct < 0 ? "text-risk-low font-semibold" : "text-risk-high font-semibold"}>
                        ({d.change_pct > 0 ? "+" : ""}{d.change_pct}%)
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
