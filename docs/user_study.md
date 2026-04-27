---
# User Study — FX Strategy Lab

## Overview
A think-aloud usability study was conducted with 4 participants to evaluate the system's usability and educational effectiveness. All sessions were conducted in person at the University of Leicester. Participants used a laptop to interact with the deployed application while being observed.

## Participants
Participant 1 was aged 21–24, a CS student with no trading experience, and rated satisfaction at 4/5. Participant 2 was aged 25–30, a finance student with basic trading knowledge, and rated satisfaction at 3/5. Participant 3 was aged 20–23, a beginner with no coding or trading experience, and rated satisfaction at 2/5. Participant 4 was aged 22–26, a junior developer with Python and data viz experience, and rated satisfaction at 5/5.

## Tasks
1. Load EUR/USD data, run MA Crossover strategy, report win rate.
2. Switch to RSI strategy, modify oversold threshold, compare runs in session summary.
3. Use SMA price cross strategy, interpret equity curve, explain forced exit.

## Task Completion Rates
Task 1 was completed by 4/4 participants (100%). Task 2 was completed by 3/4 participants (75%), while Task 3 was completed by 1/4 participants (25%).

## Key Usability Issues Found
1. Equity curve misread as price chart (2 participants) → added descriptive subtitle to chart
2. "Forced exit" terminology not understood → added tooltip/help text in UI
3. RSI parameter confusion (non-technical users) → added guidance text below sliders
4. Invalid date/interval combination returning no data → improved error message

## Key Positive Findings
- Task 1 100% completion confirms core workflow is intuitive
- Win rate and metrics described as easy to read (Participant 2)
- Tutor Mode explicitly praised: "The tutor/explanation mode actually helped a lot — without that I wouldn't fully get what's happening under the hood." (Participant 4)

## Participant Quotes
- Participant 1: "I thought the equity curve was just another price line at first."
- Participant 2: "What does forced exit mean? Is that like stop loss or something?"
- Participant 3: "I don't really get what RSI is doing or why I'd change the number. I was just guessing."
- Participant 4: "The tutor/explanation mode actually helped a lot."

## Improvements Implemented
All four usability issues above were addressed in the codebase following this study. See commit history for implementation details.

## Limitations
- Small sample (n=4); participants skewed towards students
- Long-term usage testing was not conducted; observation was limited to single sessions.
---
