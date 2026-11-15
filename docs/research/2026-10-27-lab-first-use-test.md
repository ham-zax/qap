# Pair Rotation Lab — first-use test (2026-10-27)

Purpose: check that a person who has never seen QAP can use the Lab without help.
Run time: about 10 minutes per person. Run it with 2–3 people, one at a time.

## Setup

1. Start the workbench: `./scripts/start_workbench.sh`.
2. Open `http://localhost:5173` on the tester's device (desktop and one phone).
3. Say only: "This tool checks an idea about two coins on past prices. Please think out loud."
   Do not explain any screen. Do not answer "what does this mean?" during a task;
   write the question down and answer it after the test.

## Tasks (read each one aloud; do not show this page)

| # | Task | Success when the tester… |
|---|------|--------------------------|
| 1 | "What does this page help you find out?" | says, in own words, "if swapping between two coins beats just holding them" |
| 2 | "Check the idea for Solana and Ethereum." | picks SOL and ETH and presses **Run the test** |
| 3 | "Did swapping earn more than holding? By how much?" | reads the answer and the two end amounts correctly |
| 4 | "Can you trust this result for the future? Why?" | mentions past prices only, or the check period, or fees |
| 5 | "What does 'Gap returns to normal' mean?" | opens the reading and explains it in own words |
| 6 | "Try LINK and ETH." | reads the result, and says what to do next if costs are unknown |
| 7 | (phone) "Swap the two coins." | finds the swap button without scrolling sideways |

## Record per task

`task | success yes/no | time in seconds | words the tester used | question asked`

## Pass rule

The Lab passes when each task succeeds for at least 2 of 3 testers.
Any task that fails for 2 testers becomes a fix card in TASKS.md, with the
tester's own words as evidence.
