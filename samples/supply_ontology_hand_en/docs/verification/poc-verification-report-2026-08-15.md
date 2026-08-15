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

## Environment-routing boundary

One Context Loader business query was deliberately excluded from the POC pass result: the session returned public/old resource bindings and no row for forecast `0000023181`. Before customer or ecosystem acceptance, the Agent interface must first verify the active knowledge network and its Catalog/Resource bindings. If old resources are returned, stop the business test and correct environment routing.
