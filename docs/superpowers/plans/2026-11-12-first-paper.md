# First OpenPreprint Kit short report

Goal: a short Japanese technical-report draft about OPK, with inspectable CI data and a local self-application exercise. This is not the production-completion declaration.
Baseline: 940d0d06d957cd0708f644a595911bdbc3fffa64, frozen before the manuscript.
Constraints: GitHub-only online publication; never claim a source commit/PR is an immutable paper Release; no clinical records/keys; no invented human identity, reviewer, or measured timing accuracy. Preserve the toolkit template at root. Manuscript author/rights choices remain proposals until approved.
1. Retrieve exact tested source + raw CI log. Implement standard-library evidence summarization with failing tests first (pin mismatch, inconsistent totals, duplicate test identity, failed/skipped suite).
2. Write concise design/evaluation/limitations report. Create Markdown + typeset PDF and include machine-readable test counts and provenance.
3. Reproduce the reported counts. In an isolated copy, validate the actual draft PDF and data with OPK; explicit provisional metadata only. The committed root template stays unchanged, and this does not publish a Release.
4. Push a scoped manuscript branch/PR, verify the new commit, and distinguish draft availability from formal Release status.
5. Notify only when the first actual paper Release and its required assets can be observed; polling task is read-only.
