import { useEffect, useState } from 'react';
import api from '../api/client';

const STAGES = ['Enrolled', 'Screening', 'Interview_Ready', 'Placed'];

export default function CrmPipelinePage() {
  const [candidates, setCandidates] = useState([]);
  const [stageFilter, setStageFilter] = useState('ALL');

  const loadCandidates = async () => {
    const { data } = await api.get('/crm/candidates');
    setCandidates(data);
  };

  useEffect(() => {
    loadCandidates();
  }, []);

  const handleStageChange = async (enrollmentId, newStage) => {
    await api.patch(`/crm/candidates/${enrollmentId}/stage`, { new_stage: newStage });
    loadCandidates();
  };

  const filtered = stageFilter === 'ALL' ? candidates : candidates.filter((c) => c.crm_stage === stageFilter);

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">CRM Placement Pipeline</h2>
          <p className="text-sm text-slate-400">Every stage override is recorded in the immutable audit log</p>
        </div>
        <div className="flex gap-2">
          {['ALL', ...STAGES].map((st) => (
            <button
              key={st}
              onClick={() => setStageFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border ${
                stageFilter === st
                  ? 'bg-cyan-500 text-slate-950 border-cyan-400'
                  : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-800 text-xs uppercase text-slate-400">
            <tr>
              <th className="p-4">Candidate</th>
              <th className="p-4">Cohort</th>
              <th className="p-4">Course</th>
              <th className="p-4">Completion</th>
              <th className="p-4">Quiz Avg</th>
              <th className="p-4">CRM Stage</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {filtered.map((c) => (
              <tr key={c.enrollment_id} className="hover:bg-slate-800/40">
                <td className="p-4">
                  <div className="font-medium text-white">{c.student_name}</div>
                  <div className="text-xs text-slate-400">{c.email}</div>
                </td>
                <td className="p-4 text-xs text-slate-300">{c.cohort}</td>
                <td className="p-4 text-xs text-slate-300">{c.course_title}</td>
                <td className="p-4">{c.completion_pct}%</td>
                <td className="p-4">{c.avg_quiz_score}%</td>
                <td className="p-4">
                  <select
                    value={c.crm_stage}
                    onChange={(e) => handleStageChange(c.enrollment_id, e.target.value)}
                    className="rounded-lg bg-slate-950 border border-slate-700 px-2.5 py-1.5 text-xs focus:border-cyan-400 focus:outline-none"
                  >
                    {STAGES.map((st) => (
                      <option key={st} value={st}>{st}</option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
