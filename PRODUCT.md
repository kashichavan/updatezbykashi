# Kashii Updatez: product

Confirmed facts only. Sources: the live site, the code, `db.sqlite3` read on 2026-11-02, and the founder's brief.

## Platform
Mobile web first. Desktop works, but most people arrive on a phone.

## Stack
Django server-rendered templates, plain CSS, small vanilla JS, no animation library. Render free plan (0.1 CPU). AdSense on pages.

## Users
Indian college students and freshers, mostly on cheap Android phones over mobile data, arriving from a WhatsApp, Telegram or Instagram link. Secondary: people who forward group links, and people using the recruiter people search.

## Product purpose
Founder's words: "I saw students wasting hours on outdated job posts and fake requirements."
Fresh jobs and internships with official apply links, bundled into shareable groups, plus free tools to make an ATS resume for the job in front of you.

## Positioning
Each listing closes seven days after posting. Groups are shareable bundles with ready broadcast text. Resumes are fitted to one real job and never invent anything.

## Operating context
Opened in a hostel, on a bus or between classes, usually from a chat. The first screen has to work over slow data on a cold server.

## Capabilities and constraints
- Tools: Resume Builder, ATS Score, Resume from Job Post, Resume Studio, Recruiter people search, Visual Code Debugger, SQL Debugger.
- Group URLs `/group/<slug>/` never change. No URL, form field name, logo or legal mention changes without the founder's agreement.
- People apply on company sites: 0 site applications recorded.
- All counts come from the database at render time.
- Native CSS motion only. GSAP was removed after problems on the live site.

## Brand commitments
Name: Kashii Updatez, domain kashiiupdatez.online. Founder: Kashinath (Kashii), developer, educator, content creator. YouTube @pythonkashi, Instagram @ikashii_07.

## Never invent
Placement counts, success stories, testimonials, company logos as partners, follower or subscriber counts, user numbers, "trusted by" claims, ratings, ATS vendor pass rates, prices, how listings are checked (until the founder states the process). No logo file exists: the brand is type only. No photographs of the founder or students were supplied beyond the existing author image.

## Evidence on hand
Database at capture: 1,227 jobs, 978 full time, 249 internship. Fresher 389, Internship 248. Bengaluru 638, Hyderabad 123, Pune 109, Chennai 71, Remote/Multiple 52, Mumbai 45. 296 live groups. Live home showed 246 open jobs and 66 internships. These change daily, so the site always reads them from the database.

## Product principles
1. The group page is the front door. It gets the most care.
2. One primary action per phone screen, within thumb reach.
3. Never block the first result with a login, OTP or popup.
4. A closing date on everything, because that is the promise.
5. Say only what the data can prove.

## Accessibility and inclusion
44px minimum touch targets, visible keyboard focus, semantic HTML, full reduced-motion path, contrast at WCAG AA, simple English, usable on a low-end Android over slow data.
