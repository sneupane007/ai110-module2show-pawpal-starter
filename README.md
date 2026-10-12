# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## ✨ Features

- **Priority-first scheduling**: tasks are taken highest priority first, then by preferred time, and each is placed in the earliest free slot at or after its preferred time (greedy).
- **Time-budget and day-window limits**: a task that would exceed the owner's available minutes, or end after the day's end, is skipped with a reason instead of silently dropped.
- **Sorting by time**: `Scheduler.sort_by_time()` orders tasks by preferred time, earliest first, with untimed tasks last. The sort is stable.
- **Filtering**: `Scheduler.filter_tasks()` narrows tasks by pet name and/or completion status, and the result can be sorted.
- **Conflict warnings**: `Scheduler.find_conflicts()` returns one readable warning per overlapping pair (same pet or different pets) without raising or changing the plan.
- **Daily and weekly recurrence**: completing a `daily` or `weekly` task creates the next occurrence due tomorrow or in 7 days.
- **Species-aware tasks**: dogs, cats and other pets each allow different task types, enforced in `Pet.add_task` and in the scheduler.
- **Explainable plans**: every scheduled task carries a "why" (priority, at preferred time, or moved from preferred time), and skipped tasks carry a reason.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
====================================================
 Today's Schedule - Jordan
====================================================
 TIME          TASK               PET      PRIORITY  MIN
 --------------------------------------------------
 08:00-08:30   Morning walk       Mochi    HIGH       30
 08:30-08:40   Feeding            Luna     HIGH       10
 08:40-08:50   Feeding            Mochi    HIGH       10
 09:00-09:15   Brush fur          Luna     MEDIUM     15
 --------------------------------------------------
 Scheduled: 4 tasks, 65 of 90 min used

 Why:
   - Morning walk (Mochi): high priority, at preferred time 08:00
   - Feeding (Luna): high priority, moved from preferred 08:10
   - Feeding (Mochi): high priority, moved from preferred 08:30
   - Brush fur (Luna): medium priority, at preferred time 09:00

 Skipped (1):
   - Play session (Mochi): not enough time left in the day
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite (after `pip install -r requirements.txt`):
python -m pytest
```

### What the tests cover

The suite lives in `tests/test_pawpal.py` and exercises the logic layer in `pawpal_system.py` (22 tests):

| Area | What is verified |
|------|------------------|
| Sorting | Tasks come back earliest first; untimed tasks go last; ties keep their original order; midnight (`00:00`) counts as a real time; an empty list works; the input list is not modified |
| Recurrence | Completing a daily task creates a pending copy due tomorrow and a weekly task one due in 7 days; a one-off task creates nothing; the copy keeps its title, priority, time and frequency but is a new object |
| Conflict detection | Overlapping windows are flagged across pets and within one pet; identical start times are flagged; three tasks at one time give three warnings; back-to-back, completed and untimed tasks are ignored |
| Filtering | Tasks can be filtered by pet name and completion status, alone or together |
| Plan generation | A pet with no tasks gives an empty plan; two tasks at the same time are both scheduled without overlapping; a task over the time budget is skipped with a reason |
| Basics | `mark_complete`, `add_task` and `parse_time` behave as expected |

### Test results

```
============================================= test session starts=============================================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0
rootdir: /Users/sujalneupane/Documents/codepath_ai/ai110-module2show-pawpal-starter
collected 22 items                                                                                            

tests/test_pawpal.py ......................                                                             [100%]

============================================= 22 passed in 0.02s==============================================
```

### Confidence Level: ⭐⭐⭐⭐⭐ (5/5)

All 22 tests pass, including the edge cases (empty pets, identical times, midnight, budget overflow). Not yet tested: recurrence across a month or year boundary (it depends on `date.today()`), completing the same recurring task twice, and the Streamlit UI in `app.py`.

## 📐 Smarter Scheduling

All times are stored as minutes since midnight (`parse_time("08:30") == 510`, `format_time(510) == "08:30"`). `main.py` demos every feature below.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` (wraps `sort_by_time`) | By preferred time, earliest first; unscheduled tasks last |
| Filtering | `Scheduler.filter_tasks()` (wraps `filter_tasks`) | By pet name and/or completion status |
| Conflict handling | `Scheduler.find_conflicts()` (wraps `find_conflicts`) | Warns on overlapping time windows; never crashes |
| Recurring tasks | `Task.mark_complete()`, `Pet.complete_task()`, `Scheduler.mark_task_complete()` | Daily = today + 1 day, weekly = today + 7 days |

### Sorting

`Scheduler.sort_by_time(pairs=None)` returns `(pet, task)` pairs ordered by `preferred_time`, earliest first.

- Tasks with no preferred time sort after every timed task.
- The sort is stable, so ties keep the order they were added in.
- With no argument it sorts all of the owner's tasks. Pass a list (for example the result of `filter_tasks`) to sort just that.
- Cost: O(n log n).

### Filtering

`Scheduler.filter_tasks(pet_name=None, completed=None)` returns `(pet, task)` pairs.

- `pet_name="Mochi"` keeps only that pet's tasks; `None` keeps every pet.
- `completed=False` keeps pending tasks, `True` keeps finished ones, `None` keeps both.
- The two filters combine, and the result feeds straight into `sort_by_time`.

```python
scheduler.sort_by_time(scheduler.filter_tasks("Luna", completed=False))
```

### Conflict detection

`Scheduler.find_conflicts()` returns a list of warning strings, one per overlapping pair. It does not raise and does not change the plan.

- A task's window is `[preferred_time, preferred_time + duration)`. Two tasks conflict when each starts before the other ends.
- Same start time conflicts, partial overlap conflicts, and back-to-back tasks (08:00-08:30, 08:30-08:40) do not.
- Each warning is labelled `same pet` or `different pets`.
- Completed tasks and tasks with no preferred time are ignored.
- It compares what the owner asked for. `generate_plan()` still resolves overlaps by moving the lower-priority task to the next free slot, with the reason shown in the plan's "Why" section.
- Cost: O(n²) pairwise comparison, which is fine for a day of pet-care tasks.

```
Conflict (same pet): Morning walk (Mochi) 08:00-08:30 overlaps Training (Mochi) 08:00-08:15
```

### Recurring tasks

`Task.frequency` is `"once"`, `"daily"`, or `"weekly"`.

- `Task.mark_complete()` marks the task done and returns the next occurrence: a copy that is not completed, due `date.today() + timedelta(days=1)` for daily or `+ timedelta(days=7)` for weekly. A `"once"` task returns `None`.
- `Pet.complete_task(task)` does that and adds the new task to the pet. `Scheduler.mark_task_complete(pet, task)` is the same call from the scheduler.
- The completed task stays in the pet's list, so a recurring task leaves one done copy and one pending copy.
- The next due date is counted from today, not from the old due date, so a task finished late is not scheduled in the past.

## 📸 Demo Walkthrough

### The Streamlit app (`streamlit run app.py`)

The app has three tabs.

| Tab | What you can do |
|-----|-----------------|
| **1. Setup** | Set the owner name and minutes available today; add pets (dog, cat, other). A table lists each pet and its task count. |
| **2. Tasks** | Add a task to a pet (type list depends on species, duration, priority, optional preferred time, repeats once/daily/weekly); mark a task done; filter by pet and status; view the sorted task table. |
| **3. Schedule** | Generate today's plan and read the time slots, the "Why" for each, and any skipped tasks. |

**Example workflow**

1. In **Setup**, add a dog named Mochi and a cat named Luna, and set 90 minutes available.
2. In **Tasks**, add "Morning walk" for Mochi (high, 30 min, preferred 08:00) and "Litter box" for Luna (medium, 10 min, preferred 08:00).
3. A warning appears right away: `Conflict (different pets): Morning walk (Mochi) 08:00-08:30 overlaps Litter box (Luna) 08:00-08:10`.
4. Add a daily "Meds" task for Mochi, then mark it done. The app confirms the next occurrence is due tomorrow.
5. Use the pet and status filters to see only Luna's pending tasks; the table stays sorted by time.
6. In **Schedule**, click *Generate schedule*. The walk keeps 08:00, and the litter box is shown as "moved from preferred 08:00".

**Scheduler behaviors visible in the UI**

- **Sorting**: the task table is ordered by preferred time, and tasks without a time appear last.
- **Conflict warnings**: each overlapping pair gets its own `st.warning` naming both tasks, both pets and both time windows, plus a note on what the scheduler will do (move the lower-priority task to the next free slot). They appear in the Tasks tab as soon as you add a task, so you can fix a clash before generating a plan.
- **Filtering**: pet and status filters narrow the table without changing the data.
- **Recurrence**: finishing a daily or weekly task shows its next due date and adds a new pending copy.
- **Explained plan**: the Schedule table has a Why column, and skipped tasks list their reason.

### CLI demo (`python main.py`)

```

As added (out of order):
  --:--  Play session   Mochi  [todo]
  08:30  Feeding        Mochi  [todo]
  --:--  Meds           Mochi  [todo]
  08:00  Morning walk   Mochi  [todo]
  08:00  Training       Mochi  [todo]
  09:00  Brush fur      Luna   [todo]
  08:10  Feeding        Luna   [todo]
  08:00  Litter box     Luna   [todo]

Sorted by time:
  08:00  Morning walk   Mochi  [todo]
  08:00  Training       Mochi  [todo]
  08:00  Litter box     Luna   [todo]
  08:10  Feeding        Luna   [todo]
  08:30  Feeding        Mochi  [todo]
  09:00  Brush fur      Luna   [todo]
  --:--  Play session   Mochi  [todo]
  --:--  Meds           Mochi  [todo]

Completed 'Meds' (daily); next occurrence due 2026-10-12
Completed 'Bath' (weekly); next occurrence due 2026-10-18

Mochi only:
  --:--  Play session   Mochi  [todo]
  08:30  Feeding        Mochi  [todo]
  --:--  Meds           Mochi  [done]
  08:00  Morning walk   Mochi  [todo]
  08:00  Training       Mochi  [todo]
  --:--  Meds           Mochi  [todo]
  --:--  Bath           Mochi  [done]
  --:--  Bath           Mochi  [todo]

Completed:
  --:--  Meds           Mochi  [done]
  --:--  Bath           Mochi  [done]

Luna, pending, by time:
  08:00  Litter box     Luna   [todo]
  08:10  Feeding        Luna   [todo]
  09:00  Brush fur      Luna   [todo]

Conflicts:
  ! Conflict (same pet): Morning walk (Mochi) 08:00-08:30 overlaps Training (Mochi) 08:00-08:15
  ! Conflict (different pets): Morning walk (Mochi) 08:00-08:30 overlaps Feeding (Luna) 08:10-08:20
  ! Conflict (different pets): Morning walk (Mochi) 08:00-08:30 overlaps Litter box (Luna) 08:00-08:10
  ! Conflict (different pets): Training (Mochi) 08:00-08:15 overlaps Feeding (Luna) 08:10-08:20
  ! Conflict (different pets): Training (Mochi) 08:00-08:15 overlaps Litter box (Luna) 08:00-08:10

====================================================
 Today's Schedule - Jordan
====================================================
 TIME          TASK               PET      PRIORITY  MIN
 --------------------------------------------------
 08:00-08:30   Morning walk       Mochi    HIGH       30
 08:30-08:40   Feeding            Luna     HIGH       10
 08:40-08:50   Feeding            Mochi    HIGH       10
 08:50-08:55   Meds               Mochi    HIGH        5
 08:55-09:10   Training           Mochi    MEDIUM     15
 09:10-09:20   Litter box         Luna     MEDIUM     10
 --------------------------------------------------
 Scheduled: 6 tasks, 80 of 90 min used

 Why:
   - Morning walk (Mochi): high priority, at preferred time 08:00
   - Feeding (Luna): high priority, moved from preferred 08:10
   - Feeding (Mochi): high priority, moved from preferred 08:30
   - Meds (Mochi): high priority, earliest open slot
   - Training (Mochi): medium priority, moved from preferred 08:00
   - Litter box (Luna): medium priority, moved from preferred 08:00

 Skipped (5):
   - Meds (Mochi): already completed
   - Bath (Mochi): already completed
   - Brush fur (Luna): not enough time left in the day
   - Bath (Mochi): not enough time left in the day
   - Play session (Mochi): not enough time left in the day
```
