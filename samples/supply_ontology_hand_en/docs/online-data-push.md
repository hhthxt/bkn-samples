# Online data push and binding

## Recommended order

```text
Create a dedicated database/connection → create a dedicated physical Catalog → load sample tables → Discover → verify resources → bind object types → register metrics
```

Action Datasets use the same chain: after creating the tables, run Discover again. A table name cannot be used directly as an object-type `data_source.id`.

## Agent/API mode

A physical Catalog is not a file-upload container. The supply sample must use a dedicated database and Catalog; do not reuse the existing POC `RT_Supply_Data`, otherwise sample data will be mixed with real data. Suggested names are database `supply_ontology_hand_poc` and Catalog `Supply_Ontology_Hand_POC`.

The correct chain is: create the dedicated database connection and database, load the sample tables, then let the new Catalog Discover scan the tables and create resources.

```text
PostgreSQL/MySQL database (write sample tables)
  → physical Catalog (connector)
  → discover
  → Vega resources
  → KN object_type.data_source
```

Check that every CSV has a consistent column count before upload:

```bash
python3 - <<'PY'
import csv, glob
for path in glob.glob('data/*.csv'):
    with open(path, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))
    width = len(rows[0])
    bad = [i + 1 for i, row in enumerate(rows) if len(row) != width]
    if bad:
        raise SystemExit(f'{path}: inconsistent rows {bad[:5]}')
print('CSV shape check passed')
PY
```

`create-from-csv` is only a convenience dataflow entry point; writability is not an inherent property of a physical Catalog. If the target environment enables this dataflow, use a dedicated Catalog. Otherwise, create prefixed tables through the dedicated database connection, then run Discover on the new Catalog.

The sample includes the database push script; operators do not need to write INSERT statements:

```bash
python3 tools/load_sample_data.py --interactive --create-database --table-prefix hand_
```

The script first creates the target database through the `postgres` maintenance database if it does not exist, then prompts for connection details. The password is hidden; it tests the connection and writes only after `yes`; destination tables are named `hand_<original_table>`. If the account lacks `CREATEDB`, ask a DBA to create the database and rerun without `--create-database`.

After loading the tables, use the same connection details to create the dedicated physical Catalog:

```bash
python3 tools/setup_catalog.py --interactive --table-prefix hand_ --write-config
```

Interactive mode does not write the database password. It writes the credential-free
follow-up config to `tools/config.poc.yaml`; use that file for binding.

This defaults to `Supply_Ontology_Hand_POC`, tests the connection, creates or reuses that dedicated Catalog, runs Discover, and verifies the 12 `hand_` tables. Do not configure `RT_Supply_Data` for this sample.

Do not overwrite existing business tables. Isolate this sample with a prefix:

```bash
openbkn --json bkn create-from-csv <catalog_id> \
  --files 'data/*.csv' \
  --name supply_ontology_hand_uploaded_data \
  --table-prefix hand_ \
  --batch-size 500
```

After upload, verify resources such as `hand_erp_material`, `hand_erp_mds_forecast`, and `hand_sales_order`. Update the mapping with the `hand_` names and run:

```bash
python3 tools/bind_kn_resources.py \
  --config tools/config.poc.yaml \
  --mapping tools/mapping/object_table_map.yaml
python3 tools/power_layer.py create --kn-id supply_ontology_hand_en
```

Resolve the target embedding with `--resolve-embedding` during KN import. Data upload and vector-index building are separate operations; `--build` does not prove that data upload succeeded.

## Troubleshooting

- `HTTP 404`: this usually means the CSV dataflow endpoint is not enabled; it does not mean the physical Catalog is invalid. Load the CSV into a POC-accessible PostgreSQL/MySQL, then run Catalog Discover instead of retrying `create-from-csv`.
- `Invalid Record Length`: a CSV row has a different number of columns from the header. Run the shape check first; do not blindly retry because partial tables may remain.
- Resource exists but binding fails: verify the resource belongs to the target Catalog, the `hand_` prefix is present, and the object type uses the current environment resource ID.
- Metric creation says `resource id is required`: bind object-type resources before registering metrics.
- Toolbox name validation failed: remove hyphens, spaces, and punctuation; keep only Chinese characters, letters, digits, and underscores.
- POC API request timed out: run `openbkn auth status`, then list Toolboxes or Skills to check actual state before retrying.
- Function Toolbox cannot be called: keep the local function service running and verify that the platform container can reach `http://host.docker.internal:8765`.
- Action Dataset automation failed: run `python3 tools/bootstrap_action_layer.py --dry-run`, confirm database permissions and the three `sc_` tables, then verify object-type `data_source` with `openbkn bkn object-type get`.

## Manual mode

In the UI, confirm Catalog connection and write capability, then import the CSVs. Verify table names and row counts in the resource list, and bind object types using the same mapping. Manual mode also requires prefix isolation and data binding before metric registration.
