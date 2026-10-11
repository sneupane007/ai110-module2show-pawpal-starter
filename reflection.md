# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
1. Add a pet according to their name and kind
2. add tasks

- What classes did you include, and what responsibilities did you assign to each?
1. pet class
2. each pet get their own class that inherits from the pet class
3. each pet has their method of petting, taking care and so on
4. pettasks 
5. Each pet task takes pet into consideration and shows only the relavant pet/taking care methods in the dropdown

**b. Design changes**

- Did your design change during implementation?
Yes. After turning the UML into a class skeleton, I reviewed it for missing relationships and bottlenecks and revised the design. A few more changes came up once I implemented the logic.
- If yes, describe at least one change and why you made it.
1. Added a `SkippedTask` class (task, pet, reason). The scheduler needs to explain why a task was left out, and a plain list of tasks could not carry a reason.
2. `Owner.get_all_tasks()` now returns (pet, task) pairs instead of just tasks. A task did not know which pet it belonged to, so the scheduler could not build a `ScheduledTask` from a flattened list.
3. Times are stored as minutes since midnight instead of `"08:00"` strings. Strings are awkward for arithmetic, overlap checks, and sorting.
4. Replaced `_detect_conflicts` with `_place_task`, which puts each task in the earliest free slot at or after its preferred time. Avoiding overlaps while placing is simpler than detecting them afterward. My first version used a single moving time cursor, but a high-priority task preferred at midday would have pushed every earlier-preferred task past it, so I switched to scanning for free gaps.
5. `Task` compares by identity (`eq=False`) so two identical-looking tasks stay distinct and `remove_task` cannot delete the wrong one.
6. `Pet.add_task` now rejects task types that are not allowed for that species (a cat cannot get a "walk"). The original design only filtered the dropdown, which does not protect the data. The scheduler also checks this and skips with a reason as a safety net.
7. Added a `frequency` field to `Task` (once, daily, weekly) because the project spec lists it. It is stored but the scheduler does not use it yet.
8. `DailyPlan.explain()` takes `available_minutes` so the summary can show time used against the budget, and `_place_task` takes `(task, plan)` instead of a cursor.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
The scheduler treats a task's preferred time as a soft preference and resolves overlaps by shifting, not by refusing. Tasks are placed greedily, highest priority first, each in the earliest free slot at or after its preferred time. If two tasks want overlapping times, the lower-priority one is quietly pushed later, and `find_conflicts` only returns a warning string for the overlap. It never changes the plan. The cost is that the greedy pass is not optimal: a high-priority task can take a slot that would have let two smaller tasks both keep their preferred times, and a task shifted away from its preferred time (a feeding moved from 08:10 to 08:30) may not be what the owner wanted.
- Why is that tradeoff reasonable for this scenario?
A pet owner's day has a handful of tasks, and a plan that always exists and explains itself is more useful than a perfect one. Medication and feeding (high priority) get their times first, and the "Why" lines and conflict warnings tell the owner exactly what moved. Finding an optimal arrangement would mean searching over orderings, which is hard to explain to the owner and not worth it at this size. Failing on a conflict would leave the owner with no schedule at all.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
