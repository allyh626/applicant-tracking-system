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

## 2026-11-10 — Follow-up: ended sessions and failed requests on HTMX buttons

### Prompts
1. oh yes if you could fix that I forgot about that gap
2. i am trying to check #2, when i log out i go directly to the login page,
   i know this is what i wanted to happen in the app but dont underrstand
   what youre asking me to check in step two
3. okay, is there a message displayed when someones session times out? i
   dont remember seeing one, if there isn't could you display a message
   saying why they were logged out?
4. (Answer to "When should the message appear?") Session ended
   (Recommended)
5. update prompts.md and commit and push for me

### Summary
- **Outcome:**
  - Fixed the gap from the Phase 11 code review, for both the dashboard's
    Close/Reopen and the pipeline's stage buttons:
    - **Logged-out HTMX click:** `HtmxLoginRedirectMiddleware` turns the
      redirect to login into an `HX-Redirect`, so the whole login page
      loads, not a copy squeezed into the table row. `?next=` is the page
      the user was on (from `HX-Current-URL`), not the button's POST-only
      URL.
    - **Failed HTMX request:** `base.html` has a hidden error box. It shows
      the error code for 4xx/5xx responses, or "Couldn't reach the server"
      when there's no connection. It has a Dismiss button and clears on
      the next request that works.
  - Added a "Your session ended, so you were logged out" message on the
    login page (`SessionEndedMessageMiddleware`):
    - A `was_logged_in` cookie is set while logged in, and Log out removes
      it.
    - A request with the cookie but no login means the session ended
      without Log out, so the redirect to login carries the message, once.
      This covers links, refreshes and HTMX buttons.
  - Found along the way: no session timeout is configured, so Django's
    default keeps people logged in for 2 weeks. That was left unchanged.
  - 11 new tests in `test_htmx_errors.py` and `test_session_ended.py`. 289
    tests pass; ruff check and format are clean.
- **Deviations:**
  - The user asked a follow-up question about the manual test: logging out
    in the same tab goes straight to login. I explained the two-tab setup
    (log out in Tab B, click in the stale Tab A).
  - Asked one question: when the message should appear. The user picked
    the recommended option, "session ended" (marker cookie). The other
    options were "button clicks only" and "any login redirect" with a
    generic message.
- **Sideways:**
  - Two expected login URLs in my first tests were wrong: Django leaves
    `/` unescaped in `?next=`. I fixed the test expectations; the code was
    right.
  - The session-ended tests caught a real bug: the HTMX redirect built a
    new response and dropped the cookies carrying the message. It now
    keeps them.
  - Django's test client keeps a deleted cookie with an empty value, which
    made a logout look like an ended session. The middleware now checks
    for a value, not just the cookie's name.
  - Choosing the marker cookie means logging out in another tab no longer
    shows the message, on purpose. The manual check therefore deletes the
    `sessionid` cookie in developer tools. The user didn't report that
    browser check before asking to commit.

## 2026-11-10 — Phase 11 built: dashboard openings list with HTMX close/reopen

### Prompts
1. `/implement @prd/applicant-tracking-system.md
   @plans/applicant-tracking-system.md implement phase 11`
2. yes, those three look good
3. yes you can make it pass
4. yes you can do the third now
5. yes you can make it pass
6. yes you can
7. yes you can make it pass
8. yes you can move onto the rest of the phase
9. yes you can remove those mentions of the prototype
10. okay ive checked all the acceptance criteria in the plan, and they all
    pass youc an check akk the boxes
11. update prompts.md and commit and push for me

### Summary
- **Outcome:**
  - Phase 11 is built, which finishes the plan. The dashboard has a "Job
    openings" list:
    - Each row shows the title, department, location, required skills,
      active-application count and Open/Closed status, with a Pipeline
      link.
    - Open/Closed/All tabs set `?status=`, defaulting to Open. The
      Openings page still defaults to All.
    - Close (with a browser confirm saying existing applications continue
      as normal) and Reopen (no confirm) post with HTMX to the existing
      close/reopen endpoints.
  - For an HTMX request those endpoints return only the re-rendered row
    plus the "Open openings" tile out-of-band. Other requests still
    redirect to the detail page, as in Phase 5.
  - New partials: `dashboard_opening_row.html` and
    `open_openings_total.html`. The page and the HTMX response use the
    same templates and helpers (`with_active_counts`, `opening_totals`),
    so they can't disagree.
  - The Openings page's status filter became a shared helper,
    `filter_openings_by_status`, that takes each page's own choice list.
    The first choice is the default.
  - Three behaviors were built test-first: the Open default and status
    filter, each opening's active count, and the HTMX row plus
    out-of-band total. Three more tests cover the pipeline link, the
    confirm on Close only, and the empty-filter message.
  - `prototypes/dashboard.py` was deleted. That was the last prototype,
    so the prototype mentions in `CLAUDE.md` and the Ruff exclude in
    `pyproject.toml` were removed too.
  - 278 tests pass; ruff check and format are clean. Every acceptance
    criterion in the plan is ticked.
- **Deviations:**
  - None. Every TDD test and step was approved as proposed.
  - Removing the prototype mentions was my suggestion, and the user
    agreed.
- **Sideways:**
  - Adding the active count made Django drop the model's alphabetical
    ordering, because grouped queries skip `Meta.ordering`. The new filter
    test caught it, and the helper now re-applies the model's ordering.
  - My first confirm-button test had two muddled assertions. I replaced
    them with exact URL checks before moving on.
  - Ruff flagged one test line as too long; it was split.
  - Code review raised 8 points. Two were fixed: the filter now checks the
    dashboard's own choices, and close/reopen no longer loads the opening
    twice. Four were left as they are: the PRD rule that a row stays until
    refresh, pagination being out of scope, the redirect already being
    tested in Phase 5, and HTMX callers that only future phases might add.
  - Follow-up, not fixed: an expired session or a server error during an
    HTMX click shows nothing clear. The Phase 7 pipeline buttons have the
    same gap, so both should be fixed together.
  - No browser tool was available in this session. The user checked the
    HTMX swap and the confirm box in the browser before the last box was
    ticked.

## 2026-11-08 — Phase 10 built: dashboard overview

### Prompts
1. `/implement @prd/applicant-tracking-system.md
   @plans/applicant-tracking-system.md implement phase 10`
2. i think those are good yes
3. yes that test looks right, go ahead
4. yes you can start the second behavior
5. yes that test looks right, go ahead
6. yes you can start the third behavior
7. yes that test looks right, go ahead
8. yes go ahead with the rest of the phase
9. ok let me know when the review is done
10. yes ive confirmed the stage in the browser, you can update prompts.md

### Summary
- **Outcome:**
  - Phase 10 is built. The placeholder home page is now the read-only
    dashboard:
    - Four stat tiles: open openings out of the total, active
      applications, Hired, and active candidates with the archived count.
    - A box for each of the eight stages, in order and including zeros.
      Hired, Rejected and Withdrawn are shaded and faded.
    - A count of active (non-archived) candidates for each source, every
      source shown even at zero.
    - The 10 most recent stage changes, newest first, each with the
      candidate, the opening, from → to, the user and how long ago.
  - The history entry template (`partials/stage_change_item.html`) gained
    a `show_opening` option for the dashboard, so the pipeline and detail
    pages are unchanged.
  - Three behaviors were built test-first: the totals for a known set of
    data, the eight stage counts in order including zeros, and the source
    counts leaving out archived candidates. Five more tests cover the
    tiles on the page, the final-stage styling, the newest-first limit,
    a recent change's contents and an empty database. Landing on the
    dashboard after login was already tested in Phase 1.
  - 267 tests pass; ruff check and format are clean; no migrations were
    needed. The page makes 7 queries whatever the amount of data. The user
    checked the phase in the browser, and all 5 Phase 10 criteria were
    ticked in the plan. `prototypes/dashboard.py` stays until Phase 11, as
    the plan says.
- **Deviations:**
  - No recommendations were overridden, and no questions were asked.
  - The PRD gives no limit for recent changes, so 10 was chosen
    (`DASHBOARD_RECENT_CHANGES_LIMIT`; the pipeline page shows 20).
- **Sideways:**
  - The first template draft made the candidate name in each history
    entry a link. That would also have changed the pipeline page, outside
    this phase, so it was reverted before any test ran.
  - Ruff found an import-block blank line and a long test line; both were
    fixed with `ruff check --fix` and `ruff format`.
  - The code review found no bugs. Fixed: the active and Hired totals now
    come from the per-stage counts (so they can't disagree with the stage
    boxes), the opening and candidate totals use one query each (11
    queries down to 7), the page test now checks all four tiles instead of
    two, the "+ 0 archived" wording became "0 archived", and the partial's
    comment notes that `hide_candidate` also hides `show_opening`. Kept on
    purpose: the `stage`/`source` keys the tests read, so the tests don't
    depend on display labels.

## 2026-11-08 — Phase 9 built: archive and restore candidates

### Prompts
1. `/implement @prd/applicant-tracking-system.md
   @plans/applicant-tracking-system.md implement phase 9`
2. yes those are good behaviors
3. yes, make it pass
4. yes, move on to behavior 2
5. yes, make it pass
6. yes, move on to behavior 3
7. yes you can make it pass
8. yes you can continue the phase
9. can you give me the exact link to test number eight i eep getting a 404
10. okay i tested this in the browser and it works as should
11. add the PROMPTS.md entry, then commit and push

### Summary
- **Outcome:**
  - Phase 9 is built. `Candidate.archive()` refuses, raising
    `ArchiveError` and changing nothing, while any application isn't
    Hired, Rejected or Withdrawn. The message says to "first reject or
    withdraw their N active application(s)". `restore()` clears the flag.
    A new `FINAL_STAGES` list is built from `ALLOWED_MOVES`, so "final"
    is still defined in one place.
  - New POST-only URLs: `/candidates/<pk>/archive/` and
    `/candidates/<pk>/restore/`. They redirect to the candidate page with
    a success, error or "already archived/active" message. `base.html`
    now shows Django messages on every page.
  - The candidate page has Archive/Restore buttons, an Archived badge and
    notice, and hides "Add application" while the candidate is archived
    (Edit stays). The list hides archived candidates unless
    `?archived=1` ("Show archived" checkbox), which combines with search
    and the source filter. The application form leaves archived
    candidates out, and a crafted POST with one is refused under the
    Candidate field.
  - In the Django admin, archiving follows the same active-applications
    rule (a custom admin form), and restoring is allowed.
  - Three behaviors were built test-first: the archive refusal/success
    rule, the show-archived toggle with the other filters, and refusing
    an archived candidate in the application form (12 test cases). 23
    more cases cover restore, POST-only, 404, login, buttons, badges,
    empty-list wording, editing while archived, repeat clicks and the
    admin.
  - 259 tests pass; ruff check and format are clean; no migration was
    needed (the `archived` field already existed). The user checked the
    phase in the browser, and all 6 Phase 9 criteria were ticked in the
    plan.
- **Deviations:**
  - No recommendations were overridden.
  - The user asked for the exact link for browser check 8 (a GET to the
    archive URL) after getting a 404. The real candidate IDs were listed
    from the dev database, and the link given was
    `http://127.0.0.1:8000/candidates/1/archive/`. The steps had shown
    `<id>` as a placeholder, and there is no candidate 2, so either would
    give a 404.
- **Sideways:**
  - Cycle 1's first message began "Reject or withdraw" with a capital R,
    so it failed the approved test's lowercase "reject or withdraw"
    check. The message was reworded rather than changing the approved
    test.
  - At first, `archived` was made read-only in the admin. The code review
    pointed out that this also blocked restoring there, so it was
    replaced with an admin form that refuses only archiving with active
    applications. The first admin test would also have passed on an
    invalid form; a check that the save went through (302) was added.
  - The review's other fixes: the "has archived" query now runs only when
    the list is empty, the no-matches hint mentions archived candidates
    only when some exist, and repeating archive/restore says "already …"
    instead of reporting a change. Three findings were left as they are,
    with reasons given: the admin can still add an application for an
    archived candidate (it already allows closed openings), a tiny
    archive-vs-new-application race (SQLite has no row locks), and an old
    `?candidate=` link to an archived person pre-fills nothing without
    saying why.
  - An early edit dropped a space in `views.py`, and `fields = "__all__"`
    tripped ruff's DJ007. `ruff format` fixed the first; the second was
    fixed by removing the admin form's `Meta`.

## 2026-11-08 — Phase 8 built: pipeline stage filter and application history page

### Prompts
1. `/implement @prd/applicant-tracking-system.md
   @plans/applicant-tracking-system.md implement phase
   8/openings/2/pipeline//implement @prd/applicant-tracking-system.md
   @plans/applicant-tracking-system.md implement phase 8` (pasted twice
   with a stray URL in between; read as "implement phase 8")
2. yes i agree with those behaviors for tdd
3. yes the test looks right, go ahead
4. yes, go ahead with the second behavior
5. yes the test looks right, go ahead
6. okay you can finish the phase
7. what is the exact url i use to test #5?
8. okay i have verified this phase in the broswer
9. yes can you update prompts.md and then commit and push?

### Summary
- **Outcome:**
  - Phase 8 is built. The pipeline page has a `?stage=` filter: a GET
    form with a stage dropdown, Filter and Clear. An unknown value shows
    every stage, like the other filters. A filter with no matches says
    "No applications at this stage." A row moved out of the filtered stage
    stays on screen until refresh, because the move only swaps that one
    row.
  - Added the application detail page at `/applications/<pk>/`: the
    candidate, the opening (marked if closed), the current stage and
    dates, and the full stage history oldest first, each entry with its
    user and exact time. Pipeline rows and the candidate page's
    applications list have a "History" link to it.
  - The history entry template (`partials/stage_change_item.html`) now
    takes `hide_candidate` and `exact_time` options, so the pipeline panel
    and the detail page share one template.
  - `prototypes/stage_pipeline.py` was deleted, and a tooltip in
    `prototypes/dashboard.py` that pointed to it was updated.
  - Two behaviors were built test-first: the stage filter, and the
    history in time order with user and timestamp. 10 more tests cover the
    dropdown, the empty filter, the moved row staying until refresh, links,
    404 and login.
  - 224 tests pass; ruff check and format are clean; no migrations were
    needed. The user checked the phase in the browser, and all 5 Phase 8
    criteria were ticked in the plan.
- **Deviations:**
  - No recommendations were overridden.
  - The user asked for the exact URL for verification step 5 (an unknown
    stage value): `http://127.0.0.1:8000/openings/2/pipeline/?stage=banana`.
- **Sideways:**
  - Cycle 2's first RED came from `str.index` raising `ValueError`, not an
    assertion. An `assert ... in html` was added before it, so it failed
    on an assertion as the TDD rules require, before the test was shown
    for approval.
  - The code review found five issues, and four were fixed: the moved-row
    test sent a header and an extra request the endpoint ignores, so it was
    rewritten to check the row-only swap target; a dropdown assertion
    checked the whole page instead of the stage `<select>`; the history
    entry markup was a copy of the existing partial; and the detail page
    had two links to the same pipeline. The fifth, about LF line endings,
    was a false alarm: the repo stores LF and `core.autocrlf` normalises
    them, and the diff showed only the changed lines.
  - A first dev-server smoke check failed because PowerShell 5.1's
    `Invoke-WebRequest` can't report redirects; it was redone with curl.
    Logged-out requests to the new pages redirected to login with `next`
    kept.

## 2026-11-07 — Phase 7 built: pipeline page with HTMX stage moves

### Prompts
1. `/implement @prd/applicant-tracking-system.md
   @plans/applicant-tracking-system.md implement phase 7`
2. (Answered a question dialog: chose "New stage_changed_at
   (Recommended)" for where the pipeline's "stage last changed" time comes
   from, which also approved the three TDD behaviors.)
3. yes that's good, make it pass
4. yes, go ahead with behavior 2
5. i like the behavior described but why is it not a true tdd test, are
   you not able to test it correctly as so?
6. yes could you make sure it fails before moving on?
7. yes, go ahead with behavior 3
8. yes you can make it pass
9. yes you can continue
10. yes make it pass now
11. okay you can continue with the rest of the phase
12. can you provide me with a pipline url
13. when logged out i am already on the login page by default no? in
    response to the tenth check for the broswer testing
14. i verified it in the browser and it works, tick the boxes
15. yes can you please update prompts.md for this session then commit and
    push

### Summary
- **Outcome:**
  - Phase 7 is built. Added the `StageChange` model (application, from
    stage, to stage, the user who made the move, and when) and a
    `stage_changed_at` field on Application (migration 0006). The
    migration fills `stage_changed_at` from `created_at` for applications
    that already exist.
  - The stage rules live in one table, `ALLOWED_MOVES`: one step forward,
    or Reject/Withdraw from any stage that isn't final; Hired, Rejected and
    Withdrawn allow nothing. `Application.move_to()` is the only way to
    change a stage. It checks the rule, then updates the stage and writes
    the `StageChange` in one transaction. The update only applies if the
    stage is still the one it checked, so two people moving the same
    application at once can't record two moves. A refused move raises
    `StageMoveError` and writes nothing.
  - Added the pipeline page at `/openings/<pk>/pipeline/` (candidate,
    stage badge, when the stage last changed, the stage buttons, and a
    "Recent stage changes" list) and the HTMX endpoint
    `/applications/<pk>/move/` (POST only). It returns just the row, plus
    the new history entry out-of-band inside a `<template>`. A refused move
    returns the row with the error inside it, with HTTP 200. Reject and
    Withdraw ask for confirmation. Closed openings' applications can still
    be moved.
  - The opening detail page and the openings list link to the pipeline.
    The application admin shows its stage history read-only, as an inline,
    so deleting a candidate in the admin can still cascade.
  - Three behaviors were built test-first: the full rule table (all 64
    from/to pairs), a move writes exactly one correct `StageChange`, and
    the move endpoint (a crafted refused move, then a successful move with
    the out-of-band entry, as two separate RED/GREEN steps). 17 more
    tests cover the buttons per stage, the confirmations, the page
    contents, closed openings, the concurrent move, POST-only, login, 404,
    links and the admin.
  - 212 tests pass; ruff check and format are clean. The user checked the
    phase in the browser, and all 10 Phase 7 criteria were ticked in the
    plan.
- **Deviations:**
  - No recommendations were overridden.
  - The user asked why the refused-move test wasn't a "true" TDD test. It
    passed as soon as it was written, because the rule check already ran
    before any write, so it never had a RED step. At the user's request
    the agent broke `move_to()` on purpose (writing history before the
    check), showed the test fail, then undid the break.
  - The user asked for a pipeline URL. The dev database had openings 1
    (closed) and 2 (open) but no applications, so the agent explained how
    to add some first.
  - The user asked about verification step 10, since logging out already
    shows the login page. The agent clarified that the step is to open a
    pipeline URL while logged out, and check the `?next=` redirect.
- **Sideways:**
  - Cycle 2's first RED was a `DoesNotExist` exception rather than an
    assertion failure, so the test was changed to count rows with an
    assertion before going on.
  - A normal-process test helper split the page on `</button>`, which
    lumped the navbar's Log out button in with the first stage button. It
    was replaced with a regex.
  - Ruff flagged `zip()` over successive pairs (RUF007), so the table
    uses `itertools.pairwise`, and two lines were reformatted.
  - The code review found eight issues, and five were fixed: the
    migration would have stamped every existing application with the
    migration time, the concurrent-move path reloaded every field and
    dropped the cached candidate, a timestamp test could sometimes fail on
    Windows, the out-of-band entry sat in a bare `<div>` after a `<tr>`
    (now in a `<template>`, after checking HTMX 2.0.11 supports that), and
    the three buttons repeated their HTMX attributes. The migration had
    already been applied to the dev database (with no applications), so it
    was rolled back and applied again.

## 2026-11-06 — Phase 6 built: create applications

### Prompts
1. `/implement @prd/applicant-tracking-system.md
   @plans/applicant-tracking-system.md implement phase 6`
2. go ahead with those three
3. yes that is good
4. yes
5. no that wording is good you can continue
6. yes, go ahead with behavior 3
7. yes that's good, make it pass
8. yes, continue with the rest of phase 6
9. do i need to apply migrations before manually verifying in the browser?
10. okay i verified this in the browser and it works as should. can you
    verify all the acceptance criteria mentioned in the plan  has been
    accurately implemented ?
11. can you check those off for phase six in the plan then? and can you
    verify the acceptance criteria for all the previous phases have been
    correctly implemented?
12. yes, tick those boxes too
13. can you check each acceptance criteria as the phase is being finished
    before prompts.md is updated? i would also like for you to update the
    prompts.md file for this session as well as commit and push for me as
    for every phase in the future whenever I ask.

### Summary
- **Outcome:**
  - Phase 6 is built. Added the `Application` model (migration 0005): FKs
    to Candidate and JobOpening (both cascade on delete), a stage with the
    eight fixed choices that defaults to Applied, timestamps, and a
    database constraint allowing one application per candidate and opening.
  - Added `/applications/new/`. Its opening dropdown offers only open
    openings, so a closed one sent anyway is refused with a message saying
    the opening is closed. A duplicate pair is refused with "<name> has
    already applied to <opening>.", set on the model so the admin shows it
    too. Choices show the candidate's email and the opening's department
    and location.
  - Candidate and open-opening pages have an Add application button that
    pre-selects that candidate or opening (`?candidate=` / `?opening=`).
    The candidate page now lists their applications with a stage badge.
    Application is in the admin with the stage read-only, so stages can
    only change through the Phase 7 pipeline.
  - Three behaviors were built test-first: a crafted POST with a closed
    opening is refused, a duplicate application is refused with a clear
    message, and a new application starts at Applied and shows on the
    candidate page. 17 more tests cover the dropdown, the database
    constraint, the pre-select, empty states, the admin and login.
  - 124 tests pass; ruff check and format are clean.
  - All acceptance criteria for Phases 1-6 were checked against the code,
    the tests and a short run of the real dev server (CSS and HTMX load),
    and ticked in the plan. Nothing was missing.
- **Deviations:**
  - No recommendations were overridden.
  - The user asked whether migrations had to be applied before checking
    in the browser. Yes: 0005 wasn't applied to the dev database.
  - The user asked for every plan criterion to be verified, for Phases 1-5
    as well as 6, and the boxes ticked. From now on, each phase's criteria
    are ticked before the PROMPTS.md entry, and the agent commits and
    pushes when asked.
  - Two things were left for later: archived candidates can still be
    chosen (Phase 9), and the Django admin can still add an application
    to a closed opening (the PRD only requires the app's form to refuse
    it).
- **Sideways:**
  - The candidate page first said "Applied <date>" under each
    application, which would have made test 3's `"Applied" in html` check
    pass even with a wrong stage. It was reworded to "Created <date>".
  - A normal-process test posted an empty body, which Django treats as an
    unsubmitted form, so it saw no errors. The test was changed to send
    blank fields, like a browser does.
  - The agent's own review found that `?candidate=²` would crash the form
    with a 500 error (`isdigit()` accepts "²" but `int()` can't read it).
    The check was changed to `isdecimal()` and the case added to a test.
  - Ruff flagged an en dash in a comment (RUF003) and one line to
    reformat; both were fixed.
  - The implement skill says to commit and push, but CLAUDE.md says to
    wait until the user asks, so the agent waited. The user asked at the
    end.

## 2026-11-06 — Phase 5 built: close and reopen openings, and the openings filter

### Prompts
1. `/implement @prd/applicant-tracking-system.md
   @plans/applicant-tracking-system.md implement phase 5`
2. (Answer to the agent's question on the openings list default) All
   (Recommended)
3. yes those are good tdd behaviors
4. yes thats good
5. yes you can move to the next
6. yes go ahead
7. yes you can do behavior three now
8. yes go ahead
9. yes you can finish the rest of the phase
10. ive checked in the browser and everything does as it should. When the
    405 "Method Not Allowed" page is loaded there is jsut a blank screen, I
    would like for htis to be more user friendly. I believe I had an issue
    with this in a previous step but did not implement changes towards a
    solution.
11. (Answer to the agent's question on the 405 page) Friendly 405 page
    (Recommended)
12. okay looks good, can you update prompts.md and commit and push this
    phase?

### Summary
- **Outcome:**
  - Phase 5 is built. Added POST-only `/openings/<pk>/close/` and
    `/openings/<pk>/reopen/` URLs that only flip the open/closed flag and
    redirect to the detail page. No migration was needed.
  - The opening detail page shows Close (which opens a DaisyUI confirmation
    dialog saying existing applications will continue as normal) or Reopen
    (no confirmation). The openings list has a Status filter
    (`?status=open|closed|all`) that defaults to All; an unknown value also
    means All, like the candidate source filter.
  - Three behaviors were built test-first: close and reopen flip the flag,
    a GET to either is refused with 405 and changes nothing, and the status
    filter. 15 more tests cover the confirmation text, which button shows,
    status badges, the filter form, the empty-filter message, 404s and
    login.
  - Added a project-wide middleware (`config/middleware.py`) and
    `templates/405.html` so a GET to any POST-only URL (close/reopen,
    logout, and later phases' actions) shows a styled page instead of a
    blank one. It keeps the 405 status and skips HTMX requests. 4 tests.
  - 104 tests pass; ruff check and format are clean.
- **Deviations:**
  - Asked whether the openings list should default to All or Open (the PRD
    only fixes the dashboard's default); the user chose All.
  - After checking in the browser, the user asked for a friendlier 405
    page, which was not in the plan. They had hit the same blank page with
    logout in Phase 1 but hadn't fixed it then. They chose the
    recommended project-wide middleware over redirecting back per view.
- **Sideways:**
  - The agent's first 405 test assumed a logged-out visitor opening
    `/accounts/logout/` would see the 405 page. It failed: the login gate
    redirects them to login first (matching the Phase 1 note). The test
    was changed to check that redirect instead.
  - Ruff flagged two `[...][0]` list lookups in the new tests (RUF015);
    they were changed to `next(...)`.
  - `manage.py check` shows the existing `django_tailwind_cli.W001`
    warning about the source CSS inside `assets/`. It predates this phase
    and was left alone.

## 2026-11-06 — Phase 4 built: job openings

### Prompts
1. `/implement @prd/applicant-tracking-system.md
   @plans/applicant-tracking-system.md implement phase 4`
2. yes these behaviors are good for tdd
3. yes go ahead
4. yes that looks good
5. yes go ahead
6. yes it implements the behavior, you can move on
7. yes go ahead
8. yes you can finish the rest of the phase
9. okay i have checked this manually, could you update prompts and commit
   and push the phase?

### Summary
- **Outcome:**
  - Phase 4 is built. Added the `JobOpening` model (migration 0004): title,
    department, location, description, an open/closed flag that starts
    open, a many-to-many to `Skill` for required skills, and timestamps.
    Title, department and location are trimmed in `save()`, like Candidate.
  - Added the openings list, create, detail and edit pages, an Openings
    navbar link, and JobOpening in the admin (with a searchable skill
    picker). Required skills are chosen from a multi-select; when no skills
    exist, the form links to the Skills page instead. The open/closed flag
    is not on the form (close and reopen come in Phase 5).
  - Three behaviors were built test-first: creating an opening with
    several skills, editing that adds and removes skills, and the list and
    detail pages showing each opening's own department, location and
    skills. 19 more tests cover the rest of the phase (shared skills,
    required fields, unknown skills, trimming, status unchanged by edits,
    404s, admin, login). 79 tests pass; ruff is clean.
- **Deviations:** none. The user approved every proposed behavior and test
  as written, and verified the phase in the browser before asking for this
  log, the commit and the push.
- **Sideways:**
  - The first RED for the create test failed with `DoesNotExist` instead
    of an assertion. Added an explicit `count() == 1` assertion before
    showing it, so it failed on an assertion as the TDD skill requires.
  - The implement skill says to write the PROMPTS.md entry and commit at
    the end, but this file and CLAUDE.md say entries are added only when
    the user asks and the user commits. The agent waited, and the user
    then asked for all three.
  - The Tailwind classes for the multi-select live in `forms.py`, so the
    agent rebuilt the CSS to confirm they were picked up (they were).

## 2026-11-05 — Phase 3 built: candidates

### Prompts
1. `/implement @prd/applicant-tracking-system.md
   @plans/applicant-tracking-system.md implement phase 3`
2. yes those are good
3. yes
4. yes it implements the behavior, you can move on
5. yes that looks right, go ahead
6. yes it implements the behavior, finish the rest of the phase
7. (Answer to the agent's question on email capitalisation) Ignore case,
   keep typing (Recommended)
8. when i try to search ana lopez with the updated name containing the
   special character: ó if i do not include the special character and just
   put a regular o the ana lopez candidate is not searched up
9. (Answer to the agent's question on accents in search) Search-text column
   (Recommended)
10. okay i tested in the browser, update prompts.md

### Summary
- **Outcome:**
  - Phase 3 is built. Added the `Candidate` model with the four fixed
    sources, an email that is unique regardless of capitalisation (a
    database constraint on the lowercased email, the same pattern as
    Skill) but stored as typed, and names and email trimmed in `save()`.
  - Added the candidate list (search and source filter as GET parameters),
    create, detail and edit pages, a Candidates navbar link, and Candidate
    in the admin, which is the only place a candidate can be deleted.
  - Search matches every typed word against the name and email, ignoring
    capitals and accents. This uses a hidden `search_text` field that
    `save()` fills with the folded name and email (`hiring/search.py`).
  - The two TDD behaviors were: `?q=` matches first name, last name or
    email ignoring capitalisation, and `?source=` limits the list and
    combines with `?q=`. Regular tests cover create, edit, detail, the
    duplicate-email error, the admin delete, no delete action in the app,
    and the login requirement (56 tests in total).
  - Ruff check and format pass. The user checked the pages in the browser.
- **Deviations:**
  - No recommendations were overridden. The user picked the recommended
    option for both questions the agent asked (email capitalisation and
    accents in search).
  - The user found the accent problem while testing in the browser and
    asked about it. That led to the `search_text` field.
  - The agent made the source filter ignore unknown values, which goes a
    little past the approved TDD test, and said so at the time.
- **Sideways:**
  - The code-review tool found nine issues. Seven were fixed with tests:
    email duplicates that differ only in capitals, full-name search ("Ana
    Lopez") finding nothing, the edit heading showing an unsaved name after
    a failed edit, an unknown source looking like an active filter, a
    length-based navbar check, trimming only in the form, and a "no delete"
    test that missed two pages. Two style suggestions were left as they
    were (merging the create and edit views, and moving the form layout
    out of the template).
  - Accents weren't handled at first: SQLite treats "o" and "ó" as
    different letters. The user caught it in the browser.
  - `0002_candidate.py` was regenerated once for the email constraint
    (before it had been applied). By the time of the accent fix, the
    migration had already been applied to the user's database, so the fix
    went into a new `0003` migration that also fills in existing rows.
  - A smoke-test script hung because of a stray `cat >` waiting for input,
    and was stopped. One navbar edit was a no-op and had to be redone. A
    `manage.py shell` check failed on piped input and was rerun with `-c`.
  - The implement skill says to log, commit and push, but CLAUDE.md says
    the user commits. The agent waited to be asked and did not commit.

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
