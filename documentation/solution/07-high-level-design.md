# High-level design

| Component | Responsibility | Inputs | Outputs | Proven by |
|---|---|---|---|---|
| Register spine | One record per body, keyed by its register's code | 0.2.2 release | Records, identifiers | Known-answer checks |
| Fetcher | Download, fingerprint, record provenance | Source URLs | sources/, manifest.json | c_hashes |
| Builder | Match parent names; trace chains with precedence EAO > PBD > ONS > GOV.UK > ownership | Sources, spine | tree.json, edges.csv, accountable-owner.csv | 9 checks plus negatives |
| Portal builder | Assemble page, embed data, write feeds | Builder outputs | index.html, accountability.json, ppp.csv | Footer, IDs, self-checks |
| BODS exporter | Entities and relationships as BODS 0.4 | tree.json | bods-0.4.json | Official schema |
| Trends | Editions 2012 to 2023/24, deflated, like-for-like | Official editions | trends JSON, 2020 reconciliation | 4 checks plus negatives |
| Scenarios | Three modelled lenses to 2030 | Trends, stated assumptions | scenarios-2030.json | Recompute check |
| Back-office classifier | Class A bodies, class B lines of business | GOV.UK descriptions | back-office.json | Known answers plus negatives |
| Documentation generator | Spec, dictionary, ontology, graph, navigator | Traceability spine, data files | documentation/solution, navigator.html | Parse and trace check |

**Interfaces.** All exchange is by files in open formats; the feed contract (feed-contract.json, version 1.1.0) states fields and guarantees for reusers.
