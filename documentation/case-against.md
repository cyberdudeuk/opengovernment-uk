# The case against

The strongest objections, and the answers, kept in the repository rather than on the portal.

- "Registers tried this and were retired." They were a new service that asked owners to republish. This is a join over registers that already run, published as files; if nobody touches it, the build still runs.
- "Automatic matching will make mistakes." It will make fewer than people re-matching by hand, and its rules lean towards not joining: 61 near-names are set aside rather than risked, six known false friends are checked on every build, and every join can be traced and undone. The base rate matters: in the first pilot, 28 of the 48 pairs sent to people differed only by an acronym, a legal ending or a leading "The".
- "Wikidata isn't authoritative." Agreed. It is used only as corroboration between two official registers, never as the sole source of a body or a join.
- "Inferred nations will mislead." Each inferred tag says so on the profile. The fix is for owning registers to state jurisdiction.
- "Another list makes things worse." It replaces the ten copies listed under Data and feeds with one feed, and keeps each body's own code.
- Limits. ONS matches are not confirmed by ONS. Some registers (OpenCorporates, the Charity Commission, the Companies House API) need keys this pilot doesn't have. GLEIF covers few public bodies, because most don't need an LEI.
- "A chain of accountability built from several sources can be wrong." It can. Each step names its source and where in it, the law outranks every other source, conflicts are listed rather than resolved, and 243 bodies (9%) are shown as not traced rather than given a plausible-looking owner.
- "BODS is for companies, not the state." Version 0.4 already models states and state bodies (entity types state and stateBody, interest type controlByLegalFramework). The public-sector relations it lacks travel in a named extension, so the output still validates against the official schema.
