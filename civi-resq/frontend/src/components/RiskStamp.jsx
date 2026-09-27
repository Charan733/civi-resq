const LABELS = { low: "Low", moderate: "Moderate", high: "High", critical: "Critical" };

export default function RiskStamp({ category, size = "md" }) {
  if (!category) return null;
  const sizeClass = size === "sm" ? "text-[10px] px-2 py-0.5" : "text-xs px-3 py-1";
  return (
    <span className={`risk-stamp risk-stamp-${category} ${sizeClass}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {LABELS[category] || category}
    </span>
  );
}
