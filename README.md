# Fix model training interval mismatch

## Background

Validation errors in `core_query_trigger_lambda` come from a **unit mismatch**: intervals were stored `schedules.interval` as if they were **seconds**, but the code treats those values as **minutes**. That broke validation and made schedules wrong. This affected **454 enabled models** across **519 schedules**.

**Bug fix / tracking:** [Azure DevOps work item #267692](https://mobius.visualstudio.com/Backstage/_backlogs/backlog/Team%2027%20-%20OptiGenie/Stories?System.AssignedTo=vincent_z%40optimove.com&System.IterationPath=%40currentIteration%2CBackstage%5CBacklog%2CBackstage%2CBackstage%5CBacklog%5CSprint%20230%2CBackstage%5CBacklog%5CSprint%20231%2CBackstage%5CBacklog%5CSprint%20232&workitem=267692)

## What this repo does

`update_intervals.py` aligns stored intervals with what the lambda expects (minutes) by reading a list of affected models and either updating DynamoDB or exporting current values after fixes.

## Fallback plan

If you need to put the **original** stored values back, you can: read **`interval_issues.json`** (it still has those values) and run the same update path as `update_intervals_for_affected_models()`, but **do not divide by 60**—write each model’s `interval` from the file straight into DynamoDB. That restores the pre-fix numbers (the seconds-style values the table had before).

## Prerequisites

- AWS access to read/update DynamoDB table **`core-hosted-models-ddtable`** in **`eu-west-1`**
- Python with **`boto3`**
- Input file **`interval_issues.json`** next to the script
