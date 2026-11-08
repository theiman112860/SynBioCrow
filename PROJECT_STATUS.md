# SynBioCrow authoritative project status
Updated: 2026-11-08
Status: M1 BLOCKED ON CANONICAL SOURCE RECOVERY; governance installed.

## Verified repository facts
- Repository: theiman112860/SynBioCrow.
- main README describes SynBioCrow 2.2.0, most recent main history found dated 2026-09-29.
- develop/2.4 pyproject.toml declares version 2.4.0, but its README is an older 2.3 release-candidate narrative: documentation and package metadata are not synchronized.
- Branch listing includes develop/2.3, develop/2.4, main, and governance/m1-baseline-20261108; no develop/2.6 branch was returned.
- GitHub governance files were committed and read back. GitHub Actions execution is NOT verified.
- Search for named latest seven-engine source/result ZIPs in conversation/library index returned no results. This is not proof that artifacts do not exist.

## Milestone status
| Milestone | State | Evidence |
|---|---|---|
| M1 Baseline recovery | BLOCKED | GitHub metadata and 2.4 manifest inspected; authoritative 2.6 source not found |
| M2 Seven-engine native readiness | NOT VERIFIED | Native reaction outputs needed per engine |
| M3 Reaction output normalization | NOT VERIFIED | Requires canonical source |
| M4 Reaction graph and hybrid closure | NOT VERIFIED | Requires canonical source |
| M5 Ranking and held-out evaluation | NOT VERIFIED | Historical evaluations are not a fresh pass |
| M6 Usable end-to-end application | NOT VERIFIED | Clean-install test not run |

## Task M1.1
Goal: identify canonical 2.6 source and seven-engine roster.
Context: GitHub 2.2/2.4 code, historical Colab run artifacts.
Constraints: no architecture changes, no new engine installation, no benchmark mutation.
Done-when: SHA-256 source manifest; seven native entry points; latest outputs mapped; provenance and dependencies documented.
Result: BLOCKED; no authoritative 2.6 SOURCE ZIP in accessible searched materials.

## Immediate single next action
Obtain the latest 2.6 seven-engine SOURCE ZIP or a direct Git commit/branch containing that source. Prefer the most recent seven-engine canonical notebook plus its SOURCE package. Inspect the source before any repairs.

## Immutable boundaries
Frozen 2.3 artifacts and sealed 65-path Galaxy benchmark remain untouched. Historical prospective failures remain failures.
