---
name: narrative-java
description: Write or review Java in the Narrative house style for GTNH (GregTech New Horizons) Minecraft 1.7.10 mods on Java 25 with jvmDowngrader. Covers caller-before-callee order, records for data, an exhaustive switch with no default arm, checked exceptions at boundaries, localized user-facing text, no allocation per frame, the comment and javadoc rules of narrative-python with their NLP checks, and a verified spotless/javac/Checkstyle/PMD toolchain with a --since mode for upstream PRs. Also multi-package architecture and optional-mod containment. Use for any Java written in or for a GTNH mod, and when reviewing a Java diff against this style.
---

# Narrative Java

**0% of reader effort on rote diffing, 100% on design.** (R2b-P0) Every rule below is a case of
that, or of the second principle, to prefer what the type checker and IDE can follow.

Four near-identical lines that differ in one token make the reader compare them token by token, and
every comparison is a chance to miss the difference. One parameterised call removes the comparison.

This is the root of DRY, of one-name-for-one-thing, of consistent ordering, and of the ban on
gratuitous variation. When two rules conflict, follow the rule under which the reader diffs less.

Second principle, for representation choices: **prefer what the type checker and IDE can follow**,
even when a looser form is more flexible. The type checker here is javac. (R3-P2-rank)

**The steps to run while writing and before you finish are in Procedures, the last section.**

**This document applies to every file, however many there are.** `architecture.md` adds what happens
**between** packages: which package may use which, where a shared type belongs, when one class
becomes several, and how a mod contains an optional mod. Read it when the change spans more than one
package or touches another mod. `tooling.md` has the job of each tool and the defaults that break a
rule here. Read it before you change a config.

The reason for each rule is in the rule's text, so read the rule and not the id after the rule. The
ids are provenance. A `J1-` id resolves in `benchmark/decisions.jsonl` of the narrative-java
repository, and every other id in the same file of narrative-python. Neither repository ships with
the skill. **A rule with no id and no check behind the rule does not belong here.**

## Scope

narrative-java checks **Java 25 projects only**: GTNHGradle projects with
`enableModernJavaSyntax = jvmDowngrader` or `modern` in `gradle.properties`. `verify.py` exits 2 on any
other value, and on `forceToolchainVersion` other than `-1` or `25`. A `jabel` project has Java 17
syntax and the Java 8 library, so records and `List.copyOf()` are not available. (J1-P05)

- No preview features.
- A JDK API only where the GTNHLib stubs of jvmDowngrader cover the API.
- On a guard for a runtime newer than the floor, the comment has the version:
  `// on Java 21 and later, Thread.ofVirtual() is available`. (R10-version-guard)

## Class layout

```java
package com.example.planner.data;

import java.nio.file.Path;                           // import order and groups are a spotless setting
import java.util.List;

/** Read plan files from the config directory of the mod. */
public final class PlanFiles {

    public static final String PLAN_SUFFIX = ".plan";   // constants first, grouped BY CONCERN
    public static final int MAX_PLANS = 64;

    private final Path planDir;                       // then fields, then constructors

    public PlanFiles(Path planDir) {
        this.planDir = planDir;
    }

    public List<Plan> readAll() throws PlanException {  // the entry point, then callees in
        ...                                           // first-call order
    }

    private Plan readOne(Path planPath) throws PlanException { ... }

    /** One plan file, parsed. */
    public record Plan(String name, int machineCount) {}  // nested types LAST
}
```

- **Caller before callee.** A method this class calls goes below the method's first caller. The
  entry point of the class is first: the public API, or the lifecycle handler. Nested types are
  last. `NAR101` flags a method above the method's first caller in the class. (J1-P02, Q10, R2-10)

- Order constants by concern. Constants a developer would look for at the same moment go together.
  No blank lines inside the block. (R3a-16, R3a-15)

- Layout is a spotless setting. Lines are broken at 120 columns by the GTNH Eclipse formatter, with
  each call of a chain after the first on a separate line. Do not fight it. (J1-D01)

- **Re-wrapping is a tool's job.** Spotless splits a comment line over 120 columns but never joins
  short lines, so after an edit the line breaks of the first draft remain: `The product is` / `a` /
  `float, …`. `NAR125` flags a javadoc line with room for the first word of the next line. Before the
  checks, `verify.py` re-wraps each flagged javadoc paragraph and splits each whole-line `//` comment
  over 120 columns. With `--no-fix`, run `javachecks.py --rewrap` on the file. The re-wrap moves line
  breaks only, never words. (J1-F02, J1-F08)

- Separate logically self-contained blocks inside a method with **one blank line**. That is its only
  meaning here. Short guards written as a group stay grouped. (R3a-01)

  **No tool checks this.** Place a blank line by these five rules: (`R8-NAR008`, `R8-NAR008-rule`)

  - a body of **8 lines or under takes no internal blanks at all**
  - blanks **recur into nested blocks**, and one loop body can take four
  - **a multi-line statement and the statement that consumes the result are
    one step**, so a builder chain then the `return` of the chain stay adjacent
  - a blank precedes a `return` when the phase before the `return` is unrelated, and not when the
    returned value was just built
  - **length is not the trigger**, in either direction

- If a guard grows to three lines because it logs before throwing, move the log call into a
  `reject*()` helper that logs and returns the exception. The guards are two lines again and group:
  `throw rejectLine(raw_line, "no machine count");` (R4-05)

- **Java has no keyword arguments.** A call with more than 3 positional values, or with a `null` for
  a skipped argument, is replaced by a builder, or by a parameter record. Where Lombok is present,
  use `@Builder(toBuilder = true)`. An `@Override` has the signature of the platform. `NAR131`
  flags a method with more than 3 parameters, and `NAR102` a call with two or more `null` arguments.
  (J1-P03, R2b-B1, R5-06)

- **Long strings.** In user-facing text, never `+` (J1-P04). Outside it, `+` joins a long one-line
  string. A text block is for multi-line data only. The incidental indent of a text block is removed
  at compile time, but the value still depends on the position of the closing `"""`. (J1-P04, Q03)

## Structure inside a method

- Guard clauses and early return over nesting. (Q06)

- **Write a skip guard as the negation of what a valid item is.**
  `if (!(nameMatches && Files.isRegularFile(path) && !Files.isSymbolicLink(path))) continue;`, not
  `if (!nameMatches || Files.isSymbolicLink(path) || !Files.isRegularFile(path)) continue;`
  (R10-positive-guard)

- **One level of `filter` and `map` in a stream.** Where a stream lambda would have another stream
  inside the lambda, write a loop. No stream in a per-frame or draw method. `NAR103` flags a stream
  inside a stream lambda. (J1-P06, Q07)

- **Extract a block when you can foresee reusing or testing it separately**, not merely because it
  has a name. A one-line helper called once is residue. (R2-09, R2b-E1, R2b-E2)

- If an extracted method would take 5 or more values, that is a **missing owner**, not a reason to
  leave the code inline. That owner is a **class** when two of it can exist at once, and a final
  utility class with a private constructor and static methods otherwise. A record is the answer only
  when nothing has behaviour over the values. If a general name for the group is hard to pick, the
  values are not a real group. (R7-C05-resolved, R7-C05-naming)

- Always collapse duplicated-but-drifting code, even when the shared version takes an extra
  parameter. To localise the difference is the whole point. (R2b-E4)

- Mixed `&&` and `||` parenthesise each group explicitly. Never `a && b || c && d`. `NAR123`
  enforces it. (R2b-B4)

## Naming

- Standard Java: camelCase methods, fields, locals and parameters. PascalCase types. UPPER_SNAKE
  constants. A local compile-time constant may be UPPER_SNAKE too (see **Constants**). `NAR130`
  enforces it with Checkstyle, and allows the SRG and MCP names of Minecraft (`func_…`, `field_…`,
  `p_…`) of an override. (J1-P01)

- Spell names out. No `cfg`, `idx`, `tmp`. (Q11)

- **A method name starts with a verb, and the verb's object is what the method returns.**
  `parsePlan`, `readManifest`, `computeDeletionCutoff`. Not `planFrom`, not `cutoffFor`. Record
  accessors and `@Override` methods of the platform are exempt. (R9-03)

- **A static method's name is clear without the method's class**, to a reader who has never opened
  the class. Overloads only for one operation over different argument types. Interface
  implementations are exempt. (J1-P07, R9-03, R7-B06)

  **Length is not the defect.** Where the clear name is the longer one, write the longer one.

- **Predicates take `is`, `has` or `can`:** `isReady()`, `hasPower()`, `canExtract()`. Forge,
  Minecraft, GT and Lombok `@Getter` use these names, so a call site reads the same as the library
  calls beside the call site. (J1-F1)

- **Do not restate a domain type in a parameter name:** `RebinConfig config`, not
  `RebinConfig rebinConfig`. (Q11)

- **With a generic type, the parameter name is the only place the thing is named.** `Path`,
  `String`, `int` and `Object` constrain only a value's shape. Write `Path policyJsonPath`, not
  `Path path`, and `String manifestText`, not `String text`.

- **Raw and parsed forms get different names.** Prefix the raw form with `raw`: `String rawAt` from
  the file, `Instant at` once parsed. Never `at` beside `parsed.at()`. (R10-raw-names)

- **No fully-qualified name in code.** Import the type. Call a static method through its class
  where the call is unclear without the class name: `Math.max`, `Objects.requireNonNull`.
  Static-import test assertions, and members used on most lines of a file. `NAR104` flags a
  qualified name outside the imports. Where two types of one simple name meet in a file, keep the
  rarer one qualified and silence the line with `// noqa: NAR104`. (J1-P08, R3a-08)

## Constants

Name every magic number. (Q09) Then place it by this test:

> Could someone change this value safely knowing only what the program **does**, or would they need
> to understand how the method **works**?

- **An implementation detail is inside the method.** A primitive or `String` constant is a local
  `final`, in UPPER_SNAKE. It is a compile-time constant, so there is no per-call cost. An object
  constant, such as a `Pattern`, is `private static final`, directly above the constant's only
  method. (J1-P09, R3a-12)
- **A value that players or pack makers tune is a field of the Config class** (see
  **Configuration**). (J1-P09)
- Constants that a developer changes, and that are not implementation details, stay at the top of
  the class.

*No tool checks this. This is review judgement.*

## Types

- **No raw types.** `Object` in a signature is the visible form of "any type", so `Object` is
  visible and greppable. `var` only where the right-hand side names the type:
  `var plans = new ArrayList<Plan>()`. `NAR121` reports the raw-type and unchecked warnings of
  javac. (J1-P10, R2-11)

- **Annotate the true requirement.** A parameter has the narrowest interface the method uses:
  `Iterable`, `Collection`, `List`, `Map`. Never `ArrayList` or `HashMap` in a signature. `SortedMap`
  where the order matters (see **GTNH**). `NAR140` flags a concrete collection type in a signature,
  a field or a local. `EnumMap` and `EnumSet` keep their types: `new EnumMap<>(map)` and
  `EnumSet.copyOf(set)` throw on an empty argument of another type. (J1-P11, Q13, J1-F03)

- **Domain primitives.** A one-component record, `record ScanId(int value)`, at boundaries and in
  code that runs rarely, so a bare `int` is a type error. In per-frame code each wrapper is an
  allocation, so there the name of the primitive is the type: `int scanId`. (J1-P12, Q15)

- **Nullability.** `@Nullable` from the annotation package the file already imports (PlanNH: javax
  JSR-305), with `@ParametersAreNonnullByDefault` in each `package-info.java`. `Optional` only as a
  return type. (J1-P13, R9-01)

- **A path is a `java.nio.file.Path` object**, never a `String` built with `+` or `/`. Forge returns
  `java.io.File`, as from `FMLPreInitializationEvent.getModConfigurationDirectory()`, so call
  `toPath()` on the `File` as soon as Forge returns the `File`. Use `Files` methods for file
  operations, not `File` methods. `File.delete()`, `renameTo()` and `mkdirs()` return `false` on
  failure, and `File.listFiles()` returns `null`. `Files.delete()`, `Files.move()` and
  `Files.createDirectories()` throw an `IOException` with the cause. `NAR115` flags a `File`
  operation. (J1-P14, R3a-10)

- **Amounts are exact.** `long` for item, fluid and EU counts, never `float` or `double`.
  `Math.addExact` and `Math.multiplyExact` where overflow is reachable. A rate may be a `double`.
  (J1-P15)

- **Time.** `java.time` only. Game time is a `long` named `…Ticks`, at 20 ticks per second.
  (J1-P16)

- **`enum` for closed sets.** Never write `ordinal()` to NBT, a packet or JSON: reordering the
  constants changes every saved world. Serialise `name()`, or an explicit code field. `NAR105` flags
  `ordinal()` in NBT, packet or Gson code. (J1-P17, R2-08)

- **Composition over inheritance.** An `interface` for a seam with two real implementations. No
  `abstract class` in project code. `extends` only for a class the platform requires: Forge `Block`,
  `Item` and `TileEntity`, MUI2 widgets, GT bases. A `sealed abstract class` is allowed when its
  permitted subclasses share fields: the fields are declared once, in the class. `NAR106` flags every other
  abstract class. (J1-P18, R2-01, J1-F05)

- **Give a name to a type you cannot say out loud.** Could you refer to this type in a normal
  discussion with another programmer? `Map<String, List<Pair<Float, Float>>>` has five names below
  the outermost one, and above four, give it a name: a record, or a functional interface for a
  callable. `NAR122` counts the names. (NAR005, R8-D27-resolved)

### Exhaustive dispatch with no default arm

```java
private static Level levelOf(Outcome outcome) {
    return switch (outcome) {
        case INGESTED -> Level.INFO;
        case REJECTED -> Level.WARN;
        // no default arm. A new constant of Outcome is then a compile error
    };
}
```

For an `enum` or `sealed` type, write a `switch` expression with no `default` arm. javac then rejects
a missing constant. **A `default ->` arm compiles clean and accepts the missing case.** `NAR107`
flags a `default` arm in a switch over an enum or a sealed type of the project.
(J1-P19, Q18, R3a-07)

- A `switch` **statement** over an enum has no exhaustiveness check. Rewrite it as a `switch`
  expression that returns a value.
- **Keep the `switch` even where an `EnumMap` looks natural.** `EnumMap.get()` returns `null` for a
  missing key, at run time.
- Under jvmDowngrader, the synthetic default of an exhaustive `switch` throws a stub
  `MatchException`. It is reachable only when a newer enum class is loaded than the one compiled
  against.
- **Where the behaviour is a property of the constant**, such as the amount format of a resource
  type, write the behaviour on the constant, as an abstract method or a constructor argument. javac
  then requires it of every constant, and call sites get no branches. **Where only one caller needs
  a mapping**, such as a log level for each outcome, the `switch` is in that caller. (J1-P19)
- A type-pattern switch over a type that is not sealed, such as an NEI handler object, needs a
  `default` arm.

## Data at boundaries

- Parse untrusted input into a **record at one boundary gate**, then never validate again. GTNH
  gates: `readFromNBT`, packet decode, Gson, config load. (J1-P20, Q02, Q14)

- **A parsed record contains only what its input contained.** Where one input format has a field and
  another does not, the component is `@Nullable` on the shared record, and the check that reads the
  component skips an absent value. **Never substitute a plausible default**, because the output then
  contains a fact that the file does not. (R9-01)

- **A record is the default for data.** A class that is just data is the record, not a wrapper
  around a nested one. In other classes, a field is `final` unless code reassigns the field.
  `NAR141` flags a field that could be final. (J1-P21, R8-D11-resolved)

- **A record is shallowly immutable.** The compact constructor copies a collection component with
  `List.copyOf`, or Guava `ImmutableList.copyOf`. **Never an array component:** `equals()` and
  `hashCode()` of a record compare arrays by identity, so two equal plans compare unequal. `NAR108`
  flags an array component. (J1-P22)

- **Genuinely schemaless input**: promote the fields the program computes on to typed components,
  and put the remainder in one `JsonObject` or `Map<String, JsonElement>` component. **Never merge
  the remainder into an output object.** An untrusted key with the name of an output field would
  replace that field. Nest the remainder instead. (R4-04)

## Errors

- **Checked for boundary and I/O failures, unchecked for everything else.** A parse error of a file,
  a packet or NBT `extends Exception`, so a call site with no `try` and no `throws` clause is a
  compile error. A broken invariant `extends RuntimeException`. (J1-F2, Q20)

  A checked exception cannot leave a lambda for a JDK functional interface, or an override of a
  Minecraft or Forge method. Catch it there:

  ```java
  @Override
  public void readFromNBT(NBTTagCompound compound) {
      super.readFromNBT(compound);
      try {
          plan = parsePlan(compound.getString("plan"));
      } catch (PlanException exception) {
          plan = null;
      }
  }
  ```

  An exception that leaves `readFromNBT()` is caught by Forge, which logs "its state cannot be
  restored" and drops the tile entity. A `@Mod.EventHandler` or `@SubscribeEvent` method is not an
  override, so a `throws` clause on the method compiles.

- **The name of an exception class ends in `Exception`:** `PlanException`, not `PlanError` or
  `PlanFailure`. Never `Error`, because a `java.lang.Error` subclass means the JVM is unusable.
  `NAR109` enforces both. (J1-P23)

- **Handle each failure mode narrowly and separately.** No `catch (Exception)`,
  `catch (RuntimeException)`, `catch (NullPointerException)`, `catch (Throwable)` or `catch (Error)`.
  `NAR142` flags them. There are two exceptions. One is `catch (NoClassDefFoundError)` at the
  optional-mod boundary, described in `architecture.md`. The other is `catch (RuntimeException)` in
  a degrade-and-report loop over code from another mod, whose exceptions you cannot list. Mark the
  catch `// noqa: NAR142`, with the reason:

  ```java
  for (MTEMultiBlockBase machine : machines) {
      try {
          checkConformance(machine);
      } catch (RuntimeException exception) { // noqa: NAR142, degrade and report over GT machine code
          failures.add(machine.getLocalName() + ": " + exception);
      }
  }
  ```

  (J1-P24, Q19, J1-F04)

- **Related means the handling is the same, not that the classes share a base.** Where two failures
  produce one outcome, one multi-catch `catch (A | B exception)` is correct. But check the premise
  first. A timeout and an unreachable host are different facts and deserve different words.
  (R8-D24-resolved)

- `throw new XException(message, cause)`, **and** log it. Both. `NAR144` flags a rethrow that drops
  the cause. (Q21)

- **An error message for malformed input includes the expected form.** `bad count 'twelve' in
  plan.txt (expected a whole number such as 12)`. (R10-expected-form)

- **Log the generic fact once at the raise site, however you factor that.** Route several raise
  sites through a `reject*()` helper that logs and returns the exception. (Q23, R4-02)

- **At the handle site, log what the failure meant there, but in a degrade-and-report loop log the
  aggregate, not the item.** Log the item at DEBUG and the tally at WARN. (R4-02)

- **Level follows from what an operator can act on.** A pack maker cannot act on recipe 4,812. A
  pack maker can act on "4,812 of 10,000 recipes rejected". (R4-02)

- LBYL over EAFP. You know your invariants, you do not know every exception an implementation can
  throw. (Q22)

- **Degrade and report.** Process every item, then log the tally at WARN. The exception from a bad
  item is caught in the loop, so the game does not crash. (J1-P25, Q24)

- **The config gate is the exception.** A hand-written config gate rejects the first bad entry,
  because with a half-valid config, what to do is unknown. Where an out-of-range value is reset and
  logged by the GTNHLib or Forge config loader, keep that. (J1-P26, R8-D25-resolved)

## Static state

- **A mutable static field has a comment with the reason**, on the line above or after the field on
  the same line, **or the field is an instance field of the object with the same lifetime.** A
  mutable static field is non-`final`, or a `static final` mutable collection. Fields that Forge
  requires (`@Mod.Instance`, `@SidedProxy`, config fields) and loggers are exempt. `NAR110` flags
  the rest. (J1-P27, R2b-G1)

## Logging

- **One stable event name plus parameters, never a sentence built with `+`.** The message is a
  queryable key: `LOG.warn("merge.rejected rejected={} total={}", rejected, total)`. No `+` and no
  `String.format` in a log call. They also build the string when the level is off. `NAR111` flags
  them. (J1-P28, Q08)

- **One logger per mod**, `LogManager.getLogger(MODID)`. This is the GTNH convention, and the mod name
  is then on each `latest.log` line. The log format is set by Minecraft, not by the mod. (J1-P29)

## Configuration

- **A value that players or pack makers tune is a field of the mod's Config class**, from Forge
  `Configuration` or GTNHLib `@Config`. Not a literal, not a field elsewhere. (J1-P30)
- **Where several implementations of a feature trade time for quality, all of them read one
  setting.** For example, the budget of each solver is multiplied by one `solverEffort` setting, with
  the levels High, Medium and Low. There is no `greedyStepBudget` setting beside an
  `lpIterationBudget` setting. (J1-P30)
- Third-party log noise is off globally, with a debug setting to turn the noise on. Not a save and
  restore around each call. (J1-P30)
- No environment variables and no system properties for behaviour. (J1-P30, R3a-02)

## Concurrency

**Run file I/O, a solve, or other work that takes a noticeable time on a worker thread, and pass the
result back to the client thread. The client thread never waits for that work.** World and GUI state
change only on the thread that uses them. (J1-P31b)

```java
CompletableFuture.supplyAsync(() -> computePlan(request))
    .thenAccept(plan -> Minecraft.getMinecraft().func_152344_a(() -> showPlan(plan)));
```

`func_152344_a` is the SRG name of the 1.7.10 method that queues a task for the client thread.

## Testing

- **Real dependencies**: a real temp directory with `@TempDir`, a real file. No Mockito. A test
  double is a last resort for something you cannot run. Flag each one as a known gap. Keep logic off
  Minecraft types, so the tests run headless. (R2-02, Q16)

- **Property-based tests wherever there is an invariant**: round-trips, ordering, conservation,
  numeric range. jqwik where the project already has jqwik, else JUnit 5 `@ParameterizedTest` over
  generated cases. **Assert a rule, not the implementation's output.** A table of
  `assertEquals("3.12", format(3.12))` is not a test of anything. Never re-implement production math
  in a test. (J1-P32, R2-12)

- **A test method name is the rule.** Tests are found by the `@Test` annotation, so no `test`
  prefix is needed: `runningMachineNeverDisplaysZero()`. (J1-P33)

- **Never merge a test that fails.** If a scenario is aspirational, raise the budget or disable the
  test explicitly, and say which in the PR. (J1-S12)

- **No bootstrap or loader that can be imported only from the test source set.** Put the entry
  point in the main source set, so any source set can import the entry point. (J1-S13)

- **No production change for a test.** No test-only field or variable in a production class. A test
  reads private state through reflection, not through a new accessor, unless the accessor is worth
  adding for other code. (J1-S14)

## GTNH

- **Every user-facing string is a key in the lang file** (`assets/<modid>/lang/en_US.lang`), read
  through a localization call: `StatCollector.translateToLocal(key)`,
  `StatCollector.translateToLocalFormatted(key, values)`, `ChatComponentTranslation`, or MUI2
  `IKey.lang(key)`. No literal user-facing text in code, so not `IKey.str("Machines")` and not
  `new ChatComponentText("Done")`. `NAR113` flags literal text in those calls. (J1-S15)

- **In user-facing text, never `+`.** Put `%s` placeholders in the lang entry, `%s%s` where two values
  are joined, and pass the values to the localization call. `NAR112` flags a `+` in or after one.
  (J1-P04)

  ```
  plan.machines=%s machines at %s
  ```

  ```java
  StatCollector.translateToLocalFormatted("plan.machines", count, tierName)
  ```

- **Deterministic order is a property of the field.** Declare `SortedMap`, build a `TreeMap`, and
  never sort where the map is read. Gson rebuilds a `SortedMap` field as a `TreeMap` on load, and a
  plain `Map` with keys that are not `String` as an insertion-ordered `LinkedTreeMap`. A comparator
  that defines a canonical key is allowed. (J1-S01)

- **A draw or render method writes no serialized state.** (J1-S02)

- **No allocation in a per-frame or draw method.** Reuse buffers and primitive containers. On a wrap
  or measure path, use an identity-keyed cache, `if (source == wrappedFor) return;`, with a dirty flag
  at the source, so a steady frame recomputes nothing. `NAR114` flags `new` and `.stream()` in a
  `draw*` or `render*` method. (J1-S03)

- **Optional instrumentation is called through an interface.** The implementation for "off" is a
  no-op that allocates nothing. (J1-S04)

- **A point query is answered without a scan of the whole collection.** First look for an invariant
  that removes the query, and add an index only if the query is still needed. (J1-S05)

- **A simple behaviour plus an invariant**, in place of a clever prioritisation policy. (J1-S06)

- **Reuse a type the codebase already has for the same thing**, instead of a new type with the same
  fields. (J1-S07)

- **No hardcoded fix in your mod for a bug in another mod.** Report the bug to that mod. (J1-S08)

- **Keybinds are configurable.** Register them through NEI where NEI has a keybind API. (J1-S09)

- **NEI-style lookup and hover only on sprite-like surfaces**, such as item stacks and pins, never
  on text rows. Players expect it on NEI sprites. (J1-S10)

- **Colours through the colour API of the GUI library**, MUI2 `Color`, not bit arithmetic or hex
  literals. (J1-S11)

## Javadoc

**Every top-level type has a javadoc of at least one sentence, about what the type is for.** A reader
meets it first, so it is about what the class is *for*, not how the class works. The javadoc of a
class with `main`, such as a dev tool, also has a usage example and the exit codes. `NAR118` flags a
top-level type with no javadoc. (J1-F3, R5-02)

**Write for a professional developer who has the file open.** That reader knows Java, Forge and the
vocabulary of the trade, so `API`, `idempotent` and `NBT` are the right words. One idea per
sentence. **One word for one thing, and the word is the identifier the code uses.** (R9-09)

The prose rules for comments and javadoc are in **Comments**.

### Show the thing, do not describe it

**Where a class reads or writes concrete text, paste a real sample of that text** in a `<pre>`
block: a tooltip, a chat line, a lang entry, an NEI line, a converted value. **Delete the prose the
sample replaces** rather than keeping both. (R9-08)

**Never invent a sample.** Run the code and paste what it printed. A format that appears nowhere in
the program is a lie in the shape of documentation. **Do not state what you did not observe.**

**Show one line of each shape, not the whole output.** A sample goes stale and no tool checks the
sample. Keep it small, and re-paste the sample when the output changes.

```java
/**
 * Format a machine count for the tooltip of a plan node.
 *
 * <pre>
 *     MACHINE        COUNT    RATE
 *     Electrolyzer      12    3.5/s
 *     Centrifuge         4    0.25/s
 * </pre>
 *
 * A machine with no rate shows {@code -} in the RATE column.
 */
```

A plain `<pre>` table is unchanged by the GTNH spotless config. In `<pre>{@code …}</pre>`, each tag
is moved to a separate line, and the lines between the tags are unchanged.

A conversion takes a table of cases rather than a sentence per case:

```java
/**
 * Convert an amount with a unit suffix to a count, and back.
 *
 * <pre>
 *     4096    ->           4096
 *     12K     ->          12000
 *     1.5M    ->        1500000
 * </pre>
 */
```

### Javadoc rules

**Most members get no javadoc.** A top-level type (`NAR118`) and a method over the contract
threshold (`NAR116`) need one. Any other field, constant or method gets a javadoc only for a fact
that the name, type, value and signature do not show. A javadoc whose facts are already in the
declaration only costs the reader time. Cut such a javadoc whole, not sentence by sentence. The Java
habit of a javadoc on every public member does not apply here. (J1-F07)

**State each fact once**, on the declaration the fact belongs to. Elsewhere, link to that
declaration. (J1-F07)

```java
public static final int ITEM_PIPE_CASING_TIERS = 8;
public static final int PIPE_CASING_TIERS = 4;

/** @param tier from 1 to {@link #PIPE_CASING_TIERS} */
public static ItemList pipeCasing(int tier) {
```

not

```java
/** How many item pipe casings {@link #chainItemPipeCasings} accepts, numbered from 1. */
public static final int ITEM_PIPE_CASING_TIERS = 8;

/** How many pipe casings there are. {@link #pipeCasing} numbers them from 1. */
public static final int PIPE_CASING_TIERS = 4;
```

A javadoc that is kept starts with a summary sentence. **A body is not required, and usually does
not earn its place.** (R9-09)

**Cut a sentence when any of these is true:**

- **It is visible in the file.** `final` is on the line above. `@Nullable` is in the signature.
- **Its negation would be a bug, an absurdity, or an implementation nobody would ship.** Negate the
  sentence and read it back. **Assume the reader expects competent code, and document only the
  departures.**
- **It is a language feature, explained.**
- **It goes stale and nothing checks it**, unless it is a sample you accept that cost for.

**Compress what survives:**

- **Name the property, do not explain it.** `Rows are keyed on team, total and quota, so runs are
  idempotent`.
- **State an ordering as its sort key.** `Machines sort by (-count, name)`.
- **In the summary, use the real name of what the code produces.**
- **Stop at the fact.** Where a reason has to survive, it is a `//` comment at the line the reason
  concerns.

**A body earns its place for these, and in practice for nothing else:**

- an **ordering or tie-break**, invisible without reading a comparator
- a **unit, a nullability or a provenance** absent from the signature: `Amounts are in litres`
- **where the leftover, default and failure cases go**
- a **sample** of concrete text the class reads or writes
- a **constraint from outside the program**: `Forge drops a tile entity whose readFromNBT() throws`
- a **guarantee a caller needs**: `The call writes no file, sends no packet, and changes no world`

- **A method gets a javadoc when its contract is complex**, meaning the method takes more than three
  parameters, or the method's body exceeds 20 lines. Below both, the contract goes in `//` comments.
  `NAR116` flags a method over that threshold with no javadoc. (J1-P34, Q05, R8-D18-resolved)

- **`@throws` for every exception absent from the `throws` clause**, for a method over that
  threshold. A checked exception is in the signature already. `NAR117` flags a `throw new X` with no
  `@throws X` line. `@param` and `@return` only for a fact absent from the signature: an ordering, a
  nullability, a unit, or a count whose meaning is not obvious. (J1-P34, R8-D28-resolved)

- Write nothing in a javadoc that the code does not do, and no consequence that an earlier sentence
  already implies. (Q05)

- **A javadoc is about its class alone.** Do not assert what another class does, do not claim to be
  the only place something happens, and do not count callers. Name another class only where a reader
  of *this* file needs the name to use this file. (R9-02)

- Where semantics vary by implementation (file moves, copies, path manipulation), **show a concrete
  before and after example**, not prose. (R3a-11)

## Comments

**Test: what information is in this comment and not in the code?** (R10-Q25)

These rules cover javadoc, error messages, lang entries and command help text too. `verify.py`
lists comments and javadoc only, so read messages, lang entries and help text by hand.
(R10-docstrings, R10-message-scope)

**Comments are not thinking traces.** While writing, you reasoned through edge cases, alternatives
and spec gaps. That reasoning is a thinking trace. It belongs in your report to the user, not in
the code. (R10-stance)

**Cut a comment whose content a smart reader would get from the code below the comment (including
variable names), no matter how the comment is phrased or what rule category the comment seems to
fit.** (R10-restatement-gate)

Before writing or rewording a comment, follow **Writing a comment** under **Procedures**.

**When shortening an existing comment, rewrite the sentence. Do not delete words from it until it
fits.** (R10-cleanup-rewrite)

**When you replace an existing comment, rewrite it from the code.** (R11-rewrite-from-code)

1. List the facts in the existing comment.
2. Check each fact against its source where you can: the code for a fact about the code, and vanilla
   Minecraft, a spec or a vendor's documentation for a fact from outside the code. Some facts have
   no source you can check, such as a business decision. Keep those.
3. Drop a fact only when you find it false.
4. Write a new comment from the facts you kept, by the steps of **Writing a comment**.

Reordering or trimming the existing comment's sentences is not a rewrite. The existing comment's
terms, framing and sentence order are not reference material.

**Every term passes one of two tests:**

1. **The domain's word:** the word a practitioner of the domain uses for the thing. In a mod, the
   word a player or modder uses: a cave, sky light, a block column.
2. **An identifier, as a link:** the name in the code that the reader can jump to, used as a
   pointer. In javadoc, write it as `{@link #getMachineModes}` or `{@link ExtendedBlockStorage}`. In
   an IDE, the reader can jump from the link to the target. When someone renames the target in the
   IDE, the link changes with the name. `{@link}` takes a class, a field, a method or a package. Put
   a parameter, a local variable or a value such as `null` in `{@code}`. In a `//` comment, put the
   name in backticks. Link to an identifier even when its name is unclear. From the link, the reader
   can jump to the code and see what the name stands for.

A term that passes neither test gets a plainer word or a definition at the term's first use.
(R11-rewrite-from-code, R11-pointer-wording, J1-F10)

**A descriptive word in a term is a claim.** (R11-modifier-claim)

Some words in a term are descriptive: an adjective such as `saved` in `saved index`, or a noun for a
kind of thing, such as `getters` in `the mode getters`. Each descriptive word is a claim. `saved` is
a claim that the index is saved, and `getters` is a claim that the methods only read the mode. Check
each descriptive word against its source by step 2 of the rewrite. Keep the word only when the word
is true of everything the term names. `saved` is false for an index that `setMachineMode()` sets.
When a word is false, use the domain's word or an identifier instead. Don't add words to cover the
other cases: `saved or set index` is neither the domain's word nor an identifier.

When the reader needs a fact about a library, and you can't read the library's source or find the
fact in the library's documentation, write what your code does at the call. Not `the GUI's mode sync
accepts any int`, but `MTEMultiBlockBaseGui registers setMachineMode() to receive the mode index
that a client sends`. Don't add `unchecked` or a similar word at the end. `unchecked` makes the same
claim about the library. For vanilla Minecraft and Forge, read the source and check the fact.

**Don't describe what a method's callers do.** (R11-callers)

A developer who changes a caller has no reason to read this comment, so a sentence about what the
callers do becomes false when they change. When the reader needs the reason for a requirement, state
a fact about what the method returns or changes. Not `Return a static constant. The mode methods of
this class call this on each use`, but `Return a static constant: a machine's modes don't change
while the game runs`. That javadoc is on a method that subclasses override, and the developer of
each override reads the javadoc to learn what to return. Don't comment a method that only returns a
constant. A requirement on the callers is part of the method's contract, such as `Call only on the
server thread`. A fact about a method that this method calls is allowed. That call should be in the
code below the comment.

**In a PR to another project, leave the comments that exist on the project's base branch as they
are**, even the ones the diff moves. `verify.py --since` reports only the lines the diff adds or
changes.

**Comment kinds:** (R10-topic-lists, R10-fp-fn, R10-kinds)

- **Source**: a fact or requirement from outside the code. Test: it would still be true if the code
  were deleted, and a smart reader wouldn't already know the fact. (R10-Q10, R10-Q14, R10-Q23,
  R10-Q34, R10-Q43, R10-Q48, R10-Q51, R10-business-case, R10-audience)
  - `// the vendor closes idle sockets at 60 s`
  - `// worlds saved before 1.2.0 have no "tier" tag`
  - `WARN_RATE = 1.6; // calibration spec CAL-7, section 3`
  - `// called once per tick for every loaded machine`, at the top of the method
- **Fence**: code that looks unusual, where the obvious simplification silently breaks the code.
  Test: name the simplification a smart, experienced developer would make, and the defect the
  simplification causes: a wrong result, a crash, a security hole or a performance collapse. A
  cosmetic difference doesn't count, and neither does adding a feature. Name the step the code takes
  because of the fact. (R10-Q20, R10-Q42, R10-Q44, R10-Q45, R10-Q50, R10-Q53, R10-Q55,
  R10-fence-consequence)
  - `// Integer caches -128 to 127, so == passes for small counts and fails above. Compare with equals()`
  - `// constant-time comparison to avoid timing attacks`, above `MessageDigest.isEqual(...)`
  - `// removing an item shifts the later indices. Walk backwards`
  - `// migrateNbt() before readFromNBT(). readFromNBT() reads the "count" tag`
- **Decoding aid**: a line a smart reader would need docs or a worked example to read. Test: you'd
  look it up. State the intent, not the mechanism. (R10-Q42, R10-Q46)
  - `AMOUNT = Pattern.compile(...); // a number, then an optional K, M or G suffix`
  - `// Math.fma() for one rounding in a * b + c`
  - a regex gets a string the regex matches, and one the regex rejects where the boundary is
    unclear. Put each literal in backticks, one per line, so the match boundary is visible and a
    developer can paste the literal into regex101. A description such as `any single character`
    stays plain. (R10-regex-sample, R10-regex-literals)
    ```java
    // matches:
    // `search_v2`
    // `db-host`
    // rejects:
    // `x.y`
    private static final Pattern BARE_KEY = Pattern.compile("[A-Za-z0-9_-]+");
    ```
- **Marker**: no test needed. (R10-candor, R10-Q03, R10-Q05, R10-Q36, R10-Q38, R6-12, R8-block-comments)
  - `FIXME:` incorrect behaviour, or behaviour that breaks soon after deploy. `verify.py` prints
    each one as a warning, `NAR119`, and still exits 0. (J1-F4)
  - `TODO:` tech debt, future improvement
  - a stated assumption: `// the pack ships no other mod with this keybind, so no conflict check`
  - a label on a block of at least 4 lines, ideally 6 or more: `// build the node index`
    (R10-block-label-size)
  - a rule a developer must enforce, with capitals scaled to the cost of breaking the rule:
    `// read-only: NEVER write to the NBT of a loaded chunk here`

**Never, even when a kind's test passes:**
- what the next line or a single call does (R10-Q01, R10-Q06, R10-Q39, R10-Q47, R10-Q54)
- language or library behaviour the reader knows: `<=`, case sensitivity, `null` (R10-Q19, R10-Q21, R10-Q26, R10-Q49)
- why the file follows this style guide: `so this is a record and not a class` (R9-02, R10-Q01)
- decision ids such as `(Q08)` (R7-D04-comments, `NAR012`)
- changelog: an earlier state of the code, or a fixed bug with nothing left of the bug (R10-Q04, R10-Q08, R10-Q52, `NAR015`)
- alternatives never in the code (`rather than`, `instead of`), except in architecture discussion (R10-Q07, R10-rather-than)
- risks far outside the task's scale, and decisions too inconsequential for a later reader to reconsider (R10-Q13, R10-rating)
- future needs nobody has documented or planned (R10-Q15)
- reassurance that a weakness is fine, such as `deliberately` or `on purpose` (R10-candor, R10-Q20, `NAR014`)
- guarantees about other classes or methods. Where the code depends on another method's guarantee
  and the check is cheap, check the guarantee in the code: `while (!items.isEmpty() && …)`, not
  `// store() rejects an oversized item, so the cache is never empty` (R10-Q24, R10-Q11,
  R10-other-modules, R10-check-invariant)
- how one method uses a type, written on the type (R10-usage-placement)
- illustrations of a decision just discussed in the session (R10-Q21)
- a method's return contract. State it in the javadoc, and only if the return type doesn't make the
  contract obvious. `NAR120` flags a `// returns …` comment at the top of a method.
  (R10-return-contract)

**Depth:** in proportion to the idea's difficulty for the reader. `// signed error` on a rolling
mean, more on a novel method. When the reader needs the consequence or the action as well as the
fact, write a second sentence, as a block of full sentences:
```java
// The vendor API returns at most 100 rows per page and no total count.
// Keep requesting until a page comes back short.
while ((page = fetchPage(cursor)).size() == PAGE_SIZE) {
```
A one-line comment stays one clause, or two short sentences. (R10-Q16, R10-seed-2, R10-depth-sentences,
R10-depth-example, R10-period-join)

**Sentence form:**
- a one-line `//` comment has a lowercase start and no final period. Several lines, and every javadoc, are sentences. (R10-Q26, R10-Q35, R10-docstrings)
- two sentences over a connective such as `which`, `since`, `as` or `, where`. With a connective,
  the reader may attach the second clause to the wrong noun. `// migrate before load, which reads
  the count tag` → `// migrate before load. load() reads the count tag`. A comparison with `as` to
  other code states no fact: `The product is a float, as in the machines' code` → `The machines'
  code computes this in double`, once you have checked the machines' code. `NAR021` flags `as in`,
  a sentence that opens with `As` and has no verb, `as the X verbs it`, and `, where`
  (R10-period-join, R11-connective-as-where)
- terse. Drop articles where nothing is lost, never the subject or the verb (R10-seed-10, R10-terse-narrow)
- every clause has a subject and a verb. A label for the thing is fine: `// least recently used
  first`. A predicate with its subject cut is not: `Bound to one machine` → `The setting is bound
  to one machine`. `NAR020` flags that form before `, so`, and a subordinate clause before `, so`:
  `Whether some terms differ by mode, so…`. (R10-subject-verb, R11-nar020-subordinate)
- every noun phrase refers to one real thing, at the moment the sentence is about. Name the object in
  the program each noun phrase refers to, and rewrite when:
  - the thing does not exist yet, or does not have its property yet: `// newBufferedWriter() creates
    a missing log file` → `// newBufferedWriter() creates the log file if it doesn't exist`
  - the property belongs to another object: `// in the plan's tier` → `// in the machine's tier`,
    when the tier comes from the machine
  - the referent is gone or ambiguous. A pronoun at the start of a sentence can refer to the subject
    of either sentence before the pronoun, so repeat the noun
  - a stand-in such as `the one`, `it` or `that` takes the place of a noun that fits. Repeat the noun
    (R10-stand-in)
  - `it` or `its` after two or more singular nouns in one sentence. A reader can take the pronoun
    for either noun, even when only one of the nouns makes sense. Repeat the noun the pronoun stands
    for, or split the sentence: `PumpController extends MachineBase, and it runs once per tick` →
    `PumpController extends MachineBase, and MachineBase runs once per tick`. `NAR022` flags this
    form (R11-pronoun-grammar)
  (R10-referent)
- the concrete thing, not `what the X does to the Y` (R10-nominal-chain)
- a claim is true in every case that reaches the claim. Otherwise, name the case in the sentence.
  List the paths that reach the sentence:
  - `// an expired entry is removed on lookup` → `// an expired entry is removed on lookup, or before
    any eviction`
  - count the unit the code counts: `// every file is counted` → `// the lines of every file are
    counted`
  - in an error message, advise only steps the program has not taken: `no plan file found. Check the
    config directory` → `no plan.json in config/planner/. Pass /plan load <file> to use another file`
  (R10-case-coverage)
- when a comment moves from one approach to another, mark the switch with `Alternatively,` (R10-alternative-marker)
- possessives and noun compounds over relative clauses: `the machine's recipes`, `in tick order` (R10-seed-1, R10-seed-9, R10-Q32)
- trade terms over paraphrase: `has no side effects`. Modifiers before the noun: `JSONL logs`. (R10-seed-3, R10-seed-4)
- the conclusion, not the derivation. State what the code means, not how the code gets there.
  (R10-conclusion)
- no intensifiers. Drop a word that only stresses, such as `exactly`, `always`, `precisely` or
  `simply`. Keep it when the sentence means something else without the word. (R10-intensifiers)
- the full term when a short form is ambiguous: `timezone`, not `zone` (R10-clipped-terms)
- contractions and the imperative (R10-Q28, R10-Q29, R10-we)
- callables as `name()`, and no article before an identifier (R10-Q30, R10-Q35)
- only names the reader can resolve from the comment's position (R10-Q22, R10-Q21)
- with code or an abstract noun as the subject, only verbs for what code literally does: `returns`,
  `throws`, `reads`, `writes`, `calls`, `skips`. Never agency or containment: `finds`, `knows`,
  `holds`, `carries`, `keeps its`, `draws` for a widget whose drawing is not the point. The test is
  whether the subject can perform the verb. (R10-Q31, R10-Q39, R10-seed-1, R10-seed-6, R10-seed-15, R10-skill-gaps, J1-verbs-literal)
- no `is what`, no `its own` (R10-Q40, R10-Q41, `NAR018`)
- the general case: `records are separated by blank lines`, not `two records` (R10-Q40)
- a worked example matches what the code does for every case in the example (R10-worked-example)
- no semicolon and no dash. Write two sentences (R10-no-semicolon, `NAR013`)
- a comment line over the line limit is wrapped onto the next line. Never change the wording to fit (R11-wrap-not-reword)
- a Fence is the fact the code depends on, then the step the code takes because of that fact:
  `// Character.isDigit() accepts non-ASCII digits such as '٣'. Check the range '0' to '9' too`.
  Write `X would` only when X is an alternative the code does not use. When the code under the
  comment does X, state the problem X is there for. The `X would` form in full
  (R10-fence-form, R10-fence-fact, R10-fence-alternative):
  ```java
  // Here Files.readAllBytes() is used. The alternative, Files.readString(), would throw
  // MalformedInputException on a byte that is not UTF-8.
  final byte[] planBytes = Files.readAllBytes(planPath);
  ```
- a comment on one branch of a `switch` or `if` chain is about what only that branch does. A reason
  that covers every branch goes above them once (R10-branch-comment)
- directly above the statement it concerns, not above its enclosing block. Inside `try`, it goes above
  the call the comment concerns. A comment on an argument goes above the call that passes the
  argument. End-of-line for a short note. (R10-Q34, R10-locality, R10-fence-form,
  R10-argument-placement)

`NAR012` to `NAR016` and `NAR018` flag six wording faults in comments and javadoc, and a clean run is
no evidence about the rest of these lists. Check every comment and javadoc you write or touch against
them. A dash after a list-item term is allowed. (R10-lint, R10-skill-gaps, R10-list-dash)

`NAR017` is an agent verb on a subject that cannot act, meaning a noun that is not a person, with a
verb for something only a person does: thought or speech (`a period ranks`, `the report names it`),
or, with an object, a deliberate act (`the default config sends the job to a queue`). A table,
figure or example on the page can show what is in that table, figure or example. The check parses
each sentence, and some noun compounds and participles are flagged by mistake. (R10-agentverb-check,
R10-agentverb-agency)

**A finding is information.** Read the sentence again, then rewrite or delete the sentence, except
in three cases:

1. **A misparse.** The flagged words are not the subject and verb, or not one clause, in what you
   wrote. Leave the sentence.
2. **A quoted example.** The flagged text is an example of the fault, such as a banned word in the
   rule that bans the word. Leave the sentence.
3. **The code's name for the thing.** The flagged words come from an identifier, such as `sees the
   sky` from `canBlockSeeTheSky()`. Leave the sentence, and list the sentence in your report.

**Never add a `noqa` yourself.** The exceptions are the three `noqa` uses prescribed in this skill:
`NAR104` for two types of one name, `NAR142` in a degrade-and-report loop, and `NAR130` once the
user approves an upstream name. (R11-findings)

A `// noqa: NARxxx` covers every line of the comment block, and the code line after a whole-line
block, because spotless wraps a `//` comment over 120 columns and moves a trailing noqa to the next
line. The same syntax silences a finding from any tool. (J1-P35)

## Procedures

Take these in order. **Setup** happens once per machine. **Writing a comment** applies to each
comment as you write the comment. **Verify** and **Prose review** follow once the code is written.
**Published prose** applies to each page you write, such as a README. (R10-procedures)

### Setup

narrative-java uses the lint venv of narrative-python, one per machine. Its prose checks are the same
files. (R10-setup)

Linux and macOS:

```bash
uv venv --python 3.11 ~/.local/share/narrative/lintenv
uv pip install --python ~/.local/share/narrative/lintenv/bin/python -r "${CLAUDE_SKILL_DIR}/requirements-lock.txt"
```

Windows (PowerShell):

```powershell
uv venv --python 3.11 $env:LOCALAPPDATA\narrative\lintenv
uv pip install --python $env:LOCALAPPDATA\narrative\lintenv\Scripts\python.exe -r "${CLAUDE_SKILL_DIR}/requirements-lock.txt"
```

A JDK 25 comes from the Gradle toolchain of the project. PMD 7.28.0 and Checkstyle 13.5.0 come from
Maven Central on the first run. No project file changes.

### Writing a comment

Take these steps in order before writing or rewording a comment. The kinds, the **Never** list,
**Depth** and **Sentence form** are in **Comments**.

1. **Rename first.** If the information fits in a name or a type, rename and write no comment:
   `long overQuotaBytes`, `totalCents`, `rollingMeanSignedError()`. (R10-Q25, R10-Q27, R10-Q16)
2. **Guarantee it in code.** Establish a cheap precondition, such as sorted input, upstream in the
   call flow, not in the method that depends on the precondition, and write no comment. If a code
   change removes a trap, make the change and write no comment. If explaining how the code works
   takes more than one plain clause, rewrite the code instead. (R10-Q19, R10-footgun,
   R10-hard-comment)
3. **Match a kind.** Write a comment only if it is one of the four **Comment kinds**, passes that
   kind's test, and is not under **Never**. Deleting is a valid outcome of a rewrite when the content
   fails the test. When only the wording breaks a rule, rewrite the wording and keep the content.
   (R10-keep-content)
4. **Set the depth and sentence form** by **Depth** and **Sentence form**.

### Verify

Run `verify.py` from the root of the mod. Do not call the tools by hand.

```bash
python3 "${CLAUDE_SKILL_DIR}/verify.py"
python3 "${CLAUDE_SKILL_DIR}/verify.py" --since origin/dev
```

**In a PR to another project, pass `--since` with the base branch.** Upstream code already breaks
some of these rules, and a finding on a line the diff does not touch is not the PR's to fix. Only the
lines that the diff against `merge-base(HEAD, base)` adds or changes are reported, and every line of
an untracked file.

**Ask the user before you name something by an upstream convention that `NAR130` rejects.** For
example, GT5's `MultiblockTooltipBuilder` has about 40 `TT_*` fields, such as `TT_machineType`. A new
`TT_parallels` field beside those fields breaks the Java naming convention. With approval, mark the field
`// noqa: NAR130`. (J1-F06)

`verify.py` runs one Gradle invocation with the init script `narrative.init.gradle`: `spotlessApply`
(or `spotlessCheck` with `--no-fix`), `compileJava` with the raw-type and unchecked warnings of
javac, then Checkstyle and PMD with the configs beside `verify.py`. `javachecks.py` then reads the
comments, runs the prose checks, and merges the three reports into one list with NAR codes. A
passing run ends with three lists, the input to **Prose review**: every sentence of every comment
and javadoc, every verb whose subject cannot act, and every sentence with a pronoun. With `--since`,
the lists cover only the changed lines, and they are printed after the findings too, because
upstream lines in a diff often still have findings. Without `--since`, `verify.py` prints only the
first 1000 sentences of the first list. (J1-F01, J1-F09)

| exit | meaning |
|---|---|
| 0 | every check passed. Warnings may be printed |
| 1 | at least one finding, or the code does not compile or is not formatted |
| 2 | the toolchain, `gradle.properties`, `gradlew` or a report is missing, the project is not Java 25, `--since` names no commit, or the diff changes no line |

Pass `--max-workers 1` on a busy machine. The job of each tool, the code table and the tool defaults
that break rules of this skill are in `tooling.md`. Read it before you change a config.

### Prose review

**After a passing `verify.py` run, read the three lists at the end of the output, plus every error
message, lang entry and help text.** The first list has every sentence of every comment and javadoc.
The second has each subject that cannot act, paired with the subject's verb, for every verb that is
neither a `NAR017` finding nor an operation of code. A verb such as `reads` or `runs` is an
operation of code only with a direct object and code as the verb's subject:
`PlanLoader reads the plan file`, not `the spec reads`. The third has every sentence with `it`,
`its` or a standalone `that`, each after the sentence before. Take these steps for each sentence.
(R10-prose-inventory, R10-closing-review, R11-pronoun-list, R11-literal-review)

1. Name the subject and the verb. Can that subject perform that verb?
2. For each noun phrase, name the variable, method, file or value that the phrase refers to. If none
   fits, or two do, rewrite. Check each descriptive word of the phrase by **A descriptive word in a
   term is a claim**. For each pronoun in the third list, name the noun the pronoun stands for. If
   that noun is in another sentence, repeat the noun. (R10-stand-in)
3. List the code paths that reach the line: each branch, each caller, each failure. Check the claim
   on every path.
4. Test the sentence against **Sentence form**, and the comment against the restatement gate.

An entry on a review list is a question, not a finding. When the subject can do the verb in the
domain's sense, such as a block that gets sky light, leave the sentence unchanged.
(R11-review-question)

Fix what fails and run `verify.py` again.

### Published prose

A README, a doc page or an HTML report that you write follows the prose rules of this skill, as a
comment does. When you rewrite part of a page, the rules cover the section you changed. A page that a
person wrote and you did not change is left as it is, unless the user asks for it to be checked. Name
each page to `verify.py`, which then runs the prose checks only, with no Gradle project:

```bash
python3 "${CLAUDE_SKILL_DIR}/verify.py" README.md docs/report.html
```

Handle each finding by the rule **A finding is information**. (R10-published-prose)
