# Action Dataset Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make Agent-mode Action Dataset setup automatically create idempotent decision/monitor tables from one interactive database connection and bind them to the POC knowledge network.

**Architecture:** Keep database DDL execution and OpenBKN object binding as two explicit, verifiable stages inside one bootstrap entry point. Credentials are accepted interactively or through an injected connection object and are never written to sample config. Every write has a dry-run path, and post-write checks query both the database and OpenBKN.

**Tech Stack:** Python 3, psycopg, PostgreSQL DDL, PyYAML, `openbkn` CLI, pytest.

---

### Task 1: Add failing tests for idempotent DDL execution

**Files:**
- Modify: `samples/supply_ontology_hand/tools/tests/test_setup_action_datasets.py`
- Modify: `samples/supply_ontology_hand_en/tools/tests/test_setup_action_datasets.py`

**Steps:**

1. Test that a dry-run returns the SQL without opening a database connection.
2. Test that apply executes the SQL through an injected connection and returns verification metadata.
3. Test that a missing connection field fails before any write.
4. Run the focused tests and confirm the new tests fail because the apply API is absent.

### Task 2: Implement database DDL application

**Files:**
- Modify: `samples/supply_ontology_hand/tools/setup_action_datasets.py`
- Modify: `samples/supply_ontology_hand_en/tools/setup_action_datasets.py`

**Steps:**

1. Add an interactive PostgreSQL credential prompt and a connection factory.
2. Add `apply_ddl(connection)` using the checked-in PostgreSQL SQL file.
3. Add idempotent verification for the three expected tables.
4. Preserve the existing dry-run output and add `--interactive`/`--database-url` without persisting credentials.
5. Run focused tests and then the full local test suite.

### Task 3: Add failing tests for OpenBKN dataset binding

**Files:**
- Modify: `samples/supply_ontology_hand/tools/tests/test_bind_action_datasets.py`
- Modify: `samples/supply_ontology_hand_en/tools/tests/test_bind_action_datasets.py`

**Steps:**

1. Test that mapping entries become object-type updates with dataset data sources.
2. Test dry-run produces no CLI write calls.
3. Test apply uses the configured KN ID and schema-qualified dataset names.
4. Run focused tests and confirm failure before implementation.

### Task 4: Implement OpenBKN binding and bootstrap orchestration

**Files:**
- Modify: `samples/supply_ontology_hand/tools/bind_action_datasets.py`
- Modify: `samples/supply_ontology_hand_en/tools/bind_action_datasets.py`
- Create: `samples/supply_ontology_hand/tools/bootstrap_action_layer.py`
- Create: `samples/supply_ontology_hand_en/tools/bootstrap_action_layer.py`

**Steps:**

1. Implement config/CLI resolution for KN ID and dataset schema.
2. Implement dry-run and apply binding via `openbkn bkn object-type get/update`.
3. Add the bootstrap command that performs DDL, verifies tables, binds datasets, and emits a JSON report.
4. Run focused tests and then the full local test suite.

### Task 5: Update delivery documentation

**Files:**
- Modify: `samples/supply_ontology_hand/docs/agent-operation-guide.md`
- Modify: `samples/supply_ontology_hand/docs/manual-operation-guide.md`
- Modify: `samples/supply_ontology_hand/docs/online-data-push.md`
- Modify: `samples/supply_ontology_hand/docs/faq.md`
- Modify: English counterparts under `samples/supply_ontology_hand_en/docs/`

**Steps:**

1. Document the one-command Agent flow and manual fallback.
2. State exactly where the password is entered and that it is not persisted.
3. Document dry-run, idempotency, post-write checks, and failure recovery.
4. Run documentation/path tests.

### Task 6: Execute against POC and record evidence

**Steps:**

1. Run the bootstrap command with the dedicated POC database connection.
2. Verify the three database tables and OpenBKN object-type data sources.
3. Run the Action/Playbook benchmark prerequisites.
4. Commit source, tests, docs, and the evidence report; do not push GitHub until the full benchmark passes.
