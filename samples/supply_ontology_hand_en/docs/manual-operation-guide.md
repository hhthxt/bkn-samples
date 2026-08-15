# Manual Operation Guide

## One-shot flow

```bash
cd tools
python3 load_sample_data.py --config config.yaml
python3 import_kn.py --kn-file ../kn/supply_ontology_hand_en.json
python3 bind_kn_resources.py --config config.yaml --kn-id supply_ontology_hand_en
python3 verify_sample.py --config config.yaml --kn-id supply_ontology_hand_en
```

Then follow the Action Dataset, Skill registration, and function-service instructions. Run every write command with `--dry-run` first.

## Fulfillment question

Use the future forecast cases in `docs/qa-eval-set.yaml` and record the query results, evidence, and final conclusion.
