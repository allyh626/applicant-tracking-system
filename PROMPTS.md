# PROMPTS.md — AI Usage Log

This file is the record of AI use on this codebase. At the end of every
agent session, direct the agent to write the session log with this prompt:

> Append a session log to PROMPTS.md at the repo root, under today's date,
> newest entry at the top. Record every prompt I gave you this session, in
> order, including any corrections. End the entry with a short summary:
> the outcome, any places where I deviated from a recommended answer or
> asked follow-up questions, and anything that went sideways.

Two rules:

- Entries are added only by that prompt, never unprompted.
- New entries go at the top. Never rewrite or delete an old entry — the
  log is part of your work, and an honest log of a session that went
  sideways is worth more than a tidy one.

Each entry has this shape:

    ## YYYY-MM-DD — <one-line summary>

    ### Prompts
    1. ...

    ### Summary
    - **Outcome:** what was built and what was kept
    - **Deviations:** recommendations overridden, follow-up questions asked
    - **Sideways:** failures, wrong turns, and how they were caught

## 2026-11-02 — Grill-me design interview; stage-pipeline and dashboard prototypes

(Session started 2026-11-01 and continued into 2026-11-02.)

### Prompts
1. `/grill-me` The applicant tracking system application has a required
   technology stack which includes Python, Django, SQLite, UV, Tailwind CSS
   with DaisyUI, using django-tailwind-cli, HTMX, Ruff, and automated tests
   using djangos built in testing framework or pytest. This is an internal
   hiring system used solely by employees. Staff need to keep track of
   candidates and their info, including if candidates came form the company
   website, job boards, referrals, or other outside sources. Staff should be
   able to open and close job openings. Applications are sent through a
   defined hiring process in this order: Applied, Screening, Interview, Final
   Review, Offer, Hired, Rejected, and Withdrawn. Moving a customer from one
   stage in the hiring process to the next should not reload the entire
   page. The system should keep track of required skills associated with
   each job opening, one skill can belong to many openings. Management
   decisions of candidate records over time is still undecided(when they
   should be edited, archived, deactivated, or removed). Behavior of existing
   job applications under a job opening that has closed is still undecided.
2. Q1 (separate Candidate and Application models?): a
3. Q2 (source on Candidate or Application?): a
4. Q3 (how source values are stored): yes i like a
5. Q4 (preventing duplicate candidates): i like a
6. Q5 (job opening open/closed field): yes i like a
7. Q6 (new applications on closed openings): yes i like a
8. Q7 (existing applications when an opening closes): a
9. Q8 (allowed stage moves): yes a
10. Q9 (stage-change history): yeah i like option b
11. Q10 (login and permissions): yes a
12. Q11 (skills on openings only, or candidates too?): yes a
13. Q12 (how skills get created): yes i like a
14. Q13 (candidate edit/archive/delete): yes a
15. Q14 (archiving a candidate with active applications): yes a
16. Q15 (one application per candidate per opening?): a
17. Q16 (where stage moves happen in the UI): i like a the most
18. Q17 (pytest or Django test framework): a
19. Q18 (one Django app or several): yes a
20. Q19 (candidate fields and resumes): a
21. Q20 (job opening fields): yes a
22. Q21 (list page search and filtering): a is good
23. can you prototype some of the skills weve decided on?
    *(The agent started the prototype skill and tried to read the skill's
    files; I rejected that tool call and interrupted.)*
24. `/prototype` can you prototype the system for moving applications
    throughout the hiring process in this system?
25. when i advance an applicant to the next stage the updated time changes,
    is that incorrect implementation?
26. okay yes i misunderstood what number to look at
27. yes rename the column and add the note
28. okay thank you `/prototype` can you now prototype the ui dashboard
29. okay thank you this prototype works as it should
30. thank you, can you append PROMPTS.md to show this sessions changes with
    the grill me interview and implemented prototypes?

### Summary
- **Outcome:** The 21-question grill-me interview settled the design.
  - **Models:** five models in a single `hiring` app (Candidate, JobOpening,
    Skill, Application, StageChange). Candidates have a unique email, a
    fixed-choice source plus a source-details field, an archive flag, and no
    resume upload. Openings have an `is_open` boolean and many-to-many
    required skills. Skill names are unique regardless of case. Each
    candidate can have only one application per opening.
  - **Rules:** stages move forward one step at a time, Reject and Withdraw
    are allowed from any active stage, and Hired/Rejected/Withdrawn are
    final. Every move is logged as a StageChange. Closed openings block new
    applications, but existing ones continue. Candidates can be edited any
    time and archived, but only once all their applications are final.
    Archived candidates get no new applications, and hard deletes happen
    only in the Django admin.
  - **App setup:** login is required, with no roles. Lists use basic GET
    search and filters. Tests use pytest with pytest-django.
  - **Prototypes:** two throwaway single-file prototypes (Django + HTMX +
    DaisyUI with in-memory data) were built in `prototypes/`:
    - `stage_pipeline.py`: the stage rules, HTMX row swaps, and a history
      log updated out-of-band. Includes a "Server-rule test" column and a
      `test` command that checks the rules.
    - `dashboard.py`: stat tiles, counts by stage, an openings table with an
      Open/Closed/All filter and an HTMX Close/Reopen that also updates the
      "Open openings" tile, a source breakdown, and recent stage changes.

    Both were checked with Ruff and Django's test client, and I confirmed
    in the browser that they work.
- **Deviations:** None. I accepted the recommended option on all 21
  questions; Q9's recommendation was B. I asked one follow-up question,
  about the "Updated" time changing, which was my misreading. That led to
  renaming the column to "Stage changed at" and adding a note under the
  page-load time.
  - The agent assumed, without asking separately, that archived candidates
    can't receive new applications; I didn't object.
  - The dashboard's sections weren't part of the design interview. The
    agent chose them and listed them as open choices.
  - The prototypes produced two decisions not yet in the design: refused
    stage moves return HTTP 200 with an inline error, and moved or closed
    rows stay visible under a filter until refresh.
- **Sideways:**
  - My first prototype request was interrupted when I rejected the agent's
    attempt to read the prototype skill's files. The skill had loaded with
    no instructions, so the agent used its own judgment from then on.
  - Ruff flagged the `# noqa: E402` comments as unused (RUF100); they were
    removed with `--fix`.
  - An inline Python smoke test failed because of PowerShell quoting; it was
    rerun from a script file in the scratchpad.
  - The dashboard's pre-rendered HTML fragments would have been
    auto-escaped. The agent caught this while reviewing its code, before
    running it, and fixed it with `mark_safe`.
