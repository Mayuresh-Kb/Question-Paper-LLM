import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from '../context/formState';
import { api, auth, errorMessage } from '../lib/api';
import PdfPreview from './PdfPreview';
export default function DownloadPage() {
  const { pdfId, token, resetWorkflow, handleGenerationSuccess } = useForm();
  const [record, setRecord] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!pdfId) return;
    let active = true;
    setRecord(null); setError('');
    api.get(`/papers/${pdfId}`,auth(token))
      .then(({ data }) => { if (active) setRecord(data); })
      .catch(e => { if(active) setError(errorMessage(e)); });
    return () => { active=false; };
  },[pdfId,token]);
  async function download() {
    setDownloading(true); setError('');
    try {
      const { data } = await api.get(`/papers/${pdfId}/download-link`, auth(token));
      const link = document.createElement('a');
      link.href = `${api.defaults.baseURL}${data.url}`;
      link.download = `question-paper-${pdfId}.pdf`;
      link.referrerPolicy = 'no-referrer';
      document.body.appendChild(link); link.click(); link.remove();
    } catch(e) { setError(errorMessage(e)); } finally { setDownloading(false); }
  }
  async function replace(questionId,replacementId) {
    if(!replacementId) return;
    setBusy(true); setError('');
    try { const {data}=await api.post(`/papers/${pdfId}/replace`,{question_id:questionId,replacement_id:replacementId},auth(token)); handleGenerationSuccess(data.pdf_id); }
    catch(e) { setError(errorMessage(e)); } finally { setBusy(false); }
  }
  if(!pdfId) return <div className="space-y-4"><h1 className="text-2xl font-semibold">No paper to review yet</h1><Link className="primary-button inline-block" to="/upload">Start with a question bank</Link></div>;
  const paper=record?.paper;
  const used=new Set(paper?.units.flatMap(u=>u.alternatives.flatMap(a=>a.questions.map(q=>q.id))) || []);
  return <div className="space-y-7">
    <div><p className="eyebrow">Step 3 · Review & download</p><h1 className="text-3xl font-semibold mt-2">Your question paper</h1><p className="text-sm text-slate-600 mt-2">Check the questions and PDF before using the paper. Replacements keep the original slot’s assigned marks.</p></div>
    {error && <div role="alert" className="error-box">{error} <Link className="underline" to="/configure">Return to configuration</Link></div>}
    {!paper && !error && <p role="status">Loading your paper…</p>}
    {paper && <>
      <div className="flex flex-wrap items-center justify-between gap-4 bg-blue-50 rounded-xl p-5">
        <div><strong>{paper.header.subject}</strong><p className="text-sm text-slate-600 mt-1">{paper.total_marks} marks · {paper.units.length} units · {paper.provider}</p></div>
        <button className="primary-button" onClick={download} disabled={downloading}>{downloading ? 'Preparing download…' : 'Download PDF'}</button>
      </div>
      {paper.warnings.length>0 && <ul className="list-disc pl-5 text-sm text-amber-800 space-y-1">{paper.warnings.map(w=><li key={w}>{w}</li>)}</ul>}
      <p className="text-xs text-slate-500">Bloom levels across all printed alternatives: {Object.entries(paper.bloom_counts).map(([level,count])=>`L${level}: ${count}`).join(' · ')}</p>
      <details><summary className="text-blue-700 font-semibold cursor-pointer">Review or replace selected questions</summary>
        <div className="space-y-6 mt-4">{paper.units.map(unit=><section key={unit.id} className="space-y-4">
          <h2 className="text-lg font-semibold">{unit.name} · {unit.marks} marks</h2>
          {unit.alternatives.map((alternative,index)=><div key={alternative.number} className="border border-slate-200 rounded-xl p-4 space-y-4">
            <h3 className="font-semibold">{index===1 ? 'OR — ' : ''}Question {alternative.number}</h3>
            {alternative.questions.map((q,i)=><div key={q.id} className="space-y-2 border-t border-slate-100 pt-3">
              <p className="text-sm whitespace-pre-wrap"><strong>({String.fromCharCode(97+i)})</strong> {q.text} <strong>[{q.marks}]</strong></p>
              <p className="text-xs text-slate-500">Bloom {q.bloom}{q.topic ? ` · ${q.topic}` : ''}{q.assets.length ? ' · Includes source figure' : ''}</p>
              <label className="field">Replace with an unused question<select aria-label={`Replace question ${alternative.number}${String.fromCharCode(97+i)}`} value="" disabled={busy} onChange={e=>replace(q.id,e.target.value)}>
                <option value="">Keep this question</option>{record.units.find(u=>u.id===unit.id).questions.filter(candidate=>candidate.enabled&&!used.has(candidate.id)).map(candidate=><option key={candidate.id} value={candidate.id}>{candidate.text.slice(0,160)}</option>)}
              </select></label>
            </div>)}
          </div>)}
        </section>)}</div>
      </details>
      {busy && <p role="status">Building the revised paper…</p>}
      <PdfPreview key={pdfId} pdfId={pdfId} token={token} pageCount={record.page_count} />
      <p className="text-xs text-slate-500">Paper available until {new Date(record.expires_at*1000).toLocaleString()}.</p>
    </>}
    <div className="flex flex-wrap gap-3"><Link className="secondary-button" to="/configure">Change configuration</Link><button className="secondary-button" onClick={resetWorkflow}>Start a new paper</button></div>
  </div>;
}
