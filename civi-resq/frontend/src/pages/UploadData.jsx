import { useState } from "react";
import { Upload, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import { zonesApi } from "../api/client";
import { useAuth } from "../context/AuthContext";

const CSV_COLUMNS = [
  "zone_code", "zone_name", "city", "state", "centroid_lat", "centroid_lng",
  "avg_annual_rainfall_mm", "elevation_m", "drainage_capacity_index", "land_use_type",
  "impervious_surface_pct", "population_density_per_km2", "road_accessibility_index",
  "green_cover_pct", "avg_land_surface_temp_c", "building_density_pct",
  "dist_to_hospital_km", "dist_to_school_km", "dist_to_emergency_service_km",
  "historical_flood_events_5yr",
];

export default function UploadData() {
  const { user } = useAuth();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);
    try {
      const res = await zonesApi.uploadCsv(file);
      setResult(res);
    } catch (e) {
      setError(e.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  if (!user || (user.role !== "admin" && user.role !== "civil_engineer")) {
    return (
      <div className="p-8 max-w-lg">
        <div className="bg-paper-100 border border-ink-100 rounded-lg p-6 text-sm text-ink-500">
          Uploading real-world zone data requires an admin or civil_engineer account. Please sign in first.
        </div>
      </div>
    );
  }

  return (
    <div className="p-5 md:p-8 max-w-2xl">
      <header className="mb-6">
        <h1 className="font-display text-2xl font-semibold text-ink-800">Upload Real-World Zone Data</h1>
        <p className="text-sm text-ink-500 mt-1">
          Replace or extend the demo dataset with real municipal survey data via CSV. Each row triggers a full
          risk assessment + intervention recommendation automatically on upload.
        </p>
      </header>

      <div className="bg-white rounded-lg border border-ink-100 p-5 mb-5">
        <h2 className="font-display font-semibold text-ink-700 mb-2 text-sm">Required CSV Columns</h2>
        <div className="flex flex-wrap gap-1.5">
          {CSV_COLUMNS.map((c) => (
            <span key={c} className="text-[11px] font-mono bg-paper-100 text-ink-600 px-2 py-1 rounded">
              {c}
            </span>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg border border-ink-100 p-6">
        <label className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-ink-200 rounded-lg py-10 cursor-pointer hover:border-monsoon-400 transition-colors">
          <Upload size={28} className="text-ink-400" />
          <span className="text-sm text-ink-500">
            {file ? file.name : "Click to select a .csv file"}
          </span>
          <input type="file" accept=".csv" className="hidden" onChange={(e) => setFile(e.target.files[0])} />
        </label>

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="w-full mt-4 flex items-center justify-center gap-2 bg-monsoon-500 hover:bg-monsoon-600 text-white font-medium text-sm py-2.5 rounded-md disabled:opacity-40"
        >
          <FileText size={15} /> {uploading ? "Uploading & assessing…" : "Upload & Assess"}
        </button>

        {error && (
          <div className="mt-4 flex items-start gap-2 bg-risk-critical/10 border border-risk-critical text-risk-critical rounded-md p-3 text-sm">
            <AlertCircle size={16} className="flex-shrink-0 mt-0.5" /> {error}
          </div>
        )}

        {result && (
          <div className="mt-4 space-y-2">
            <div className="flex items-center gap-2 bg-risk-low/10 border border-risk-low text-risk-low rounded-md p-3 text-sm">
              <CheckCircle2 size={16} className="flex-shrink-0" /> {result.created} zone(s) created and assessed.
            </div>
            {result.errors?.length > 0 && (
              <div className="bg-risk-moderate/10 border border-risk-moderate text-risk-moderate rounded-md p-3 text-xs space-y-1">
                {result.errors.map((e, i) => (
                  <div key={i}>{e}</div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
