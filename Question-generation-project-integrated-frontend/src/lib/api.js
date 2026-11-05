import axios from 'axios';
export const api = axios.create({
  baseURL: (import.meta.env.VITE_FASTAPI_URL || '/api').replace(/\/$/, ''),
  timeout: 120000,
});
export const auth = (token) => ({ headers: { 'X-Session-Token': token } });
export function errorMessage(error) {
  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(item => `${item.loc?.slice(1).join(' › ') || 'Input'}: ${item.msg}`).join('; ');
  if (error.code === 'ECONNABORTED') return 'The request timed out. Try fewer scanned pages or fewer units.';
  return error.message === 'Network Error' ? 'Cannot reach the backend. Start the API server and retry.' : error.message || 'Something went wrong. Please retry.';
}
