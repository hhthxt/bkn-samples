# Supply Sample Executive Handbook Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a complete Chinese HTML business handbook for the supply-chain sample and link it from the default README.

**Architecture:** Replace the minimal standalone handbook with one self-contained HTML page driven by verified local Markdown/JSON evidence. Use semantic HTML and embedded CSS, keeping localhost Benchmark and POC validation as separate labelled evidence panels.

**Tech Stack:** Static HTML5, embedded CSS, existing Markdown/JSON verification artifacts, Python pytest.

---

### Task 1: Add handbook contract test

**Files:**
- Create: `samples/supply_ontology_hand/tools/tests/test_handbook_html.py`
- Modify: `samples/supply_ontology_hand/docs/handbook.html`

**Step 1:** Write a test that requires Chinese language metadata, the executive-summary title, business-story/data/network/validation sections, and links to Benchmark plus POC reports.

**Step 2:** Run `PYTHONPATH=tools python3 -m pytest tools/tests/test_handbook_html.py -q`; expect failure against the minimal handbook.

**Step 3:** Implement the expanded semantic HTML with the required IDs and relative links.

**Step 4:** Re-run the handbook test; expect pass.

### Task 2: Build business narrative and capability matrices

**Files:**
- Modify: `samples/supply_ontology_hand/docs/handbook.html`

**Step 1:** Add executive summary, business story flow, scenario matrix, data assets, ontology overview, and capability matrix.

**Step 2:** Use only verified values: 12 tables, 78,635 rows, 15 object types, 19 relations, 8 metrics, 3 Skills, 3 Actions, 137 forecasts, 90 open forecasts, and 56,340 open quantity.

**Step 3:** Add separate localhost Benchmark and POC evidence panels, including the stated non-release boundaries.

**Step 4:** Run the handbook contract test and `git diff --check`.

### Task 3: Add README entry and validate rendering

**Files:**
- Modify: `samples/supply_ontology_hand/README.md`
- Modify: `samples/supply_ontology_hand/docs/handbook.html`

**Step 1:** Link the handbook prominently from the default Chinese README.

**Step 2:** Inspect the HTML using the local browser/rendering capability and correct visual overflow or unreadable contrast.

**Step 3:** Run `PYTHONPATH=tools python3 tools/verify_sample.py`; expect all tests passed.

### Task 4: Commit and publish review branch

**Files:**
- Commit all Task 1–3 files.

**Step 1:** Run `git diff --check` and `PYTHONPATH=tools python3 tools/verify_sample.py`.

**Step 2:** Commit with `docs: add supply sample executive handbook`.

**Step 3:** Push the branch and create a non-auto-merge PR describing the business audience and verification evidence.
