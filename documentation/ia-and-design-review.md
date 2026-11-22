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

## Review and changes, 22 November 2026 (implemented)

### What we found

| Layer | Before | Problem |
|---|---|---|
| Global navigation | Two different menus: the portal page listed 11 views plus 5 page links; the other pages listed 10 items, a different set | The menu changed depending on where you were; Reconcile, Quality, Help, Product and Ask were unreachable from subpages; organised around the build, not people's questions |
| Masthead | Search card on the home page only; no notifications | Nothing to find or follow from other pages |
| Home page | Ten sections: splash, jump strip, figures, highlights, spotlight, who are you, I want to, why it exists, where to start, where next | Four wayfinding sections overlapped and were scattered; background sat in the middle; long scroll |
| In-page (vertical) | The portal page's drawer lists each view's sections; subpages use tabs | Nation by nation has 11 sections and no drawer |
| Org charts | Left to right only | Depth across a wide screen hides the hierarchy most people expect |

### What changed

**One global navigation**, defined once (`tools/design.py` NAV) and rendered identically on every page. It's grouped by the questions above, adapted to what exists today:

| Menu | Holds |
|---|---|
| Home | |
| Find | Register; Ask a question |
| The state | Explore the anatomy; Nation by nation; UK and the world; Org charts |
| Who answers | |
| Funding | |
| Change | |
| Data | Data and feeds; Developer hub |
| Contribute | What needs a person; Contributor charter; Report a mistake |
| About | Quality and trust; Product and roadmap; Help; Documentation; Design system |

- Groups open as disclosure menus with a one-line description per destination. One is open at a time, and Escape or a click elsewhere closes it.
- The current page and its group are marked.
- What doesn't fit folds into More, which shows each group as a headed list.
- Groups hold whole views and pages, never in-page anchors.
- The menu has its own row under the masthead on every page.

**Masthead utilities on every page:** search (hands off to the register), notifications, latest changes, and the theme switch. The ticker sits directly under the masthead on the home page.

**Home page, in order of precedence:**
1. Splash (what this is, with the rings picture).
2. Jump strip.
3. Find your way: one card, three tabs (Who are you? / I want to… / Every section, grouped as in the menu).
4. The state in numbers: headline figures, with the breakdown behind "Show the breakdown".
5. Highlights beside the spotlight.
6. About this register: collapsed, last.

The page menu went from nine sections to six.

**Org charts run top to bottom.** A parent whose children are all closed stacks them in a column under it, so a level with hundreds of bodies stays readable. Left to right is one click away, and the choice is remembered.

**Checks:**
- every page must carry the shared navigation and its More group (`tools/design.py`, OG-D75);
- the portal page's generator runs in CI, and committed outputs must match a fresh build (OG-D76);
- the browser test opens every page and tab at phone and desktop widths.

### Next, in order of value

1. Done, 22 November: **Tabs for Who answers** (10 sections on one page): chains, where accountability ends, money, PFI, trading funds and corporations, confidence, gaps, ledger, single source. About a day.
2. Done, 22 November (Nation by nation and the design system page): **A drawer on subpages with many sections**, starting with Nation by nation (11). It should reuse the portal page's drawer: retractable, icons, counts, new flags. About a day.
3. Done, 22 November: **Breadcrumbs on body profiles** (Register > family > body), so people know where they are after a search. Half a day.
4. Clarified rather than merged, 22 November (renamed "Help and guides" and "Requirements and design", cross-linked; a merge would hide the requirements behind a help page): **Merge Help and Documentation under About** into one "How it works" page with tabs (guides, tours, glossary, requirements and design). About a day.
5. Done, 22 November: **Ask in the masthead search:** offer "Ask about this" as the last search suggestion, so the AI is one step from anywhere. Half a day.

### Also added, 22 November

- **World map:** every country is named where its name fits, with its treaty count in the current view; zoom (buttons, Ctrl or Cmd and the wheel) and drag to pan; the tooltip gives treaties by kind; a selected country gets a summary card (treaties by kind, trade agreement, tax treaty, Commonwealth).
- **Home-page rings:** one line-icon set for every type of body and every link on the outer ring; nations and territories carry two-letter codes rather than flags.
- **Classification:** department names in a description no longer decide a body's purpose (OG-D78).

### Effort to run

None beyond the existing checks. A new page needs one line in NAV and one in PAGES. The audit fails until both are there.

