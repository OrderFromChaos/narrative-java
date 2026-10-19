# Narrative Java

Makes Claude's Java for GTNH mods read like a reviewed upstream PR: the comment rules and NLP lint of
[narrative-python](https://github.com/OrderFromChaos/narrative-python), 30 Java and GTNH checks, and a
`--since` mode for only the lines your PR adds or changes.

- **Comments a human would write.** The NLP lint of narrative-python runs on every `//` comment and
  javadoc, unchanged. `the panel knows`, `the cache keeps`, `deliberately`, and clauses joined by a
  semicolon or a dash are all findings.
- **The GTNH habits upstream reviewers ask for**: user-facing text through the lang file, no
  allocation in a draw method, no `ordinal()` saved to NBT, a `switch` over an enum with no
  `default`, an optional mod behind one guarded class, and checked exceptions at the file and packet
  boundaries.
- **Quiet on code you did not write.** On PlanNH `origin/dev`, a full run has 1,682 findings in
  upstream code. With `--since origin/dev` and a planted change, the output has the 4 planted
  findings and none of the 1,682.
- **No build change.** PMD and Checkstyle run through a Gradle init script, so `git status` stays
  clean and no `dependencies.gradle` change ends up in your PR.

⚠️ For Java 25 projects only: GTNHGradle with `enableModernJavaSyntax = jvmDowngrader` or `modern`. A
`jabel` project (Java 17 syntax, Java 8 library) exits 2 with the reason. The style also puts a
caller above its callees in a class, which may differ from the rest of an existing codebase. **It will not
migrate the rest of your codebase unless you ask.**

## Example

A run on a PlanNH clone with one method added to `MachineProfile.java` and one new file (paths
shortened):

```
$ python3 ~/.claude/skills/narrative-java/verify.py --since origin/dev
gradle         spotless, compileJava, narrativeCheckstyle and narrativePmd ran
./src/main/java/com/sbancuz/plannh/Planted.java:3: NAR118 Planted has no javadoc. A top-level type has one of at least one sentence
./src/main/java/com/sbancuz/plannh/Planted.java:5: NAR124 package-private member. Make it private or public
./src/main/java/com/sbancuz/plannh/data/MachineProfile.java:125: NAR017 'profile knows'
./src/main/java/com/sbancuz/plannh/data/MachineProfile.java:126: NAR104 fully-qualified name in code. Import the type
4 findings, 0 warnings over 226 files
```

## Install

### As a plugin (updates itself)

In Claude Code:

```
/plugin marketplace add OrderFromChaos/narrative-java
/plugin install narrative-java@narrative-java
```

Then open `/plugin`, go to **Marketplaces**, select `narrative-java` and select **Enable
auto-update**. Invoke the skill as `/narrative-java:narrative-java`, or let Claude load the skill
when a task involves Java for a GTNH mod.

### By hand

```bash
git clone git@github.com:OrderFromChaos/narrative-java.git
cd narrative-java

./install.sh
```

`install.sh` copies the 14 files of the skill to `~/.claude/skills/narrative-java`, or to a path you
give `install.sh`. Invoke the skill as `/narrative-java`. **To update, run
`git pull && ./install.sh`.**

### The lint venv

narrative-java uses the lint venv of narrative-python, one per machine, at
`~/.local/share/narrative/lintenv` (`%LOCALAPPDATA%\narrative\lintenv` on Windows). If you have
narrative-python, you have it already. Otherwise, the first run of `verify.py` prints the setup steps,
with uv. The JDK comes from the Gradle toolchain of the mod, and PMD and Checkstyle
come from Maven Central on the first run.

# Details

- [`skill/SKILL.md`](skill/SKILL.md): the rules. [`skill/architecture.md`](skill/architecture.md):
  packages and other mods. [`skill/tooling.md`](skill/tooling.md): the job of each tool, every NAR
  code, and the tool defaults that break a rule.
- [`benchmark/decisions.jsonl`](benchmark/decisions.jsonl): one record per Java decision, in the
  schema of narrative-python. [`benchmark/proposals_java_mapping.md`](benchmark/proposals_java_mapping.md):
  each Python rule and the rule's Java form. [`benchmark/spikes.md`](benchmark/spikes.md): the
  toolchain tests, and the end-to-end runs on PlanNH.
- [`tests/`](tests/): for each code, a fixture that breaks the rule and one that does not, 88 files,
  checked by `python3 tests/run_fixtures.py --gradle <gradle>`. The cases of `javachecks.py --rewrap`
  are in `tests/rewrap/`, checked by `tests/run_rewrap.py` with the interpreter of the lint venv.
- The prose checks are copies of the files of narrative-python. `python3 sync_prose.py` updates them,
  and `python3 verify_docs.py` fails when a copy differs.

## License

Apache-2.0. The WordNet and VerbNet licences are in `skill/words.json`.
