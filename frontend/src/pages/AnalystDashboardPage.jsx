import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import api from '../api/client';
import KpiCard from '../components/KpiCard';

export default function AnalystDashboardPage() {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    api.get('/analytics/summary').then((res) => setSummary(res.data));
  }, []);

  const handleExportCsv = async () => {
    const res = await api.get('/analytics/export/csv', { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'cognis_cohort_telemetry.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  if (!summary) return <div className="p-8 text-slate-400">Loading Cognis BI telemetry...</div>;

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">BI Command Center</h2>
          <p className="text-sm text-slate-400">Real-time cohort completion, placement funnel &amp; at-risk learner telemetry</p>
        </div>
        <button
          onClick={handleExportCsv}
          className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm"
        >
          Export Telemetry CSV
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Total Learners" value={summary.total_learners} subtext={`${summary.active_enrollments} active enrollments`} />
        <KpiCard label="Avg Completion" value={`${summary.avg_completion_rate}%`} subtext="Across active cohorts" />
        <KpiCard label="Avg Quiz Score" value={`${summary.avg_quiz_score}%`} subtext="Assessment benchmark" />
        <KpiCard label="Interview Ready" value={summary.interview_ready_count} subtext={`${summary.placed_count} Placed · ${summary.at_risk_count} At-Risk`} />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <h3 className="text-sm font-semibold mb-4 text-slate-200">Placement Pipeline Funnel</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={summary.stage_funnel}>
                <XAxis dataKey="stage" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }} />
                <Bar dataKey="count" name="Candidates" fill="#22d3ee" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <h3 className="text-sm font-semibold mb-4 text-slate-200">Cohort Completion vs. Quiz Score (%)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={summary.cohort_breakdown}>
                <XAxis dataKey="cohort" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }} />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="avg_completion" name="Completion %" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="avg_score" name="Quiz Avg %" fill="#34d399" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <h3 className="text-sm font-semibold mb-4 text-slate-200">At-Risk Learners (Inactive &gt;5 Days or Quiz Avg &lt;60%)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-slate-400 border-b border-slate-800 uppercase">
              <tr>
                <th className="py-2.5 pr-4">Learner</th>
                <th className="py-2.5 pr-4">Cohort</th>
                <th className="py-2.5 pr-4">Course</th>
                <th className="py-2.5 pr-4">Completion</th>
                <th className="py-2.5 pr-4">Quiz Avg</th>
                <th className="py-2.5">Inactive</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {summary.at_risk_learners.map((r, i) => (
                <tr key={i}>
                  <td className="py-2.5 pr-4 font-medium text-white">{r.student_name}</td>
                  <td className="py-2.5 pr-4 text-slate-400">{r.cohort}</td>
                  <td className="py-2.5 pr-4 text-slate-300">{r.course_title}</td>
                  <td className="py-2.5 pr-4">{r.completion_pct}%</td>
                  <td className="py-2.5 pr-4 text-amber-400">{r.avg_quiz_score}%</td>
                  <td className="py-2.5 text-rose-400">{r.days_inactive}d</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
