# What to learn from the BODS interoperability toolkit, OpenSanctions and OpenCorporates

Reviewed 22 November 2026. Repositories read in full (shallow clones, nothing run from them):

- the BODS interoperability toolkit and its companion repositories (the shared fixture pack and its pytest plugin, the BODS validator, the BODS-to-FollowTheMoney and BODS-to-OpenCorporates converters, OpenCheck, the BODS agent skill);
- OpenSanctions: `followthemoney`, `nomenklatura`, `yente` and the `opensanctions` crawler repository;
- OpenCorporates: its two public repositories (`legal`, `de_data_quality`). Its data model is mostly visible through the BODS-to-OpenCorporates converter, not its own code.

Each finding says what was adopted in this portal now, what is next, and what was rejected and why. The last section is a checklist to apply across the rest of the estate.

## 1. Adopted in this portal now

| From | Pattern | What this portal now does | Check that proves it |
|---|---|---|---|
| OpenSanctions (`followthemoney`) | Publish in the model the investigative tools already load | `docs/data/register.ftm.json`: public bodies (`PublicBody`), companies they control (`Company`), international bodies (`Organization`), control and ownership links, renames and mergers (`Succession`) and memberships | `tools/ftm_export.py` checks every entity against FtM 4.11.3's own compiled model: schema, property, reference target and its range, required properties, country codes, dates. Negative test: an unknown property and an `Ownership` of a non-asset are both caught |
| bods-ftm | Follow the published BODS-to-FtM mapping rather than inventing one | Links are taken from the BODS file, so the two exports can't disagree. Shareholding in a company becomes `Ownership`; any other control becomes `Control`, with `controlType: state` for control by law | Same check; known answers (the Met Office has its Wikidata id; the UK's institution holdings are `Membership`; machinery-of-government changes are `Succession`) |
| OpenSanctions, OpenCheck | Machine-readable licensing for every file | `REUSE.toml` plus `LICENSES/`: MIT code, CC BY 4.0 documentation, OGL v3 data, and the vendored licences (ISC, Apache-2.0, OFL-1.1, CC0) kept as their authors set them | `reuse lint` in CI (216 of 216 files at the time of writing). Negative test: removing a licence text fails it |
| Shared BODS fixture pack | One agreed test case per edge case, each with an `.expected.md` | Three public-sector cases the pack doesn't have: a state's shares and votes in an international body; control by legal framework (designation into a department's accounts); sponsorship carried in a namespaced extension | `tools/bods_fixtures_ps.py`: each bundle cut from the published BODS file and checked by lib-cove-bods. Negative test: an invalid interest type is caught |
| OpenCheck (`okf/`, agent skill) | Tell AI agents where everything is | `docs/llms.txt` (llmstxt.org convention), generated from the same list as the data catalogue so it can't drift | Generated in `tools/standards.py`, listed in the catalogue and the sitemap |
| OpenCheck | "Absence is not evidence"; sources are never added together; no stand-in figures | Already a rule here. It now appears in the fixture expectations too: "MUST NOT add shares across sources or invent a total" | The fixtures' `.expected.md` |

One place where this portal departs from the published mapping, on purpose: FollowTheMoney only lets an `Ownership` point at an `Asset`, and an intergovernmental bank is not one. So the UK's shares in the five institutions are a `Membership`, and its description gives the share of votes. Fixture 20 says this, so a converter author meets the question before their code does.

## 2. Next, in order of value for effort

1. **Declarative source manifests with assertions** (OpenSanctions dataset YAML). Each source this portal reads would get one small file: who publishes it, whether it is official, how often it changes, its address, its licence, and minimum and maximum counts (for example, "Commonwealth members: 50 to 60"). A failed assertion stops the build. Today these checks exist, but they are spread across each tool. Effort: about one day to move them; it then saves time on every new source.
2. **Source-degradation reporting** (OpenCheck). When a source can't be read, publish a small machine-readable note (source, when, why, what is now stale) rather than only failing CI. The five institutions this portal could not read are the first case. Effort: half a day.
3. **A data dictionary generated from code** (OpenCheck). Build the field list for every export from the code that writes it, so documentation can't drift from data. Effort: half a day per export.
4. **Licence files inside download bundles** (OpenCheck). Put `LICENSES.md` beside the data in any zip or bundle, not only in the repository. Effort: an hour.
5. **An agent skill with evaluations** (the BODS agent skill). A short instruction file for agents ("how to answer 'who answers for X' from this portal's data"), with a handful of questions that have known answers, run in CI. Effort: about a day. Low upkeep once written.
6. **A "start here: what do you want to do?" page** (the toolkit). This portal's wayfinder already does this for people. A developer version would point to the right file for each job: validate, convert, analyse, integrate. Effort: half a day.

## 3. Rejected, and why

| Pattern | Why not |
|---|---|
| yente's `/reconcile` (W3C/OpenRefine Reconciliation API) | It needs a running server. That breaks the free, static, low-upkeep hosting rule. Static FtM and JSON-LD files give other tools the same data to reconcile against locally |
| nomenklatura's resolver as a dependency | Heavy for one maintainer. This portal's `set-aside-decisions.json` and same-as rules already do the same job, a judgements store with reasons, in plain files |
| Installing the FollowTheMoney library | It needs a compiled ICU dependency (`pyicu`), and that adds upkeep. The portal checks against FtM's own compiled model, vendored at a pinned commit, instead |
| Copying OpenCorporates' code | Little is public. What matters is its convention: jurisdiction plus company number (for example `gb/00445790`). The FtM export already carries the Companies House number as `registrationNumber` with country `gb`, and a converter can build that form from it |

## 4. Arrangements that would help both sides

These are offers, not actions. Opening issues or pull requests on others' repositories is the maintainer's decision.

- **The shared fixture pack** gains three public-sector cases it doesn't have. This portal gains a shared definition of "correct" for its own BODS.
- **OpenCheck's state-controlled signal** builds its state nodes from Wikidata, GEM, EITI, OpenSanctions and GLEIF. This register could become an official-sourced UK input: every body, its accountable department and the source of each link. OpenCheck gets UK coverage; this portal gets its data used and checked by another tool.
- **OpenSanctions** could load `register.ftm.json` as a UK public-bodies dataset, and its matching would surface this portal's errors back to it.
- See also `documentation/open-ownership-reuse.md` for Open Ownership itself.

## 5. Best-practice checklist for the rest of the estate

Apply when warranted, scaled to the repository. Each item is free and needs no server.

1. **Licensing:** `REUSE.toml` and `LICENSES/`, with `reuse lint` in CI. Keep vendored code under its own licence.
2. **Exchange formats:** publish in the formats the neighbouring tools already read (DCAT for catalogues, FtM for entities and links, BODS for ownership and control). Follow a published mapping before inventing one, and write down every place you depart from it.
3. **Validate against the other side's model**, not your own reading of its documentation. Vendor the compiled schema at a pinned commit.
4. **Test cases with stated expectations:** small fixed bundles, each with a written "correct handling is…". Offer them upstream where a shared pack exists.
5. **Agents:** an `llms.txt` generated from the same source as the catalogue. Later, an agent skill with known-answer evaluations.
6. **Sources as data:** a manifest per source, with count assertions that fail closed, and a published note when a source degrades.
7. **Decisions as data:** every manual judgement stored with its reason and evidence, and re-checkable.
8. **Determinism:** build twice; any difference fails CI. Then any output change has a cause in the inputs.

## Effort to run (one-person band)

- **What was added today:** about 5 minutes a month. Everything runs in the existing CI workflow.
- **The FtM model is pinned.** Upgrading means replacing one vendored file and re-running the check: about 15 minutes, once or twice a year.
- **Fixtures** regenerate from the published BODS file on every build. They only need attention if the fixture pack changes its layout.
- **REUSE** needs one line in `REUSE.toml` whenever a new kind of file is added; the linter fails until it is there.
- **Next steps 1 to 6** add about 4 days of build work in total and then save time, because new sources and exports follow one pattern.

## Limits

- The FtM check uses FtM's compiled model, not the FtM library. Rules that live only in library code (some value cleaning) are not exercised.
- Wikidata identifiers are corroborating evidence only.
- The OpenCorporates assessment rests on its public repositories and the converter, not on its API.
- The upstream arrangements are untested proposals. None has been discussed with the maintainers.
