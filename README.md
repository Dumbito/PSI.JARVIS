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

Development — Foundation phase.

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
