import { useEffect, useState } from 'react';
import { api, auth, errorMessage } from '../lib/api';
export default function PdfPreview({ pdfId, token, pageCount }) {
  const [page, setPage] = useState(1);
  const [src, setSrc] = useState('');
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true, url = '';
    setSrc(''); setError('');
    api.get(`/papers/${pdfId}/pages/${page}`, { ...auth(token), responseType: 'blob' }).then(({ data }) => {
      if (active) { url = URL.createObjectURL(data); setSrc(url); }
    }).catch(e => { if (active) setError(errorMessage(e)); });
    return () => { active = false; if (url) URL.revokeObjectURL(url); };
  }, [page, pdfId, token]);
  return <section aria-label="PDF preview" className="rounded-xl border border-slate-200 overflow-hidden">
    <div className="flex justify-between items-center gap-3 bg-slate-50 p-3 border-b border-slate-200">
      <button className="secondary-button" disabled={page === 1} onClick={() => setPage(p => p-1)}>Previous page</button>
      <span className="text-sm" aria-live="polite">Page {page} of {pageCount}</span>
      <button className="secondary-button" disabled={page === pageCount} onClick={() => setPage(p => p+1)}>Next page</button>
    </div>
    {error && <p role="alert" className="error-box m-4">{error}</p>}
    {!src && !error && <p role="status" className="p-6 text-sm">Rendering PDF page…</p>}
    {src && <img src={src} alt={`Rendered question paper, page ${page} of ${pageCount}`} className="w-full h-auto" />}
    <p className="text-xs text-slate-500 p-3 border-t border-slate-200">This is a rendered page from the actual PDF. Use the question review above for accessible text.</p>
  </section>;
}
