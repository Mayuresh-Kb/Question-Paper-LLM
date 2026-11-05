import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FormContext } from './formState';
import { api, auth, errorMessage } from '../lib/api';
const KEY = 'question-paper-session-v1';
function restore() {
  try { return JSON.parse(sessionStorage.getItem(KEY)) || {}; } catch { return {}; }
}
export function FormProvider({ children }) {
  const [saved, setSaved] = useState(restore);
  const [session, setSession] = useState(null);
  const [sessionError, setSessionError] = useState('');
  const [loadingSession, setLoadingSession] = useState(Boolean(saved.uploadId));
  const [storageWarning, setStorageWarning] = useState('');
  const location = useLocation();
  const navigate = useNavigate();
  const { uploadId = null, token = '', pdfId = null, draft = null } = saved;
  const currentStep = location.pathname === '/download' ? 3 : location.pathname === '/configure' ? 2 : 1;
  useEffect(() => {
    try { sessionStorage.setItem(KEY, JSON.stringify(saved)); }
    catch { setStorageWarning('Browser storage is unavailable. Keep this tab open to retain your session.'); }
  }, [saved]);
  useEffect(() => {
    if (!uploadId || session?.upload_id === uploadId) return;
    let active = true;
    setLoadingSession(true);
    api.get(`/uploads/${uploadId}`, auth(token)).then(({ data }) => {
      if (active) { setSession(data); setSessionError(''); }
    }).catch(error => { if (active) setSessionError(errorMessage(error)); })
      .finally(() => { if (active) setLoadingSession(false); });
    return () => { active = false; };
  }, [uploadId, token, session?.upload_id]);
  const handleUploadSuccess = (data) => {
    if (!data.upload_id || !data.session_token || !data.units?.length) throw new Error('The upload response is incomplete. Please retry.');
    setSession(data); setSessionError(''); setLoadingSession(false);
    setSaved({ uploadId: data.upload_id, token: data.session_token, pdfId: null, draft: null });
    navigate('/configure');
  };
  const handleGenerationSuccess = (id) => {
    if (!id) throw new Error('The server did not return a paper. Please retry.');
    setSaved(previous => ({ ...previous, pdfId: id })); navigate('/download');
  };
  const resetWorkflow = () => {
    setSaved({}); setSession(null); setSessionError(''); setLoadingSession(false); navigate('/upload');
  };
  const goToStep = step => {
    if (step === 1) navigate('/upload');
    if (step === 2 && uploadId) navigate('/configure');
    if (step === 3 && pdfId) navigate('/download');
  };
  return <FormContext.Provider value={{ currentStep, uploadId, token, pdfId, session, setSession,
    uploadedFiles: session?.units.map(u => u.filename) || [], draft,
    setDraft: value => setSaved(previous => ({ ...previous, draft: value })),
    sessionError, loadingSession, storageWarning, handleUploadSuccess, handleGenerationSuccess, resetWorkflow, goToStep }}>
    {children}
  </FormContext.Provider>;
}
