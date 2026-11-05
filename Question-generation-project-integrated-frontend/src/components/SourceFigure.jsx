import { useEffect, useState } from 'react';
import { api, auth } from '../lib/api';
export default function SourceFigure({ uploadId, token, asset, alt = "Extracted source figure — verify it belongs to this question" }) {
  const [src, setSrc] = useState('');
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let active = true, url = '';
    api.get(`/uploads/${uploadId}/assets/${asset.replace(/\.png$/, '')}`, { ...auth(token), responseType: 'blob' })
      .then(({ data }) => { if (active) { url = URL.createObjectURL(data); setSrc(url); } })
      .catch(() => { if (active) setFailed(true); });
    return () => { active = false; if (url) URL.revokeObjectURL(url); };
  }, [asset, token, uploadId]);
  if (failed) return <p className="text-red-700 text-sm">Source figure unavailable. Re-upload the bank.</p>;
  return src ? <img src={src} alt={alt} className="max-h-64 max-w-full border border-slate-200 my-3" /> : <p className="text-sm">Loading source figure…</p>;
}
