# Contributing

OpenGovernment UK is an open-source public good. It gets better when people who know a part of the state correct it,
and when people who use it say what they need. Everyone is welcome: public servants, journalists, researchers, students,
civil society and anyone else with an interest in how the state is organised.

## Ways to help

| You want to | Do this |
|---|---|
| Correct a body, a link or a figure | Open a **Data correction** issue and cite the source that says so |
| Resolve a name that couldn't be matched | Pick one from "What couldn't be matched" on the site and open a **Data correction** issue |
| Suggest a source | Open a **Feedback** issue with the source's address and licence |
| Fix or improve code | Fork, branch, and open a pull request; CI runs every check |
| Improve the documentation | Pull request against `documentation/` |

## The rules every change follows

1. **Cite an authoritative source** for every fact. No source, no change.
2. **No personal data.** Bodies, offices and roles only: no names of office holders, no contact details.
3. **Never guess a match.** If two records might be the same body, say why and let a reviewer decide.
4. **Checks must pass.** `python tools/check.py && python tools/check.py --negative && python tools/check_trends.py` and `ruff check tools`.
5. **Every defect gets a guard.** If you fix a mistake, add the check that stops it coming back, in the same pull request.

## Review

Pull requests and data corrections are reviewed in public. Maintainers merge when the source is cited and the checks pass.
Please be patient: this is maintained by volunteers.

By contributing you agree that your code is released under MIT, your documentation under CC BY 4.0, and data corrections
under the Open Government Licence v3.0, and you agree to follow the [code of conduct](CODE_OF_CONDUCT.md).
