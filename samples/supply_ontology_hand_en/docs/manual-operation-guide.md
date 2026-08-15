# Manual Operation Guide: UI and Scripts

Manual mode combines console UI operations with scripts. It does not use Agent dialogue for the business decision.

## Step 1: Human database-table import (required)

Database-table import is a required online prerequisite. The operator must perform it with database credentials; importing the KN JSON in the OpenBKN UI alone is not sufficient:

```bash
python3 tools/load_sample_data.py --interactive --create-database --table-prefix hand_
```

Enter the PostgreSQL host, port, database, username, and password. After the connection test succeeds, type `yes`; the script creates `hand_`-prefixed tables and preserves existing business tables.

## UI operations

1. Sign in to the OpenBKN console.
2. Open “Domain Knowledge Networks → Knowledge Network Management”.
3. Use “Import” to upload `kn/supply_ontology_hand_en.json`.
4. Check the network name, object types, relation types, metrics, and Actions.
5. Select the matching resources and bind the object types in the data-resource screen.
6. Confirm that the network is queryable before running the scripts.

## Script operations

```bash
cd tools
python3 load_sample_data.py --config config.yaml
python3 import_kn.py --json ../kn/supply_ontology_hand_en.json
python3 setup_catalog.py --interactive --table-prefix hand_ --write-config
python3 bind_kn_resources.py --config config.yaml --kn-id supply_ontology_hand_en --table-prefix hand_
python3 verify_sample.py --config config.yaml --kn-id supply_ontology_hand_en
```

Then follow the Action Dataset, Skill registration, and function-service instructions. Run every write command with `--dry-run` first.

Record UI screenshots, environment-specific resource IDs, and operation timestamps in the verification report; do not write environment-specific IDs back into the portable KN JSON.

## Fulfillment question

Use the future forecast cases in `docs/qa-eval-set.yaml` and record the query results, evidence, and final conclusion.
