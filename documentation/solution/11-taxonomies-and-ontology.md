# Taxonomies and ontology

- **Ontology:** ontology.ttl (OWL, Turtle). It extends W3C ORG; `og:PublicBody` corresponds to BODS `stateBody` and FollowTheMoney `PublicBody`.
- **Taxonomies** (SKOS concept schemes in the same file): accountability relations (accounts, sponsors, controls, parent, owns) and back-office classes (A, B).
- **Planned:** COFOG divisions and groups as a SKOS scheme, and the Australian-style body types mapped to UK types.

| UK class | ORG | BODS 0.4 | FollowTheMoney |
|---|---|---|---|
| og:PublicBody | org:FormalOrganization | entityType stateBody | PublicBody |
| og:accountsTo / og:sponsoredBy | org:subOrganizationOf (looser) | relationship, controlByLegalFramework | Membership / Directorship (looser) |
| og:ownedBy | — | relationship, shareholding | Ownership |
| og:ProjectCompany | org:FormalOrganization | entityType registeredEntity | Company |

The files parse with rdflib on every build; a malformed file fails the build.
