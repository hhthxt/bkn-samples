# FAQ: Third-party import and embedding model binding

## Q1: Why does import report that the model cannot be fetched?

The usual cause is that `index_config.vector_config.model_id` came from another environment. Model IDs are environment-scoped resources and are not guaranteed to work across environments or tenants. This sample reproduced the problem in the POC.

## Q2: How should a third-party user check the embedding model?

After OAuth login, run:

```bash
openbkn --json model small list
openbkn --json model small get-default --type embedding
```

Confirm `model_type` is `embedding` and use the returned `model_id`. Never copy an ID from another environment, an old report, or another user’s JSON.

## Q3: How should the JSON be repaired?

Replace `vector_config.model_id` for every vector-enabled property with an embedding ID available in the target environment, keeping `vector_config.enabled` unchanged. In Agent mode, let the import script resolve the target default embedding dynamically:

```bash
python3 tools/import_kn.py --json kn/supply_ontology_hand_en.json --resolve-embedding
```

## Q4: How can I validate without writing to the platform?

```bash
python3 tools/import_kn.py --json kn/supply_ontology_hand_en.json --dry-run
```

Dry-run checks the local JSON and request preparation only. A real target-environment API import or schema check is still required to prove that the model ID is valid.

## Q5: How do I confirm that embedding works after import?

Run `openbkn --json bkn get <kn_id> --stats`, then perform one semantic search against a vector-enabled field. Record the result, model ID, and timestamp. Network creation alone does not prove that asynchronous indexing has completed.

## Q6: Why can the metric count be zero after import?

Knowledge-network import and metric registration are separate capabilities. `metrics_total: 0` means metrics are not registered in the target environment; it does not mean object or relation import failed. After registration, verify with:

```bash
openbkn --json bkn metric list <kn_id>
```

Skill registration, function services, and action bindings must also be verified separately.

## Q7: How does Manual mode handle this?

Select an embedding available in the target environment in the UI before importing the JSON. The rule is the same as Agent mode: do not reuse a model ID from another environment.

## Q8: Why does Toolbox creation reject the name?

The POC accepts only Chinese characters, letters, digits, and underscores in Toolbox names. Remove hyphens, spaces, and punctuation.

## Q9: What should I do after a POC API timeout?

Do not blindly retry creation. Run `openbkn auth status`, then list Toolboxes and confirm whether the requested name already exists before retrying.

## Q10: Does `setup_action_datasets.py --apply` create the tables?

Agent mode now uses `bootstrap_action_layer.py --interactive --apply` to execute idempotent DDL and verify the three tables. The password is not persisted. Manual mode may still execute the SQL directly.

## Q11: Why is a function Toolbox created but not callable?

Keep `fn_service` running on port 8765 and verify that the OpenBKN platform container can reach `http://host.docker.internal:8765`. Local browser reachability alone is insufficient.

## Q12: The OpenAPI upload succeeded but the tools cannot be called

Upload success does not mean the tools are enabled. Check each tool status in the Toolbox, enable any `disabled` tool with its returned `tool_id`, and verify again.
