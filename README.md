# Question Paper Generator

A local, teacher-reviewed examination-paper generator. The React frontend and FastAPI backend now share one validated API. It selects existing questions from numbered banks; it does not invent questions from lecture notes.

## Start on this computer

Dependencies have been installed in the root `.venv` and the frontend's `node_modules`. Tesseract with English language data is installed for local OCR.

```sh
./start.sh
```

Open http://127.0.0.1:5173. Stop both servers with Ctrl+C. If servers are already running, use the existing browser page instead of starting another copy.

## Setup on another computer

Use Python 3.10+ (tested with 3.12) and Node.js 22.12+.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r Question-Paper-Generation-main/requirements-lock.txt
cd Question-generation-project-integrated-frontend
npm ci
cd ..
./start.sh
```

For scanned PDFs, install the external Tesseract engine and English language data:

- macOS: `brew install tesseract`
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr tesseract-ocr-eng`
- Windows: follow the [Tesseract installation instructions](https://tesseract-ocr.github.io/tessdoc/Installation.html), add it to PATH or set `TESSERACT_CMD` to the executable's absolute path.

Check with `tesseract --list-langs` (it must include `eng`). The backend reports engine availability through `/health`; missing language data produces an actionable upload error. Text PDF, DOCX and TXT processing remains available without Tesseract.

The dependency lock includes test packages. `requirements.txt` lists the direct runtime dependencies; `requirements-dev.txt` adds pytest. On Windows, activate the virtual environment and start the servers manually using the commands below instead of the shell launcher.

Manual startup, in two terminals:

```sh
cd Question-Paper-Generation-main
../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

```sh
cd Question-generation-project-integrated-frontend
npm run dev
```

API documentation: http://127.0.0.1:8000/docs. Health/configuration: http://127.0.0.1:8000/health.

## Try the complete flow

1. Upload `examples/unit-1.txt` and `examples/unit-2.txt` in that order. Each file is one unit. Text PDFs and DOCX also work; legacy `.doc` files must be converted.
2. Open **Review & edit** to correct question text, source marks, Bloom levels or topic labels. Disable questions to exclude them. Save changes before generation.
3. Enter the subject and exam header. Choose units explicitly. For example, allocate 15 marks to Unit 1 and 20 to Unit 2, with two subquestions per alternative.
4. Choose **Balanced** or **Random**; neither needs an API key. The paper totals 35 attemptable marks. Each unit has two main questions separated by OR, and each alternative carries that unit's full marks.
5. Review the rendered PDF pages (no browser PDF plugin required) and optionally replace a selected question with an unused question from the same unit. A replacement preserves the slot's assigned marks and creates a new paper, preserving the previous saved output.
6. Download the PDF. Reloading the tab restores the current upload, configuration and paper. **Start a new paper** clears the current browser workflow; it does not immediately delete earlier server files.

Uploads and papers expire after seven days by default. The server removes expired managed records hourly and on startup. Session access tokens are kept in browser session storage; losing or clearing that browser session loses access. This is local session isolation, not a faculty account/login system.

## Question-bank format

Use numbered questions with marks at the end of the question or on the next line. Optional tags provide explicit metadata:

```text
1. Explain a binary search tree. [5 Marks] [BTL: 2] [Topic: Trees]
2. Design a balanced search algorithm.
(8)
[BTL: 6] [Topic: Searching]
```

Supported question starts include `1.`, `10)`, `100.`, `Q1.`, `Q.1.`, and `Question 1:`. Multiline question text and alphabetic subparts are preserved as one bank question. TXT must be UTF-8. DOCX supports paragraphs and simple number/question/marks tables. Supported metadata ordering and source layouts are covered by tests; complex multi-column papers should be converted to the explicit format or corrected in review.

Missing marks default to 1 and are flagged. Missing Bloom levels are estimated from command words and clearly marked **estimated**; these are heuristics, not validated pedagogical classifications. Topics are optional, teacher-supplied labels. Exact normalized duplicates are disabled; semantic duplicates still need human review.

Limits: 12 files, 10 MB per file, 30 MB total, 100 PDF pages per file, 500 questions per unit, 12 subquestions per alternative. At least twice the requested subquestion count must be available because both OR alternatives are unique. Repeats across selected units are also rejected.

## Selection and marks

- **Unit test (default):** selects exactly two uploaded units at 8 marks each, for 16 attemptable marks. It produces Q1 OR Q2 for the first selected unit and Q3 OR Q4 for the second. Additional uploaded banks remain available but are not selected automatically.
- **Random:** samples eligible questions uniformly without replacement.
- **Balanced:** prefers the selected Bloom difficulty and topic variety using reviewed metadata; alternatives use the same target levels. It uses the closest available questions, not a guaranteed difficulty quota.
- **Gemini-assisted:** asks Gemini to return only IDs from the selected banks, then validates units, counts, uniqueness and membership locally. Model-provided text and marks are never trusted. Invalid responses fail clearly, without pretending a local fallback is AI output.

Marks are allocated proportionally from source marks, with at least one mark per subquestion and an exact alternative total. All input totals and counts are validated before generation. Output displays attemptable marks, not the sum of both OR alternatives.

## Optional Gemini configuration

Copy `Question-Paper-Generation-main/.env.example` to `.env` in that folder and set `GEMINI_API_KEY`. Set `GEMINI_MODEL` to a supported model available to your account. Restart the backend after configuration changes. Never put the key in frontend environment variables.

Gemini receives the selected banks' text, topics, marks and Bloom metadata only when that method is explicitly chosen. Local modes send no source material to an external model. Gemini calls have timeouts and one retry for transient HTTP failures. The implementation uses the documented REST API through `httpx`, so there is no missing or implicit Google SDK dependency. API reference: https://ai.google.dev/api/generate-content.

A real Gemini call requires your own key and available quota. Automated tests stub valid, invalid and unavailable-provider cases; they do not consume your API quota.

## Figures, mathematics and PDF output

The parser attaches raster/vector diagrams and image regions from text PDFs using question positions, and inline DOCX images using their paragraph placement. Questions are always rendered as selectable text; only genuine diagrams and illustrations remain images. Review these associations and disable incorrectly attached figures. Scanned/image-only PDF pages use local Tesseract OCR automatically. General layout understanding is not built in. Table-heavy PDFs and page-spanning figures need particular care.

PDF output uses the sequence **Q1 Unit 1 OR Q2 Unit 1, Q3 Unit 2 OR Q4 Unit 2**, continuing for later units. It escapes paragraph markup, aligns marks, wraps long text, includes reviewed diagrams, prints authoritative totals and numbers pages. A Unicode-capable font is used when available. Unsupported glyphs fail with an actionable error instead of silently disappearing. Full LaTeX equation typesetting and arbitrary scripts are outside the supported format.

## OCR for scanned banks

Upload a PDF containing clear, upright printed scans using the normal upload screen. Try `examples/printed-scan.pdf`, a raster-only bank with four questions. Pages dominated by an image, or containing graphics without extractable text, are recognized automatically; normal text pages use their existing text. Select **Re-read all PDF pages with OCR** when a PDF has garbled text that automatic detection misses. `/upload` also accepts the multipart field `ocr_mode=auto|force`.

Recognition runs locally through [Tesseract's TSV output](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html); no cloud call or API key is involved. Word coordinates are converted back into PDF coordinates. OCR questions show their source page, a recognition score and original excerpts for comparison in **Review & edit**. The score is the lowest mean line score within that question, not a probability of correctness. Always verify numbering, text, marks and equations against the original. Unrecognized question boundaries can merge questions; correct the text or exclude affected entries before generation.

**Selectable-text output:** Question wording is never embedded as a screenshot. Native PDF/DOCX/TXT text is printed directly, while scanned pages are converted through OCR and must be corrected in review. Source excerpts are retained only as protected review references. Ruled question/marks tables are segmented into cells, and explicit exam subquestions are separated from candidate instructions. A quality gate disables text that is too short, incomplete, dominated by symbols or visibly corrupted by OCR; enabled questions are checked again before generation.

In **Review & edit**, compare every extracted question against its original excerpt and correct its wording, program indentation, equations and symbols. The corrected field is the authoritative PDF text. Attached diagrams/images are shown separately and can be included or excluded per question. Standalone JPG/PNG bank upload remains unsupported; combine scanned pages into a PDF first.

Re-upload previously imported PDFs once to use selectable-text output and the new quality checks. Previously saved papers are not rewritten. Check question boundaries on unfamiliar layouts; column detection is heuristic, and low-quality or damaged scans can still require a cleaner source. Teacher review remains required for academic correctness and meaning; structural checks cannot fact-check subject matter.

Limits cover the whole upload: 20 OCR pages, 90 seconds total and 20 seconds per page. At most two OCR processes run at once; each rendered page is capped at 12 million pixels. Temporary OCR images are removed after processing. Original files and review excerpts follow the existing session retention/access controls. Failures roll back the entire upload, rather than returning a partially read bank. Split large scans into smaller uploads if a limit is reached.

`TESSERACT_CMD` defaults to `tesseract`; `OCR_LANGUAGE` defaults to `eng`. Additional installed Tesseract languages can be configured server-side, but question parsing and Bloom estimation are designed for English banks, and PDF font coverage still applies. Restart the backend after changing configuration.

## Tests and builds

```sh
.venv/bin/python -m pytest Question-Paper-Generation-main/tests -q
cd Question-generation-project-integrated-frontend
npm test
npm run lint
npm run build
```

Tests cover source parsing and figures, the supplied PDF banks, the strict 16-mark unit-test format, input validation, exact marks, duplicate prevention, unequal unit marks for custom exams, subset selection, upload rollback, session access, expiry/cleanup, model response validation, replacements, and actual PDF download/text checks.

## Storage and production deployment

By default, new files live in `Question-Paper-Generation-main/storage/sessions/` and `storage/papers/`; the seniors' original examples are left intact. Set `STORAGE_DIR` to an absolute persistent directory when necessary. Never serve storage as a public static directory. Figures, previews and paper records require the session token. The download button requests a protected link that expires after five minutes; the session token itself is never put in a URL. Avoid logging request headers, signed download query strings, or document contents.

The included production container builds the React app, installs Tesseract with English language data, serves the frontend and FastAPI from one origin, and stores managed files under `/data`. The browser uses `/api`, while the original unprefixed API remains available for local compatibility.

On a machine with Docker and Compose:

```sh
docker compose up --build -d
```

Open `http://localhost:8000`. Check `http://localhost:8000/api/health` for service and OCR status. `docker compose down` stops the app while retaining its named data volume.

For a managed container host, deploy the repository root with its `Dockerfile` and configure:

- one running instance and one worker;
- a persistent disk mounted at `/data`;
- at least 1 GB RAM and a request timeout of at least 120 seconds for OCR uploads;
- the platform-provided `PORT` and HTTPS endpoint;
- optional server-only `GEMINI_API_KEY` and `GEMINI_MODEL` values;
- optional `RETENTION_HOURS`, which defaults to 168 hours.

The container health check calls `/api/health`. Hashed frontend assets are cached for one year; HTML uses no-cache so new deployments load promptly. The backend also provides SPA fallback for `/upload`, `/configure`, `/review` and `/download`.

Keep this deployment at one instance. Sessions, cleanup locks and generated files use the local persistent volume and are not coordinated across replicas. Multiple replicas require shared object storage plus a database or another distributed session/locking design.

This is not a public multi-tenant service: institutional authentication, durable user-owned libraries, backups, distributed job scheduling and multi-worker coordination require a separate deployment scope. Put it behind the hosting platform's access control, VPN or private network until faculty authentication is added. There are no unsupported claims of analytics, cloud sync, accuracy percentages or faculty login in the interface.

A GitHub Actions workflow in `.github/workflows/ci.yml` runs the backend suite and frontend tests, lint and production build when this project is pushed to a GitHub repository.
# Question-Paper-LLM
