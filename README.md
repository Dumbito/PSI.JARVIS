# PSI.JARVIS V.1

Scientific Paper Screening & Analysis System.

## Purpose

PSI.JARVIS is a modular, reproducible and auditable platform for scientific literature management, screening, analysis and reporting.

## Principles

- Deterministic algorithms
- Explicit scientific rules
- Human methodological authority
- Data preservation
- Traceability
- Provenance
- Reproducibility
- Auditability
- Versioning
- No generative AI for primary screening

## Status

Development — foundation, acquisition, external synchronization, persisted screening evidence and professional desktop GUI layers implemented. The current architecture also provides an isolated AI/NLP assistant boundary for local Ollama inference without granting the provider scientific authority.

## Scientific UX contract

The desktop workflow is organized around the same path used by a systematic literature review: project/protocol → paper → screening → evidence → audit/reporting. The GUI exposes persisted state and delegates write operations to application services; it does not re-implement screening or deduplication rules.

The interface makes processing state, screening context, deduplication, provenance, exclusion reasons and audit history visible where the underlying data exists. Empty, unavailable and not-yet-persisted states are represented explicitly rather than inferred.

Scientific decisions remain authoritative in the deterministic `ScreeningEngine` and persisted screening/audit repositories. A refresh, navigation event or presentation-layer action cannot silently rewrite a persisted decision.

## Analysis and reporting

The analysis layer already exposes deterministic reporting surfaces for:

- screening statistics and metrics
- inclusion/exclusion decisions
- exclusion reasons
- deduplication
- criteria and rule behavior
- metadata quality
- authors
- journals
- publication years
- sensitivity/configuration analysis

Reports reuse the existing domain/application reporting layer rather than duplicating scientific calculations in the GUI. Exported reports therefore remain derived artifacts of persisted scientific state.

## PRISMA flow

The current PRISMA representation is deliberately limited to stages that PSI.JARVIS persists as scientific state: records identified, duplicates removed, records screened, screening exclusions, and records retained for the next stage. Full-text retrieval, report retrieval failures, study-level eligibility assessment and final study inclusion are not inferred when their underlying events are absent.

The Reports workspace provides a run selector and a read-only PRISMA-style diagram. Counts are derived from the selected persisted screening run and its screening decisions, preserving the project's provenance and deterministic-authority model.

The `PrismaFlow` domain object validates stage relationships so inconsistent counts cannot be rendered as a valid flow.

## AI/NLP assistant boundary

AI/NLP is an auxiliary capability, not the scientific authority. The domain contains an explicit assistant contract and the infrastructure contains a provider adapter for local Ollama inference:

- suggestions are separate from `ScreeningResult` and `ScreeningAudit`
- model identity and prompt version are captured with the suggestion
- the input hash provides deterministic provenance for the assistant input envelope
- optional confidence is range-validated
- assistant output carries a fixed `assistant-only` authority label
- promotion of an assistant suggestion into a scientific screening decision is explicitly rejected
- Ollama connectivity is isolated behind `OllamaClient`
- model discovery uses Ollama's local `/api/tags` endpoint
- generation uses the local `/api/generate` endpoint with streaming disabled for deterministic response handling
- connection settings can be supplied through `PSI_OLLAMA_BASE_URL` and `PSI_OLLAMA_TIMEOUT`
- no Ollama dependency is required; the adapter uses Python's standard library HTTP client

The current Ollama integration is provider-level and deliberately read-only with respect to scientific state. It does not persist or promote model output into screening results. A future GUI assistant can consume the same contract without weakening the scientific boundary.

## GUI engineering and robustness

The PySide6 interface uses non-blocking property/geometry animations and explicit widget ownership. Global page transitions do not use `QGraphicsOpacityEffect`.

Regression coverage checks the Qt-sensitive architecture, including:

- main page-stack animation behavior
- `QTabWidget` internal stack exclusion
- geometry-based tab/dialog transitions
- table hover overlays without graphics effects
- single application-owned animation filter
- PRISMA diagram and panel lifecycle/refresh behavior
- persisted run selection and stage mapping

The CI workflow installs the Qt test plugin and runs the GUI suite in an offscreen environment. Every push to `main` and every pull request executes the complete test suite plus whitespace validation.

## Desktop GUI

PSI.JARVIS includes a PySide6 desktop workspace with a read-only presentation layer over persisted application state. It exposes:

- Dashboard metrics for projects, papers and screening progress
- Project and paper inspection
- Paper search and metadata/abstract/provenance details
- Bibliographic source connection visibility
- Persisted screening decisions and filters
- Metadata-change audit history
- Analysis and reporting capability surfaces without duplicating domain logic
- A run-scoped PRISMA-style flow view derived only from persisted screening evidence
- Runtime settings and methodological safeguards

The GUI does not replace the deterministic screening engine, resolve synchronization conflicts, or silently alter audited scientific decisions.

Launch locally with:

```text
psi-gui
```

## Testing and development dependencies

Install the project with the test suite dependencies using:

```text
python -m pip install -e '.[test]'
```

Development tooling can be installed with:

```text
python -m pip install -e '.[dev]'
```

## Bibliographic sources

PSI.JARVIS supports remote bibliographic acquisition through adapters for PubMed, Scopus, Web of Science and Zotero. Provider-specific transports remain isolated from the application and screening layers.

Remote acquisitions produce immutable acquisition receipts and per-record provenance. Provenance records include the source key, source record identifier when available, adapter/version metadata, request and input hashes, mapping versions and the raw-record hash.

## External synchronization

The synchronization layer is deliberately conservative:

- New external records are inserted with their provenance.
- Existing records are matched by DOI, then PMID, then normalized title.
- Incoming metadata can fill local fields that are empty.
- Non-empty metadata discrepancies become explicit conflicts and are not overwritten automatically.
- New provenance can be appended without replacing prior provenance.
- Metadata changes are stored in `metadata_change_history` and are idempotent by deterministic change key.
- Screening results and screening audits are outside the synchronization write path and are not modified by metadata synchronization.

SQLite schema migrations now include the synchronization history layer as schema version 7.

## Scopus connection

PSI.JARVIS supports Scopus as a remote bibliographic source through the Elsevier Scopus Search API.

Scopus requires an Elsevier API key. Full API access can depend on the user's institutional subscription and network entitlements. OAuth access is available only when Elsevier has enabled the corresponding OAuth integration for the application.

### Environment configuration

The Scopus integration reads credentials from environment variables and never requires secrets to be committed to the repository.

Required for API access:

```text
PSI_SCOPUS_API_KEY
```

Optional transport settings:

```text
PSI_SCOPUS_INSTTOKEN
PSI_SCOPUS_BASE_URL
PSI_SCOPUS_TIMEOUT
PSI_SCOPUS_COUNT
```

OAuth settings, when enabled for the Elsevier application:

```text
PSI_SCOPUS_CLIENT_ID
PSI_SCOPUS_CLIENT_SECRET
PSI_SCOPUS_AUTHORIZATION_ENDPOINT
PSI_SCOPUS_TOKEN_ENDPOINT
PSI_SCOPUS_SCOPES
PSI_SCOPUS_REDIRECT_PORT
```

The local OAuth token store is created under:

```text
~/.config/psi-jarvis/connections/scopus.json
```

The file is created with owner-only permissions (`0600`).

### CLI

Check connection state:

```text
psi scopus status
```

Start an OAuth connection through the system browser:

```text
psi scopus login
```

Remove the locally stored OAuth session:

```text
psi scopus logout
```

A successful OAuth login does not itself grant Scopus access. Elsevier still evaluates the API key and the user's or institution's entitlements when processing API requests.
