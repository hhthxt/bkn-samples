# Supply Ontology Hand Delivery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver Chinese and English, one-shot, self-contained supply-chain BKN samples that can be imported, bound, operated by an Agent or manually, and verified in the POC environment before any push to `main`.

**Architecture:** Keep two independent sample directories, `supply_ontology_hand` and `supply_ontology_hand_en`. Each directory contains its own KN JSON, sample data, reproducible initialization/binding scripts, Agent/manual handbooks, blind test set, Playbook cases, and benchmark report. The verified localhost export is the stage2-capable schema baseline, but environment-specific resource identifiers are replaced by deterministic post-import binding.

**Tech Stack:** OpenBKN CLI/API, JSON, CSV/SQL, Python 3, pytest, Markdown, generated HTML.

---

### Task 1: Establish the delivery workspace and baseline inventory

**Files:**
- Create: `docs/plans/2026-08-15-supply-ontology-hand-delivery.md`
- Inspect: `samples/supply_ontology_hand/**`

**Step 1: Record the target branch and clean baseline**

Run: `git status --short --branch`

Expected: branch `codex/supply-ontology-hand-delivery`; no unrelated changes.

**Step 2: Inventory existing KN, data, tools, and tests**

Run: `find samples/supply_ontology_hand -maxdepth 3 -type f | sort`

Expected: existing Chinese baseline is captured before restructuring.

**Step 3: Commit the plan**

Run: `git add docs/plans/2026-08-15-supply-ontology-hand-delivery.md && git commit -m "docs: plan supply ontology hand delivery"`

Expected: one plan-only commit.

### Task 2: Define the two self-contained sample contracts

**Files:**
- Create: `samples/supply_ontology_hand_en/README.md`
- Modify: `samples/supply_ontology_hand/README.md`
- Modify: `samples/supply_ontology_hand/README_cn.md`
- Create: `samples/supply_ontology_hand/docs/sample-contract.yaml`
- Create: `samples/supply_ontology_hand_en/docs/sample-contract.yaml`

**Step 1: Write contract tests for required delivery paths**

Test: `samples/supply_ontology_hand/tools/tests/test_delivery_contract.py`

Assert each language sample has KN JSON, data, import, binding, setup, Agent/manual docs, QA set, Playbook cases, and report paths.

**Step 2: Run the contract tests and confirm they fail for the missing English sample**

Run: `python3 -m pytest samples/supply_ontology_hand/tools/tests/test_delivery_contract.py -q`

Expected: FAIL because the English delivery tree is not yet present.

**Step 3: Create the two sample trees and language-specific READMEs**

Keep each sample independently runnable. Do not introduce stage directories. Explain the one-shot flow: initialize data, import KN, resolve/bind resources, register Skills/Functions, start services, run Agent/manual checks, run blind benchmark.

**Step 4: Run contract tests**

Run: `python3 -m pytest samples/supply_ontology_hand/tools/tests/test_delivery_contract.py -q`

Expected: PASS.

### Task 3: Normalize the verified localhost KN export for migration

**Files:**
- Create: `samples/supply_ontology_hand/kn/supply_ontology_hand.json`
- Create: `samples/supply_ontology_hand_en/kn/supply_ontology_hand_en.json`
- Create: `samples/*/tools/normalize_kn_export.py`
- Test: `samples/*/tools/tests/test_kn_migration_contract.py`

**Step 1: Capture the localhost export and compare it with the existing test JSON**

Run: `openbkn --json bkn export supply_ontology_hand > /tmp/supply_ontology_hand.localhost.json`

Compare object types, relations, metrics, actions, Skills object, and action dataset bindings against the existing sample JSON and test fixtures.

**Step 2: Write failing migration tests**

Assert the delivered JSON contains the verified full capability set, has no localhost resource IDs, and preserves stable technical IDs and action contracts.

**Step 3: Implement normalization**

Remove environment-specific resource IDs, timestamps, creator metadata, and duplicate local-only objects. Preserve schema, display labels, property names, relation semantics, metric definitions, and verified Action contracts. Keep the canonical `skills` object name/ID used by `find_skills`.

**Step 4: Generate English KN JSON from the normalized Chinese schema**

Translate display names, descriptions, metric/action labels, and user-facing documentation fields. Preserve technical IDs, property names, and relation/action identifiers.

**Step 5: Run migration tests**

Run: `python3 -m pytest samples/supply_ontology_hand/tools/tests/test_kn_migration_contract.py -q`

Expected: PASS.

### Task 4: Refresh sample data with future forecast scenarios

**Files:**
- Modify: `samples/supply_ontology_hand/data/erp_mds_forecast.csv`
- Create/modify: related supply, inventory, BOM, production, purchase, and planning CSVs
- Create: `samples/supply_ontology_hand_en/data/*.csv`
- Test: `samples/*/tools/tests/test_future_forecast_cases.py`

**Step 1: Add failing fixture tests**

Require several forecast orders with due dates between `2026-09-30` and `2026-12-31`, including feasible, shortage, shared-material, and no-substitution cases. Keep `0000023181` only as a historical regression fixture if it remains useful.

**Step 2: Update Chinese data consistently**

Preserve IDs, codes, dates, quantities, keys, and expected business outcomes. Ensure the new forecast orders have complete downstream inventory/BOM/capacity/purchase evidence.

**Step 3: Translate the business values into English**

Translate material, supplier, organization, warehouse, status, type, unit, and notes values. Keep CSV column names, keys, codes, numbers, dates, and technical statuses stable.

**Step 4: Run data integrity tests**

Run: `python3 -m pytest samples/supply_ontology_hand/tools/tests/test_future_forecast_cases.py -q`

Expected: PASS for both language datasets and identical decision inputs.

### Task 5: Package reproducible import, binding, Skills, Functions, and Actions

**Files:**
- Modify/create: `samples/*/tools/load_sample_data.py`
- Modify/create: `samples/*/tools/import_kn.py`
- Modify/create: `samples/*/tools/bind_kn_resources.py`
- Create: `samples/*/tools/setup_action_datasets.py`
- Create: `samples/*/tools/bind_action_datasets.py`
- Create: `samples/*/tools/register_skills.py`
- Create: `samples/*/tools/start_function_service.py`
- Create: `samples/*/tools/action_gateway.py`
- Create: `samples/*/tools/mapping/action_dataset_map.yaml`
- Test: `samples/*/tools/tests/test_reproducible_setup.py`

**Step 1: Write setup tests**

Verify scripts use environment variables/configuration for business domain, KN ID, datasource, and service URLs; no hard-coded localhost resource IDs.

**Step 2: Implement the one-shot setup commands**

Provide dry-run and apply modes. Default to dry-run for destructive or platform-writing operations. Register `skills` through the dataset-backed object class, start the function service, bind Action Datasets, and include the corrected `close_monitor_task` contract.

**Step 3: Run local script tests**

Run: `python3 -m pytest samples/supply_ontology_hand/tools/tests -q`

Expected: all local tests pass without requiring POC credentials.

### Task 6: Write Agent/manual handbooks and Playbook verification materials

**Files:**
- Create: `samples/supply_ontology_hand/docs/handbook.html`
- Create: `samples/supply_ontology_hand_en/docs/handbook.html`
- Create/modify: `samples/*/docs/agent-operation-guide.md`
- Create/modify: `samples/*/docs/manual-operation-guide.md`
- Create/modify: `samples/*/docs/playbook.md`
- Create/modify: `samples/*/docs/qa-eval-set.yaml`

**Step 1: Add the future delivery question to both handbooks and QA sets**

Use the scenario: product `U00-000080`, several future forecast numbers, demand quantity, due date, and substitution disabled. Require evidence-backed answers, not only a yes/no result.

**Step 2: Document Agent mode**

Give exact prompts, expected tool/Skill/Action routing, confirmation points, and failure handling.

**Step 3: Document manual mode**

Give exact CLI/API steps for import, binding, data query, metric query, Skill lookup, function call, Action dry-run, and `close_monitor_task` execution.

**Step 4: Link HTML handbook from both READMEs**

The HTML must summarize ontology, data lineage, capability map, operating modes, and verification evidence.

### Task 7: Run local blind benchmark and generate reports

**Files:**
- Modify: `samples/*/tools/benchmark_third_party.py`
- Create: `samples/*/docs/verification/benchmark-result.json`
- Create: `samples/*/docs/verification/benchmark-report.md`
- Test: `samples/*/tools/tests/test_benchmark_packaging.py`

**Step 1: Ensure reference answers are not read by the runner**

Run the benchmark with reference-answer loading disabled and record the question count, pass rate, Playbook accuracy, and action outcomes.

**Step 2: Run the full local suite**

Run from each sample's `tools/` directory: `python3 -m pytest tests -q`

Expected: PASS with no skipped critical coverage.

**Step 3: Generate Chinese and English reports**

Reports must include the exact commit, KN export checksum, dataset checksum, environment, test counts, failures, and known limitations.

### Task 8: Execute the complete POC validation gate

**Files:**
- Create: `samples/*/docs/verification/poc-runbook.md`
- Create: `samples/*/docs/verification/poc-result.json`
- Modify: `samples/*/README.md`

**Step 1: Run the import/bind flow in `https://poc.openbkn.ai/`**

Use the manual runbook and record all generated resource IDs in the private run log, not in portable KN JSON.

**Step 2: Run the Agent scenarios**

Verify future forecast feasibility, no-substitution behavior, metric explanation, Skill discovery, Function invocation, Playbook execution, and safe Action confirmation.

**Step 3: Run the manual scenarios**

Repeat the same checks through CLI/API and compare results with the Agent path.

**Step 4: Publish the POC result into the sample report**

The gate is passed only if all critical cases pass, evidence is reproducible, and no platform-specific workaround is omitted from the runbook.

### Task 9: Review, commit, and prepare the main-branch push

**Files:**
- All files under `samples/supply_ontology_hand/`
- All files under `samples/supply_ontology_hand_en/`

**Step 1: Run repository-level checks**

Run: `git diff --check` and both sample test suites.

Expected: no whitespace errors and all tests pass.

**Step 2: Review the delivery tree**

Confirm no secrets, localhost-only IDs, temporary files, `.pytest_cache`, or stale stage terminology are included.

**Step 3: Commit the completed delivery**

Use a descriptive commit such as `feat: deliver bilingual supply ontology hand samples`.

**Step 4: Wait for explicit POC pass evidence**

Do not push `main` until the POC report is complete and reviewed.

**Step 5: Push only after the gate is passed**

Push the reviewed branch or merge to `main` according to the user's final instruction.
