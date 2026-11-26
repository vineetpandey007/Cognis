export default function KpiCard({ label, value, subtext }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-bold text-white">{value}</p>
      {subtext && <p className="mt-1.5 text-xs text-cyan-400">{subtext}</p>}
    </div>
  );
}
