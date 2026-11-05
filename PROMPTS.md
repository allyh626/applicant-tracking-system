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

## 2026-11-04 — Phase 2 built: skills page

### Prompts
1. `/implement @prd/applicant-tracking-system.md
   @plans/applicant-tracking-system.md implement phase 2`
2. yes those are good behaviors for tdd
3. yes go ahead
4. yes i feel this implements the behavior, you can move on
5. yes go ahead
6. yes you can move onto the third behavior
7. yes go ahead
8. i feel it does both, you can complete the rest of the phase
9. okay i testd in the browser, you can update prompts.md and commit and
   push.

### Summary
- **Outcome:**
  - Phase 2 is built. Added the `Skill` model with a case-insensitive
    unique constraint on `Lower("name")`, names trimmed in `save()`, and
    alphabetical ordering that ignores capitalisation.
  - Added the `/skills/` page (list plus add form, redirect after a
    successful add), a Skills navbar link, and Skill in the admin.
  - The three TDD behaviors were: the database refuses "python" when
    "Python" exists, the skills form refuses "python" and " Python " with a
    form error instead of crashing, and spaces around a name are removed on
    save. Regular tests cover adding and listing, alphabetical order, blank
    names, the login requirement and adding a skill in the admin
    (18 tests in total).
  - Ruff check and format pass. The user checked the page in the browser.
- **Deviations:**
  - No recommendations were overridden and no follow-up questions were
    asked. The user approved each TDD step as proposed.
  - The agent turned off Ruff's RUF012 rule in `pyproject.toml` without
    asking, because it flags normal Django class attributes like
    `fields = [...]`.
- **Sideways:**
  - The alphabetical-order test failed at first: SQLite sorted "django"
    after "SQL". Fixed by ordering on the lowercased name.
  - The implement skill says to log, commit and push at the end, but
    CLAUDE.md says the user commits and asks for the log. The agent waited
    until the user asked.
  - The code review was done by the agent reading the changes itself, not
    with the separate code-review tool. It found no bugs and noted one
    small limit (names aren't trimmed during `full_clean()` before saving).

## 2026-11-04 — Phase 1 built: project skeleton and login gate

### Prompts
1. `/implement @prd/applicant-tracking-system.md
   @plans/applicant-tracking-system.md implement phase 1`
2. so a user will have to sign in on every page they visit?
3. okay yes those two behaviors are good
4. yes that looks right
5. yes i think it has been implemented, you can move onto behavior 2
6. yes it's implemented, go ahead and finish the phase
7. when i do #7 i did not get a 405 page
8. okay yes i see it returns a 405 error, can you update prompts.md then
   commit and push this phase to github?

### Summary
- **Outcome:**
  - Phase 1 is built. A uv project with Django 6.1.3 and the `hiring` app,
    django-tailwind-cli with DaisyUI (corporate theme, Tailwind CLI version
    pinned), HTMX 2.0.11 saved in `assets/js/`, Ruff, and pytest-django.
  - `LoginRequiredMiddleware` makes every page require login. Login and
    logout use Django's views under `/accounts/`, and logout is POST only.
  - Added a base layout (navbar, username, Log out button), a DaisyUI login
    page and a placeholder dashboard at `/`.
  - Tests: a shared `staff_client` fixture and 9 tests in
    `tests/test_auth.py`. The two TDD behaviors were "anonymous request to
    `/` redirects to login with `?next=/`" and "logout POST ends the session
    and returns to login". Other tests cover login returning you to the page
    you asked for, a wrong password, logout refusing GET, and an account
    created in the admin being able to log in.
  - Ruff check and format pass, and the README has setup and run steps.
- **Deviations:**
  - I asked whether users would have to sign in on every page. The agent
    explained that you sign in once, and the session cookie keeps you signed
    in (Django's default is 2 weeks) until you log out.
  - The implement skill says the agent writes PROMPTS.md, commits and
    pushes. The agent left those for me, following CLAUDE.md, until I asked
    in prompt 8.
- **Sideways:**
  - `uv init` found the `pyproject.toml` in the parent `CIDM3312` folder and
    added this project to that shared workspace, so the lock file and `.venv`
    landed outside the repo. The agent removed it from the parent's member
    list, re-ran `uv lock` there (it only removed the added packages), and
    recreated the project with `--no-workspace`.
  - The logout test passed the first time it ran, so it never went RED,
    because the setup work had already wired in the logout redirect. The
    agent removed `LOGOUT_REDIRECT_URL` for one run to show the test fails
    without it, then put it back.
  - PowerShell added a BOM to `settings.py` while doing that, and the agent
    removed it.
  - The first `ruff format` also reformatted the two prototypes. The agent
    restored them with git and excluded `prototypes/` from Ruff.
  - The agent dropped a "no sign-up page" test because it would pass no
    matter what (Django returns 404 for unknown URLs).
  - Manual step 7 (visit `/accounts/logout/` to see a 405) was written
    wrong. Step 6 had already logged me out, so the login gate redirected
    me to login instead. Django's 405 page is also blank. The corrected step
    is to log in first and check the status in the browser's Network tab.

## 2026-11-03 — Implementation plan written from the PRD

### Prompts
1. `/prd-to-plan prd/applicant-tracking-system.md — read HANDOFF.md first
   for context`
2. yes i was going to suggest combining phase 3 and 4
3. when i run the implement skill would i tell the agent to look at the plan
   and only do phase 1?
4. okay thank you can you append prompts.md with this session

### Summary
- **Outcome:**
  - The agent read `HANDOFF.md` and the PRD, and proposed shared decisions
    for every phase: one `hiring` app, numeric IDs in URLs,
    `LoginRequiredMiddleware` so every page requires login, a URL map, and
    the five models and how they connect.
  - It proposed 12 vertical-slice phases and asked whether that was the
    right size, suggesting 3+4 or 5+6 as possible merges.
  - Phases 3 and 4 were merged (candidates with their search and filter),
    and `plans/applicant-tracking-system.md` was written with 11 phases,
    each with user stories and an acceptance checklist. The PRD's testing
    list is spread across the phases, and each prototype is deleted in the
    phase that replaces it (`stage_pipeline.py` in Phase 8, `dashboard.py`
    in Phase 11).
  - The agent explained how to run `/implement` on one phase:
    `/implement @prd/applicant-tracking-system.md
    @plans/applicant-tracking-system.md implement phase 1`. It pointed out
    that the skill's last step commits and pushes, so I should say "don't
    commit or push" if I want to commit myself, and that Phase 1 may have
    few TDD candidates because it's mostly setup.
- **Deviations:**
  - The agent recommended keeping phases 3 and 4 separate, but I chose to
    merge them (I had already planned to suggest it). Phases 5 and 6 stayed
    separate.
  - I asked a follow-up question about how to scope `/implement` to one
    phase.
  - Two decisions were made by the agent without asking me: the dashboard's
    close/reopen buttons reuse the opening's close/reopen URLs (sending back
    just the row for HTMX requests), and "recent stage changes" uses a fixed
    limit chosen in Phase 10, since the PRD gives no number.
- **Sideways:** nothing went wrong this session.

## 2026-11-02 — PRD written from the design interview; handoff for planning

(Continues the same session as the entry below.)

### Prompts
1. should i delete these prototypes before moving foreward?
2. `/to-prd`
3. can you update PROMPTS.md with the prd creation youve implemented and
   create a handoff document so i can use the handoff skill to continue to
   make a plan from the prd

### Summary
- **Outcome:**
  - **Prototypes:** the agent recommended keeping `prototypes/` for now.
    Commit them along with the log, use them as a reference while building,
    and delete each one in the same commit as its real version.
  - **PRD:** `/to-prd` produced `prd/applicant-tracking-system.md`, built
    from the grill-me decisions and the confirmed prototypes. It has the
    problem and solution, 56 user stories, implementation decisions
    (models, stage rules, opening and archive rules, login, pages and HTMX
    behaviour, what to test), an out-of-scope list, and further notes.
  - **Handoff:** `HANDOFF.md` was written at the repo root so the next
    session can run `/prd-to-plan`.
- **Deviations:**
  - I didn't reply to the keep-or-delete recommendation; I moved straight
    on to `/to-prd`.
  - The handoff skill can only be started by the user, so the agent wrote
    `HANDOFF.md` by following that skill's instructions rather than
    invoking it.
- **Sideways:**
  - The PRD template says not to include file paths, but the PRD's Further
    Notes mention `PROMPTS.md` and the prototypes folder. These were kept
    as pointers rather than code locations.
  - The previous log entry couldn't be edited, so this one was added on top
    instead of amending it.

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
