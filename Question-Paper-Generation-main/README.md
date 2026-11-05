# Backend

See the root `../README.md` for setup, supported question-bank formats, optional Gemini configuration, and deployment limitations.

From this directory: `../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000`.

API docs: http://127.0.0.1:8000/docs. Bank, generation, paper and preview routes require the `X-Session-Token` returned by `POST /upload`. Downloads accept the session header or a five-minute signed link returned by the authenticated download-link endpoint. `/health` and `/upload` are public local endpoints.

`POST /generate` accepts `upload_id`, `header`, `mode` (`random`, `balanced`, or `gemini`), `difficulty`, `total_marks`, and `units`. Each unit specifies `unit_id`, `marks`, and `questions_per_alternative`. Unknown fields are rejected. Marks must equal the sum of selected unit marks. See the generated OpenAPI documentation for complete examples and schemas.
