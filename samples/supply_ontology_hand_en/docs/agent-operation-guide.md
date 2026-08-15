# Agent Operation Guide: API, CLI, and Scripts

## Goal

The Agent does not depend on the web UI. It uses OpenBKN APIs, the `openbkn` CLI, and sample scripts to import, bind, verify capabilities, and answer a fulfillment commitment question.

## Step 1: Human database-table import (Agent prerequisite)

This step must be performed by the deployment/POC operator because it requires database connection details and a password. From the sample root, run:

```bash
python3 tools/load_sample_data.py --interactive --create-database --table-prefix hand_
```

Enter the PostgreSQL host, port, database, username, and password. The script tests the connection and writes only after you type `yes`; destination tables use the `hand_` prefix. Agent automation starts after Catalog Discover.

## Operation entry point

```text
Agent → OpenBKN API / openbkn CLI → KN, Resources, Skills, Functions, Actions → test set and report
```

Recommended entry sequence:

```bash
openbkn auth status
python3 tools/import_kn.py --json kn/supply_ontology_hand_en.json --dry-run
python3 tools/setup_catalog.py --interactive --table-prefix hand_ --write-config
python3 tools/import_kn.py --json kn/supply_ontology_hand_en.json --resolve-embedding
python3 tools/bind_kn_resources.py --config tools/config.yaml --kn-id supply_ontology_hand_en --table-prefix hand_
python3 tools/register_skills.py --dry-run
python3 tools/setup_action_datasets.py --engine postgres
python3 tools/bind_action_datasets.py --mapping tools/mapping/action_dataset_map.yaml
```

Use dry-run for every platform write first. The Agent must rely on returned capabilities and evidence rather than guessing object types, fields, Skills, or Actions.

## Recommended user question

Can product `U00-000080` be delivered by `2026-10-31` in a quantity of `3000`? The forecast number is `0000023181-FUTURE`; do not use substitute materials. Explain inventory, producible quantity, material shortages, and the evidence for the conclusion.

## Verification sequence

1. Confirm that the knowledge network and data sources are ready.
2. Find the fulfillment analysis Skill.
3. Retrieve forecast, product, inventory, BOM, production, and purchasing evidence.
4. Call the function that calculates the deliverable quantity.
5. Return the conclusion, evidence, and risks.
6. Show a dry-run and impact scope before any Action and wait for confirmation.
