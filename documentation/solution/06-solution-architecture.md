# Solution architecture

**Shape.** A static, file-based pipeline in one public repository. There is no server, database or account to run, so the attack surface is the repository and the published files.

```mermaid
flowchart TB
  subgraph Sources[Official open sources]
    GOVUK[GOV.UK organisations] ; EAO[Estimates and Accounts Orders] ; ONS[ONS classification] ; PBD[Public Bodies directory] ; CH[Companies House] ; GLEIF ; PFI[PFI register] ; WD[Wikidata] ; IATI
  end
  Sources --> FETCH[fetch.py + manifest]
  FETCH --> BUILD[build.py]
  BUILD --> TREE[(data/*.json, *.csv)]
  TREE --> CHECKS{checks}
  CHECKS --> PORTAL[patch_portal.py] --> SITE[docs/: page, feeds, BODS, concordance, navigator]
  TREE --> BODS[export_bods.py] --> SITE
  TREE --> TRENDS[trends.py, scenarios.py, functions.py] --> SITE
  SITE --> PAGES[GitHub Pages]
```

**Key decisions**

| Decision | Why | Trade-off |
|---|---|---|
| Static site on GitHub Pages | Free, no maintenance, nothing to patch | No server-side search or write-back |
| Source files that name people are fetched, not committed | Keeps personal data out of the repository | A rebuild needs network access |
| Safe-fail matching (no fuzzy joins) | A wrong join is worse than a gap | 884 names left unresolved, each listed |
| BODS 0.4 with a public-accountability extension | An existing open standard, with tooling | The extension isn't part of the standard yet |
| Manual refresh, no schedule | A one-person band can't nurse failing scheduled jobs | Freshness depends on someone running it |

**Security.** Workflows read-only; actions pinned to commit SHAs; dependencies pinned; output escaped; no evaluation of input; ruff with security rules; fail closed.
