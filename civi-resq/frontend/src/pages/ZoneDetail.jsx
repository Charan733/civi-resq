import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, RefreshCw, Droplets, Thermometer, Navigation as NavIcon, Download } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from "recharts";
import { zonesApi } from "../api/client";
import RiskStamp from "../components/RiskStamp";

const RISK_COLORS = { low: "#4C9A6B", moderate: "#D9A441", high: "#D97D34", critical: "#C1443A" };

function ScoreGauge({ label, score, category, icon: Icon }) {
  return (
    <div className="bg-white rounded-lg border border-ink-100 p-4">
      <div className="flex items-center gap-2 text-ink-500 text-xs font-medium uppercase tracking-wide mb-2">
        <Icon size={14} /> {label}
      </div>
      <div className="flex items-end justify-between">
        <span className="font-display text-3xl font-semibold text-ink-800 tabular-nums">{score?.toFixed(1)}</span>
        <RiskStamp category={category} size="sm" />
      </div>
      <div className="mt-2 h-1.5 bg-paper-200 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${score}%`, background: RISK_COLORS[category] }}
        />
      </div>
    </div>
  );
}

function ExplanationChart({ factors, riskLabel }) {
  const data = [...factors]
    .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
    .slice(0, 6)
    .map((f) => ({
      name: f.feature.replace(/_/g, " "),
      impact: f.impact,
      value: f.value,
    }));
  return (
    <div>
      <h3 className="text-sm font-semibold text-ink-600 mb-2">{riskLabel} — Top Contributing Factors (SHAP)</h3>
      <ResponsiveContainer width="100%" height={Math.max(160, data.length * 34)}>
        <BarChart data={data} layout="vertical" margin={{ left: 110, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#DCE4E7" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} />
          <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={105} />
          <Tooltip
            formatter={(val, _name, props) => [
              `${val > 0 ? "+" : ""}${val.toFixed(1)} pts (value: ${props.payload.value})`,
              "Impact",
            ]}
          />
          <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.impact >= 0 ? "#C1443A" : "#4C9A6B"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="text-[11px] text-ink-400 mt-1">
        Red bars increase risk, green bars decrease it — magnitude shows the estimated point impact on the score.
      </p>
    </div>
  );
}

const COST_LABELS = { low: "Low (<10L)", medium: "Medium (10L-1Cr)", high: "High (1Cr-10Cr)", very_high: "Very High (>10Cr)" };

export default function ZoneDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reassessing, setReassessing] = useState(false);

  const load = () => {
    setLoading(true);
    zonesApi
      .detail(id)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [id]);

  const handleReassess = async () => {
    setReassessing(true);
    try {
      await zonesApi.reassess(id);
      load();
    } catch (e) {
      alert("Reassessment requires civil_engineer or admin login.");
    } finally {
      setReassessing(false);
    }
  };

  if (loading) return <div className="p-8 text-ink-400 font-mono text-sm">Loading zone profile…</div>;
  if (error) return <div className="p-8 text-risk-critical text-sm">Error: {error}</div>;
  if (!data) return null;

  const { zone, risk_assessment, interventions } = data;

  return (
    <div className="p-5 md:p-8 max-w-[1200px]">
      <Link to="/map" className="inline-flex items-center gap-1.5 text-sm text-ink-500 hover:text-ink-700 mb-4">
        <ArrowLeft size={15} /> Back to map
      </Link>

      <header className="flex flex-wrap items-start justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="font-display text-2xl font-semibold text-ink-800">{zone.zone_name}</h1>
            {risk_assessment && <RiskStamp category={risk_assessment.overall_risk_category} />}
          </div>
          <p className="text-sm text-ink-500 font-mono mt-1">
            {zone.zone_code} · {zone.city}, {zone.state} · {zone.land_use_type}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {risk_assessment && (
            <div className="text-right">
              <div className="font-display text-3xl font-semibold text-ink-800 tabular-nums">
                {risk_assessment.overall_vulnerability_score.toFixed(1)}
              </div>
              <div className="text-[11px] text-ink-400 uppercase tracking-wide">Overall Vulnerability</div>
            </div>
          )}
          <button
            onClick={handleReassess}
            disabled={reassessing}
            className="flex items-center gap-1.5 text-xs font-medium bg-ink-700 text-white px-3 py-2 rounded-md hover:bg-ink-600 disabled:opacity-50"
          >
            <RefreshCw size={13} className={reassessing ? "animate-spin" : ""} /> Reassess
          </button>
          {risk_assessment && (
            <a
              href={`${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}/api/reports/zones/${id}/pdf`}
              className="flex items-center gap-1.5 text-xs font-medium bg-monsoon-500 text-white px-3 py-2 rounded-md hover:bg-monsoon-600"
            >
              <Download size={13} /> Download Report
            </a>
          )}
        </div>
      </header>

      {!risk_assessment ? (
        <div className="bg-paper-100 border border-ink-100 rounded-lg p-6 text-center text-ink-500 text-sm">
          This zone hasn't been assessed yet. Click "Reassess" to run the risk models.
        </div>
      ) : (
        <>
          {/* Score gauges */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <ScoreGauge label="Flood / Waterlogging Risk" score={risk_assessment.flood_risk_score} category={risk_assessment.flood_risk_category} icon={Droplets} />
            <ScoreGauge label="Urban Heat Risk" score={risk_assessment.heat_risk_score} category={risk_assessment.heat_risk_category} icon={Thermometer} />
            <ScoreGauge label="Accessibility Risk" score={risk_assessment.accessibility_risk_score} category={risk_assessment.accessibility_risk_category} icon={NavIcon} />
          </div>

          {/* Raw parameters */}
          <div className="bg-white rounded-lg border border-ink-100 p-5 mb-6">
            <h2 className="font-display font-semibold text-ink-700 mb-3">Input Parameters</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              {[
                ["Rainfall", `${zone.avg_annual_rainfall_mm} mm/yr`],
                ["Elevation", `${zone.elevation_m} m`],
                ["Drainage Capacity", `${zone.drainage_capacity_index}/100`],
                ["Impervious Surface", `${zone.impervious_surface_pct}%`],
                ["Population Density", `${zone.population_density_per_km2}/km²`],
                ["Road Accessibility", `${zone.road_accessibility_index}/100`],
                ["Green Cover", `${zone.green_cover_pct}%`],
                ["Land Surface Temp", `${zone.avg_land_surface_temp_c}°C`],
                ["Building Density", `${zone.building_density_pct}%`],
                ["Dist. to Hospital", `${zone.dist_to_hospital_km} km`],
                ["Dist. to School", `${zone.dist_to_school_km} km`],
                ["Flood Events (5yr)", zone.historical_flood_events_5yr],
              ].map(([label, val]) => (
                <div key={label} className="bg-paper-100 rounded-md p-2.5">
                  <div className="text-[10px] text-ink-400 uppercase tracking-wide">{label}</div>
                  <div className="font-mono font-medium text-ink-700 mt-0.5">{val}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Explainability */}
          <div className="bg-white rounded-lg border border-ink-100 p-5 mb-6">
            <h2 className="font-display font-semibold text-ink-700 mb-1">Why This Score? (Explainable AI)</h2>
            <p className="text-xs text-ink-400 mb-4">
              SHAP feature-importance breakdown showing exactly which inputs drove each ML prediction.
            </p>
            <div className="grid md:grid-cols-3 gap-6">
              <ExplanationChart factors={risk_assessment.explanation.flood} riskLabel="Flood Risk" />
              <ExplanationChart factors={risk_assessment.explanation.heat} riskLabel="Heat Risk" />
              <ExplanationChart factors={risk_assessment.explanation.accessibility} riskLabel="Accessibility Risk" />
            </div>
            <div className="mt-4 pt-4 border-t border-ink-100 text-xs text-ink-500 font-mono">
              {risk_assessment.explanation.overall_formula}
            </div>
          </div>

          {/* Interventions */}
          <div className="bg-white rounded-lg border border-ink-100 p-5">
            <h2 className="font-display font-semibold text-ink-700 mb-3">Recommended Interventions</h2>
            {interventions.length === 0 ? (
              <p className="text-sm text-ink-400">No interventions triggered — this zone's risk levels are within acceptable thresholds.</p>
            ) : (
              <div className="space-y-3">
                {interventions.map((iv) => (
                  <div key={iv.id} className="border border-ink-100 rounded-lg p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                      <h3 className="font-semibold text-ink-700 capitalize">{iv.intervention_type.replace(/_/g, " ")}</h3>
                      <span
                        className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full font-semibold ${
                          iv.priority_level === "urgent"
                            ? "bg-risk-critical/15 text-risk-critical"
                            : iv.priority_level === "high"
                            ? "bg-risk-high/15 text-risk-high"
                            : iv.priority_level === "medium"
                            ? "bg-risk-moderate/15 text-risk-moderate"
                            : "bg-risk-low/15 text-risk-low"
                        }`}
                      >
                        {iv.priority_level} priority
                      </span>
                    </div>
                    <p className="text-sm text-ink-500 mb-3">{iv.reason}</p>
                    <div className="flex flex-wrap gap-4 text-xs font-mono text-ink-500">
                      <span>Cost: <b className="text-ink-700">{COST_LABELS[iv.estimated_cost_category]}</b></span>
                      <span>Risk Reduction: <b className="text-ink-700">~{iv.expected_risk_reduction_pct}%</b></span>
                      <span>Affected Pop.: <b className="text-ink-700">{iv.affected_population.toLocaleString()}</b></span>
                      <span>Priority Score: <b className="text-ink-700">{iv.priority_score}/100</b></span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
