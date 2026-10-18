---
name: self-consistency-narrative-java
description: Check the narrative-java skill's own files against its own rules, so no violation reaches agents that load it. Covers the prose of skill/*.md and README.md, the Java code examples in skill/*.md, the Python scripts, the fixtures, and the copies of the narrative-python prose files. Use when the user asks for a self-consistency pass, a self-evaluation, or to re-apply the rules to the skill.
---

# Self-consistency of narrative-java

Agents copy the wording and the examples of `skill/*.md`, so a violation there is copied into new code.
Run every step from the repository root. Change nothing that a rule does not require, and commit
nothing.

1. **New rules since the last pass.** `git log -1 --format=%cs -- skill/` gives the date. Read every
   record of `benchmark/decisions.jsonl` from that date on, and look for examples that a new rule
   makes wrong.

2. **Prose of the docs.** The wording checks one code at a time, without NAR012, because the docs
   cite decision ids as provenance:

   ```bash
   for code in NAR013 NAR014 NAR015 NAR016 NAR018; do python3 skill/checks.py --select $code skill/SKILL.md skill/architecture.md skill/tooling.md README.md; done
   ~/.local/share/narrative/lintenv/bin/python skill/agentverbs.py skill/SKILL.md skill/architecture.md skill/tooling.md README.md
   ~/.local/share/narrative/lintenv/bin/python skill/agentverbs.py --review skill/SKILL.md skill/architecture.md skill/tooling.md README.md
   ```

   Known and accepted: in `SKILL.md`, the NAR014, NAR016 and NAR018 hits on the lines with the banned
   words as examples, and the NAR017 misparses `value knowing` and `Comments thinking`, which narrative-python
   has too. Take the steps of **Prose review** in `skill/SKILL.md` for each pair of the review list.

3. **Java examples.** Write each fenced `java` block of `skill/*.md` to a `.java` file in the
   scratchpad, and run `javachecks.py` on them for the comment checks:

   ```bash
   ~/.local/share/narrative/lintenv/bin/python skill/javachecks.py <scratch>/examples/
   ```

   The blocks are fragments, so NAR118 on them is expected. Every other finding is a fault in an
   example. An inline example in backticks, such as `` `// the vendor closes idle sockets at 60 s` ``,
   is not covered. Read those by hand.

4. **Python scripts**, with the toolchain of narrative-python, from a scratch directory whose
   `pyproject.toml` is narrative-python's `skill/pyproject-snippet.toml`:

   ```bash
   cd <scratch> && PATH=<narrative-python>/.lintenv/bin:$PATH <narrative-python>/.lintenv/bin/python <narrative-python>/skill/verify.py --venv <narrative-python>/.lintenv <repo>/skill/javachecks.py <repo>/skill/verify.py <repo>/tests/run_fixtures.py <repo>/sync_prose.py <repo>/verify_docs.py
   ```

   All 7 checks must pass.

5. **Fixtures**: `python3 tests/run_fixtures.py --gradle <gradle>` reports 0 files with the wrong
   codes. One Gradle run at a time, at `nice -n 19`.

6. **Records and copies**: `python3 verify_docs.py` reports 0 problems.

7. **Fix and report.** Fix a clear violation in place. A change to a rule goes to the user first.
   Run the steps again. After the user commits, `./install.sh` updates the installed copy.
