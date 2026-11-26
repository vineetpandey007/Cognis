import { useEffect, useState } from 'react';
import api from '../api/client';

export default function StudentPortalPage() {
  const [courses, setCourses] = useState([]);
  const [toast, setToast] = useState('');

  const loadCourses = async () => {
    const { data } = await api.get('/lms/my-courses');
    setCourses(data);
  };

  useEffect(() => {
    loadCourses();
  }, []);

  const notify = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(''), 3500);
  };

  const handleNextModule = async (course) => {
    const nextMod = Math.min(course.modules_completed + 1, course.total_modules);
    const { data } = await api.post('/lms/complete-module', { course_id: course.course_id, module_number: nextMod });
    notify(`Module ${nextMod} completed! Current CRM Stage: ${data.crm_stage}`);
    loadCourses();
  };

  const handleQuickQuiz = async (course) => {
    const score = Math.floor(78 + Math.random() * 21);
    const { data } = await api.post('/lms/submit-quiz', { course_id: course.course_id, score });
    notify(`Quiz scored ${score}% (New Avg: ${data.avg_quiz_score}%). Stage: ${data.crm_stage}`);
    loadCourses();
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">My Learning Tracks</h2>
          <p className="text-sm text-slate-400">Reach &ge;80% completion &amp; &ge;75% quiz average for automatic Interview_Ready promotion</p>
        </div>
        {toast && (
          <div className="text-xs px-3.5 py-2 rounded-lg bg-emerald-500/15 border border-emerald-500/40 text-emerald-300">
            {toast}
          </div>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {courses.map((c) => (
          <div key={c.enrollment_id} className="rounded-xl border border-slate-800 bg-slate-900 p-6 space-y-4">
            <div className="flex justify-between items-start gap-3">
              <div>
                <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">{c.domain}</span>
                <h3 className="text-lg font-semibold mt-1 text-white">{c.course_title}</h3>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 whitespace-nowrap">
                {c.crm_stage}
              </span>
            </div>

            <div className="text-sm text-slate-300">
              Progress: <span className="font-semibold text-white">{c.modules_completed}/{c.total_modules}</span> modules ({c.completion_pct}%) · Quiz Avg: <span className="font-semibold text-cyan-300">{c.avg_quiz_score}%</span>
            </div>

            <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
              <div className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-full transition-all" style={{ width: `${c.completion_pct}%` }} />
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => handleNextModule(c)}
                disabled={c.modules_completed >= c.total_modules}
                className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs disabled:opacity-40"
              >
                {c.modules_completed >= c.total_modules ? 'All Modules Completed' : `Complete Module ${c.modules_completed + 1}`}
              </button>
              <button
                onClick={() => handleQuickQuiz(c)}
                className="px-4 py-2 rounded-lg border border-slate-700 hover:bg-slate-800 text-xs font-medium"
              >
                Submit Assessment Quiz
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
