# Third-Party Agent Skill Orchestration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the supply-chain sample explicitly support orchestration Skills where the third-party Agent retains trace context, retrieves evidence, invokes a deterministic Toolbox function with `resolved_context`, and produces a governed report.

**Architecture:** Skills remain declarative contracts. A small local orchestration adapter will validate the required fields and build the function request without storing a second copy of Agent context. The adapter will never query data or execute Actions; platform/Agent integrations remain responsible for managed Context Loader and Toolbox calls.

**Tech Stack:** Python 3.11, pytest, JSON/YAML contract fixtures, Markdown handbooks, OpenBKN CLI/Context Loader.

---

### Task 1: Add failing orchestration-contract tests

**Files:**
- Create: `samples/supply_ontology_hand/tools/tests/test_skill_orchestration_contract.py`
- Create: `samples/supply_ontology_hand_en/tools/tests/test_skill_orchestration_contract.py`

**Steps:**

1. Test that an S1 orchestration request requires `conversation_id`, `interaction_id`, `resolved_context`, and the seven `backward_plan` datasets.
2. Test that the adapter preserves the Agent-provided IDs and snapshot without creating a persistence layer.
3. Test that missing receipt, missing demand fields, or incomplete datasets fail before function invocation.
4. Test that the contract explicitly distinguishes orchestration Skills from `execute_skill` shell Skills.
5. Run the two new test files and verify they fail because the adapter/contract helper does not exist.

### Task 2: Implement the minimal local orchestration contract helper

**Files:**
- Create: `samples/supply_ontology_hand/tools/skill_orchestration.py`
- Create: `samples/supply_ontology_hand_en/tools/skill_orchestration.py`

**Steps:**

1. Implement a pure `build_toolbox_request()` helper that accepts the existing Agent context, resolved snapshot, operation ID, and business parameters.
2. Validate required Trace IDs, receipt completeness, exact dataset names, forecast identity, demand date, quantity, and substitute policy.
3. Return a JSON-serializable request containing `bkn_context`, `resolved_context`, and function arguments.
4. Do not add database access, network calls, formula calculation, Action execution, or disk persistence.
5. Run the new tests and verify they pass.

### Task 3: Add the Agent-mode runbook and examples

**Files:**
- Modify: `samples/supply_ontology_hand/docs/第三方Agent数据交接说明.md`
- Modify: `samples/supply_ontology_hand_en/docs/第三方Agent数据交接说明.md`
- Modify: the relevant Agent-mode sections under `docs/handbook/` and `docs/playbook/`

**Steps:**

1. Document the exact sequence: start Interaction → recall Skill → query once → assemble `resolved_context` → call Toolbox → render report → finish Interaction.
2. State that IDs are retained by the Agent and only need to be passed through in `bkn_context` on each call.
3. Add a concrete future-forecast example using `0000023181-FUTURE`, due `2026-10-31`, quantity `3000`, substitutions disabled.
4. Document failure behavior and the prohibition on offline fallback during online POC validation.
5. Add the distinction between orchestration Skills and shell-executable Skills; do not instruct users to call `execute_skill` for S1.

### Task 4: Update POC verification and benchmark evidence

**Files:**
- Modify: `samples/supply_ontology_hand/docs/verification/poc-verification-report-2026-08-15.md`
- Modify: `samples/supply_ontology_hand_en/docs/verification/poc-verification-report-2026-08-15.md`
- Modify: relevant benchmark/evidence JSON if the contract test count changes

**Steps:**

1. Record that Skill recall passed and orchestration contract validation is a separate gate.
2. Record the current POC limitation: the Context Loader catalog does not yet expose a managed Toolbox call for `resolved_context`.
3. Keep the execute-skill failure evidence and explicitly state that no Action was executed.
4. Avoid claiming the full online Skill execution loop passed until a managed Toolbox endpoint is available.

### Task 5: Run verification and commit

**Files:**
- Test: both Chinese and English `tools/tests/` suites

**Steps:**

1. Run focused orchestration and documentation tests in each sample.
2. Run the full test suites from `tools/` with `python3 -m pytest -q`.
3. Run `git diff --check` and inspect the final diff.
4. Commit the implementation and documentation changes with a focused message.
