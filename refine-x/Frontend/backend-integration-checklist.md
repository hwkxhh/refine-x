# RefineX — Backend Integration Checklist
> Full frontend audit conducted: March 1, 2026  
> Every page, component, button, and data source has been reviewed.

---

## Output 1 — Frontend Completion Status

| # | Feature | Built in Frontend | Notes |
|---|---------|:-----------------:|-------|
| **AUTH & USER** | | | |
| 1 | Sign up form (name, email, password, org) | ✅ Yes | Submits to `setTimeout` fake — no real API call |
| 2 | Sign in form (email, password) | ✅ Yes | Submits to `setTimeout` fake — no real API call |
| 3 | Forgot password form | ✅ Yes | Form renders but `onSubmit` is not wired — no handler at all |
| 4 | Email verification screen | ❌ No | No page exists, not linked anywhere |
| 5 | Google OAuth button | ✅ Yes (UI only) | Button renders, no `onClick`, no OAuth flow |
| 6 | Microsoft OAuth button | ✅ Yes (UI only) | Button renders, no `onClick`, no OAuth flow |
| 7 | Session / token management | ❌ No | No `localStorage`, no cookies, no auth context anywhere |
| 8 | Protected routes / route guards | ❌ No | Any URL is accessible without login |
| 9 | Sign out button | ✅ Yes (UI only) | Links to `/` — no session invalidation |
| **ONBOARDING** | | | |
| 10 | Step 1 — Org type selector + team size | ✅ Yes | Local state only — never sent anywhere |
| 11 | Step 2 — Workspace name + goal | ✅ Yes | Local state only — never sent anywhere |
| 12 | Step 3 — File upload dropzone | ✅ Yes (UI only) | No file is sent; clicking "Analyze This File" goes straight to `/dashboard/upload` |
| **DASHBOARD HOME** | | | |
| 13 | Greeting with user's first name | ✅ Yes | Hardcoded "John" — not from session or API |
| 14 | Date display | ✅ Yes | Hardcoded "Tuesday, 22 February 2026" |
| 15 | KPI cards (analyses run, files cleaned, issues resolved, avg quality) | ✅ Yes | All 4 values fully hardcoded |
| 16 | Recent analyses list | ✅ Yes | Hardcoded array of 3 items |
| 17 | Latest insights feed | ✅ Yes | Hardcoded array of 3 items |
| 18 | Chart carousel ("Your Charts") | ✅ Yes | Hardcoded list — no actual charts rendered, only metadata cards |
| 19 | Recommendations section | ✅ Yes | Fully hardcoded — 3 static items |
| 20 | "Re-run" button on analysis card | ✅ Yes (UI only) | `<button>` with no handler |
| 21 | "Share" button on analysis card | ✅ Yes (UI only) | `<button>` with no handler |
| 22 | "Mark as read" on insight | ✅ Yes (UI only) | `<button>` with no handler |
| 23 | "Save" on insight | ✅ Yes (UI only) | `<button>` with no handler |
| 24 | Chart "Expand" button | ✅ Yes (UI only) | `<button>` with no handler |
| 25 | Chart "Download" button | ✅ Yes (UI only) | `<button>` with no handler |
| 26 | Chart "Edit" button | ✅ Yes (UI only) | `<button>` with no handler |
| 27 | "New Analysis" CTA button | ✅ Yes | Routes to `/dashboard/upload` ✓ |
| **FILE UPLOAD** | | | |
| 28 | File upload dropzone (drag-and-drop + click) | ✅ Yes | File is accepted locally — `setTimeout` simulates upload, no real HTTP request |
| 29 | Upload progress bar | ✅ Yes (UI only) | `animate-pulse` fake — not tied to real transfer |
| 30 | Data preview table after upload | ✅ Yes | Shows `mockCSVData` hardcoded rows — not from the actual uploaded file |
| 31 | Goal input field | ❌ No | Not present on upload page — only in onboarding workspace step |
| 32 | Workspace selector on upload | ❌ No | Not present — no dropdown to assign file to a workspace |
| 33 | "Proceed to Analysis" after upload | ✅ Yes | Routes to `/dashboard/project/new/profile` ✓ |
| **ANALYSIS FLOW — DATA PROFILING** | | | |
| 34 | Column profile cards (type, unique values, missing %, quality badge) | ✅ Yes | Data from `mockColumnProfiles` — hardcoded |
| 35 | Expandable column detail rows | ✅ Yes | Local state toggle — hardcoded data |
| 36 | Summary KPI cards (total columns, excellent, needs attention, avg completeness) | ✅ Yes | Computed from hardcoded mock data |
| **ANALYSIS FLOW — DATA CLEANING** | | | |
| 37 | Auto-Clean toggle | ✅ Yes | Toggle is wired locally |
| 38 | "Run Auto-Clean" button | ✅ Yes | `setTimeout` simulates cleaning — logs are hardcoded strings, nothing sent to backend |
| 39 | Before / After data toggle | ✅ Yes | Swaps local `showBefore` state — "after" just highlights a hardcoded cell, no real diff |
| 40 | Column-level fill strategy dropdowns | ✅ Yes (UI only) | `<select>` renders but selections are never stored or sent |
| **ANALYSIS FLOW — DOMAIN DETECTION** | | | |
| 41 | AI domain detection result + confidence score | ✅ Yes | Fully hardcoded — `confidence: 87`, domain `"Sales & Revenue"` |
| 42 | Alternative domain selector | ✅ Yes | Local state — selection is never sent anywhere |
| 43 | "Key Indicators Detected" list | ✅ Yes | Hardcoded column names (Revenue, Customer_Segment, etc.) |
| **ANALYSIS FLOW — ANALYTICS SELECTION** | | | |
| 44 | Analytics type selector (6 types) | ✅ Yes | Multi-select with local state — selection never sent anywhere |
| 45 | "Group by" dropdowns per analytic | ✅ Yes (UI only) | Renders but value never sent |
| 46 | Estimated time calculator | ✅ Yes | Computed from local hardcoded `estimatedTime` strings |
| 47 | "Continue to Visualization" button | ✅ Yes | Hardcoded route to `/dashboard/project/1/visualize` |
| **VISUALIZE PAGE** | | | |
| 48 | KPI cards (Revenue, Orders, Avg Order Value, Customers) | ✅ Yes | All hardcoded |
| 49 | Revenue Trend line chart | ✅ Yes | Hardcoded dummy data |
| 50 | Orders by Month bar chart | ✅ Yes | Hardcoded dummy data |
| 51 | Sales by Category donut chart | ✅ Yes | Hardcoded dummy data |
| 52 | Sales by Category toggle (bar / progress / pie) | ✅ Yes | Local state — `mockCategoryData` |
| 53 | Regional Performance chart | ✅ Yes | `mockRegionData` — hardcoded |
| 54 | Top Products chart | ✅ Yes | `topProductsData` — hardcoded |
| 55 | Salesperson Performance chart | ✅ Yes | `salespersonData` — hardcoded |
| 56 | Goal vs Actual chart | ✅ Yes | `goalVsActualData` — hardcoded |
| 57 | AI Insight blocks under every chart section | ✅ Yes | All insight text is hardcoded strings |
| 58 | "Filters" button | ✅ Yes (UI only) | No handler |
| 59 | "Export" button | ✅ Yes (UI only) | No handler |
| **INSIGHTS PAGE (`/project/[id]/insights`)** | | | |
| 60 | Executive summary block | ✅ Yes | Hardcoded prose |
| 61 | AI insight cards with confidence scores | ✅ Yes | `mockInsights` array — hardcoded |
| 62 | Recommendations list | ✅ Yes | Hardcoded array of 4 items |
| 63 | Statistical summary panel | ✅ Yes | All numbers hardcoded |
| 64 | "Export PDF" button | ✅ Yes (UI only) | No handler |
| 65 | "Share" button | ✅ Yes (UI only) | No handler |
| 66 | "Edit Summary" button | ✅ Yes (UI only) | No handler |
| 67 | "View Details" / "Dismiss" per insight | ✅ Yes (UI only) | No handlers |
| **ANALYSES PAGE (`/dashboard/analyses`)** | | | |
| 68 | Analyses list with status, score, meta | ✅ Yes | Hardcoded array of 3 items |
| 69 | Search + filter + sort controls | ✅ Yes (UI only) | Inputs render but are not wired to filter the list |
| **PROJECTS PAGE (`/dashboard/projects`)** | | | |
| 70 | Projects grid with status badges | ✅ Yes | `mockProjects` — hardcoded |
| 71 | Search (filters the list) | ✅ Yes | Client-side filter over hardcoded data ✓ |
| 72 | Status filter tabs | ✅ Yes | Client-side filter over hardcoded data ✓ |
| 73 | Project three-dot menu (Duplicate, Archive, Delete) | ✅ Yes (UI only) | Menu renders, no handlers on items |
| **DATASETS PAGE (`/dashboard/datasets`)** | | | |
| 74 | Dataset list with row/column/quality info | ✅ Yes | Hardcoded array of 2 items |
| 75 | "Show cleaned" button | ✅ Yes (UI only) | No handler |
| 76 | "Download CSV" button | ✅ Yes (UI only) | No handler — does not download anything |
| 77 | "Download XLSX" button | ✅ Yes (UI only) | No handler — does not download anything |
| **VISUALIZATIONS STUDIO PAGE** | | | |
| 78 | Chart list with type badges | ✅ Yes | Hardcoded array of 4 items |
| 79 | "Expand" button | ✅ Yes (UI only) | No handler |
| 80 | "Download PNG" button | ✅ Yes (UI only) | No handler |
| 81 | "Download SVG" button | ✅ Yes (UI only) | No handler |
| 82 | "Edit Chart" button | ✅ Yes (UI only) | No handler |
| 83 | "+ New Chart" button | ✅ Yes (UI only) | No handler |
| **INSIGHTS PAGE (`/dashboard/insights`)** | | | |
| 84 | Insights feed | ✅ Yes | Hardcoded array of 3 items |
| 85 | Category filter dropdown | ✅ Yes (UI only) | Renders but does not filter |
| 86 | Date range / workspace filter inputs | ✅ Yes (UI only) | Renders, not wired |
| **HISTORY PAGE** | | | |
| 87 | Audit log timeline | ✅ Yes | Hardcoded array of 6 events |
| 88 | Filter inputs (action type, date, workspace) | ✅ Yes (UI only) | Render, not wired |
| 89 | "Download full audit log (CSV)" button | ✅ Yes (UI only) | No handler — downloads nothing |
| **REPORTS PAGE** | | | |
| 90 | Reports grid with status + metrics | ✅ Yes | Hardcoded `mockReports` array |
| 91 | Search + status + date filters | ✅ Yes | Client-side filter over hardcoded data ✓ |
| 92 | Three-dot menu per report (View, Download, Share, Delete) | ✅ Yes (UI only) | Menu renders, no handlers |
| **TEAM PAGE** | | | |
| 93 | Members table (name, email, role, last active, status) | ✅ Yes | Hardcoded array of 3 members |
| 94 | Invite member form (email input + role select + Send Invite) | ✅ Yes (UI only) | Button renders, no handler |
| 95 | Role change dropdown | ❌ No | Role is displayed in table as static text — no dropdown to change it |
| 96 | Remove member button | ❌ No | Not present in current table |
| **SETTINGS PAGE** | | | |
| 97 | Profile form (first name, last name, email, company) | ✅ Yes | `defaultValue` props — not connected to user session |
| 98 | Avatar / "Change Avatar" button | ✅ Yes (UI only) | No file picker or upload logic |
| 99 | Save Changes button | ✅ Yes | Sets a local `saved` state for 3 seconds — no API call |
| 100 | Change Password form (current, new, confirm) | ✅ Yes | Inputs render — no submit handler |
| 101 | Enable 2FA button | ✅ Yes (UI only) | No handler |
| 102 | Theme selector (Light / Dark / Auto) | ✅ Yes (UI only) | Buttons render — no theme switching logic |
| 103 | Notification toggles (4 items) | ✅ Yes | `defaultChecked` — state not persisted anywhere |
| 104 | Data retention dropdown | ✅ Yes (UI only) | `defaultValue="90 days"` — not sent anywhere |
| 105 | Delete Account button | ✅ Yes (UI only) | No handler, no confirmation modal |
| **BILLING PAGE** | | | |
| 106 | Current plan display (Professional, $29/mo) | ✅ Yes | Hardcoded |
| 107 | Usage meters (projects, storage, API calls) | ✅ Yes | All hardcoded numbers |
| 108 | Plan comparison + Upgrade/Downgrade buttons | ✅ Yes (UI only) | Buttons render, no handler |
| 109 | Monthly / Yearly toggle | ✅ Yes | Local state — changes displayed price only |
| 110 | Payment method card display | ✅ Yes | Hardcoded `•••• 4242` |
| 111 | "Update Payment Method" button | ✅ Yes (UI only) | No handler |
| 112 | "Add Payment Method" button | ✅ Yes (UI only) | No handler |
| 113 | "Cancel Subscription" button | ✅ Yes (UI only) | No handler |
| 114 | Billing history table | ✅ Yes | Hardcoded array of 4 invoices |
| 115 | "Download" invoice button | ✅ Yes (UI only) | No handler — downloads nothing |
| **TEMPLATES PAGE** | | | |
| 116 | Template cards grid | ✅ Yes | `mockTemplates` — hardcoded 4 items |
| 117 | "Use Template" button | ✅ Yes (UI only) | No handler |
| 118 | "Request Custom Template" button | ✅ Yes (UI only) | No handler |
| **HEADER** | | | |
| 119 | Global search bar | ✅ Yes (UI only) | Styled input — searches nothing |
| 120 | Notification bell with red dot | ✅ Yes (UI only) | Red dot hardcoded — no count, no dropdown |
| 121 | Workspace dropdown ("Rider Payments") | ✅ Yes (UI only) | Hardcoded name — no real workspace list |
| 122 | "+ New Workspace" link | ✅ Yes (UI only) | `<button>` with no handler |
| 123 | User menu (name, email, links) | ✅ Yes | Hardcoded "John Doe / john@example.com" |
| 124 | Sign Out link in user menu | ✅ Yes (UI only) | Links to `/` — no session cleared |

---

## Output 2 — Backend Integration Checklist

---

### 🔐 Category 1: Authentication & Session

- [ ] **POST /api/auth/signup**
  - **Sends:** `{ name, email, password, organization? }`
  - **Expects back:** `{ user: { id, name, email, org }, token }` (JWT or session cookie)

- [ ] **POST /api/auth/login**
  - **Sends:** `{ email, password }`
  - **Expects back:** `{ user: { id, name, email }, token }`

- [ ] **POST /api/auth/logout**
  - **Sends:** auth token / session cookie
  - **Expects back:** `{ success: true }`

- [ ] **POST /api/auth/forgot-password**
  - **Sends:** `{ email }`
  - **Expects back:** `{ message: "Reset link sent" }`

- [ ] **POST /api/auth/reset-password**
  - **Sends:** `{ token, newPassword }`
  - **Expects back:** `{ success: true }`

- [ ] **GET /api/auth/verify-email?token=**
  - **Sends:** verification token in query string
  - **Expects back:** `{ success: true }` + redirect

- [ ] **GET /api/auth/oauth/google** — initiates Google OAuth flow
  - **Expects back:** redirect to Google, then callback with `{ user, token }`

- [ ] **GET /api/auth/oauth/microsoft** — initiates Microsoft OAuth flow
  - **Expects back:** redirect to Microsoft, then callback with `{ user, token }`

- [ ] **GET /api/auth/me**
  - **Sends:** auth token (header)
  - **Expects back:** `{ id, name, email, organization, plan, avatarUrl }` — used to hydrate the user context, replace hardcoded "John Doe" everywhere

---

### 🏢 Category 2: Onboarding & Workspace Setup

- [ ] **POST /api/onboarding/complete**
  - **Sends:** `{ organizationType, teamSize, workspaceName, workspaceGoal }`
  - **Expects back:** `{ workspaceId, redirectUrl }` — marks onboarding as done

- [ ] **POST /api/workspaces**
  - **Sends:** `{ name, goal, organizationId }`
  - **Expects back:** `{ id, name, goal, createdAt }`

- [ ] **GET /api/workspaces**
  - **Sends:** auth token
  - **Expects back:** `[{ id, name, goal, createdAt, projectCount }]` — populates the workspace dropdown in the header

- [ ] **DELETE /api/workspaces/:id**
  - **Sends:** workspace ID
  - **Expects back:** `{ success: true }`

---

### 📁 Category 3: File Upload & Processing

- [ ] **POST /api/files/upload**
  - **Sends:** `multipart/form-data` with `file` (CSV/XLSX), `workspaceId`, `goal?`
  - **Expects back:** `{ fileId, fileName, rows, columns, previewRows: [...], uploadedAt }` — replaces the fake `mockCSVData` preview

- [ ] **GET /api/files/:fileId/profile**
  - **Sends:** `fileId`
  - **Expects back:** `{ columns: [{ name, type, uniqueValues, missingPercent, quality, stats: { min, max, mean, sampleValues } }] }` — replaces `mockColumnProfiles`

- [ ] **POST /api/files/:fileId/clean**
  - **Sends:** `{ autoClean: true, columnRules: [{ column, strategy: 'mean'|'median'|'mode'|'zero'|'drop' }] }`
  - **Expects back:** `{ cleanedFileId, log: ["Removed 23 duplicates", ...], rowsBefore, rowsAfter }` — replaces the fake `cleaningLog` setTimeout

- [ ] **GET /api/files/:fileId/cleaned-preview**
  - **Sends:** `fileId`
  - **Expects back:** `{ headers, rows, changedCells: [{ row, col }] }` — powers the Before/After toggle with real diff highlighting

- [ ] **GET /api/files/:fileId/download?format=csv|xlsx**
  - **Sends:** `fileId`, `format`
  - **Expects back:** binary file download stream — powers "Download CSV" and "Download XLSX" buttons

---

### 🤖 Category 4: AI Analysis Engine

- [ ] **POST /api/analysis/detect-domain**
  - **Sends:** `{ fileId }`
  - **Expects back:** `{ domains: [{ id, name, confidence }] }` sorted by confidence — replaces hardcoded `domains` array with `confidence: 87`

- [ ] **POST /api/analysis/run**
  - **Sends:** `{ fileId, cleanedFileId, domainId, selectedAnalytics: ['revenue', 'customer', ...], groupBy: { revenue: 'month', ... } }`
  - **Expects back:** `{ analysisId, status: 'queued' }` — kicks off the async analysis job

- [ ] **GET /api/analysis/:analysisId/status** *(polling endpoint OR WebSocket channel)*
  - **Sends:** `analysisId`
  - **Expects back:** `{ status: 'processing'|'complete'|'failed', currentPhase: string, progress: 0-100 }` — powers a real progress screen (currently no processing screen exists — needs to be built)

- [ ] **GET /api/analysis/:analysisId/results**
  - **Sends:** `analysisId`
  - **Expects back:** `{ kpis: {...}, charts: [...], insights: [...], recommendations: [...] }` — replaces all hardcoded dashboard and visualize page data

---

### 📊 Category 5: Charts & Visualizations

- [ ] **GET /api/analysis/:analysisId/charts**
  - **Sends:** `analysisId`
  - **Expects back:** `[{ chartId, title, type, data: [...], config: {...} }]` — replaces all hardcoded `mockChartData`, `mockCategoryData`, `mockRegionData`, etc.

- [ ] **POST /api/charts** *(custom chart builder)*
  - **Sends:** `{ analysisId, chartType, xAxis, yAxis, groupBy, title }`
  - **Expects back:** `{ chartId, title, type, data: [...] }`

- [ ] **GET /api/charts/:chartId/export?format=png|svg|pdf**
  - **Sends:** `chartId`, `format`
  - **Expects back:** binary file download — powers the Export PNG / SVG / PDF buttons

- [ ] **DELETE /api/charts/:chartId**
  - **Sends:** `chartId`
  - **Expects back:** `{ success: true }`

---

### 💡 Category 6: AI Insights

- [ ] **GET /api/analysis/:analysisId/insights**
  - **Sends:** `analysisId`, optional `?category=anomaly|trend|performance|opportunity`
  - **Expects back:** `[{ id, category, severity, text, source, confidence, createdAt }]` — replaces all hardcoded insight arrays across every page

- [ ] **POST /api/insights/:insightId/save**
  - **Sends:** `insightId`, auth token
  - **Expects back:** `{ saved: true }` — powers the "Save" button on insight cards

- [ ] **POST /api/insights/:insightId/dismiss**
  - **Sends:** `insightId`
  - **Expects back:** `{ dismissed: true }` — powers the "Dismiss" button

- [ ] **POST /api/insights/:insightId/mark-read**
  - **Sends:** `insightId`
  - **Expects back:** `{ read: true }`

- [ ] **GET /api/insights/executive-summary/:analysisId**
  - **Sends:** `analysisId`
  - **Expects back:** `{ summary: string }` — replaces hardcoded executive summary prose

- [ ] **PUT /api/insights/executive-summary/:analysisId**
  - **Sends:** `{ summary: string }` *(from "Edit Summary" button)*
  - **Expects back:** `{ updated: true }`

---

### 📋 Category 7: Projects & Analyses

- [ ] **GET /api/projects**
  - **Sends:** auth token, optional `?workspaceId=&status=&search=`
  - **Expects back:** `[{ id, name, description, status, rows, columns, domain, lastModified, createdAt }]` — replaces `mockProjects`

- [ ] **GET /api/projects/:id**
  - **Sends:** project ID
  - **Expects back:** full project object with associated analyses

- [ ] **POST /api/projects/:id/duplicate**
  - **Sends:** `projectId`
  - **Expects back:** `{ newProjectId }`

- [ ] **PATCH /api/projects/:id/archive**
  - **Sends:** `projectId`
  - **Expects back:** `{ status: 'archived' }`

- [ ] **DELETE /api/projects/:id**
  - **Sends:** `projectId`
  - **Expects back:** `{ success: true }`

- [ ] **POST /api/projects/:id/rerun**
  - **Sends:** `projectId`
  - **Expects back:** `{ analysisId, status: 'queued' }` — powers the "Re-run" button

- [ ] **GET /api/analyses**
  - **Sends:** auth token, optional `?workspaceId=&status=&sort=`
  - **Expects back:** `[{ id, fileName, goal, status, score, rows, columns, issueCount, createdAt }]` — replaces hardcoded analyses on `/dashboard/analyses`

---

### 🗂️ Category 8: Datasets

- [ ] **GET /api/datasets**
  - **Sends:** auth token, optional `?workspaceId=`
  - **Expects back:** `[{ id, name, rows, columns, qualityScore, issueCount, status }]` — replaces hardcoded datasets on `/dashboard/datasets`

- [ ] **GET /api/datasets/:id/cleaned-preview**
  - **Sends:** `datasetId`
  - **Expects back:** `{ headers, rows }` — powers "Show cleaned" button

- [ ] **GET /api/datasets/:id/download?format=csv|xlsx**
  - **Sends:** `datasetId`, `format`
  - **Expects back:** binary file download

---

### 📈 Category 9: Reports

- [ ] **GET /api/reports**
  - **Sends:** auth token, optional `?status=&search=&dateRange=`
  - **Expects back:** `[{ id, title, domain, createdAt, status, metrics: { insights, charts, pages } }]` — replaces `mockReports`

- [ ] **GET /api/reports/:id/download**
  - **Sends:** `reportId`
  - **Expects back:** binary PDF download

- [ ] **POST /api/reports/:id/share**
  - **Sends:** `reportId`, `{ recipientEmails?: [] }` or generates a shareable link
  - **Expects back:** `{ shareUrl: string }`

- [ ] **DELETE /api/reports/:id**
  - **Sends:** `reportId`
  - **Expects back:** `{ success: true }`

---

### 🙋 Category 10: Team & Members

- [ ] **GET /api/team/members**
  - **Sends:** auth token, `workspaceId` or `orgId`
  - **Expects back:** `[{ id, name, email, role, lastActive, status }]` — replaces hardcoded members array

- [ ] **POST /api/team/invite**
  - **Sends:** `{ email, role: 'Admin'|'Analyst'|'Viewer', workspaceId }`
  - **Expects back:** `{ inviteId, status: 'sent' }` — powers "Send Invite" button

- [ ] **PATCH /api/team/members/:memberId/role**
  - **Sends:** `{ role: 'Admin'|'Analyst'|'Viewer' }`
  - **Expects back:** `{ updated: true }` — powers role change dropdown (not yet built in UI)

- [ ] **DELETE /api/team/members/:memberId**
  - **Sends:** `memberId`
  - **Expects back:** `{ success: true }` — powers Remove Member button (not yet built in UI)

---

### ⚙️ Category 11: User Settings & Profile

- [ ] **GET /api/user/profile**
  - **Sends:** auth token
  - **Expects back:** `{ id, firstName, lastName, email, company, timezone, avatarUrl, notificationPreferences, dataRetentionDays }` — replaces all hardcoded "John Doe" / "john@example.com"

- [ ] **PUT /api/user/profile**
  - **Sends:** `{ firstName, lastName, email, company, timezone }`
  - **Expects back:** `{ updated: true }` — powers "Save Changes" in settings

- [ ] **POST /api/user/avatar**
  - **Sends:** `multipart/form-data` with `avatar` image file
  - **Expects back:** `{ avatarUrl: string }` — powers "Change Avatar"

- [ ] **PUT /api/user/password**
  - **Sends:** `{ currentPassword, newPassword }`
  - **Expects back:** `{ success: true }` or `{ error: "Incorrect current password" }`

- [ ] **PUT /api/user/notifications**
  - **Sends:** `{ emailNotifications: bool, analysisComplete: bool, weeklyReports: bool, productUpdates: bool }`
  - **Expects back:** `{ updated: true }` — makes notification toggles persistent

- [ ] **PUT /api/user/preferences**
  - **Sends:** `{ dataRetentionDays: 30|90|365|null, autoSave: bool, theme: 'light'|'dark'|'auto' }`
  - **Expects back:** `{ updated: true }`

- [ ] **POST /api/user/2fa/enable**
  - **Sends:** auth token
  - **Expects back:** `{ qrCodeUrl, secret }` — triggers 2FA setup flow

- [ ] **DELETE /api/user/account**
  - **Sends:** `{ confirmPassword }` (for safety)
  - **Expects back:** `{ success: true }` — powers Delete Account button

---

### 💳 Category 12: Billing & Subscriptions

- [ ] **GET /api/billing/subscription**
  - **Sends:** auth token
  - **Expects back:** `{ plan: 'free'|'professional'|'enterprise', billingPeriod: 'monthly'|'yearly', price, renewalDate, usage: { projects, storageGb, apiCalls } }` — replaces all hardcoded billing data

- [ ] **POST /api/billing/upgrade**
  - **Sends:** `{ planId, billingPeriod }`
  - **Expects back:** `{ checkoutUrl }` or `{ success: true }` (if using Stripe, returns a Stripe Checkout session URL)

- [ ] **POST /api/billing/cancel**
  - **Sends:** auth token
  - **Expects back:** `{ cancellationDate, accessUntil }` — powers "Cancel Subscription"

- [ ] **POST /api/billing/payment-method**
  - **Sends:** Stripe `paymentMethodId`
  - **Expects back:** `{ last4, brand, expiryMonth, expiryYear }` — powers "Add / Update Payment Method"

- [ ] **GET /api/billing/invoices**
  - **Sends:** auth token
  - **Expects back:** `[{ id, date, amount, status, downloadUrl }]` — replaces hardcoded invoice table

- [ ] **GET /api/billing/invoices/:id/download**
  - **Sends:** `invoiceId`
  - **Expects back:** binary PDF download

---

### 🔔 Category 13: Notifications

- [ ] **GET /api/notifications**
  - **Sends:** auth token
  - **Expects back:** `[{ id, text, read, createdAt, type }]` + `{ unreadCount: number }` — powers the bell badge count and dropdown list

- [ ] **POST /api/notifications/mark-all-read**
  - **Sends:** auth token
  - **Expects back:** `{ updated: true }` — powers "Mark all read"

- [ ] **DELETE /api/notifications/:id**
  - **Sends:** `notificationId`
  - **Expects back:** `{ success: true }`

---

### 🔍 Category 14: Search

- [ ] **GET /api/search?q=**
  - **Sends:** `q` (query string), auth token
  - **Expects back:** `{ analyses: [...], insights: [...], datasets: [...], projects: [...] }` — powers the global search bar in the header

---

### 📜 Category 15: Audit Log / History

- [ ] **GET /api/history**
  - **Sends:** auth token, optional `?workspaceId=&actionType=&dateFrom=&dateTo=`
  - **Expects back:** `[{ id, icon, event, actor, workspaceId, createdAt }]` — replaces hardcoded `historyItems`

- [ ] **GET /api/history/export**
  - **Sends:** auth token, optional filters
  - **Expects back:** CSV file download — powers "Download full audit log (CSV)" button

---

### 📦 Category 16: Templates

- [ ] **GET /api/templates**
  - **Sends:** auth token, optional `?category=`
  - **Expects back:** `[{ id, name, description, category, uses, previewImageUrl }]` — replaces `mockTemplates`

- [ ] **POST /api/templates/:id/use**
  - **Sends:** `templateId`, `{ workspaceId }`
  - **Expects back:** `{ projectId }` + redirect to upload flow with template pre-configured

- [ ] **POST /api/templates/request-custom**
  - **Sends:** `{ description, contactEmail }`
  - **Expects back:** `{ submitted: true }` — powers "Request Custom Template"

---

### 🛡️ Category 17: Route Protection (Middleware)

- [ ] **Middleware / Auth guard** on all `/dashboard/*` routes
  - If no valid session token → redirect to `/auth/login`
  - If onboarding not complete → redirect to `/auth/onboarding`
  - Currently: **zero route protection exists** — all dashboard pages are accessible without any login

---

## Summary Counts

| Category | Total Endpoints Needed |
|----------|----------------------:|
| Auth & Session | 9 |
| Onboarding & Workspaces | 4 |
| File Upload & Processing | 5 |
| AI Analysis Engine | 4 |
| Charts & Visualizations | 4 |
| AI Insights | 6 |
| Projects & Analyses | 8 |
| Datasets | 3 |
| Reports | 4 |
| Team & Members | 4 |
| User Settings & Profile | 8 |
| Billing & Subscriptions | 6 |
| Notifications | 3 |
| Search | 1 |
| Audit Log / History | 2 |
| Templates | 3 |
| Route Protection | 1 (middleware) |
| **TOTAL** | **75** |

---

> **Note for the backend developer:** The frontend currently stores zero session state. There is no auth context, no token storage, and no HTTP client configured. The first thing needed after any endpoints are built is: (1) a global auth context/provider in the Next.js app, (2) a token storage strategy (httpOnly cookie recommended), and (3) an API client layer (e.g. `axios` instance or `fetch` wrapper) with the auth header automatically attached to every request.
