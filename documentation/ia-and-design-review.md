# Information architecture and design review (for 0.4)

**Status:** review and proposal, 22 November 2026. This sets the brief for the next release.

## What changes and why

OpenGovernment UK is now an open-source public good that depends on contributions. Its readers are not only public servants but also journalists, researchers, civil society and businesses.

The 0.2 to 0.3 portal grew view by view:
- **Ten top-level sections, organised around the build:** Explore, Register, Reconcile, Changes, Who answers, Data, Quality, Help, Product, Ask.
- **Several are about how the register is made** (Reconcile, Quality, Product), not what people come to find.
- **Contribution is buried** in a footer form.

## Who comes, and what they ask

| Audience | Typical question | First thing they need |
|---|---|---|
| Member of the public, civil society | Who runs this, and who do I hold to account? | Search a body, then a plain answer: who it answers to, what it costs, how to ask (FOI) |
| Journalist | Who owns this, who pays, what changed? | Ownership and money chains, change history, downloadable evidence with sources |
| Researcher, academic | How has the state changed, and can I get it all? | Time series, bulk files, SQL, citation, method |
| Public servant | What is the right reference for this body? | Stable keys, APIs, feeds, lineage of every fact |
| Business, supplier | Who buys what, and through which body? | Contracts by body (OCDS), the procuring authority behind PFI |
| Contributor | What can I fix today? | The queue of unmatched names and corrections, each with its source rule |

## Proposed information architecture

The global navigation follows people's questions, not the build:
1. **Find**: search and browse every body, by family, nation, function and sector.
2. **The state**: the whole anatomy as a hierarchy you drill into, from the Crown and Parliament down to the smallest unit, with horizontal and vertical lineage.
3. **Who answers**: accountability chains, sponsorship and ownership (BODS graphs).
4. **Money**: funding, running costs, PFI and contracts, following the money.
5. **Change**: machinery of government over time, family trees of bodies, trends since 2012 and the lenses to 2030.
6. **Data**: downloads, APIs and standards (BODS, OCDS, FtM, ORG, DCAT), with the feed contract.
7. **Contribute**: what needs fixing, how to fix it, and the rules for sources; a review queue and recognition for contributors.
8. **About**: method, quality and checks, roadmap, governance, licences.

Ask (AI) sits on every page as a search-and-answer bar, not as a separate destination.

## Visualisation and analytics

| Need | Technique |
|---|---|
| Anatomy as a hierarchy | Collapsible tree with drill-down to the lowest unit; a sunburst or icicle for the shape of the whole state |
| Accountability and ownership | BODS graph (bods-dagre), vertical (who answers) and horizontal (who it shares owners or functions with) |
| Money flows | Sankey from Parliament to departments to bodies; treemap of running costs by size and function |
| Change over time | Genealogy timeline (predecessors, successors, mergers); small multiples of counts by classification |
| Geography | Map of bodies by nation and region, where an address or area is known |
| Indicators and dashboards | Coverage, agreement between sources, unresolved queue, closures and creations a year, running costs released, contributions merged |

Every chart has a table view, a text summary and its source.

## Design direction

- **Its own look, not a government template.** It must not be mistaken for an official government service: neutral, civic and editorial, with the trust signals of a public reference.
- **Keep what works:** the warm paper-and-ink palette, the display serif with a readable sans for body text, the retractable drawer with item counts, and tabs inside views.
- **Improve:**
  - a calmer masthead;
  - fewer top-level items, as above;
  - a consistent component set for summary cards, chain steps, evidence chips and data tables;
  - charts that share one validated palette, safe for colour-blind readers, in light and dark;
  - motion only where it explains, and respects reduced motion.
- **Evidence everywhere:** each fact carries a small source chip that opens its provenance.

## Equality, diversity, inclusion and accessibility

- **WCAG 2.2 AA as the floor:** keyboard access to every control, visible focus, 4.5:1 contrast, no meaning by colour alone, text alternatives for every chart, and support for 400% zoom and phone widths.
- **Plain English** at about reading age 9 for summaries, with a glossary and tooltips for every technical term, and readable without jargon.
- **Inclusive by design:** no personal data; neutral language about bodies and people; Welsh-language summaries as a goal for Welsh bodies.
- **Research with people who use assistive technology,** journalists and community groups before release; publish what was learned.

## Effort to run, for one maintainer

The redesign is a one-off build. Running it adds no services: the site stays static on GitHub Pages, the data is rebuilt by the existing workflows, and contributions arrive as GitHub issues and pull requests. The ongoing cost is the review time for contributions, so the contribution page should make good submissions easy and invalid ones impossible (structured forms, a required source).
