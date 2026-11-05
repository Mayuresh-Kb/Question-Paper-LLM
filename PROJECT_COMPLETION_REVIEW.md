# Question Paper Generator — completion review

Historical audit from 5 October 2026, before implementation. The issues below describe the original handover, not the current application. See `IMPLEMENTATION_STATUS.md` for completed changes, verification and remaining boundaries.

## Assessment

This is a partially integrated prototype. It has a React/Vite frontend and a FastAPI backend with upload, generation, and PDF download code. It is not yet a reliably complete application. The most important remaining work is integration, parsing correctness, marks correctness, and validation—not additional landing-page design.

The implemented design selects existing questions from uploaded question banks. It instructs Gemini to copy question text exactly and rejects selections that are not in the bank. It does not currently generate new questions from notes or a syllabus.

## What already exists

- Frontend pages for uploading files, setting examination details and marks, and downloading a paper.
- Drag-and-drop upload, examination presets, loading indicators, and basic error messages.
- Backend endpoints: `POST /upload`, `POST /generate`, and `GET /download/{pdf_id}`.
- Text-PDF parsing into question/marks/Bloom-level records.
- Gemini-based selection followed by local constraints that enforce two alternative main questions per unit and prevent exact-text repeats within that unit.
- Proportional allocation of marks and a ReportLab PDF builder.
- A separate diagram extractor, plus previously generated sample images and PDFs. These files do not demonstrate that the current integrated application works.

## Priority 1 — make the basic flow work

### 1. Complete startup and browser-to-backend configuration

**Evidence:** `main.py:19` starts the backend on port 5000, while `Upload.jsx:6`, `MarkConfig.jsx:23`, and `DownLoad.jsx:6` default to port 8000. The backend has no CORS middleware and Vite has no backend proxy. `llm_service.py:10–16` imports `google.genai` and creates the client at import time, but `requirements.txt` does not include `google-genai`.

**Remaining work:** add and verify the Gemini dependency; provide environment examples for the API key/model and frontend backend URL; choose consistent ports; configure allowed browser origins or a same-origin proxy; report missing configuration clearly. Add actual setup instructions, including supported Python/Node versions. The frontend README is still the Vite template, and no backend README was found.

**Done when:** a clean setup can start both apps and complete upload → generation → download in a browser using the documented steps.

### 2. Agree on a single generation request format

**Evidence:** `MarkConfig.jsx:223–270` sends `mode`, `preferences`, and `header.max_marks`. `models.py:5–25` has no mode/preferences fields and expects `header.total_marks`. The intelligent mode sends a marks list such as `[15, 15, 20, 20]`, but the backend requires one integer. The frontend also allows a list for total paper marks, which the backend requires to be an integer.

**Impact:** intelligent mode's default request fails schema validation. Mode selection does not choose a backend algorithm. The header's entered maximum marks are ignored and the backend's default 100 can be printed instead.

**Remaining work:** define one shared contract; use one authoritative total; either implement per-unit marks and the two selection modes, or remove unsupported controls. Display field-specific validation errors in the frontend.

### 3. Align file support and unit assignment

**Evidence:** `Upload.jsx:17` accepts PDF, DOCX, DOC, and TXT, but `endpoints.py:33` rejects everything except PDF. `endpoints.py:63–76` sorts filenames and requires exactly one PDF per unit. The frontend describes selecting a subset of units and does not clearly enforce the one-file-per-unit restriction.

**Remaining work:** support the advertised formats or restrict the interface to text-based PDFs. Make the input format explicit. Record file-to-unit mapping instead of inferring it from alphabetical filename order; either implement subset selection or derive the unit count from the upload. Give duplicate filenames unique stored names so two files cannot overwrite one another within an upload.

**Done when:** uploading Unit 2 before Unit 1 cannot silently change their meaning, and every accepted file format works through generation.

## Priority 2 — ensure the paper is correct

### 4. Repair and test question parsing

**Evidence:** `parser.py:27–54` fails to recognize question starts such as `10)` and `100.`. Marks are mainly read from a subsequent line. `parser.py:154` can treat the next question as a marks line and skip it. The parser uses text extraction only; there is no OCR path for scanned PDFs.

**Reproduced:** two numbered questions with inline `[5 Marks]` and `[10 Marks]` became one question assigned 2 marks. A bank with `9)` and `10)` lost question 10. The same two questions with separate numeric marks lines parsed correctly.

**Remaining work:** support the agreed bank formats with robust question boundaries, inline/separate marks, multiline questions, subparts, and page-header/footer handling. Reject unsupported/scanned inputs clearly, or add OCR if required. Show extracted questions and marks for review before generation.

### 5. Fix marks totals and prevent infinite allocation loops

**Evidence:** `_apply_weighted_marks` in `llm_service.py:93–123` forces every subquestion to have at least one mark. If there are more subquestions than available marks, its adjustment loop cannot finish. Request fields have no positive-value or feasibility constraints.

**Reproduced:** three subquestions sharing two marks did not terminate; the isolated test process was stopped after two seconds. The loop condition also establishes why it cannot converge.

**Additional issue:** `llm_service.py:292` labels a unit as twice its marks allocation even though its two questions are OR alternatives. A 15-mark unit is labeled 30. `endpoints.py:80–89` merely logs mismatched paper totals and continues. The `total_marks` parameter is not used to enforce the final paper total in `generate_question_paper_json`.

**Remaining work:** validate positive counts and feasible marks before any model call; reject inconsistent totals; bound allocation loops; calculate attemptable marks correctly for OR choices; keep the header, unit totals, and subquestion totals consistent. Clarify that the current “questions per unit” setting actually means subquestions per alternative main question.

**Done when:** a 30-mark, two-unit paper has two 15-mark units, each alternative totals 15, and all invalid configurations return a clear error promptly.

### 6. Implement or remove the promised intelligence features

**Evidence:** every parsed question gets Bloom level 3 (`parser.py:161–162`). There is no difficulty target, topic coverage constraint, or distinct random/intelligent backend branch. Missing model selections are filled using random sampling. The output deliberately preserves original question wording.

**Remaining work, if required by the project:** obtain or classify real Bloom/difficulty metadata; expose the intended distribution; implement and validate topic/difficulty balancing; implement separate selection strategies. If new question generation or rephrasing is required, that is additional work, not an existing capability.

### 7. Connect diagrams to the complete pipeline

**Evidence:** `diagram_extractor.py` is not called by the active upload/generation/parser pipeline. The current bank stores only text, marks, and Bloom level. `pdf_builder.py` renders paragraphs but no diagram images.

**Remaining work:** carry diagram references and source locations from extraction through selection to PDF rendering; verify question-to-diagram matching. If diagrams are out of scope, state the text-only restriction and handle diagram-dependent questions explicitly.

### 8. Validate and review the final PDF

The PDF builder exists, but needs checks for long questions, page breaks, aligned marks, multiline instructions, special characters, and mathematical content. Escape user/source text before placing it inside ReportLab paragraph markup. Add a preview/review step if teachers are expected to approve or edit the paper before export.

The current default instructions say “Answer all questions” while the generated structure contains OR choices. Instructions and exam templates should match the actual paper structure.

## Priority 3 — make the application dependable

### 9. Repair session handling and misleading success states

**Evidence:** `FormContext.jsx:13–16` keeps upload and download identifiers only in memory, so a reload loses the workflow. `MarkConfig.jsx:224` substitutes a fake upload session when no upload exists; the warning does not prevent submitting. `MarkConfig.jsx:280–281` invents a PDF identifier if a successful HTTP response lacks one.

**Remaining work:** guard configuration/download routes; preserve and validate session state; reject malformed success responses; remove fabricated identifiers; retain form values when navigating back. Offer actionable retry/re-upload messages.

### 10. Handle failures, long operations, and stored files

**Evidence:** synchronous PDF work and a synchronous Gemini stream run inside the async generation route. The application has no explicit generation job/status API, cancellation flow, or application-controlled retry/timeout policy. Parsing exceptions create empty unit banks and can surface later as generic generation errors. Bank-size feasibility is checked after the Gemini call.

**Remaining work:** validate each unit and question count before calling Gemini; move blocking work off the async event loop; provide useful failure messages and bounded model calls. Add background jobs/progress if generation duration or multi-user use warrants it. Limit upload size/count, verify PDF content, sanitize filenames, validate identifiers, restrict file access to stored records, and clean up expired uploads/outputs and failed partial uploads.

### 11. Add a small, meaningful verification suite and handover documentation

No project test suite or CI configuration was found. Cover parser formats, API payloads, marks feasibility and totals, unit mapping, no-repeat rules, insufficient banks, malformed model responses, and upload-to-download integration. Use a controlled model stub for repeatable automated tests, plus one real Gemini smoke run and visual inspection of generated PDFs.

Document accepted input format, configuration, start commands, API examples, selection rules, model dependency, known limitations, and deployment steps. Remove or substantiate the hard-coded “99% accuracy” and “95% time saved” claims shown on the homepage.

## Scope-dependent features — confirm before implementing

The homepage advertises analytics, version control, cloud sync, and security, but no corresponding application workflows were found. MongoDB and authentication packages appear in requirements; that does not constitute implemented database or login support.

For a local college demonstration, accounts, cloud sync, analytics, and paper history can remain out of scope if the agreed requirements permit it. For a shared faculty application, add authentication, ownership checks, durable question banks and paper history, and a deployment/storage plan. Saved templates, manual question replacement, answer keys, and multiple paper sets are also scope decisions—not automatically mandatory omissions.

## Suggested completion order

1. Establish the required exam format and whether the input is a question bank or teaching material.
2. Fix dependencies, connection configuration, and the frontend/backend contract.
3. Correct the parser, unit mapping, validation, and marks calculations.
4. Demonstrate a complete text-PDF workflow with a known bank and verified totals.
5. Add required advanced features: unequal marks, difficulty/Bloom balance, diagrams, additional formats, and review/editing.
6. Add regression tests, setup documentation, and any required shared-user deployment features.

## Verification performed and limitations

- Inspected the frontend routes/state, API requests, backend routes/models/configuration, parser, selection code, PDF builder, and diagram module.
- All ten backend Python files passed syntax parsing.
- Executed the actual parser and allocation function definitions in isolation, with synthetic input lines and no external API calls. Reproduced the parsing, OR-total, and nonterminating allocation issues described above.
- Attempted the frontend build; it could not start because Vite/dependencies are not installed in the supplied folder.
- The available system Python lacks FastAPI, Pydantic, PyMuPDF, ReportLab, and the Gemini SDK. No environment file was supplied. No dependency installation, live Gemini request, full server run, browser workflow, or visual PDF validation was performed.
- Existing PDF samples were not treated as proof that the current source works. Findings about request handling and UI behaviour are source-based unless explicitly marked reproduced.

The clean-install dependency fix, a real end-to-end run, and final PDF checks remain necessary to confirm completion.
