# Supply Ontology Hand POC Verification Report

Date: 2026-08-15  
Environment: `https://poc.openbkn.ai/`  
Knowledge network: `supply_ontology_hand`

## Conclusion

The POC data load, physical Catalog, object bindings, Action Dataset bootstrap and binding, function Toolbox, and Skill publication paths are complete. The offline third-party blind benchmark passed. The three Action Dataset object types are bound through discovered Resources; the unsupported `data_source.type=dataset` binding is not used.

No real purchase, monitor-task creation, or monitor-task close was executed in this verification. Actions remain at schema, binding, and dry-run gates.

## Resource evidence

| Item | Result |
|---|---|
| Database | `supply_ontology_hand_poc` |
| Data | 12 `hand_` tables, 78,635 rows |
| Physical Catalog | `Supply_Ontology_Hand_POC` |
| Catalog ID | `d9vuoqtjdthc73bmpprg` |
| Action Toolbox | `af2ad8cb-9c32-4c07-aea8-fc05161d12e7`, published |
| Toolbox tools | 13/13 enabled |

After Catalog Discover, the Action Dataset Resources were:

| Object type | Resource | Resource ID |
|---|---|---|
| Monitor task item | `public.sc_plan_monitor_item` | `da00p1ljdthc73bmqa9g` |
| Monitor task | `public.sc_plan_monitor_task` | `da00p1ljdthc73bmqaa0` |
| PR decision | `public.sc_pr_decision` | `da00p1ljdthc73bmqaag` |

All three object types read back with `data_source.type=resource` and the expected Resource IDs.

## Blind benchmark

```json
{
  "benchmark": "third_party_behavioral_blind",
  "reference_answers_read": false,
  "question_cases_loaded": 3,
  "playbook_accuracy": 1.0,
  "passed": true
}
```

## Agent Interaction verification

A traceable read-only Interaction was completed through the authenticated POC CLI Context Loader:

- `conversation_id`: `conv_ebf77eb23300783b9bc396203ac4369`
- `interaction_id`: `int_164102eccbc4f239601ec1706b6e8d8a`
- Forecast object: `supply_ontology_hand_forecast`
- Product: `U00-000080`
- Matched instance: `id=0000023181`, quantity `3000`, due date `2026-05-31`, status `正常`
- Interaction: `completed`; `evidence_status=complete`

An earlier query through the in-app connector returned old/public resources. That was an environment-routing issue in the connector, not a POC data issue. Customer and ecosystem acceptance must verify the active KN ID and Catalog/Resource bindings first. If old resources are returned, stop the business test and correct routing.

This Interaction verified the forecast fact only. Fulfillment still requires the S1 evidence chain: finished-goods inventory, primary BOM materials, material inventory, purchasing/production plans, and delivery dates, with substitute usage explicitly disabled.

## S1 fulfillment evidence result

The same POC Context Loader then completed a read-only S1 Interaction:

- Forecast: `U00-000080` / `0000023181`, quantity `3000`, due `2026-05-31`, status normal.
- Product: object exists as “北斗车载智能终端系统”.
- BOM: five primary-material rows were found, all with `alt_priority=0`; substitutes were disabled.
- Finished-goods inventory: 61 available units were found in the queried records, insufficient to cover 3,000 units directly.
- Plans/purchasing: production records exist before the due date, but the snapshot does not prove that 3,000 units remain unconsumed and deliverable; some purchase orders have June/July 2026 delivery dates, after the target date.

S1 conclusion: **The evidence does not prove delivery of 3,000 units by 2026-05-31; treat the commitment as at risk and do not release it.** No Action was executed.
