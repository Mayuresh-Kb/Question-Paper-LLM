# Implementation and handover status

Core workflow verified on 6 October 2026; OCR extension verified on 9 October 2026; production packaging verified on 10 October 2026. The teacher-reviewed question-bank workflow is implemented and tested. Setup and usage are in [README.md](README.md). The original [completion review](PROJECT_COMPLETION_REVIEW.md) is retained as historical context.

## Completed

- Connected the React frontend to the FastAPI backend with consistent request/response models, configuration and error reporting.
- Added numbered TXT and DOCX bank support, repaired PDF parsing, and added explicit warnings for missing metadata, duplicates and unsupported input.
- Added bank review: edit text, unit names, source marks, Bloom levels and topics; exclude questions and inspect or disable attached figures.
- Implemented random and metadata-based balanced selection without an API key. Added optional Gemini selection restricted to validated question IDs, with bounded retries and clear failure messages.
- Enforced explicit unit selection, sufficient questions, no repeated questions and exact marks. Both OR alternatives carry the full unit marks; the paper total counts only the alternatives students attempt.
- Added a strict default unit-test format: exactly two selected units, 8 marks per unit and 16 attemptable marks, producing Q1 OR Q2 followed by Q3 OR Q4. Extra uploaded banks are not selected automatically.
- Added question replacement from the same unit, preserving assigned marks and saving a new paper without overwriting the previous result.
- Restored the active upload, configuration and paper after refreshing the browser tab.
- Added authenticated paper and figure access, expiring sessions, scheduled cleanup, upload limits and five-minute signed download links.
- Added actual PDF page previews, working PDF downloads, selectable question text, separately embedded diagrams/images, page numbers and long-question pagination. Unsupported font characters produce an actionable error.
- Removed unsupported product claims and added sample banks, dependency locks, setup instructions, a local startup script and a GitHub Actions verification workflow.
- Added a production container that builds the frontend, installs Tesseract, serves the SPA and `/api` from one origin, persists files under `/data`, runs as a non-root user and exposes a health check. Docker Compose and CI container-build configuration are included.

## OCR extension

Local Tesseract 5.5.3 with English data is installed. Scanned PDF pages and mixed text/scan banks use automatic OCR, with a force-OCR option for broken text layers. Review displays recognition scores and authenticated source excerpts for comparison. Generated questions always print as selectable text; genuine diagrams and illustrations remain separate images. Missing-engine, engine-failure, timeout, low-confidence and resource-limit paths are covered. The shared upload budget limits OCR to 20 pages and 90 seconds, with 20 seconds per page.

A real raster-only sample is available at `examples/printed-scan.pdf`. The real-engine integration test verifies upload, four recognized questions and source marks, protected source previews, generation and PDF download. Setup, limits and source-quality guidance are in the README.

## Verification performed

- Backend: **81 tests passed**, including source parsing, legacy Symbol-font normalization, supplied PDF banks, strict 16-mark unit-test validation, exact marks, question-quality rejection, Q1/Q2 and Q3/Q4 unit sequencing, selectable PDF text, access control, expiry, replacement, diagram output, long-question layout, production SPA/API routing and mocked Gemini successes/failures.
- Frontend: **6 tests passed**; lint and production build passed after a clean dependency installation.
- Frontend dependency installation reported **0 known vulnerabilities** at verification time. Python dependency consistency check passed.
- Browser: uploaded two banks, edited and saved a unit, checked unsaved-edit protection, generated a 35-mark paper using unequal 15/20 unit allocations, replaced a question, refreshed to restore the result, viewed the rendered PDF and downloaded the revised file successfully.
- OCR browser check: uploaded the raster-only sample, verified four questions and their 5-mark source values, viewed the original scan beside the recognized text, saved the bank, generated a 15-mark paper and downloaded the resulting PDF.
- Visually inspected the normal paper, attached-figure output and a three-page long-question paper. Confirmed the long question begins on the first page and continues without clipping or a header-only blank page.
- The CI workflow is configured but has not run remotely; this workspace has not been published to a repository.
- The real production frontend build was loaded through FastAPI: `/upload`, `/api/health` and its hashed JavaScript asset returned successfully, with OCR reported available and immutable asset caching enabled. Docker is not installed on this computer, so the container image itself still needs its first build on the chosen host or CI runner.

The backend test run emits dependency deprecation warnings; there were no test failures.

## Configuration and scope remaining

**Optional Gemini activation:** supply a valid server-side `GEMINI_API_KEY` and an available model in the backend `.env`, then restart the backend. Live provider access and quota were not verified because no key was supplied; provider behavior was tested with mocks. Balanced and random modes work locally without this configuration.

**Teacher review:** check extracted question text, estimated Bloom levels, diagram associations, factual correctness and academic suitability before issuing an examination. Automated checks block obvious corruption and incomplete wording, but they cannot prove subject-matter correctness. PDF figure association and metadata estimation are heuristics. Complex layouts may need correction in the review screen.

**Hosting:** the application is packaged for a single-instance container host with a persistent `/data` disk. No hosting provider, repository or domain has been supplied, so no public instance has been created. Keep the first deployment behind provider access control, a VPN or a private network because institutional login is not implemented.

**Additional product scope:** Reliable handwritten/mathematical transcription, automatic diagram isolation, generation of new questions from teaching notes, full LaTeX typesetting, institutional accounts and a public multi-user deployment are not included. The current application selects existing questions from uploaded banks. Browser session storage provides continuity in the current tab, not a durable faculty account or cross-device library.

## Run and demonstrate

Use the existing local app at `http://127.0.0.1:5173` while its servers are running. On a later session, run `./start.sh` from the project folder. Follow the sample walkthrough in the README; no API key is needed for that demonstration.

## Document-quality repair

The uploaded exam papers exposed instruction numbering being parsed as questions, merged subquestions and scan-table reading-order errors. The parser now segments ruled question cells, separates explicit exam subquestions, excludes candidate instructions and ignores diagonal text in selection metadata. Original excerpts remain visible for review, while corrected wording is printed as selectable PDF text. Diagrams remain separate image assets. Obvious OCR corruption and incomplete questions are disabled until corrected.

Verified on two actual uploaded papers: 24 separate subquestions from a native exam and 15 question rows from a scanned exam table. Additional regression tests cover instruction exclusion, selectable text, diagram embedding, table marks and unit-alternative numbering. Re-upload old PDFs to apply the new extraction; existing saved outputs remain unchanged.
