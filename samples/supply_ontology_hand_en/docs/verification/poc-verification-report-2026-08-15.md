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
| Function Toolbox | Published; `backward_plan` tool `91565dd5-7df6-4d94-8e7a-2172488b6de5`, enabled |

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

## Skill Registry POC status

The future forecast scenarios are present in POC: `0000023181-FUTURE` is 3,000 units due 2026-10-31; `0000023181-SHORT` is 6,000 units due 2026-11-30.

During `find_skills` validation, the POC object class `skills` was found with a null `data_source`, so recall failed. The sample now includes:

1. `datasets/postgres/002_skill_registry.sql`
2. `tools/setup_skill_dataset.py` to create and idempotently seed the registry from published Skills in the current environment
3. `tools/bind_skill_dataset.py` to bind `skills` to the discovered Resource
4. Matching English/Chinese tests and Agent/manual documentation

The supplemental POC step is now complete: Resource ID `da01diljdthc73bmqf10` is bound to object class `skills`, with `object_type_ids`, `skill_query`, and the other physical mappings exposed. A traceable Context Loader Interaction successfully recalled three published Skills: S1, S2, and S3. Skill Registry is now counted as passed for the POC.

## Skill executable-contract check

We then read S1 through the POC Context Loader and attempted to validate the `execute_skill` contract. The platform requires `entry_shell` to be explicitly declared by `SKILL.md`; S1 currently declares that the Toolbox `backward_plan` should be preferred, but declares no `entry_shell`. The managed Interaction was therefore closed as `failed`. No offline CLI fallback, fabricated entry, or business Action was executed.

This is an execution-entry distinction, not a lack of function support: the POC function Toolbox is published and `backward_plan` is enabled. `execute_skill` is for Skills with an explicit `entry_shell`; the Context Loader MCP catalog is separate from the Toolbox catalog. S1 should be orchestrated by the third-party Agent, which submits `resolved_context` and business parameters through the OpenBKN Toolbox Tool interface.

## Function Toolbox online-call result

We followed the correct path and attempted a real call in one managed Interaction. The Agent assembled `forecast=1`, `bom=5`, `material=6`, `inventory=15`, `purchase_order=6`, `purchase_request=28`, and `mrp=8` rows, then invoked the enabled `backward_plan` tool. The call did not enter function execution because the POC platform returned:

```text
dial tcp: lookup host.docker.internal on 10.96.0.10:53: no such host
```

Conclusion: the Agent → OpenBKN Execution Factory REST Proxy → Function Toolbox path, request contract, and Agent orchestration are wired correctly. The blocker is downstream forwarding: the Toolbox `service_url` cannot be resolved from the POC platform container. An administrator must configure a POC-reachable HTTPS/service address or deploy the function service into a network reachable by POC; the Agent and business user do not need to know that backend address.
