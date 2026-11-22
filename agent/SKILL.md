---
name: opengovernment-uk
description: Answer questions about UK public bodies (who a body answers to, who owns or controls it, its codes, the UK's international memberships, treaties, trade and tax agreements, and its shares in international financial institutions) from OpenGovernment UK's published open data, citing the source of every fact.
---

# Answering questions from OpenGovernment UK

OpenGovernment UK is an open register of the UK state. It is a pilot, not an official list, and is not affiliated with any public body. Everything below is published at https://cyberdudeuk.github.io/opengovernment-uk/ under the Open Government Licence v3.0.

## Rules

1. **Answer only from the files.** Never fill a gap from memory. If the files don't hold the answer, say so.
2. **Cite the source each fact gives.** Every link carries its official source (for example a designation order or a GOV.UK page). Name it.
3. **Say when something is worked out.** Purpose, activity and reach are worked out, not official, and some may be wrong.
4. **Absence is not evidence.** A body missing from the register may still exist.
5. **Never add sources together.** Report each institution's figure as it publishes it.
6. **Check freshness.** `data/source-status.json` says when each source was read and whether it is current. Mention it if a source is stale or was not read.
7. **No people.** The register names roles, not people. Don't look people up through it.

## Where each answer is

| Question | File | How |
|---|---|---|
| Who does a body answer to? | `accountable-owner.csv` | Find the row by `name`; read `accountable_owner`, `answerable_to` and `chain`. The chain shows each step with its relation and source |
| Who controls or sponsors a body, and by what? | `bods-0.4.json` | Relationship statements: `interestedParty` controls `subject`. Interest type `controlByLegalFramework` means designation by law; `publicAccountability.relation` gives accounts, sponsors, parent, owns or controls |
| What are a body's codes elsewhere? | `concordance.csv` | One row per body: GOV.UK, ONS, GSS, NHS ODS, Companies House, LEI, charity numbers, Wikidata, data.gov.uk |
| The UK's shares and votes in an international financial institution | `bods-0.4.json` | Relationships whose `publicAccountability.relation` is `member-shareholder`; interest `votingRights` gives the share of votes as the institution publishes it |
| A trade agreement or tax treaty with a country | `data/international.jsonld` | The `schema:Country` node: `og:tradeAgreementInEffect`, `og:taxTreaty`, `og:commonwealthMember`, `og:treatyCount` |
| The UK's memberships of international bodies | `data/international.jsonld` | `org:Membership` nodes, each with the UK body that leads |
| Anything as FollowTheMoney entities | `data/register.ftm.json` | One entity per line |
| What every field means | `documentation/solution/10-data-dictionary.md` in the repository | Generated from the files |
| What could not be read, and why | `data/source-status.json` | `not_read` |

Start from `data/catalogue.jsonld` (DCAT) or `llms.txt` to find any other file.

## Checked

`agent/evals.json` holds questions with known answers. `tools/agent_evals.py` answers each one by the recipe above from the published files, on every build, and fails if any answer changes. This checks that the files can answer the questions; it does not run a language model. To evaluate a model, give it this file and the questions, and compare its answers with `expected`.
