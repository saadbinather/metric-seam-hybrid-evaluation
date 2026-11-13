# Blind human annotation instructions

Annotate only the supplied claim/evidence pair. Do not search the paper, open
reserved source files, or consult model outputs.

Enter `human_verdict` as `supported`, `unsupported`, or `unresolved`, plus a
concise `human_reason`. Supported requires independent evidence for the same
scope and focal quantity. Unsupported means the scope is clear but the value
or relation fails. Unresolved means scope, entity binding, units, or relation
cannot be determined from the displayed passages alone.

Reader 1 completes all 40 rows. Reader 2 independently completes only the
fixed 12-row file. Do not compare files until both are complete. Blank verdicts
or reasons cannot be locked.
