# Contributor charter

OpenGovernment UK is an open register of the UK state, built in the open as a public good. This charter says what contributors and maintainers can expect from each other, how work is credited, and how anyone can grow from a first correction to looking after part of the register.

It sits alongside [CONTRIBUTING.md](../CONTRIBUTING.md) (how to make a change) and the [code of conduct](../CODE_OF_CONDUCT.md) (how we treat each other).

## What we're building together

One register of every UK public body that anyone can trust, check and reuse. Each body is listed with the code its own register gives it, who it answers to, and the evidence for every link. It is published in the formats other tools already read, and anyone can use it for free.

## Our principles

1. **Evidence over opinion.** Every fact cites an authoritative source. A correction with a source beats an argument without one, whoever makes it.
2. **Roles, not people.** We publish bodies, offices and roles. We never publish names of office holders, contact details or anything that identifies a private person.
3. **No guessing.** If two records might be the same body, we say why and let a person decide. Anything worked out is labelled as worked out.
4. **Open by default.** Discussion, review and decisions happen in public issues and pull requests.
5. **Every mistake leaves a guard.** When something goes wrong, we fix it and add the check that stops it happening again.
6. **Neutral.** We state facts as the official source states them, with the source, and take no political position, including on contested sovereignty or international relations.

## What contributors can expect from maintainers

- **A reply.** We aim to respond to every issue and pull request within two weeks. This is maintained by a small number of volunteers, so it's an aim, not a guarantee. If something is urgent (for example, personal data published by mistake), say so in the title.
- **Reasons.** If we can't accept a change, we'll say why and what would make it acceptable.
- **Credit.** Every accepted contribution is credited (see below), in the form you choose.
- **Your work stays yours.** You keep copyright; you license it to everyone under the project's licences (see below). There is no contributor licence agreement.
- **Safety.** We act on code of conduct reports, and we'll remove anything that puts a person at risk.

## What maintainers ask of contributors

- Cite the source for any fact, preferably the official register or the law itself, with a link to the exact place.
- Don't include personal data: no names of office holders, email addresses or phone numbers, including in issues.
- Keep the checks passing, and add a check when you fix a mistake.
- Be patient and kind. Assume good faith.

## Ways to take part

From quickest to most involved:

| Contribution | How | Typical time |
|---|---|---|
| Report a mistake | [Data correction form](https://github.com/cyberdudeuk/opengovernment-uk/issues/new?template=data-correction.yml) with the source | 5 minutes |
| Match a body the matcher couldn't | Pick one from "What couldn't be matched" on the site; open a data correction | 10 minutes |
| Suggest a source | [Feedback form](https://github.com/cyberdudeuk/opengovernment-uk/issues/new?template=feedback.yml) with its address and licence | 10 minutes |
| Tell us you reuse the data | [Reuse form](https://github.com/cyberdudeuk/opengovernment-uk/issues/new?template=reuse.yml) | 5 minutes |
| Add a crosswalk row or a test case | Pull request against `sources/crosswalks.json` or `tests/fixtures/` | 1 hour |
| Build an add-on or integration | Build on the published files or the MCP connector; tell us | Your choice |
| Improve code or documentation | Fork, branch, pull request; CI runs every check | Your choice |
| Steward an area | Look after a family of bodies or a nation (below) | An hour or two a month |

Issues labelled `good first issue` are a good place to start. `help wanted` marks work we'd especially welcome.

## Recognition

Contributions are credited in the way the contributor chooses: your GitHub handle, a name you're happy to publish, an organisation, or anonymously.

- **CONTRIBUTORS.md** lists everyone whose contribution was accepted, by kind of contribution.
- **Release notes** credit the corrections and features in each release.
- **The citation file** (CITATION.cff) lists contributors who opt in, so academic and official reuse cites you too.
- **The developer hub** lists add-ons and integrations built on the register, with a link to each.
- **The source page** names who found each new source, if they wish.
- **Stewards** are named for the area they look after.

## Stewardship

A steward looks after part of the register, such as NHS bodies, Welsh public bodies, or the Crown Dependencies. They are usually someone who knows that part of the state well. A steward:

- reviews data corrections for their area, and says whether the source supports them;
- spots changes (renames, mergers, new bodies) and opens issues for them;
- is named as steward for the area, and can step down at any time.

Anyone who has had several corrections accepted in an area can ask to become its steward, in an issue. A maintainer agrees in public. Stewards have no merge rights by default; maintainers merge once a steward has reviewed.

## Licensing of contributions

Inbound licence equals outbound licence:

- **Code:** MIT.
- **Documentation**, including test-case expectations and this charter: CC BY 4.0.
- **Data and corrections:** Open Government Licence v3.0. Only contribute facts from sources whose terms allow this. Official UK public sector information under OGL is fine; so is data under CC0 or CC BY. Data under a non-commercial or share-alike licence can be linked to but not copied in.

Every file's licence is recorded machine-readably in [REUSE.toml](../REUSE.toml) and checked on every build.

Please sign off your commits (`git commit -s`) to confirm you have the right to contribute them, under the [Developer Certificate of Origin](https://developercertificate.org/).

## Decisions

Maintainers make final decisions, in public, with reasons. Disagreements about facts are settled by the best available source; disagreements about direction are recorded in the [direction ledger](direction-ledger.md). Anyone can propose a change to this charter by pull request.

## Effort for maintainers (kept honest)

Reviewing a sourced correction takes about 10 minutes. The maintainer aims to triage new issues weekly. If contributions grow beyond what one person can review, stewards share the load first.
