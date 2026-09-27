import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts";
import { AlertTriangle, Activity, MapPinned, Wrench, TrendingUp } from "lucide-react";
import { analyticsApi, zonesApi } from "../api/client";
import RiskStamp from "../components/RiskStamp";

const RISK_COLORS = { low: "#4C9A6B", moderate: "#D9A441", high: "#D97D34", critical: "#C1443A" };

function StatCard({ icon: Icon, label, value, sublabel, accent }) {
  return (
    <div className="bg-white rounded-lg border border-ink-100 p-5 flex items-start gap-4">
      <div className={`w-10 h-10 rounded-md flex items-center justify-center flex-shrink-0 ${accent}`}>
        <Icon size={19} className="text-white" />
      </div>
      <div className="min-w-0">
        <div className="text-2xl font-display font-semibold text-ink-800 tabular-nums">{value}</div>
        <div className="text-sm text-ink-500 mt-0.5">{label}</div>
        {sublabel && <div className="text-xs text-ink-400 mt-1 font-mono">{sublabel}</div>}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([analyticsApi.dashboard(), zonesApi.list()])
      .then(([s, z]) => {
        setStats(s);
        setZones(z);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-96 text-ink-400 font-mono text-sm">
        Loading assessment data…
      </div>
    );
  }
  if (error) {
    return (
      <div className="p-8">
        <div className="bg-risk-critical/10 border border-risk-critical text-risk-critical rounded-lg p-4 text-sm">
          Couldn't reach the CIVI-RESQ API ({error}). Confirm the backend is running at the configured API URL.
        </div>
      </div>
    );
  }

  const pieData = [
    { name: "Low", value: stats.low_zones, key: "low" },
    { name: "Moderate", value: stats.moderate_zones, key: "moderate" },
    { name: "High", value: stats.high_zones, key: "high" },
    { name: "Critical", value: stats.critical_zones, key: "critical" },
  ];

  const topZones = [...zones]
    .filter((z) => z.overall_vulnerability_score != null)
    .sort((a, b) => b.overall_vulnerability_score - a.overall_vulnerability_score)
    .slice(0, 6);

  const metricsData = Object.entries(stats.model_metrics || {}).map(([risk, m]) => ({
    risk: risk[0].toUpperCase() + risk.slice(1),
    r2: m.r2_score,
    mae: m.mae,
  }));

  return (
    <div className="p-5 md:p-8 max-w-[1400px]">
      <header className="mb-7">
        <h1 className="font-display text-2xl md:text-3xl font-semibold text-ink-800 tracking-tight">
          Urban Vulnerability Overview
        </h1>
        <p className="text-ink-500 text-sm mt-1">
          AI-assisted preliminary risk assessment across {stats.total_zones} monitored zones — Guntur &amp; Vijayawada
        </p>
      </header>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon={MapPinned} label="Zones Analyzed" value={stats.total_zones} accent="bg-ink-600" />
        <StatCard
          icon={AlertTriangle}
          label="Critical Zones"
          value={stats.critical_zones}
          sublabel={`${stats.high_zones} high risk`}
          accent="bg-risk-critical"
        />
        <StatCard
          icon={Activity}
          label="Avg. Vulnerability"
          value={stats.avg_vulnerability_score?.toFixed(1)}
          sublabel="out of 100"
          accent="bg-monsoon-500"
        />
        <StatCard
          icon={Wrench}
          label="Interventions Recommended"
          value={stats.total_interventions_recommended}
          sublabel={`${stats.urgent_interventions} urgent`}
          accent="bg-ink-500"
        />
      </div>

      <div className="grid lg:grid-cols-5 gap-6 mb-8">
        {/* Risk distribution */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-ink-100 p-5">
          <h2 className="font-display font-semibold text-ink-700 mb-1">Overall Risk Distribution</h2>
          <p className="text-xs text-ink-400 mb-2">Zones by overall vulnerability category</p>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={2}>
                {pieData.map((entry) => (
                  <Cell key={entry.key} fill={RISK_COLORS[entry.key]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-3 justify-center mt-1">
            {pieData.map((d) => (
              <div key={d.key} className="flex items-center gap-1.5 text-xs text-ink-500">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: RISK_COLORS[d.key] }} />
                {d.name} ({d.value})
              </div>
            ))}
          </div>
        </div>

        {/* Model performance */}
        <div className="lg:col-span-3 bg-white rounded-lg border border-ink-100 p-5">
          <h2 className="font-display font-semibold text-ink-700 mb-1">ML Model Performance</h2>
          <p className="text-xs text-ink-400 mb-3">
            R² score per risk model (XGBoost regressors, evaluated on held-out test split)
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={metricsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#DCE4E7" />
              <XAxis dataKey="risk" tick={{ fontSize: 12, fontFamily: "Inter" }} />
              <YAxis domain={[0, 1]} tick={{ fontSize: 11, fontFamily: "IBM Plex Mono" }} />
              <Tooltip />
              <Bar dataKey="r2" fill="#1F6F63" radius={[4, 4, 0, 0]} name="R² Score" />
            </BarChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-3 gap-3 mt-3 text-xs">
            {Object.entries(stats.model_metrics || {}).map(([risk, m]) => (
              <div key={risk} className="bg-paper-100 rounded-md p-2.5 font-mono">
                <div className="text-ink-600 font-semibold uppercase">{risk}</div>
                <div className="text-ink-400 mt-0.5">MAE {m.mae} · RMSE {m.rmse}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top risk zones */}
      <div className="bg-white rounded-lg border border-ink-100 p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-display font-semibold text-ink-700 flex items-center gap-2">
            <TrendingUp size={17} className="text-risk-critical" />
            Highest-Risk Zones
          </h2>
          <Link to="/map" className="text-xs text-monsoon-600 font-medium hover:underline">
            View all on map →
          </Link>
        </div>
        <div className="divide-y divide-ink-100">
          {topZones.map((z) => (
            <Link
              key={z.id}
              to={`/zones/${z.id}`}
              className="flex items-center justify-between py-3 hover:bg-paper-100 -mx-2 px-2 rounded transition-colors"
            >
              <div>
                <div className="font-medium text-ink-700 text-sm">{z.zone_name}</div>
                <div className="text-xs text-ink-400 font-mono">
                  {z.zone_code} · {z.city}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm text-ink-600 tabular-nums">
                  {z.overall_vulnerability_score?.toFixed(1)}
                </span>
                <RiskStamp category={z.overall_risk_category} size="sm" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
