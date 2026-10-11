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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
