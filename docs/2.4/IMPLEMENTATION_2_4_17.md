# SynBioCrow 2.4.17 — Development Literature-Anchor Evaluation

2.4.16 solved the score-tie problem: distinct within-target scores rose from 14 to 519 for curcumin, 10 to 437 for dammaradienol, 20 to 1,916 for jasmonic acid, and 23 to 206 for MIBK.

2.4.17 asks the more important question: does the new ordering recover literature-supported pathway chemistry on the development split?

Because the current 2.4 tranche does not contain a curated reaction-by-reaction gold route, 2.4.17 does **not** fabricate exact reaction truth. It uses conservative pathway anchors explicitly supported by the four development papers and resolves their structures through PubChem. Candidate routes are scored by anchor recall and the system reports the best recall appearing within Top-1/5/10/50/100 of the frozen 2.4.16 ordering.

This is an evaluation-only stage:
- four development records only;
- bakuchiol and D-allitol validation records remain sealed;
- no generation;
- no weight fitting;
- unresolved anchor structures fail closed;
- anchor recovery is not described as exact-route recovery.

A later curated exact-reaction gold set can replace this proxy without changing the validation firewall.
