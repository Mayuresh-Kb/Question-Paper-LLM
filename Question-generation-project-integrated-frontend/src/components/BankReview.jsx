import { useState } from 'react';
import { useForm } from '../context/formState';
import { api, auth, errorMessage } from '../lib/api';
import SourceFigure from './SourceFigure';
export default function BankReview({ unit, onDirtyChange }) {
  const { uploadId, token, setSession } = useForm();
  const [editing, setEditing] = useState(false);
  const [questions, setQuestions] = useState(unit.questions);
  const [name, setName] = useState(unit.name);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const change = (id, field, value) => { setQuestions(old => old.map(q => q.id === id ? { ...q, [field]: value } : q)); onDirtyChange(unit.id, true); };
  async function save() {
    setSaving(true); setError('');
    try {
      const payload = { unit_id: unit.id, name, questions: questions.map(q => ({ id: q.id, text: q.text,
        source_marks: Number(q.source_marks), bloom: Number(q.bloom), topic: q.topic,
        enabled: q.enabled, include_figures: q.include_figures, render_mode: 'text' })) };
      const { data } = await api.put(`/uploads/${uploadId}/unit`, payload, auth(token));
      setSession(data); onDirtyChange(unit.id, false); setEditing(false);
    } catch (e) { setError(errorMessage(e)); } finally { setSaving(false); }
  }
  const cancel = () => { setQuestions(unit.questions); setName(unit.name); setError(''); setEditing(false); onDirtyChange(unit.id, false); };
  return <section className="border border-slate-200 rounded-xl overflow-hidden">
    <button type="button" className="w-full text-left p-4 flex justify-between gap-3 hover:bg-slate-50" onClick={() => setEditing(v => !v)} aria-expanded={editing}>
      <span><strong>{unit.name}</strong><span className="block text-xs text-slate-500 mt-1">{unit.filename} · {unit.questions.filter(q => q.enabled).length} enabled / {unit.questions.length} extracted</span></span>
      <span className="text-blue-700 text-sm shrink-0">{editing ? 'Collapse' : 'Review & edit'}</span>
    </button>
    {editing && <div className="p-4 border-t border-slate-200 space-y-5">
      <label className="field">Unit name<input value={name} maxLength={200} onChange={e => { setName(e.target.value); onDirtyChange(unit.id, true); }} /></label>
      {unit.warnings.map((warning, i) => <p key={i} className="text-xs text-amber-800">{warning}</p>)}
      <p className="text-sm text-slate-600">Correct extraction errors and metadata here. Bloom: 1 Remember, 2 Understand, 3 Apply, 4 Analyze, 5 Evaluate, 6 Create. Estimated levels need teacher review.</p>
      {questions.map((q, i) => <div key={q.id} className="border-t border-slate-200 pt-4 space-y-3">
        <div className="flex items-center justify-between text-sm"><strong>Question {i+1}{q.source_page ? ` · page ${q.source_page}` : ''}</strong>
          <label><input type="checkbox" checked={q.enabled} onChange={e => change(q.id, 'enabled', e.target.checked)} /> Include in bank</label></div>
        {q.extraction_method === 'ocr' && <p className="text-sm text-amber-800">Read with OCR{q.ocr_confidence != null ? ` · recognition score ${q.ocr_confidence}/100` : ''}. This score is not a guarantee of accuracy. Check wording, numbering and marks against the scan.</p>}
        {q.quality_issues?.length > 0 && <ul className="list-disc pl-5 text-sm text-red-700">{q.quality_issues.map(issue => <li key={issue}>{issue}</li>)}</ul>}
        {!q.source_fragments?.length && q.source_previews?.length > 0 && <details className="text-sm"><summary className="cursor-pointer text-blue-700">Compare with source scan (review only)</summary>
          {q.source_previews.map(asset => <SourceFigure key={asset} {...{ asset, uploadId, token }} alt="Original scanned question excerpt for comparison with OCR text" />)}</details>}
        {q.source_fragments?.length > 0 && <details className="text-sm"><summary className="cursor-pointer text-blue-700">Compare with original question</summary>
          <p className="text-slate-600 mt-2">Review only: the generated PDF prints the corrected text below, not this source image.</p>
          {q.source_fragments.map(asset => <SourceFigure key={asset} {...{asset, uploadId, token}} alt="Original question for comparison" />)}</details>}
        <label className="field">Question text for PDF<textarea rows={4} maxLength={12000} value={q.text} onChange={e => change(q.id, 'text', e.target.value)} /></label>
        <div className="grid sm:grid-cols-3 gap-3">
          <label className="field">Source marks<input type="number" min={1} max={200} value={q.source_marks} onChange={e => change(q.id, 'source_marks', e.target.value)} /></label>
          <label className="field">Bloom level ({q.bloom_source})<select value={q.bloom} onChange={e => change(q.id, 'bloom', e.target.value)}>{[1,2,3,4,5,6].map(n => <option key={n} value={n}>{n}</option>)}</select></label>
          <label className="field">Topic (optional)<input maxLength={150} value={q.topic} onChange={e => change(q.id, 'topic', e.target.value)} /></label>
        </div>
        {q.assets.length > 0 && <><label className="text-sm"><input type="checkbox" checked={q.include_figures} onChange={e => change(q.id, 'include_figures', e.target.checked)} /> Include diagram or image with this question</label>
          {q.assets.map(asset => <SourceFigure key={asset} {...{ asset, uploadId, token }} />)}</>}
      </div>)}
      {error && <p role="alert" className="error-box">{error}</p>}
      <div className="flex gap-3"><button type="button" className="primary-button" onClick={save} disabled={saving}>{saving ? 'Saving…' : 'Save bank changes'}</button>
        <button type="button" className="secondary-button" onClick={cancel} disabled={saving}>Discard changes</button></div>
    </div>}
  </section>;
}
