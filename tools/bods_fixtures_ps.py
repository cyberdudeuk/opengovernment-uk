"""Public-sector BODS 0.4 test cases, in the layout of the shared BODS fixture pack -> tests/fixtures/bods/public-sector/

The shared pack (github.com/StephenAbbott/bods-fixtures) gives adapters and query engines one agreed set of edge cases,
each a small statement bundle plus an .expected.md saying what correct handling looks like. It has no public-sector
cases yet. These three are cut from this portal's real BODS file, so they stay true to what is published, and each
bundle is checked with Open Ownership's own lib-cove-bods (schema and normative rules). They are ready to offer to the
pack; offering them is the maintainer's decision.

  python tools/bods_fixtures_ps.py             build and check
  python tools/bods_fixtures_ps.py --negative  prove the check fails when it should
"""
import json, pathlib, subprocess, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from licences import licence_of  # noqa: E402  shared with tools/standards.py

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "tests/fixtures/bods/public-sector"

CASES = {
    "20-state-shareholding-in-international-body": {
        "pick": lambda s, n: s.get("publicAccountability", {}).get("relation") == "member-shareholder" and "Reconstruction" in n[s["recordDetails"]["subject"]],
        "md": """# 20 · A state holding shares and votes in an international body

## What this tests
A state as the interested party: the United Kingdom (`entityType.type: state`) holds a shareholding and voting rights
in the International Bank for Reconstruction and Development (`legalEntity`, identified by its LEI). The figures are
the bank's own published share of subscriptions and share of votes.

## Shape (BODS v0.4)
- 2 `recordType: entity`: the United Kingdom (`state`, jurisdiction GB) and the bank (`legalEntity`, XI-LEI)
- 1 `recordType: relationship` with two interests, both `direct` and `beneficialOwnershipOrControl: false`:
  `shareholding` (share of subscriptions, exact) and `votingRights` (share of votes, exact)
- a namespaced extension, `publicAccountability`, says the state is a member and shareholder

## Conformance expectations
- Adapters MUST keep both interests (do not merge them because they describe one holding).
- Adapters MUST NOT treat the state as a beneficial owner (`beneficialOwnershipOrControl` stays false) nor drop it
  for not being a person: BODS represents state ownership by design.
- Sink adapters SHOULD map the state to a public-body type (for FollowTheMoney, `PublicBody`). FollowTheMoney only lets
  an `Ownership` point at an `Asset`, so a converter needs a rule for an intergovernmental body (this portal uses a
  `Membership` and states the share in its description).
- Query engines asked "who holds the bank" MUST return the state with the stated shares, and MUST NOT add shares across
  sources or invent a total.
"""},
    "21-control-by-legal-framework": {
        "pick": lambda s, n: s.get("publicAccountability", {}).get("relation") == "accounts",
        "md": """# 21 · A public body controlled by law: designation into a department's accounts

## What this tests
Control that comes from the law rather than from shares: a UK public body is designated, by an Estimates and Accounts
Order, into a government department's Supply Estimate and accounts. Interest type `controlByLegalFramework`.

## Shape (BODS v0.4)
- 2 `recordType: entity`: the department (`stateBody`, subtype `governmentDepartment`) and the body (`stateBody`)
- 1 `recordType: relationship`, one interest: `controlByLegalFramework`, `direct`, `beneficialOwnershipOrControl: false`,
  with `details` naming the designation
- `source.type: officialRegister`, with the designation order and its fingerprint in `source.description`

## Conformance expectations
- Adapters MUST keep `controlByLegalFramework` (do not collapse it to `otherInfluenceOrControl`).
- Sink adapters mapping to FollowTheMoney SHOULD emit `Control` with `controlType: state` (the published BODS-to-FtM
  mapping does this when the interested party is a state or state body).
- No percentage is stated; a query engine MUST NOT assign one.
"""},
    "22-sponsorship-in-an-extension": {
        "pick": lambda s, n: s.get("publicAccountability", {}).get("relation") == "sponsors",
        "md": """# 22 · Sponsorship carried in a namespaced extension, not as ownership

## What this tests
A department sponsors an arm's-length body: it answers for it to Parliament but does not own it. The relationship uses
the weakest fitting interest (`otherInfluenceOrControl`) and puts the public-sector meaning in a namespaced extension
(`publicAccountability`: relation `sponsors`, how the match was made, the source's own wording).

## Shape (BODS v0.4)
- 2 `recordType: entity` (`stateBody`)
- 1 `recordType: relationship`, one interest: `otherInfluenceOrControl`, `beneficialOwnershipOrControl: false`
- `publicAccountability` extension on the relationship

## Conformance expectations
- Validators MUST accept the extension (BODS allows additional properties) and adapters SHOULD carry it through.
- Adapters MUST NOT promote sponsorship to ownership or to a beneficial interest.
- Query engines following "who owns" MUST NOT traverse this link; "who answers for" MAY.
"""}}


def bundle(pick):
    b = json.loads((ROOT / "docs/bods-0.4.json").read_text())
    names = {s["recordId"]: s["recordDetails"]["name"] for s in b if s["recordType"] == "entity"}
    rel = next(s for s in b if s["recordType"] == "relationship" and pick(s, names))
    want = {rel["recordDetails"]["subject"], rel["recordDetails"]["interestedParty"]}
    ents = [s for s in b if s["recordType"] == "entity" and s["recordId"] in want]
    seen, out = set(), []
    for s in ents:
        if s["recordId"] not in seen: seen.add(s["recordId"]); out.append(s)
    return out + [rel]


def cove(statements):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(statements, f); p = f.name
    jsv = json.loads(subprocess.run(["libcovebods", "jsv", p], capture_output=True, text=True).stdout or "[]")  # noqa: S603,S607 fixed program, our own temp file
    pv = json.loads(subprocess.run(["libcovebods", "pv", p], capture_output=True, text=True).stdout or "{}").get("additional_checks", [])  # noqa: S603,S607
    return len(jsv) + len(pv)


def main():
    if "--negative" in sys.argv:
        s = bundle(CASES["21-control-by-legal-framework"]["pick"]); s[-1]["recordDetails"]["interests"][0]["type"] = "ownsTheWholeThing"
        if cove(s) == 0: sys.exit("fixtures negative: an invalid interest type was not caught")
        if licence_of("tests/elsewhere/x.json") == "OGL-UK-3.0": sys.exit("fixtures negative: licence check passes a file outside the data annotation")
        print("fixtures negative: an invalid interest type is caught by lib-cove-bods; a file outside the data annotation is not given OGL"); return
    OUT.mkdir(parents=True, exist_ok=True); problems = []
    for name, c in CASES.items():
        s = bundle(c["pick"])
        n = cove(s)
        if n: problems.append(f"{name}: {n} lib-cove-bods findings")
        if sum(1 for x in s if x["recordType"] == "relationship") != 1 or sum(1 for x in s if x["recordType"] == "entity") != 2: problems.append(f"{name}: expected 2 entities and 1 relationship")
        (OUT / f"{name}.json").write_text(json.dumps(s, indent=1, ensure_ascii=False))
        (OUT / f"{name}.expected.md").write_text(c["md"])
        if licence_of(f"tests/fixtures/bods/public-sector/{name}.json") != "OGL-UK-3.0": problems.append(f"{name}: REUSE.toml does not give it the Open Government Licence (OG-D65)")
    (OUT / "README.md").write_text("# Public-sector BODS 0.4 test cases\n\nIn the layout of the shared BODS fixture pack (one statement bundle and one `.expected.md` per case). Cut from this portal's published BODS file and checked with lib-cove-bods on every build by `tools/bods_fixtures_ps.py`. Data: Open Government Licence v3.0.\n")
    if problems: sys.exit("fixtures: " + "; ".join(problems))
    print("fixtures:", len(CASES), "public-sector cases, each valid under lib-cove-bods")


if __name__ == "__main__":
    main()
