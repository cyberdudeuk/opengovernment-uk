# Knowledge graph and navigator

- **Knowledge graph:** knowledge-graph.jsonld links needs, requirements, components, checks and documents. It is generated from `tools/artefacts.py`, so it always matches the specification.
- **Navigator:** docs/navigator.html on the site. Choose any item to highlight its lineage both ways: the needs a requirement serves, what meets it, the checks that prove it and the documents that describe it.
- **Trace check:** every requirement must serve a need, every Done requirement must have a component, and every check and document reference must exist. A negative test proves the check fails on a requirement that serves nothing.
