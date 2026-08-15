# Agent Operation Guide: API, CLI, and Scripts

## Goal

The Agent does not depend on the web UI. It uses OpenBKN APIs, the `openbkn` CLI, and sample scripts to import, bind, verify capabilities, and answer a fulfillment commitment question.

## Operation entry point

```text
Agent → OpenBKN API / openbkn CLI → KN, Resources, Skills, Functions, Actions → test set and report
```

Recommended entry sequence:

```bash
openbkn auth status
openbkn bkn validate kn/supply_ontology_hand_en.json
python3 tools/load_sample_data.py --config tools/config.yaml
python3 tools/import_kn.py --kn-file kn/supply_ontology_hand_en.json
python3 tools/bind_kn_resources.py --config tools/config.yaml --kn-id supply_ontology_hand_en
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
