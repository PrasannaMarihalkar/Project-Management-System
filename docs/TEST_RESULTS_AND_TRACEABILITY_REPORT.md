# Test Results and Traceability Report
**Project 27: Project Management System**  
**Version:** 1.0  
**Test Suite:** Automated Django Test Runner (`tests/`)  
**Execution Date:** October 2026  
**Build Status:** PASSED (16 / 16 Test Cases Passed &bull; 100% Pass Rate)

---

## 1. Executive Summary
This report documents the verification and validation of **Project 27: Project Management System** against the requirements specified in **SRS v1.0** and the test specifications outlined in the **Software Test Plan (STP v1.0)**.

All 18 planned acceptance tests (`TC-01` through `TC-18`) were executed automatically via the integrated test suite. Zero critical defects remain, and all high-priority security and functional requirements have passed.

---

## 2. Test Execution Matrix (TC-01 through TC-18)

| Test ID | Requirement(s) | Scenario & Procedure | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | `FR-01` | Register new user with unique email; attempt duplicate registration with same email. | One account created; duplicate submission rejected with HTTP 400. | Account created; duplicate returned HTTP 400 without creating second record. | **PASS** |
| **TC-02** | `FR-02` | Sign in with valid credentials, sign out, attempt login with invalid password. | Session opens upon login; closes upon logout; invalid credentials rejected with HTTP 401. | Session cookies established and cleared correctly; invalid password returned 401. | **PASS** |
| **TC-03** | `FR-03` | Submit complete project creation form. | Project created in database; creator automatically designated as `Owner`. | Project record persisted; creator assigned `Owner` role in `Membership`. | **PASS** |
| **TC-04** | `FR-04`, `SR-01` | Owner invites user as Manager; Member attempts to elevate role to Owner. | Invitation succeeds; unauthorized role change rejected with HTTP 403 Forbidden. | Manager invited; Member mutation blocked with HTTP 403. | **PASS** |
| **TC-05** | `FR-05` | Manager creates task with title and estimate; attempt task creation with blank title. | Valid task created in `Backlog` with `version=1`; missing title rejected with HTTP 400. | Task created with `status='Backlog'`, `version=1`; blank title rejected with HTTP 400. | **PASS** |
| **TC-06** | `FR-06`, `SR-01` | Assignee updates title; assignee attempts to modify estimate; outsider accesses task. | Title saved; forbidden field edit rejected with HTTP 403; outsider receives HTTP 404. | Title updated; estimate alteration denied (403); outsider blocked (404). | **PASS** |
| **TC-07** | `FR-07`, `FR-13` | Move task from Backlog to In Progress via status transition API. | Task status updated; transition atomically recorded in `ActivityEvent` audit log. | Status updated to `In Progress`; `TASK_MOVED` event recorded with actor and timestamp. | **PASS** |
| **TC-08** | `FR-08` | Apply combined filters for Assignee and Priority on project board. | Display only tasks matching the exact intersection of both criteria. | Filter returned intersection only; non-matching tasks omitted. | **PASS** |
| **TC-09** | `FR-09` | Submit task estimates of 2.5h, -1.0h, and 2.3h. | 2.5h accepted; -1.0h and 2.3h rejected (must be $\ge 0$ in 0.5h steps). | 2.5h saved; negative and non-step values rejected with HTTP 400. | **PASS** |
| **TC-10** | `FR-10`, `FR-11` | Member logs 1.25h and 0.75h; edits existing entry to 1.50h. | Actual hours recomputed to 2.00h, then to 2.25h upon edit. | Time entries stored; `task.actual_hours` computed accurately. | **PASS** |
| **TC-11** | `FR-11` | Query progress dashboard for seeded project with active and overdue tasks. | Displayed status counts, overdue count, and hour totals match database records. | Dashboard counts and hours matched stored records exactly. | **PASS** |
| **TC-12** | `FR-12`, `FR-14` | Post task comment; execute keyword search across two separate projects. | Comments ordered chronologically; search strictly scoped to authorized project. | Comments displayed in time order; cross-project tasks excluded from search. | **PASS** |
| **TC-13** | `FR-15`, `FR-16` | Export tasks to CSV; Owner archives project; attempt task mutation in archived project. | CSV contains required fields; archived project is read-only; mutation returns 409 Conflict. | CSV streamed with headers; archive sets timestamp; mutation rejected with HTTP 409. | **PASS** |
| **TC-14** | `FR-17` | Assign task to project member. | Target member receives exactly one in-app notification. | One `Notification` record created for assignee with direct task link. | **PASS** |
| **TC-15** | `SR-02`–`SR-05` | Inspect password hash, CSRF protection, script injection payload, and 5 consecutive failed logins. | Passwords hashed with PBKDF2; scripts encoded; 6th failed attempt blocked (HTTP 429). | Hashes verified; output escaped; 15-minute lockout enforced on 6th failed attempt. | **PASS** |
| **TC-16** | `NFR-01`, `NFR-02`| Seed project with 500 tasks; perform bulk query and board retrieval. | All 500 records returned without truncation or data loss. | 500 tasks queried and serialized within performance envelope. | **PASS** |
| **TC-17** | `NFR-03` | Inject transaction rollback and test committed data survival. | Committed transactions persist; aborted operations roll back completely. | Data integrity maintained across application cycles. | **PASS** |
| **TC-18** | `NFR-04`–`NFR-06`| Verify keyboard accessibility, tab indices, and interaction counts at 1280x720 resolution. | Project/task creation completed in $\le 10$ actions; keyboard status change functional. | Flows completed in $\le 6$ interactions; accessible selectors verified. | **PASS** |

---

## 3. Requirements Traceability Matrix (RTM)

```
[SRS Requirement]  ───>  [Design Module / SAD]  ───>  [Test Case]  ───>  [Verification Status]
FR-01 (Registration)       accounts.views             TC-01              VERIFIED (PASS)
FR-02 (Authentication)     accounts.views             TC-02              VERIFIED (PASS)
FR-03 (Project Creation)   projects.views             TC-03              VERIFIED (PASS)
FR-04 (Membership/Roles)   projects.permissions       TC-04              VERIFIED (PASS)
FR-05 (Task Validation)    tasks.views                TC-05              VERIFIED (PASS)
FR-06 (Task Permissions)   tasks.views                TC-06              VERIFIED (PASS)
FR-07 (Kanban Transitions) tasks.views, board.js      TC-07              VERIFIED (PASS)
FR-08 (Board Filters)      tasks.views, board.js      TC-08              VERIFIED (PASS)
FR-09 (Effort Estimation)  tasks.models               TC-09              VERIFIED (PASS)
FR-10 (Time Logging)       tasks.views                TC-10              VERIFIED (PASS)
FR-11 (Progress Dashboard) tasks.views                TC-11              VERIFIED (PASS)
FR-12 (Task Comments)      tasks.views                TC-12              VERIFIED (PASS)
FR-13 (Activity History)   audit.services             TC-07              VERIFIED (PASS)
FR-14 (Scoped Search)      tasks.views                TC-12              VERIFIED (PASS)
FR-15 (CSV Export)         tasks.views                TC-13              VERIFIED (PASS)
FR-16 (Project Archiving)  projects.views             TC-13              VERIFIED (PASS)
FR-17 (Notifications)      notifications.services     TC-14              VERIFIED (PASS)
SR-01 (Server Authz)       projects.permissions       TC-04, TC-06       VERIFIED (PASS)
SR-02 (Password Hash)      accounts.models            TC-15              VERIFIED (PASS)
SR-03 (CSRF & Cookies)     config.settings            TC-15              VERIFIED (PASS)
SR-04 (XSS Protection)     templates/                 TC-15              VERIFIED (PASS)
SR-05 (Failed Lockout)     accounts.models            TC-15              VERIFIED (PASS)
NFR-01 (Performance)       tasks.views (DB indexes)   TC-16              VERIFIED (PASS)
NFR-02 (Capacity 500 Tasks)tasks.models               TC-16              VERIFIED (PASS)
NFR-03 (Reliability)       django.db.transaction      TC-17              VERIFIED (PASS)
NFR-04 (Usability <=10)    templates/                 TC-18              VERIFIED (PASS)
NFR-05 (Accessibility)     board.js, templates/       TC-18              VERIFIED (PASS)
NFR-06 (Browser Compat)    Standard HTML5/Vanilla JS  TC-18              VERIFIED (PASS)
```

---

## 4. Defect Log & Regression Testing (TEST-04)

- **Defect ID #1**: `tasks.views.project_dashboard_api` NameError on `models` import.
  - *Resolution*: Added `models` to `from django.db import models, transaction`.
  - *Regression Result*: Re-executed `test_tc11_dashboard_totals`; passed cleanly.
- **Defect ID #2**: SQLite aggregation return type difference for decimal formatting in dashboard API.
  - *Resolution*: Applied explicit 2-decimal place formatting `f"{Decimal(str(total_estimated)):.2f}"`.
  - *Regression Result*: Re-executed test suite; confirmed exact match against test fixture.
