# POC API Verification Report

Date: 2026-08-15  
Environment: `https://poc.openbkn.ai`  
Mode: Agent API / CLI

POC `RT_Supply_Data` has been confirmed as a healthy physical PostgreSQL Catalog connected to the `Supply_Data` database. The issue is not a missing Catalog connection; the sample CSVs have not been written to that database, and the CSV dataflow endpoint returns HTTP 404.

## Passed

- Chinese KN `supply_ontology_hand` imported and read back successfully.
- English KN `supply_ontology_hand_en` imported and read back successfully.
- Both networks contain 15 object types, 19 relations, and 3 actions.
- Target-environment embedding resolution succeeded.
- Ten available object types were bound to POC resources. The sales-order object remains unbound because no isomorphic `sales_order` table exists.
- Seven non-sales-order metrics and seven logic properties were registered successfully.

## Not passed

### Online sample data push

`bkn create-from-csv` received HTTP 404 from the dataflow endpoint for the current POC Catalog. No isolated sample-data resources were created. The POC needs a writable physical Catalog or an enabled CSV dataflow API.

### Metric blind test

The metric definitions execute, but queries read the existing POC ERP data rather than the sample CSV snapshot. All 11 non-sales-order cases returned mismatches:

| Metric | Sample expected | POC returned |
|---|---:|---:|
| Product count | 30 | 431 |
| Material count | 3497 | 14283 |
| Supplier count | 230 | 3372 |
| Open forecast count | 90 | 568 |

This is a data-source mismatch, not evidence of a formula defect.

## Release gates

1. Use a writable physical Catalog to upload all 12 sample CSVs with the `hand_` prefix;
2. Discover and verify resource row counts;
3. Bind all 11 object types to the `hand_` resources;
4. Add the `sales_order` table, then register the eighth metric and sales-order logic property;
5. Re-run metric blind tests, function, Skill, Playbook, and Action verification;
6. Push the GitHub mainline only after all gates pass.
