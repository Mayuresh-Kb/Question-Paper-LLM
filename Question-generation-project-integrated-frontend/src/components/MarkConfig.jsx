import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from '../context/formState';
import { api, auth, errorMessage } from '../lib/api';
import { buildPayload, initialDraft } from '../lib/blueprint';
import BankReview from './BankReview';

function Configuration() {
  const { session, uploadId, token, draft: savedDraft, setDraft: persistDraft, handleGenerationSuccess, storageWarning } = useForm();
  const [draft, setDraft] = useState(() => savedDraft?.paper_format ? savedDraft : initialDraft(session.units));
  const [dirtyBanks, setDirtyBanks] = useState({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [health, setHealth] = useState(null);
  useEffect(() => { api.get('/health').then(({ data }) => setHealth(data)).catch(() => setHealth({ gemini_configured: false })); }, []);
  const update = value => { setDraft(value); persistDraft(value); };
  const header = (key, value) => update({ ...draft, header: { ...draft.header, [key]: value } });
  const plan = (id, key, value) => update({ ...draft, plans: { ...draft.plans, [id]: { ...draft.plans[id], [key]: value } } });
  const total = session.units.reduce((sum, u) => sum + (draft.plans[u.id]?.selected ? Number(draft.plans[u.id].marks) || 0 : 0), 0);
  const selectedCount = session.units.filter(u => draft.plans[u.id]?.selected).length;
  const hasDirtyBanks = Object.values(dirtyBanks).some(Boolean);
  async function generate(e) {
    e.preventDefault(); setError('');
    if (hasDirtyBanks) { setError('Save or discard your question-bank edits before generating.'); return; }
    setBusy(true);
    try {
      const payload = buildPayload(uploadId, draft, session.units);
      const { data } = await api.post('/generate', payload, auth(token));
      if (data.status !== 'ok' || !data.pdf_id) throw new Error('The server did not return a completed paper. Please retry.');
      handleGenerationSuccess(data.pdf_id);
    } catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  }
  function preset(kind) {
    if (kind === 'unit') {
      update({ ...draft, paper_format:'unit_test', header: { ...draft.header, exam_name:'Unit Test', duration:'1 hour' },
        plans: Object.fromEntries(session.units.map((u, i) => [u.id, { selected:i<2, marks:8, count:2 }])) });
      return;
    }
    const count = kind === 'mid' ? 2 : Math.min(4, session.units.length);
    update({ ...draft, paper_format:'custom', header: { ...draft.header, exam_name:kind === 'mid' ? 'Mid Term Examination' : 'End Semester Examination', duration:kind === 'mid' ? '1 hour' : '2 hours' },
      plans: Object.fromEntries(session.units.map((u, i) => [u.id, { selected:i<count, marks:kind === 'end' && count===4 && i>1 ? 20 : 15, count:2 }])) });
  }
  return <div className="space-y-8">
    <div><p className="eyebrow">Step 2 · Review & configure</p><h1 className="text-3xl font-semibold mt-2">Build your examination paper</h1>
      <p className="text-sm text-slate-600 mt-3">Review the extracted bank, then choose your units and marks. Each unit produces two alternative main questions; students attempt one.</p></div>
    {storageWarning && <p className="error-box">{storageWarning}</p>}
    <section className="space-y-3"><h2 className="text-lg font-semibold">1. Review your question banks</h2>
      <p className="text-sm text-slate-600">Upload order determines the initial unit order. Names, questions, source marks, topics, and Bloom levels can be corrected below.</p>
      {session.units.map(unit => <BankReview key={unit.id} unit={unit} onDirtyChange={(id, value) => setDirtyBanks(old => ({ ...old, [id]: value }))} />)}
    </section>
    <form onSubmit={generate} className="space-y-7">
      <fieldset disabled={busy} className="space-y-7 disabled:opacity-70">
        <section className="space-y-4"><h2 className="text-lg font-semibold">2. Examination details</h2>
          <div className="flex flex-wrap gap-2">{[['unit', 'Unit test · 16 marks'], ['mid', 'Mid term'], ['end', 'End semester']].map(([id, label]) => <button className="secondary-button" type="button" key={id} onClick={() => preset(id)}>{label}</button>)}</div>
          <div className="grid sm:grid-cols-2 gap-4">
            {[['institution','Institution',250], ['exam_name','Examination',200], ['subject','Subject',200], ['duration','Duration',80]].map(([id,label,max]) => <label key={id} className="field">{label}<input required maxLength={max} value={draft.header[id]} onChange={e => header(id,e.target.value)} /></label>)}
            <label className="field">Exam date<input type="date" value={draft.header.date} onChange={e => header('date',e.target.value)} /></label>
            <div className="rounded-lg bg-blue-50 p-4"><span className="text-xs uppercase text-blue-800 font-semibold">Total attemptable marks</span><p className="text-2xl font-semibold mt-1" aria-live="polite">{total}</p></div>
          </div>
          <label className="field">Additional instructions<textarea rows={3} maxLength={3000} value={draft.header.instructions} onChange={e => header('instructions',e.target.value)} /></label>
          <p className="text-xs text-slate-500">Unit test format uses exactly two units at 8 marks each: Q1 OR Q2 for the first unit, then Q3 OR Q4 for the second.</p>
        </section>
        <section className="space-y-4"><h2 className="text-lg font-semibold">3. Unit blueprint</h2>
          {session.units.map(u => <div key={u.id} className="grid sm:grid-cols-[1fr_140px_170px] gap-4 border-b border-slate-200 pb-4 items-end">
            <label className="text-sm"><input type="checkbox" checked={draft.plans[u.id]?.selected || false} disabled={draft.paper_format==='unit_test' && selectedCount>=2 && !draft.plans[u.id]?.selected} onChange={e => plan(u.id,'selected',e.target.checked)} /> <strong>{u.name}</strong><span className="block ml-5 text-xs text-slate-500 mt-1">{u.questions.filter(q=>q.enabled).length} questions available</span></label>
            <label className="field">Unit marks<input type="number" required min={1} max={200} disabled={!draft.plans[u.id]?.selected || draft.paper_format==='unit_test'} value={draft.plans[u.id]?.marks ?? 8} onChange={e => plan(u.id,'marks',e.target.value)} /></label>
            <label className="field">Subquestions / alternative<input type="number" required min={1} max={12} disabled={!draft.plans[u.id]?.selected} value={draft.plans[u.id]?.count ?? 2} onChange={e => plan(u.id,'count',e.target.value)} /></label>
          </div>)}
          <p className="text-xs text-slate-500">Two subquestions per alternative require four unique bank questions in each selected unit. A unit test always has four main questions; students attempt Q1 or Q2 and Q3 or Q4.</p>
        </section>
        <section className="space-y-4"><h2 className="text-lg font-semibold">4. Selection method</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <label className="field">Method<select value={draft.mode} onChange={e => update({ ...draft, mode:e.target.value })}>
              <option value="balanced">Balanced — difficulty & topic preferences</option><option value="random">Random — uniform sampling</option>
              <option value="gemini" disabled={!health?.gemini_configured}>Gemini-assisted{health?.gemini_configured ? '' : ' — API key required'}</option>
            </select></label>
            <label className="field">Difficulty preference<select disabled={draft.mode==='random'} value={draft.difficulty} onChange={e => update({ ...draft, difficulty:e.target.value })}>
              <option value="balanced">Mixed levels</option><option value="easy">Easy — Bloom 1–2</option><option value="medium">Medium — Bloom 3–4</option><option value="hard">Hard — Bloom 5–6</option>
            </select></label>
          </div>
          <p className="text-sm text-slate-600">Random and Balanced run locally. Difficulty balance depends on the questions and metadata available; it is not a guaranteed quota.</p>
          {draft.mode==='gemini' && <p className="text-sm text-amber-800">Gemini receives the selected units’ question text and metadata. It selects existing questions; it does not invent new questions. Requests can take up to about two minutes.</p>}
        </section>
      </fieldset>
      {hasDirtyBanks && <p className="text-sm text-amber-800">Save or discard your bank edits before generating.</p>}
      {error && <p role="alert" className="error-box">{error}</p>}
      <button className="primary-button w-full" disabled={busy || hasDirtyBanks || total<=0} type="submit">{busy ? 'Selecting questions and preparing your paper…' : 'Generate & preview paper'}</button>
    </form>
  </div>;
}
export default function ConfigurePage() {
  const { uploadId, session, loadingSession, sessionError } = useForm();
  if (loadingSession) return <p role="status">Restoring your question bank…</p>;
  if (!uploadId || !session || sessionError) return <div className="space-y-4"><h1 className="text-2xl font-semibold">Upload a question bank first</h1><p role="alert">{sessionError || 'Your session has no uploaded question bank.'}</p><Link className="primary-button inline-block" to="/upload">Go to upload</Link></div>;
  return <Configuration key={uploadId} />;
}
