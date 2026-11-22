# Upstream offers: issue drafts

Ready to paste as one issue per project, if and when the maintainer of OpenGovernment UK decides to send them. Nothing here has been sent. Each issue links to the shared memorandum and to that project's schedule only. Replace `<memorandum link>` with the memorandum's share link before posting.

Record each outcome, including declines, in `documentation/direction-ledger.md`, so no project is asked twice.

## 1. bods-fixtures (BODS interoperability toolkit)

**Title:** Offer: three public-sector BODS 0.4 test cases (state shareholding, control by law, sponsorship extension)

> The pack has no public-sector or state-ownership cases yet. OpenGovernment UK, an open register of UK public bodies, has written three in the pack's layout (statement bundle plus `.expected.md`). Each is cut from published data and checked by lib-cove-bods with no findings:
>
> 1. A state's shares and votes in an international body (the UK and the IBRD). This also raises a mapping question: FollowTheMoney only allows an `Ownership` of an `Asset`, so how should an intergovernmental holding be converted?
> 2. A public body controlled by law, through designation into a department's accounts (`controlByLegalFramework`).
> 3. Sponsorship carried in a namespaced extension, not as ownership.
>
> Cases: https://github.com/cyberdudeuk/opengovernment-uk/tree/main/tests/fixtures/bods/public-sector
>
> If they're wanted, I'll open a pull request with whatever numbering and wording you prefer. If not, no problem at all. The wider, non-binding proposal is here (Schedule A): `<memorandum link>`

## 2. opencheck

**Title:** Offer: an official-sourced UK source of state bodies for the state-control signal

> OpenCheck's state-control signal builds its state nodes from sources that each cover part of the world. OpenGovernment UK publishes about 3,500 UK public bodies, each with its accountable department and the official source of every link, as BODS 0.4 and FollowTheMoney. Would it be useful as a UK source? If so, which format suits you best?
>
> Files: https://cyberdudeuk.github.io/opengovernment-uk/bods-0.4.json and https://cyberdudeuk.github.io/opengovernment-uk/data/register.ftm.json
>
> Proposal (Schedule A): `<memorandum link>`

## 3. Open Ownership

**Title:** A public-sector use of BODS 0.4, offered as an example

> OpenGovernment UK applies BODS 0.4 to a whole state's public bodies: `state` and `stateBody` entities, `controlByLegalFramework`, and a namespaced `publicAccountability` extension. The file has no schema errors and no lib-cove-bods findings. The profile is public. If it fits your list of tools or examples, a listing would be welcome; so would any correction to how the standard is used.
>
> Profile: https://github.com/cyberdudeuk/opengovernment-uk/blob/main/documentation/bods-public-sector-profile.md
>
> Proposal (Schedule B): `<memorandum link>`

## 4. OpenSanctions

**Title:** Dataset suggestion: UK public bodies as reference data (FollowTheMoney, OGL v3.0)

> `register.ftm.json` holds UK public bodies, the companies they control, international bodies, control and ownership links, successions and memberships. Every entity is checked against FollowTheMoney 4.11.3's compiled model. It's offered as reference data for recognising state entities, kept clearly apart from sanctions lists. Licence: Open Government Licence v3.0.
>
> File: https://cyberdudeuk.github.io/opengovernment-uk/data/register.ftm.json
>
> Proposal (Schedule C): `<memorandum link>`

## 5. OpenCorporates

> OpenCorporates has few public repositories, so this goes through its own contact route rather than an issue.

**Subject:** UK public bodies that are companies, with their controlling public body

> OpenGovernment UK lists the UK public bodies that are companies (59 at present). Each comes with its Companies House number and the public body that controls it, citing the official source. Would a sourced public-ownership flag be useful to your users?
>
> Proposal (Schedule D): `<memorandum link>`
