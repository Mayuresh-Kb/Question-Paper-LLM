# Frontend

React + Vite question-paper workflow. See `../README.md` for full setup and usage.

- `npm ci`: install locked dependencies (Node 22.12+).
- `npm run dev`: local app at http://127.0.0.1:5173; `/api` proxies to FastAPI on port 8000.
- `npm test`: validate request construction and blueprint checks.
- `npm run lint`: ESLint checks.
- `npm run build`: production build in `dist`.
- `npm run preview`: check the built frontend locally.

`VITE_FASTAPI_URL` optionally overrides `/api` when the backend is hosted separately. Never configure a Gemini key in the frontend. Session tokens and form configuration persist for the current browser session only.
