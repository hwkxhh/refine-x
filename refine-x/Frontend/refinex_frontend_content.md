# RefineX — Complete Frontend Content Specification
## Every Page. Every Section. Every Word.
### Production-Level SaaS — Million Dollar Standard

---

> **How to use this document:**
> Every page of the app is defined here with exact copy, section names, button labels, empty states, error messages, tooltips, microcopy, and UI content. Developers and designers should treat this as the single source of truth for what appears on every screen. Nothing should be invented on the fly during development.

---

## DESIGN LANGUAGE & BRAND VOICE

### Brand Personality
RefineX speaks like a **senior data analyst who is also a great communicator** — confident, precise, never condescending, occasionally witty. It never says "Oops!" It never says "Uh oh." It explains what happened, why it matters, and what to do next.

### Tone Principles
- **Confident, not arrogant** — "We found 3 issues" not "Unfortunately there were some problems"
- **Precise, not cold** — "Your pass rate dropped 12% in March" not "Metric deviation detected"
- **Helpful, not hand-holding** — Tell the user what to do once. Trust them.
- **Direct** — No filler words. No "Please note that..." Just say it.

### Naming Conventions Used in UI
| Term | What It Means |
|---|---|
| **Analysis** | A single uploaded file + all its cleaning + insights |
| **Dataset** | The cleaned version of the uploaded file |
| **Insight** | An AI-generated natural language observation |
| **Issue** | A data quality problem found during cleaning |
| **Suggestion** | An AI recommendation for the user's goals |
| **Run** | One execution of the cleaning pipeline on a file |
| **Workspace** | A collection of related analyses (e.g., "Q3 Payroll") |
| **Goal** | The business objective the user defines before analysis |

---

# SECTION 1: PUBLIC PAGES (PRE-LOGIN)

---

## PAGE 1.1 — LANDING PAGE

---

### 1.1.1 — Navigation Bar

**Logo:** `RefineX`
**Tagline under logo:** `Data Intelligence`

**Nav Links:**
- `How It Works`
- `Features`
- `Use Cases`
- `Pricing`
- `Blog`

**CTA Buttons:**
- `Sign In` (ghost/outline)
- `Start for Free →` (primary, filled)

---

### 1.1.2 — Hero Section

**Pre-headline label:**
`The Data Analyst in Your Browser`

**Headline (large, bold):**
```
Your data has answers.
RefineX finds them.
```

**Subheadline:**
```
Upload any CSV or spreadsheet. RefineX cleans it, 
understands it, and tells you what it actually means — 
in plain language. No code. No data science degree. 
No waiting.
```

**Primary CTA:**
`Analyze Your First File Free →`

**Secondary CTA:**
`Watch 2-min Demo`

**Trust signal below CTAs:**
`No credit card required · Works with CSV, XLSX, XLS · Results in under 60 seconds`

**Hero Visual Description (for designer):**
An animated mockup showing a raw messy spreadsheet on the left transforming into a clean dashboard with charts on the right. The transformation should be animated — rows cleaning themselves, colors appearing, insights sliding in.

**Social proof strip below hero:**
```
Trusted by teams at schools, hospitals, NGOs, retailers, and exporters worldwide
```
+ 5 generic industry logos (placeholder)

---

### 1.1.3 — Problem Section

**Section label:** `WHY IT EXISTS`

**Headline:**
```
Most organizations collect data.
Almost none can use it.
```

**Body:**
```
You have spreadsheets. Months of records. Years of data. 
But making sense of it requires tools that assume you're 
a developer, or consultants who charge by the hour.

RefineX was built for the people actually doing the work — 
school administrators, clinic managers, NGO coordinators, 
store owners — who need answers, not software degrees.
```

**3 Problem Cards:**

Card 1:
- Icon: messy grid
- Title: `Your data is messier than you think`
- Body: `Duplicate rows, inconsistent names, missing values, wrong formats — they silently break every report you've ever made.`

Card 2:
- Icon: clock
- Title: `Cleaning data manually takes days`
- Body: `The average analyst spends 60–80% of their time just cleaning data. That's not analysis — that's janitorial work.`

Card 3:
- Icon: broken chart
- Title: `Raw data produces wrong insights`
- Body: `Charts built on uncleaned data mislead decisions. You can't afford to act on a number that's wrong because of a typo.`

---

### 1.1.4 — How It Works Section

**Section label:** `THE PROCESS`

**Headline:**
```
Four steps from messy file
to actionable insight
```

**Step 1:**
- Number: `01`
- Title: `Upload your file`
- Body: `Drop any CSV or Excel file. Multiple sheets, merged cells, ugly formatting — we've seen worse. RefineX accepts it all.`

**Step 2:**
- Number: `02`
- Title: `Tell us your goal`
- Body: `What are you trying to understand? "Increase student admissions." "Reduce delivery costs." "Track monthly sales." Your goal shapes everything.`

**Step 3:**
- Number: `03`
- Title: `RefineX cleans and analyzes`
- Body: `Our logic-first pipeline fixes 40+ types of data issues automatically. AI handles the parts that require judgment. You're notified at every step.`

**Step 4:**
- Number: `04`
- Title: `Read your insights`
- Body: `Plain-language findings. Smart charts. Specific recommendations. Your data, finally making sense.`

---

### 1.1.5 — Features Section

**Section label:** `WHAT IT DOES`

**Headline:**
```
Everything a senior analyst would do.
At a fraction of the time and cost.
```

**Feature Grid (6 features):**

Feature 1:
- Icon: shield-check
- Title: `Intelligent Data Cleaning`
- Body: `40+ cleaning formulas across every data type — names, dates, phone numbers, amounts, scores, and more. Logic-first. No AI guesswork on your core data.`

Feature 2:
- Icon: brain
- Title: `AI-Powered Insights`
- Body: `After cleaning, our AI reads your data and generates plain-English observations. Not generic statistics — specific findings relevant to your goal.`

Feature 3:
- Icon: chart-line
- Title: `Smart Visualizations`
- Body: `RefineX selects the most relevant chart types for your data and goal. Bar, line, scatter, heatmap — chosen by logic, not defaults.`

Feature 4:
- Icon: alert-triangle
- Title: `Issue Transparency`
- Body: `Every cleaning decision is logged and explained. You always know what was changed, why, and what we couldn't fix without you.`

Feature 5:
- Icon: users
- Title: `Team Collaboration`
- Body: `Share datasets, assign columns for manual review, leave comments, and track changes across your team. Everyone sees the same clean truth.`

Feature 6:
- Icon: clock-rewind
- Title: `Full History`
- Body: `Every upload, every cleaning run, every insight is saved. Compare this month's data to last month's in one click.`

---

### 1.1.6 — Use Cases Section

**Section label:** `WHO USES IT`

**Headline:**
```
Built for every organization
that keeps records
```

**Use Case Tabs:**

Tab 1: `Schools & Universities`
- Headline: `Turn enrollment data into enrollment strategy`
- Body: `Track admissions year over year. Understand which programs are growing. See which months bring the most new students. Identify dropout patterns before they become problems.`
- Sample insight shown: `"Admissions in Science programs dropped 18% in Q2 compared to last year. March historically shows the highest drop-off rate."`

Tab 2: `Hospitals & Clinics`
- Headline: `Patient data that actually informs care`
- Body: `Track bed occupancy, patient flow, diagnosis patterns, and staff workload. Clean messy medical records automatically. Stay compliant with PII protection built in.`
- Sample insight shown: `"Average patient wait time increased 23 minutes in the last 6 weeks. Tuesday afternoons show the highest congestion."`

Tab 3: `NGOs & Development Organizations`
- Headline: `Prove your impact with clean data`
- Body: `Track beneficiary counts, program reach, fund utilization, and outcomes across projects. Generate donor-ready reports from messy field data.`
- Sample insight shown: `"Program coverage increased 34% this quarter. Northern districts remain underserved — only 12% of target beneficiaries reached."`

Tab 4: `Retail & Supermarkets`
- Headline: `Sales data that tells you what to stock next`
- Body: `Analyze salesperson performance, seasonal demand, stock movement, and customer patterns. Turn weekly sales sheets into weekly strategy.`
- Sample insight shown: `"Category B products account for 67% of revenue but only 31% of shelf space. Consider reallocation."`

Tab 5: `Logistics & Delivery`
- Headline: `Every route, every rider, every rupee`
- Body: `Track delivery performance, rider productivity, store-level metrics, and payout accuracy. Catch formula errors before they become payroll disputes.`
- Sample insight shown: `"83% of riders received minimum guarantee this period. Store-level order volume may need rebalancing."`

---

### 1.1.7 — Comparison Section

**Section label:** `VS. THE ALTERNATIVES`

**Headline:**
```
Not another BI tool.
Not another AI toy.
```

**Comparison Table:**

| | RefineX | Excel | Power BI / Tableau | Generic AI Chat |
|---|---|---|---|---|
| Cleans data automatically | ✅ | ❌ | ❌ | ⚠️ Inconsistent |
| Explains what it changed | ✅ | ❌ | ❌ | ❌ |
| Non-technical users | ✅ | ⚠️ Limited | ❌ Requires training | ⚠️ Limited |
| Logic-first (not AI guesswork) | ✅ | — | — | ❌ |
| Domain-agnostic | ✅ | ✅ | ⚠️ Complex setup | ✅ |
| Audit trail for cleaning | ✅ | ❌ | ❌ | ❌ |
| Works with messy real-world data | ✅ | ❌ | ❌ | ⚠️ |
| Plain language insights | ✅ | ❌ | ⚠️ Limited | ✅ |

---

### 1.1.8 — Testimonials Section

**Section label:** `WHAT PEOPLE SAY`

**Headline:**
```
From people who used to
spend Sundays cleaning spreadsheets
```

**Testimonial 1:**
- Quote: `"I uploaded three years of student admission data and within 90 seconds I had a chart showing exactly where we were losing applicants. That would have taken me two days in Excel."`
- Name: `Administrative Director`
- Organization: `Private School, Kathmandu`

**Testimonial 2:**
- Quote: `"Our field data comes in from 12 different people with 12 different formats. RefineX cleans it in one pass. Our donors now get reports that actually make sense."`
- Name: `Program Manager`
- Organization: `Education NGO, Lalitpur`

**Testimonial 3:**
- Quote: `"I found a formula error in our rider payment sheet that had been there for 6 weeks. RefineX caught it in the first scan. That's real money recovered."`
- Name: `Operations Lead`
- Organization: `Delivery Network, Hyderabad`

---

### 1.1.9 — Pricing Section

**Section label:** `PRICING`

**Headline:**
```
Simple pricing.
No surprise bills.
```

**Subheadline:**
`Start free. Upgrade when you need more.`

**Plan 1 — Starter (Free)**
- Price: `₹0 / $0` · `Forever free`
- Tagline: `For individuals exploring their data`
- Features:
  - `5 analyses per month`
  - `Files up to 5MB`
  - `Basic cleaning (15 formula types)`
  - `3 chart types`
  - `7-day history`
  - `Email support`
- CTA: `Start Free`

**Plan 2 — Professional (Recommended)**
- Price: `₹2,499 / $29` · `per month`
- Tagline: `For teams making data-driven decisions`
- Badge: `Most Popular`
- Features:
  - `Unlimited analyses`
  - `Files up to 100MB`
  - `Full cleaning pipeline (40+ formula types)`
  - `All chart types`
  - `Unlimited history`
  - `Multi-file comparison`
  - `AI insights & recommendations`
  - `5 team members`
  - `Priority support`
- CTA: `Start 14-Day Free Trial`
- Note: `No credit card required for trial`

**Plan 3 — Organization**
- Price: `Custom pricing`
- Tagline: `For large teams and enterprises`
- Features:
  - `Everything in Professional`
  - `Unlimited team members`
  - `SSO / SAML login`
  - `Custom data retention policy`
  - `Dedicated onboarding`
  - `SLA guarantee`
  - `API access`
  - `On-premise deployment option`
- CTA: `Talk to Sales`

**FAQ below pricing:**

Q: `Can I use RefineX for free forever?`
A: `Yes. The Starter plan is free with no time limit. You get 5 analyses per month, which is enough to explore your data and see what RefineX can do.`

Q: `What file types do you support?`
A: `CSV, XLSX, XLS, and TSV. We're adding Google Sheets and Airtable direct connections soon.`

Q: `Is my data secure?`
A: `Your files are encrypted in transit and at rest. We never train AI models on your data. You can delete your data at any time from your account settings.`

Q: `What happens when my trial ends?`
A: `You'll move to the free Starter plan automatically. You won't lose your existing analyses — you just won't be able to run new ones until you upgrade or wait for your monthly reset.`

Q: `Can I cancel anytime?`
A: `Yes. No contracts, no cancellation fees. Cancel in two clicks from your account settings.`

---

### 1.1.10 — Footer CTA Section

**Headline:**
```
Your data is waiting
to tell you something.
```

**Body:**
`Upload your first file in 30 seconds. No account required to try.`

**CTA:** `Analyze a File Now — It's Free`

---

### 1.1.11 — Footer

**Column 1 — Brand**
- Logo: `RefineX`
- Tagline: `Intelligent data cleaning and analytics for every organization.`
- Social icons: LinkedIn, Twitter/X, GitHub, YouTube

**Column 2 — Product**
- How It Works
- Features
- Pricing
- Changelog
- Roadmap
- Status Page

**Column 3 — Use Cases**
- For Schools
- For Hospitals
- For NGOs
- For Retail
- For Logistics

**Column 4 — Resources**
- Documentation
- Formula Rulebook
- Blog
- Webinars
- API Reference

**Column 5 — Company**
- About
- Careers `· We're Hiring`
- Press Kit
- Contact
- Privacy Policy
- Terms of Service

**Bottom bar:**
`© 2025 RefineX. Built for people who work with data.`

---

## PAGE 1.2 — HOW IT WORKS (Detailed)

**Headline:**
```
RefineX doesn't guess.
It follows a rulebook.
```

**Subheadline:**
`Every transformation, every decision, every flag is governed by a documented formula. Here's exactly what happens to your data.`

**Phase 1 — Upload & Structure**
- Title: `We start by understanding what you gave us`
- Content: Explains file acceptance, multi-sheet detection, header detection, structural issues (merged cells, summary rows, empty rows)

**Phase 2 — Column Classification**
- Title: `Every column gets identified and labeled`
- Content: Explains HTYPE detection — how RefineX figures out whether a column is a name, a date, a phone number, or a score

**Phase 3 — Cleaning Pipeline**
- Title: `40+ formulas run on every relevant column`
- Content: Explains the four-phase pipeline with real examples (spelling corrections, format standardization, missing value handling)

**Phase 4 — Formula Verification**
- Title: `We check if the math in your data adds up`
- Content: Explains calculated column detection and row-by-row verification

**Phase 5 — Insights**
- Title: `Then the AI takes over — briefly`
- Content: Explains exactly what the AI does (insight generation, chart recommendation, anomaly narration) and what it doesn't do (core cleaning, formula decisions)

**Full Formula Rulebook CTA:**
`Read the Complete Formula Rulebook →`

---

## PAGE 1.3 — PRICING (Standalone)

Same content as section 1.1.9, expanded with a billing toggle (Monthly / Annual — Annual saves 20%) and a full feature comparison table.

---

## PAGE 1.4 — BLOG

**Headline:** `The RefineX Journal`
**Subheadline:** `Writing about data, decisions, and the messy gap between them.`

**Featured Post:**
- Category tag: `DATA QUALITY`
- Title: `The hidden cost of a typo in a spreadsheet`
- Excerpt: `A single formatting inconsistency in a date column can silently break six months of trend analysis. Here's how to find it before it finds you.`

**Post Categories:**
- All Posts
- Data Cleaning
- Analytics
- Use Cases
- Product Updates
- Tutorials

---

## PAGE 1.5 — ABOUT

**Headline:**
```
Built by people who were
tired of cleaning data manually
```

**Body:**
```
RefineX started as a frustration.

We kept watching brilliant people — school administrators, 
clinic coordinators, NGO program managers, store owners — 
spend their best hours fighting spreadsheets instead of 
making decisions.

The tools that existed were built for data scientists. 
The people who needed help weren't data scientists. 
They were just trying to do their jobs.

So we built something for them.

RefineX is a logic-first data intelligence platform. 
We don't rely on AI to guess what your data means. 
We follow a documented rulebook, built from 20+ years 
of data analyst best practices, and we explain every 
decision we make.

Because trust in your data starts with understanding 
what was done to it.
```

**Mission Statement:**
`To make data literacy accessible to every organization, regardless of technical capacity.`

**Values:**
- `Transparency` — Every decision explained. Every formula documented.
- `Logic First` — Deterministic before probabilistic. Rules before guesses.
- `Respect for Data` — We don't change what we can't verify. We ask.
- `Access` — Built for the world, not just Silicon Valley.

---

## PAGE 1.6 — CONTACT / SUPPORT

**Headline:** `We read every message`

**Support Options:**

Option 1: `Send a message`
- Form with: Name, Email, Subject (dropdown), Message
- Dropdowns: General inquiry / Bug report / Feature request / Billing / Partnership

Option 2: `Documentation`
- Link to docs

Option 3: `Email`
- `hello@refinex.io`

**Response time note:** `We typically respond within 24 hours on business days.`

---

# SECTION 2: AUTHENTICATION PAGES

---

## PAGE 2.1 — SIGN UP

**Page headline:** `Start analyzing your data`

**Subheadline:** `Free forever. No credit card.`

**Form fields:**
- `Full Name`
- `Work Email`
- `Password` (with strength indicator)
- `Organization Name` (optional — helps personalize experience)

**CTA Button:** `Create My Account`

**Social sign-up options:**
- `Continue with Google`
- `Continue with Microsoft`

**Below form:**
`Already have an account?` `Sign In →`

**Terms note:**
`By creating an account you agree to our Terms of Service and Privacy Policy.`

---

## PAGE 2.2 — SIGN IN

**Page headline:** `Welcome back`

**Form fields:**
- `Email`
- `Password`
- `Remember me` checkbox

**CTA Button:** `Sign In`

**Links:**
- `Forgot password?`
- `Don't have an account?` `Sign up free →`

**Social sign-in:**
- `Continue with Google`
- `Continue with Microsoft`

---

## PAGE 2.3 — FORGOT PASSWORD

**Headline:** `Reset your password`
**Body:** `Enter your email and we'll send you a link to reset your password.`
**Field:** `Work Email`
**CTA:** `Send Reset Link`
**Back link:** `← Back to Sign In`

---

## PAGE 2.4 — EMAIL VERIFICATION

**Headline:** `Check your inbox`
**Body:** `We sent a verification link to **{email}**. Click it to activate your account.`
**Sub-note:** `Didn't get it? Check your spam folder, or` `Resend email`
**Support note:** `Having trouble?` `Contact support`

---

## PAGE 2.5 — ONBOARDING FLOW (New User, 3 Steps)

### Onboarding Step 1 — Tell us about yourself

**Headline:** `Welcome to RefineX. Let's set things up.`
**Subheadline:** `This takes 60 seconds and helps us personalize your experience.`

**Question 1:** `What best describes your organization?`
Options (single select, card-style):
- 🏫 `School or University`
- 🏥 `Hospital or Clinic`
- 🤝 `NGO or Non-profit`
- 🛒 `Retail or Supermarket`
- 🚚 `Logistics or Delivery`
- 🏢 `Business or Corporation`
- 🏛️ `Government or Public Sector`
- 🔬 `Research or Academia`
- `Other`

**Question 2:** `How many people work with data at your organization?`
Options:
- `Just me`
- `2–5 people`
- `6–20 people`
- `20+ people`

**CTA:** `Continue →`

---

### Onboarding Step 2 — Your first workspace

**Headline:** `Create your first workspace`
**Body:** `A workspace keeps related datasets and analyses together. You can create more later.`

**Field:** `Workspace name`
**Placeholder:** `e.g., Monthly Payroll, Student Records, Sales Reports`

**Field:** `What goal does this workspace serve?`
**Placeholder:** `e.g., Track rider payment accuracy each week`

**CTA:** `Create Workspace →`
**Skip link:** `I'll set this up later`

---

### Onboarding Step 3 — Upload your first file

**Headline:** `Now, let's see your data.`
**Body:** `Upload any CSV or Excel file. We'll show you what RefineX does with it.`

**Upload area:**
`Drag and drop your file here`
`or` `Browse files`
`Accepts CSV, XLSX, XLS · Up to 5MB on free plan`

**Sample file option:**
`Don't have a file ready?` `Try with our sample dataset →`
`(A messy sales report from a fictional retail store)`

**CTA after upload:** `Analyze This File →`
**Skip:** `Skip for now — take me to my dashboard`

---

# SECTION 3: MAIN APP — DASHBOARD

---

## PAGE 3.1 — MAIN DASHBOARD (Home)

### 3.1.1 — Top Navigation Bar

**Left:** RefineX logo

**Center search bar:**
`Search datasets, insights, or analyses...`

**Right:**
- `+ New Analysis` (primary button)
- Notification bell (with badge count)
- User avatar (dropdown: Profile, Settings, Billing, Sign Out)

---

### 3.1.2 — Left Sidebar Navigation

**Workspace selector** (dropdown at top of sidebar):
- Current workspace name
- `+ New Workspace`

**Navigation items:**
- 🏠 `Home`
- 📊 `Analyses`
- 📁 `Datasets`
- 💡 `Insights`
- 📈 `Visualizations`
- 🕓 `History`
- 👥 `Team`
- ⚙️ `Settings`

**Bottom of sidebar:**
- `Upgrade to Pro` (if on free plan)
- `Documentation`
- `Help & Support`

---

### 3.1.3 — Dashboard Welcome Banner (First 7 days only)

**Text:** `Good morning, {first_name}. Your workspace is ready.`
**Body:** `Upload your first file to start. RefineX will clean it, analyze it, and tell you what it found.`
**CTA:** `Upload a File →`
**Dismiss:** `×`

---

### 3.1.4 — Dashboard Header

**Greeting:** `Good morning, {first_name}.` ← changes by time of day
**Date:** `Tuesday, 22 February 2026`
**Context line:** `You have 3 unreviewed issues and 2 new insights since your last visit.`

---

### 3.1.5 — Quick Stats Bar (4 stat cards across top)

**Card 1 — Total Analyses**
- Label: `Analyses Run`
- Value: `{n}`
- Sub: `This month`

**Card 2 — Files Cleaned**
- Label: `Files Cleaned`
- Value: `{n}`
- Sub: `Across {n} workspaces`

**Card 3 — Issues Found & Fixed**
- Label: `Issues Resolved`
- Value: `{n}`
- Sub: `{n} flagged · {n} auto-fixed`

**Card 4 — Data Quality Score**
- Label: `Avg. Data Quality`
- Value: `{n}/100`
- Sub: `↑ {n} pts from last month`

---

### 3.1.6 — Recent Analyses Section

**Section title:** `Recent Analyses`
**Link:** `View all →`

**Analysis Card (repeated per recent file):**
- File icon (type-specific: CSV, XLSX)
- File name: `Raw_Data.xlsx`
- Workspace tag: `Rider Payments`
- Date: `Analyzed 2 hours ago`
- Status badge: one of — `Complete` · `Issues Found` · `Awaiting Review` · `In Progress`
- Stats row: `415 rows · 13 columns · 8 issues found · 3 auto-fixed`
- Data Quality Score: small circular gauge showing score
- Actions: `View Report` · `Re-run` · `Share`

**Empty state (no analyses yet):**
- Illustration: empty file tray
- Headline: `No analyses yet`
- Body: `Upload your first file and RefineX will get to work.`
- CTA: `Analyze a File →`

---

### 3.1.7 — Insights Feed Section

**Section title:** `Latest Insights`
**Link:** `View all insights →`

**Insight Card (repeated):**
- Category tag: `PERFORMANCE` · `ANOMALY` · `TREND` · `WARNING` · `OPPORTUNITY`
- Insight text (example): `"Rider productivity at Manikonda store is 42% above the network average this week. Consider redistributing order load from underperforming stores."`
- Source: `From: Raw_Data.xlsx · Rider Payments`
- Timestamp: `Generated 2 hours ago`
- Actions: `Mark as read` · `Save` · `Share`

**Empty state:**
- Headline: `No insights yet`
- Body: `Run your first analysis and RefineX will generate insights based on your data and goals.`

---

### 3.1.8 — Visualizations Carousel Section

**Section title:** `Your Charts`
**Link:** `Open Visualization Studio →`

**Chart thumbnails** (3–4 visible, scrollable):
- Chart thumbnail image
- Chart title: e.g., `Orders by Store — This Period`
- File source: `Raw_Data.xlsx`
- Chart type badge: `Bar` · `Line` · `Scatter` · `Heatmap`
- Actions: `Expand` · `Download` · `Edit`

**Empty state:**
- Headline: `No charts yet`
- Body: `Charts are created automatically after your first analysis.`

---

### 3.1.9 — Recommendations Section (AI-powered)

**Section title:** `RefineX Recommends`
**Section subtext:** `Based on your data patterns and goals`

**Recommendation Card 1 (example):**
- Icon: trend-up
- Tag: `THIS MONTH`
- Title: `Order volume typically peaks in the 3rd week of this month`
- Body: `Based on historical patterns in your dataset, delivery demand usually increases 18–22% between days 15–21. Consider increasing rider availability during this window.`
- Source: `Pattern detected across 3 months of data`
- Action buttons: `Got it` · `Show me the data`

**Recommendation Card 2 (example):**
- Icon: alert
- Tag: `DATA HEALTH`
- Title: `Your last 3 uploads have had name casing inconsistencies`
- Body: `Rider names in your payment files are consistently entered in mixed case. This affects deduplication and may be causing some riders to appear multiple times. Consider standardizing data entry at the source.`
- Action buttons: `Ignore` · `Fix in my files`

**Recommendation Card 3 (example):**
- Icon: lightbulb
- Tag: `OPPORTUNITY`
- Title: `You have 6 months of data — you can now run a seasonal trend analysis`
- Body: `With 6 uploads in the same format, RefineX can detect seasonal patterns in your order volume. This analysis takes about 90 seconds.`
- Action button: `Run Trend Analysis →`

---

### 3.1.10 — Upload Shortcut (always visible)

**Floating card at bottom of dashboard or persistent widget:**
- `+ Analyze a new file`
- `Drop a file here or click to browse`
- Accepts: CSV, XLSX, XLS

---

## PAGE 3.2 — ANALYSIS FLOW (Upload → Results)

This is the core product flow. A user uploads a file and walks through the analysis.

---

### 3.2.1 — Upload Screen

**Headline:** `What would you like to analyze?`

**Upload zone:**
```
Drag and drop your file here

or

Browse files
```
`Supported formats: CSV, XLSX, XLS, TSV · Max file size: 100MB`

**After file is selected, show:**
- File name: `Raw_Data.xlsx`
- File size: `2.4 MB`
- Detected: `2 sheets found`
- `Change file` link

**Goal input:**
`What is this analysis for?`
`Placeholder: e.g., "Track rider payment accuracy" or "Understand monthly sales trends"`
`Subtext: This helps RefineX choose the most relevant insights and charts.`

**Workspace selection:**
`Add to workspace:`
Dropdown: `[Current Workspace]` · `+ Create new workspace`

**CTA:** `Start Analysis →`

---

### 3.2.2 — Processing Screen (Live Progress)

**Headline:** `Analyzing your file...`

**Progress tracker (4 phases, animated):**

Phase 1 (in progress / complete):
- Icon: structure grid
- `Structural Analysis`
- Status: `Complete — 2 sheets detected, 1 summary row separated, 2 empty rows removed`

Phase 2:
- Icon: tag
- `Column Classification`
- Status: `Classifying 13 columns...`
- `Store Name → Organization Name`
- `Contact Number → Phone Number`
- `Rider First Name → First Name`
- *(animates as each column is classified)*

Phase 3:
- Icon: wrench
- `Data Cleaning`
- Status: `Running 40+ formulas...`
- Progress bar showing `23 of 415 rows processed`

Phase 4:
- Icon: lightbulb
- `Generating Insights`
- Status: `Waiting...`

**Processing messages (rotate every few seconds):**
- `Checking for duplicate records...`
- `Verifying formula integrity...`
- `Detecting outliers...`
- `Cross-referencing column relationships...`
- `Generating natural language summary...`

**Cancel button:** `Cancel Analysis`

---

### 3.2.3 — Analysis Complete — Overview Tab

**Page header:**
- File name: `Raw_Data.xlsx`
- Workspace: `Rider Payments`
- Analyzed: `22 Feb 2026 · 3 minutes ago`
- Data Quality Score (large, prominent): `90 / 100` with color ring
- Share button · Download button · Re-run button

**Tabs:**
`Overview` · `Issues` · `Dataset` · `Visualizations` · `Insights` · `History`

---

**OVERVIEW TAB CONTENT:**

**Summary Cards Row:**

Card 1: `415 rider records`
Card 2: `13 columns`
Card 3: `8 issues found`
Card 4: `5 auto-fixed · 3 need review`

**What We Found (executive summary, AI-generated):**
```
This is a rider payment sheet covering 25 dark store locations 
in Hyderabad. The data is structurally clean with one major 
exception: a TOTAL summary row at the bottom was accidentally 
included in the data body and has been removed.

All three payment formulas were detected and verified: 
Fuel (Distance × ₹3), Payment on Orders (₹500 + ₹40 per 
extra order), and Total Earning (Payment + Fuel). No formula 
errors were found.

The main quality issue is name casing — 255 rider names are 
entered in inconsistent formats. This does not affect calculations 
but will cause problems with deduplication across future uploads.

One cross-sheet discrepancy was found: the summary sheet 
reports 567 total riders while the payment sheet contains 415. 
This needs your review.
```

**Issues Summary (expandable list):**
- 🔴 `1 critical` — Cross-sheet rider count discrepancy (152 riders)
- 🟠 `3 important` — 255 name casing issues, 1 spelling error in column name, newline in store name
- 🟡 `4 minor` — Float-to-string conversion needed, stray value in empty row, 2 null rows, 241 MG eligibility flags

**Quick Actions:**
- `Review All Issues`
- `View Cleaned Dataset`
- `See Visualizations`
- `Read Full Insights`

---

### 3.2.4 — Issues Tab

**Header:**
`8 Issues Found · 5 Auto-Fixed · 3 Need Your Review`

**Filter bar:**
`All` · `Critical` · `Important` · `Minor` · `Auto-Fixed` · `Needs Review`

**Issue Cards:**

---

**Issue Card (Critical — Needs Review):**

Badge: 🔴 `CRITICAL`
Status badge: `NEEDS YOUR REVIEW`

Title: `Cross-sheet rider count discrepancy`

Body:
```
The Store Avg. Orders sheet reports 567 total riders, but the 
Payment Sheet contains 415 rider records. 152 riders are 
unaccounted for.

This may mean:
· Some riders were not included in this payment period
· The summary sheet covers a different time range
· The payment sheet is incomplete
```

**What we did:** `Nothing — this requires your judgment`

**Actions:**
`This is expected — the sheets cover different periods`
`The payment sheet is incomplete — I'll upload the missing records`
`I'm not sure — flag for team review`

---

**Issue Card (Important — Auto-Fixed):**

Badge: 🟠 `IMPORTANT`
Status badge: ✅ `AUTO-FIXED`

Title: `Column name spelling error: "Fule" → "Fuel"`

Body:
```
The column named "Fule" appeared to be a typo for "Fuel". 
The column name has been corrected.

Original: Fule
Corrected: Fuel

This column stores fuel reimbursement amounts calculated 
as Distance × ₹3.00.
```

**What we did:** `Renamed column. Original name preserved in audit log.`

**Undo link:** `Undo this change`

---

**Issue Card (Important — Needs Review):**

Badge: 🟠 `IMPORTANT`
Status badge: `NEEDS YOUR REVIEW`

Title: `255 rider names have inconsistent casing`

Body:
```
Rider names are entered in three inconsistent formats 
across the dataset:

· 149 first names are all-lowercase (e.g., "gangirala")
· 106 first names are ALL-CAPS (e.g., "AVULA")
· Remaining names are in Title Case (correct)

This inconsistency does not affect payments but will cause 
duplicate riders to appear in future deduplication checks.
```

**Proposed fix:** `Standardize all names to Title Case`

**Preview:**
```
Before → After
gangirala Anirudh → Gangirala Anirudh
AVULA Adharsh → Avula Adharsh
buchala sainikhil → Buchala Sainikhil
```

`Showing 3 of 255`

**Actions:**
`Apply Title Case to All Names` (primary)
`Review Each Name Manually`
`Skip — I'll fix this later`

---

**Issue Card (Minor — Auto-Fixed):**

Badge: 🟡 `MINOR`
Status badge: ✅ `AUTO-FIXED`

Title: `Trailing newline in store name: NM West Marredpally`

Body:
```
6 rows had the store name "Dark Store - Hyderabad - NM West 
Marredpally\n" — with a hidden newline character at the end.

This would cause filtering and cross-sheet joins to fail 
silently for this store.
```

**What we did:** `Stripped trailing newline from all 6 rows.`

---

### 3.2.5 — Dataset Tab

**Header:** `Cleaned Dataset · 415 rows · 13 columns`

**Sub-header controls:**
- `Show original` / `Show cleaned` toggle
- `Highlight changes` toggle (shows changed cells in yellow)
- `Filter rows` dropdown
- `Search rows` input
- `Download CSV` · `Download XLSX`

**Data table** — full scrollable table of cleaned data

**Column headers with metadata tags:**
Each column header shows:
- Column name
- HTYPE badge (e.g., `📞 Phone` · `👤 Name` · `💰 Amount`)
- Quality score (small indicator)
- Sort/filter options

**Row-level indicators:**
- Yellow highlight on changed cells
- 🔴 dot on rows with unresolved issues
- ✅ dot on rows that were cleaned

**Pagination:** `Showing 1–50 of 415 rows` · `< Previous` · `Next >`

---

### 3.2.6 — Visualizations Tab

**Header:** `Visualizations`
**Sub:** `RefineX selected these charts based on your data and goal`

**Chart 1:**
- Title: `Orders by Store — Current Period`
- Type: `Horizontal Bar Chart`
- Insight label below: `Nacharam leads with 355 orders. Attapur has the lowest volume at 67.`
- Actions: `Expand` · `Download PNG` · `Download SVG` · `Edit Chart`

**Chart 2:**
- Title: `Rider Earnings Distribution`
- Type: `Histogram`
- Insight label: `Most riders earned between ₹600–₹800. 8 riders earned under ₹100 (single-order riders).`

**Chart 3:**
- Title: `MG Dependency by Store`
- Type: `Stacked Bar (MG vs non-MG riders)`
- Insight label: `Vanasthalipuram has 100% MG dependency — every rider received minimum guarantee.`

**Chart 4:**
- Title: `Order Count vs. Total Earning (per rider)`
- Type: `Scatter Plot`
- Insight label: `Strong positive correlation (r=0.87). One outlier rider at 47 orders is visible.`

**Chart 5:**
- Title: `Top 10 Riders by Total Earning`
- Type: `Ranked Bar`

**"Add a chart" button:**
`+ Create Custom Chart`

---

### 3.2.7 — Insights Tab

**Header:** `Insights`
**Sub:** `Generated by RefineX AI based on your cleaned data and goal`

**Goal reminder bar:**
`Your goal: Track rider payment accuracy` · `Edit goal`

**Insight 1:**
- Category: `ANOMALY`
- Headline: `152 riders in the summary sheet are not in the payment sheet`
- Body: `The Store Avg. Orders sheet lists 567 total riders, but your payment sheet contains only 415. The 152-rider gap may indicate missing payment records, a different time range, or incomplete data export. This discrepancy should be investigated before using this data for payroll.`
- Severity: `High`
- Action: `Flag for Team Review`

**Insight 2:**
- Category: `EFFICIENCY`
- Headline: `83% of riders required minimum guarantee payment this period`
- Body: `345 out of 415 riders received the ₹500 MG floor payment, meaning their order-based earnings alone were below the store threshold. This is a significant cost indicator. It suggests either the MG threshold is set conservatively, or order volume is insufficient to allow most riders to earn above the floor independently.`
- Severity: `Medium`
- Action: `Show related data`

**Insight 3:**
- Category: `PERFORMANCE`
- Headline: `Manikonda store has the highest average orders per rider (18.83)`
- Body: `Despite having only 12 riders — one of the smaller teams — Manikonda's riders averaged 18.83 orders each this period, the highest in the network. Habsiguda and Nacharam also perform above average. Attapur and NM West Marredpally show the lowest averages (7.44 and 9.33 respectively).`
- Severity: `Informational`

**Insight 4:**
- Category: `DATA QUALITY`
- Headline: `All three payment formulas verified — no errors found`
- Body: `Fuel reimbursement (Distance × ₹3.00), Payment on Orders (₹500 + ₹40 per extra order above 16), and Total Earning (Payment + Fuel) were all verified across every row. No calculation discrepancies were found in the payment data.`
- Severity: `Good`

**Insight 5:**
- Category: `ATTENTION`
- Headline: `8 riders completed only 1 order and earned under ₹50`
- Body: `Eight riders delivered a single order this period, earning between ₹8.57 and ₹41.48. None received minimum guarantee. These may be new riders, test accounts, or early churners. Consider a separate review process for single-order riders.`
- Severity: `Low`

---

### 3.2.8 — History Tab (per analysis)

**Header:** `Analysis History — Raw_Data.xlsx`

**Timeline:**

Event 1:
- Timestamp: `22 Feb 2026, 14:32`
- Event: `Analysis completed`
- Detail: `415 rows processed · 8 issues found · 5 auto-fixed`

Event 2:
- Timestamp: `22 Feb 2026, 14:33`
- Event: `Issue resolved by you`
- Detail: `Applied Title Case to 255 rider names`

Event 3:
- Timestamp: `22 Feb 2026, 14:35`
- Event: `Issue marked as expected`
- Detail: `Cross-sheet discrepancy marked as "different time periods"`

Event 4:
- Timestamp: `22 Feb 2026, 14:40`
- Event: `Chart downloaded`
- Detail: `"Orders by Store" exported as PNG`

---

## PAGE 3.3 — ANALYSES LIST PAGE

**Page title:** `Analyses`
**Subtext:** `All files you've analyzed in this workspace`

**Filter/sort bar:**
- Search: `Search by file name or goal...`
- Filter: `All Statuses` · `Complete` · `Issues Found` · `Needs Review`
- Sort: `Most Recent` · `Oldest` · `Highest Quality Score` · `Lowest Quality Score`
- View toggle: Grid / List

**Analysis cards (grid or list view)** — same as dashboard recent cards

**Empty state:**
- Headline: `No analyses in this workspace yet`
- Body: `Upload your first file to get started.`
- CTA: `Upload a File →`

---

## PAGE 3.4 — INSIGHTS PAGE (Global)

**Page title:** `Insights`
**Subtext:** `AI-generated observations across all your datasets`

**Filter bar:**
- `All` · `Anomalies` · `Trends` · `Performance` · `Data Quality` · `Opportunities`
- `Date range` picker
- `Workspace` filter

**Insight feed** — all insights across all analyses, newest first

**Saved Insights section:**
`Insights you've saved` (bookmarked items)

---

## PAGE 3.5 — VISUALIZATIONS STUDIO

**Page title:** `Visualization Studio`
**Subtext:** `All charts from your analyses. Create new ones. Download any.`

**Chart gallery** (grid view of all charts ever created)
- Filter by: Workspace, Analysis, Chart Type, Date

**Create Custom Chart button:** `+ New Chart`

**Custom Chart Builder:**
- Select dataset (from analyzed files)
- Select X-axis column
- Select Y-axis column (or metric)
- Select chart type: Bar, Line, Scatter, Pie, Heatmap, Area, Radar, Treemap
- Add filters
- Add labels / title
- Color scheme picker
- `Generate Chart`

---

## PAGE 3.6 — HISTORY PAGE

**Page title:** `History`
**Subtext:** `Every upload, every change, every insight — fully logged`

**Timeline view** — chronological log of all actions across all analyses

**Entry types and their display:**

- 📤 `File uploaded: Raw_Data.xlsx` · `22 Feb 2026, 14:30`
- 🔧 `Auto-fix applied: Column renamed "Fule" → "Fuel"` · `22 Feb 2026, 14:31`
- 👤 `You resolved: Name casing applied to 255 rows` · `22 Feb 2026, 14:33`
- 💡 `5 insights generated` · `22 Feb 2026, 14:32`
- 📊 `Chart created: Orders by Store` · `22 Feb 2026, 14:35`
- ⬇️ `Chart downloaded: Orders by Store (PNG)` · `22 Feb 2026, 14:40`
- 👥 `Shared with: priya@org.com` · `22 Feb 2026, 14:45`

**Filter options:**
- By action type
- By date range
- By workspace
- By user (team plan)

**Export history:** `Download full audit log (CSV)`

---

## PAGE 3.7 — TEAM PAGE

**Page title:** `Team`
**Subtext:** `Manage who has access to your workspaces`

**Members table:**

| Name | Email | Role | Last Active | Status |
|---|---|---|---|---|
| Aarav Sharma | aarav@org.com | Admin | Today | Active |
| Priya Mehta | priya@org.com | Analyst | Yesterday | Active |
| Ravi Kumar | ravi@org.com | Viewer | 5 days ago | Active |

**Roles explained:**
- `Admin` — Full access. Can invite, remove, and manage billing.
- `Analyst` — Can upload files, run analyses, create charts. Cannot manage team.
- `Viewer` — Can view analyses, charts, and insights. Cannot upload or modify.

**Invite member:**
- Field: `Email address`
- Dropdown: `Role`
- Button: `Send Invite`

**Pending invites section:**
`Priya@neworg.com — Invite sent 2 days ago` · `Resend` · `Cancel`

---

## PAGE 3.8 — SETTINGS PAGE

**Page title:** `Settings`

**Tabs:**
- `Profile`
- `Workspace`
- `Notifications`
- `Integrations`
- `Billing`
- `Data & Privacy`

---

**Profile Tab:**
- Avatar upload
- Full Name (editable)
- Email (editable)
- Organization
- Timezone
- Language: `English` · `हिन्दी` · `नेपाली`
- `Save Changes`
- `Change Password` section
- `Delete Account` (danger zone, red)

---

**Workspace Tab:**
- Workspace name (editable)
- Default goal for this workspace
- Default currency (for amount columns)
- Default country (for phone/postal validation)
- Delete workspace (danger zone)

---

**Notifications Tab:**

Toggle controls:
- `Email me when an analysis is complete` — On/Off
- `Email me when issues need my review` — On/Off
- `Email me when a team member shares something` — On/Off
- `Weekly data health digest` — On/Off
- `Monthly insights summary` — On/Off
- `Product updates and announcements` — On/Off

---

**Integrations Tab:**

Available integrations:
- Google Sheets `Connect →` (coming soon badge)
- Google Drive `Connect →` (coming soon)
- Airtable `Connect →` (coming soon)
- Slack `Connect →` (coming soon)
- Zapier `Connect →` (coming soon)
- REST API `View API Keys →`

---

**Billing Tab:**
- Current plan: `Professional`
- Next billing date: `22 March 2026`
- Amount: `₹2,499 / month`
- Payment method: Visa ending in 4242 · `Update`
- `Download Invoice`
- Usage this month: `23 analyses of unlimited`
- `Upgrade Plan` / `Downgrade Plan`
- `Cancel Subscription` (danger zone)

---

**Data & Privacy Tab:**
- `Download all my data` — Exports everything as ZIP
- `Delete all analyses` — Clears all analysis data (keeps account)
- `Delete account permanently` — Full deletion, 30-day recovery window
- PII settings: `Mark certain columns as restricted by default` toggle
- Data retention: `Keep analysis history for: 30 days / 90 days / 1 year / Forever`

---

## PAGE 3.9 — WORKSPACES PAGE

**Page title:** `Workspaces`
**Subtext:** `Organize your analyses by project, department, or time period`

**Workspace Cards:**

Card:
- Workspace name: `Rider Payments`
- Description: `Weekly payment tracking for delivery network`
- Stats: `12 analyses · 47 insights · Last active: Today`
- Members: `3 members`
- Actions: `Open` · `Settings` · `Archive`

**Create workspace button:** `+ New Workspace`

**Archived workspaces toggle:** `Show archived workspaces`

---

# SECTION 4: NOTIFICATIONS & SYSTEM MESSAGES

---

## 4.1 — Notification Center (Bell dropdown)

**Header:** `Notifications`
**Mark all read link**

**Notification types:**

Type 1 — Analysis complete:
`Your analysis of Raw_Data.xlsx is complete. 8 issues found, 5 auto-fixed.`
`2 minutes ago` · `View Report →`

Type 2 — Issue needs review:
`3 issues in Raw_Data.xlsx need your input before analysis can finalize.`
`5 minutes ago` · `Review Issues →`

Type 3 — Team activity:
`Priya Mehta resolved 3 issues in Monthly Sales Report.`
`1 hour ago`

Type 4 — Insight:
`New insight: Your Manikonda store is outperforming the network average by 42%.`
`2 hours ago` · `View Insight →`

Type 5 — System:
`Your Professional trial ends in 3 days. Upgrade to keep access.`
`Today` · `Upgrade Now →`

---

## 4.2 — Toast Notifications (in-app, temporary)

**Success:**
`✅ Analysis complete. 415 rows cleaned.`

**Info:**
`ℹ️ 3 issues need your review before this analysis is finalized.`

**Warning:**
`⚠️ Large file detected. Analysis may take up to 2 minutes.`

**Error:**
`❌ File format not supported. Please upload a CSV, XLSX, or XLS file.`

**Auto-fix notification:**
`🔧 We fixed 5 issues automatically. See what changed →`

---

## 4.3 — Empty States (All Pages)

**No analyses:**
Headline: `Nothing to show yet`
Body: `Run your first analysis and your results will appear here.`
CTA: `Upload a File`

**No insights:**
Headline: `No insights generated yet`
Body: `Insights are created after your first analysis. Try uploading a file.`

**No visualizations:**
Headline: `No charts yet`
Body: `Charts are automatically created during analysis.`

**No team members:**
Headline: `You're the only one here`
Body: `Invite teammates to collaborate on analyses and share insights.`
CTA: `Invite a Team Member`

**No history:**
Headline: `Nothing logged yet`
Body: `Every action you and your team take will appear here.`

**Search with no results:**
Headline: `No results for "{query}"`
Body: `Try a different search term or browse your analyses directly.`

---

## 4.4 — Error Pages

**404 — Page Not Found:**
Headline: `This page doesn't exist`
Body: `The page you're looking for may have been moved or deleted.`
CTA: `Back to Dashboard`

**500 — Server Error:**
Headline: `Something went wrong on our end`
Body: `We've been notified and are working on it. Try refreshing, or come back in a few minutes.`
CTA: `Try Again` · `Contact Support`

**File processing error:**
Headline: `We couldn't process this file`
Body: `This can happen with heavily formatted Excel files, password-protected sheets, or corrupted files. Try saving as CSV and re-uploading.`
CTA: `Try Again` · `Contact Support`

**File too large:**
Headline: `This file is too large for your plan`
Body: `Your file is {size}MB. The {plan} plan supports files up to {limit}MB.`
CTA: `Upgrade to Pro` · `Compress and try again`

**Session expired:**
Headline: `Your session has expired`
Body: `Please sign in again to continue.`
CTA: `Sign In`

---

## 4.5 — Confirmation Dialogs

**Delete analysis:**
Title: `Delete this analysis?`
Body: `"Raw_Data.xlsx" and all its insights, charts, and history will be permanently deleted. This cannot be undone.`
Confirm: `Delete Analysis`
Cancel: `Keep It`

**Re-run analysis:**
Title: `Re-run this analysis?`
Body: `This will re-process the original file with the latest cleaning rules. Any manual changes you made will be preserved, but may be overridden if they conflict with new findings.`
Confirm: `Re-run`
Cancel: `Cancel`

**Remove team member:**
Title: `Remove {name} from this workspace?`
Body: `They will lose access immediately. Their past contributions will remain.`
Confirm: `Remove Member`
Cancel: `Cancel`

**Cancel subscription:**
Title: `Are you sure you want to cancel?`
Body: `You'll keep Pro access until {date}. After that, you'll move to the free plan. Your data and analyses will be kept for 90 days.`
Confirm: `Yes, Cancel My Subscription`
Cancel: `Keep My Subscription`

---

# SECTION 5: ONBOARDING & HELP CONTENT

---

## 5.1 — Tooltips (hover text on UI elements)

**Data Quality Score:**
`A 0–100 score measuring Completeness, Validity, Uniqueness, Consistency, and Accuracy across all columns. Higher is better.`

**MG Applicable badge (in example data):**
`RefineX detected this as a boolean (yes/no) column. Values were standardized from 1.0/0.0 to True/False.`

**HTYPE badge:**
`Header Type — the category RefineX assigned to this column. Click to see which cleaning formulas were applied.`

**Issue severity badges:**
- Critical: `Requires your immediate attention. Analysis accuracy may be affected.`
- Important: `Significant issue found. Review recommended before using this data.`
- Minor: `Small issue detected. Auto-fixed or low impact.`

**Auto-Fixed badge:**
`RefineX applied a safe, reversible fix. Click to see what changed and undo if needed.`

---

## 5.2 — Onboarding Tooltips (first-time user tooltips, highlighted with pulse dot)

After first analysis completes:
1. `This is your Data Quality Score. A score above 80 means your data is ready to use.` → (points to DQS gauge)
2. `These are issues we found. Some were fixed automatically. Others need your decision.` → (points to issues tab)
3. `These charts were chosen because they best represent your data and goal.` → (points to visualizations tab)
4. `These are AI-generated insights — specific observations about your data in plain language.` → (points to insights tab)

---

## 5.3 — Feature Discovery Banners (contextual, dismissible)

**When user has 3+ analyses:**
`💡 You now have enough data to compare periods. Try uploading last month's file and selecting "Compare with existing analysis".`
`Try It →` · `Dismiss`

**When user has only one workspace:**
`💡 Workspaces help you organize analyses by project or department. Create a second workspace for a different dataset type.`
`Create Workspace →` · `Dismiss`

**When user hasn't invited anyone:**
`💡 Analyses are more useful with team input. Invite a colleague to review flagged issues.`
`Invite Someone →` · `Dismiss`

---

## 5.4 — Help Documentation Structure

**Docs homepage sections:**
- Getting Started
  - Uploading your first file
  - Understanding your analysis results
  - Reading the Data Quality Score
  - Resolving issues

- Core Concepts
  - What is a Header Type (HTYPE)?
  - How the cleaning pipeline works
  - The 4 cleaning phases explained
  - When does RefineX use AI?

- Column Types Reference
  - Full list of all 47 Header Types with examples

- Formula Reference
  - Complete formula rulebook (linked to PDF)

- Charts & Visualizations
  - How chart types are selected
  - Creating custom charts

- Team & Collaboration
  - Inviting team members
  - Roles and permissions
  - Commenting and flagging

- Integrations
  - API reference
  - Webhooks
  - Google Sheets (coming soon)

- Troubleshooting
  - My file won't upload
  - Analysis took too long
  - A cleaning decision seems wrong
  - How to undo changes

---

# SECTION 6: EMAIL COMMUNICATIONS

---

## 6.1 — Transactional Emails

**Welcome email:**
Subject: `Welcome to RefineX — let's analyze your first file`
Body:
```
Hi {first_name},

Your account is ready.

RefineX is your personal data analyst — upload any CSV or 
Excel file and get clean data, smart charts, and plain-language 
insights within minutes.

Start by uploading your first file:
[Analyze a File →]

If you have any questions, reply to this email. 
We read every message.

— The RefineX Team
```

**Analysis complete email:**
Subject: `Your analysis of {filename} is ready`
Body:
```
Hi {first_name},

Your file {filename} has been analyzed.

Data Quality Score: {score}/100
Issues found: {n} ({n} auto-fixed, {n} need your review)
Insights generated: {n}

[View Your Report →]

— RefineX
```

**Issue review reminder (24 hours after upload if issues unresolved):**
Subject: `3 issues in {filename} are waiting for your review`
Body:
```
Hi {first_name},

Your analysis of {filename} has 3 issues that need your 
input to be resolved.

[Review Issues →]

Issues don't expire, but unresolved issues may affect 
the accuracy of your insights.

— RefineX
```

**Trial ending email (3 days before):**
Subject: `Your RefineX Pro trial ends in 3 days`

**Monthly digest email:**
Subject: `Your RefineX summary for {month}`
Includes: Total analyses run, files cleaned, top insight of the month, data quality trend

---

# SECTION 7: MOBILE APP CONTENT

*RefineX mobile is a companion app for reviewing insights and approving issues — not full analysis.*

---

## 7.1 — Mobile Navigation (Bottom bar)

- 🏠 `Home`
- 💡 `Insights`
- ⚠️ `Issues` (badge with count)
- 📊 `Charts`
- 👤 `Profile`

---

## 7.2 — Mobile Home Screen

**Header:** `Good morning, {name}`

**Quick stat cards (scrollable horizontal):**
- `{n} analyses this month`
- `{n} issues need review`
- `{n} new insights`

**Recent analyses list**
**Recent insights feed**

---

## 7.3 — Mobile Issue Review

**Issue card (swipeable):**
- Issue title
- Description
- Proposed fix
- Swipe right: `Approve Fix ✅`
- Swipe left: `Flag for Review 🚩`
- Tap: `See Full Details`

---

## 7.4 — Mobile Empty States

**No issues:**
`🎉 All caught up`
`No issues need your attention right now.`

**No insights:**
`No new insights today.`
`Run an analysis from the desktop to generate insights.`

---

# SECTION 8: ADMIN PANEL (Internal — RefineX Team Only)

*Not visible to customers. For RefineX operations team.*

---

**Dashboard overview:**
- Total registered users
- Active users (last 30 days)
- Total analyses run today / this week / this month
- Average analysis time
- Most common file types uploaded
- Most triggered issue types
- Error rate in processing

**User management:**
- Search users
- View plan, usage, last active
- Manually upgrade/downgrade plan
- Impersonate user (for support)
- Ban / suspend account

**Feature flags:**
- Toggle features on/off per user or plan tier
- A/B test control panel

**System health:**
- Processing queue status
- Error logs
- Uptime monitor

---

*End of RefineX Frontend Content Specification*
*Version 1.0 — Covers Landing Page through Admin Panel*
*Total pages defined: 35+*
*Total UI strings defined: 500+*
