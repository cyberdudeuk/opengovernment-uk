# Public bodies: trends since 2012 and three lenses to 2030

**Status:** analysis, 22 November 2026. Figures marked *modelled* are the arithmetic of stated assumptions, not forecasts or government plans. Everything else is reproduced from the cited sources by `tools/trends.py` and `tools/scenarios.py`.

## Summary

- **The number of bodies falls slowly; the money does not.** The Cabinet Office's own editions list 295 entries in 2012-13 and 251 in 2023-24 (−15%). For bodies tracked like-for-like, real-terms government funding is down about 11% over the same period. But total funding through these bodies has risen, because a few very large bodies dominate. In 2023-24, NHS England, the Education and Skills Funding Agency, HMRC and Network Rail received about £306bn of the £370bn.
- **Closing small bodies releases little money.** In 2023-24 the 98 entries with under 50 staff reported £6m of administration spend between them, and the 64 advisory NDPBs £22m. NHS England alone accounted for £1.89bn, 34% of all ALB administration spend.
- **History says counts mostly fall by reclassification, not abolition.** Of the 901 bodies in the 2010 review, 21% were abolished and 13% merged; the rest were kept or reformed. Of the bodies removed from the Cabinet Office database between 2016 and 2019, 143 were reclassified, 35 replaced or merged, and only 7 closed outright (National Audit Office).
- **The current review is real but modest.** The Cabinet Office reports 16 bodies closed or merged under the review launched in April 2025, NHS England among them (abolition by March 2027 under the Health Bill).
- **Three lenses to 2030 (modelled):**
  - *Evolution:* about 211 entries, releasing about £1.2bn a year of running costs.
  - *Reform:* about 156 entries, about £1.4bn.
  - *Revolution* (AI-enabled, digitally native by default): about 111 entries, £1.7bn to £2.0bn.

  Even the most radical lens releases at most about 37% of the £5.5bn administration base, and almost nothing of the programme money, which pays for functions that continue whoever delivers them.

## The November 2020 baseline: checked before use

The *Public Bodies database-Nov2020* workbook in the Government Data SharePoint archive joins four sources: Public Bodies transparency data, WGA, NAO's government companies list and ONS.

**What the workbook actually holds.** We compared it name by name with the published editions. Its transparency sheet is the **2019** edition, with data as at March 2019, not the 2020 edition:
- it contains bodies that only appear in 2019 (Ebbsfleet Development Corporation, FCO Services, Forest Enterprise England, the Single Financial Guidance Body);
- it lacks bodies new in 2020 (Money and Pensions Service, Government Property Agency, Defence Equipment and Support).

It was therefore one edition stale on the day it was saved.

**What enters the solution, and what doesn't:**
- Nothing from the workbook enters the solution as data. It also holds personal fields, such as chairs and senior sponsors, which are never read.
- The historical baseline is the official *Public Bodies 2020* edition, reconciled with today's register:

  | Verdict | Bodies |
  |---|---:|
  | Still current | 202 |
  | Replaced (successor named) | 15 |
  | Closed | 3 |
  | For a person to resolve | 24 |
  | **Total** | **244** |

- Examples of replacements:
  - Crown Commercial Service → Government Commercial Agency
  - Information Commissioner's Office → Information Commission
  - Gangmasters and Labour Abuse Authority → Fair Work Agency
  - Valuation Office Agency → HM Revenue & Customs
- The 24 left for a person are mostly statutory names that differ from the everyday name. For example, "Commission for Equality and Human Rights" is the Equality and Human Rights Commission. None is guessed.
- **Rule:** 2020 values are kept only as dated historical observations. They never overwrite a current fact, and a body's current state always comes from today's registers. The full list is in `data/reconciliation-2020.csv`.

## Trends from the Cabinet Office's own editions

| Edition | Figures for | Entries | NDPB | Exec. agency | NMD | Staff (FTE, as listed) | Entries reporting funding | Like-for-like real change in funding |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 2012 | 2011-12 | 262 | 262 | – | – | 105,225 | 59% | |
| 2013 | 2012-13 | 295 | 231 | 42 | 22 | 239,285 | 66% | −17.1% (122 bodies) |
| 2014 | 2013-14 | 283 | 219 | 41 | 21 | 230,456 | 70% | +1.6% (155) |
| 2015 | 2013-14 | 282 | 215 | 43 | 23 | 234,660 | 72% | not used: year uncertain |
| 2016 | 2015-16 | 273 | 209 | 40 | 24 | 269,545 | 70% | −3.6% (152) |
| 2017 | 2016-17 | 254 | 194 | 39 | 21 | 273,127 | 69% | +1.3% (140) |
| 2018-19 | 2017-18 | 250 | 183 | 37 | 20 | 275,696 | 74% | −2.6% (139) |
| 2019 | 2018-19 | 244 | 184 | 39 | 20 | 299,171 | 69% | −6.2% (105) |
| 2020 | 2019-20 | 244 | 186 | 39 | 19 | 317,439 | **39%** | +10.7% (72) |
| 2022/23 | 2022-23 | 249 | 191 | 38 | 20 | 390,397 | 76% | +11.9% (59) |
| 2023/24 | 2023-24 | 251 | 192 | 39 | 20 | 397,003 | 76% | −3.8% (136) |

**How to read it:**
- **Entries are the stable count.** Group entries such as the Independent Monitoring Boards are counted as one in some editions and as many in others, so "number of bodies" swings and isn't used.
- **2012 covers NDPBs only.** From 2013 the editions also list some executive agencies and non-ministerial departments; the directories from 2022/23 do the same.
- **Funding totals are not comparable across editions.** Coverage of a few very large bodies changes:
  - NHS England is missing in 2020;
  - HMRC appears from 2019;
  - the Education Funding Agency appears from 2013.

  The like-for-like column therefore compares only bodies present in both editions, in 2025-26 prices (HM Treasury GDP deflator, October 2026).
- **Outliers are set aside, not adjusted.** Any body whose funding moves more than threefold, or is negative, is set aside and listed in `data/public-bodies-trends.json`. These are source anomalies: for example, Office for Students funding entered in the wrong unit in 2020, and negative values for the Government Legal Department and Ofwat.
- **Two links are thin.** The 2020 edition reports funding for only 39% of entries, and the 2019-20 to 2022-23 comparison spans three years with 59 bodies. The chained like-for-like change from 2012-13 to 2023-24 is about **−11%**, with those two links carrying the most doubt.
- **Staff growth is mostly composition.** Listed staff rise from about 239,000 to 397,000, but mostly because HMRC enters the series in 2019 and NHS England grows. A like-for-like staff series is the next analytic step.
- **Creation and closure.** GOV.UK records 1 to 7 new organisations a year with a start date, against 9 to 20 dated closures a year since 2015, with closures rising since 2023 (11, 16, 20, 20). Only some closures carry dates, so these are lower bounds.

## Where the money and the running costs sit (2023-24)

| Size | Entries | Administration spend | Staff (FTE) |
|---|---:|---:|---:|
| Under 50 staff | 98 | £6m | 796 |
| 50 to 499 | 77 | £747m | 16,204 |
| 500 or more | 76 | £4,742m | 380,002 |
| **All** | **251** | **£5.5bn** | **397,003** |

Advisory bodies are often paid for inside their sponsor department, so the small-body figure is understated. It is still small.

## Three lenses to 2030 (modelled)

The baseline is the Public Bodies Directory 2023/24. All three lenses start from the same known events:
- 16 bodies closed or merged under the 2025 review;
- NHS England's expected saving of up to about £1bn a year by the end of the Parliament, as stated by the minister in committee.

| Lens | What changes | Entries in 2030 | Running costs released a year | Share of the £5.5bn |
|---|---|---:|---:|---:|
| **Evolution** | The review runs its course. Closures continue at about 5 a year net after 2026; no change inside large bodies | 211 (−16%) | about £1.2bn | 22% |
| **Reform** | Consolidate by function: about 10 expert councils replace the 64 advisory NDPBs; 15 regulators merged; 10 agencies brought back into departments; shared corporate services save 10% in large and medium bodies | 156 (−38%) | about £1.4bn | 25% |
| **Revolution** | Digitally native by default: independent advice on demand from standing panels with AI-assisted evidence synthesis; regulators converge on a few sector regulators; transactional agencies run on departmental platforms; every new body needs an independence test and a sunset clause; AI and automation save 20 to 30% of running costs in large bodies | 111 (−56%) | £1.7bn to £2.0bn | 37% |

**What it would take, and what could go wrong:**
- **Independence has value.** The 2010 tests (technical function, political impartiality, independent fact-finding) still describe why many bodies exist. Advice on demand must keep its independence visibly, or the saving costs trust.
- **Most bodies are statutory.** Closing them needs primary legislation or order-making powers. That pace, not the analysis, sets the timetable: the Health Bill took over a year from announcement to introduction.
- **Reorganisations cost money first.** Transition costs typically consume the first year or two of savings. They aren't modelled here.
- **Counts are a poor measure of success.** The NAO's base rate shows counts falling mostly by relabelling. Success should be measured by function: running cost per function delivered, duplication removed, and time to decision.
- **AI changes the work, not the accountability.** Someone must still answer to Parliament for each function. That is why this register traces every body to an elected body.

## Preparing for the next decade

1. **Function before form.** Catalogue functions, not bodies, so overlaps show regardless of who holds them. This register's accountability chains are the starting point.
2. **A sunset clause by default.** Every new body gets a review date and a statutory end unless renewed.
3. **An independence test at creation.** Use the three 2010 tests, recorded on the register, so the reason a body exists is visible.
4. **Shared platforms before new bodies.** Common digital and corporate services make bringing a function back into a department cheap.
5. **Measure what is released.** Report administration spend released, not the number of bodies closed.

## Limits of the evidence

- The Cabinet Office editions are self-reported by departments and change scope over time.
- The 2021 edition is missing.
- The 2015 edition mostly restates 2013-14 annual reports.
- Money coverage ranges from 39% to 76% of entries.
- Real terms use the whole-economy GDP deflator, not a public-sector one.
- Scenario parameters are judgements; change them in `tools/scenarios.py`.

## Sources

- Cabinet Office, *Public Bodies* editions 2012 to 2020 and *Public Bodies Directory* 2022/23 and 2023/24 (GOV.UK collection "Public bodies"), OGL v3.0. File links are in `tools/trends.py`.
- HM Treasury, *GDP deflators at market prices, and money GDP*, October 2026 (Budget).
- Health Bill policy papers (GOV.UK) and committee debate, 2026; the Cabinet Office statement on the ALB review as reported by Civil Service World, 2026; Parliamentary written answer HL2549, 16 September 2026.
- Public Administration Select Committee, *Smaller Government: Shrinking the Quango State* (HC 537, 2010-11), for the 2010 outcomes.
- Institute for Government explainers on public bodies reform, citing the National Audit Office for 2016 to 2019 removals.

## Reproduce

```
python tools/trends.py --fetch      # download the editions (OGL; not redistributed because they name office holders)
python tools/trends.py              # series, like-for-like change, 2020 reconciliation
python tools/scenarios.py           # the three lenses
```
