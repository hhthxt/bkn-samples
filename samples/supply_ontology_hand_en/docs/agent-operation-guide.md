# Agent Operation Guide

## Goal

Use the Agent to import and bind the sample, verify capabilities, and answer a fulfillment commitment question.

## Recommended user question

Can product `U00-000080` be delivered by `2026-10-31` in a quantity of `3000`? The forecast number is `0000023181-FUTURE`; do not use substitute materials. Explain inventory, producible quantity, material shortages, and the evidence for the conclusion.

## Verification sequence

1. Confirm that the knowledge network and data sources are ready.
2. Find the fulfillment analysis Skill.
3. Retrieve forecast, product, inventory, BOM, production, and purchasing evidence.
4. Call the function that calculates the deliverable quantity.
5. Return the conclusion, evidence, and risks.
6. Show a dry-run and impact scope before any Action and wait for confirmation.
