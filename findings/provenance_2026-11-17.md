# Provenance card, 2026-11-17

Three of the five checks in protocol section 5 can be computed from published data; two cannot, and are marked as such.

## share concentration — computed

- board: robotwin
- models: 36
- top3_share_of_trials: 0.083
- reading: high share means the board is dominated by few sources; it does not by itself indicate gaming

## temporal clustering — computed

- board: robochallenge
- cells_with_timestamp: 769
- busiest_hour_utc: 2026-05-07T06
- cells_in_busiest_hour: 10
- cells_sharing_minute_with_another: 15
- reading: batch submission in a short window is a flag, not a verdict; a single sweep of a benchmark produces the same pattern

## pairwise consistency — computed

- board: robotwin
- pairs_with_shared_tasks: >=20 tasks
- fully_consistent_pairs: 192
- examples: [{'model_a': '4D-WAM', 'model_b': 'ACT', 'shared_tasks': 50, 'wins_a': 50}, {'model_a': '4D-WAM', 'model_b': 'DP', 'shared_tasks': 50, 'wins_a': 50}, {'model_a': '4D-WAM', 'model_b': 'FastWAM', 'shared_tasks': 50, 'wins_a': 50}, {'model_a': '4D-WAM', 'model_b': 'starVLA', 'shared_tasks': 50, 'wins_a': 50}, {'model_a': 'ACT', 'model_b': 'Abot-M0', 'shared_tasks': 50, 'wins_a': 0}, {'model_a': 'ACT', 'model_b': 'Awomo-0.6', 'shared_tasks': 50, 'wins_a': 0}, {'model_a': 'ACT', 'model_b': 'CloudRobo-WM', 'shared_tasks': 50, 'wins_a': 0}, {'model_a': 'ACT', 'model_b': 'CloudRobo-WM-Preview', 'shared_tasks': 50, 'wins_a': 0}, {'model_a': 'ACT', 'model_b': 'EWAM', 'shared_tasks': 50, 'wins_a': 0}, {'model_a': 'ACT', 'model_b': 'GO-3 Nano Preview', 'shared_tasks': 50, 'wins_a': 0}]
- reading: perfect consistency across many tasks is suspicious only when the tasks are heterogeneous; check task families before reading it

## selective submission — partial

- reason: submitted-vs-retained counts are published for RoboChallenge (32,980 benchmark episodes against 769 leaderboard cells) but attempt counts per cell are unstated, so the retention ratio cannot be normalised
- robochallenge_episodes_per_cell: 42.9

## contamination probe — not implemented

- reason: no perturbed task variant has been run; a probe without a positive control would produce an uninterpretable number
