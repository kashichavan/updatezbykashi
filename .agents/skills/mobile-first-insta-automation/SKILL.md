---
name: mobile-first-insta-automation
description: >-
  Enterprise guide for building mobile-first responsive Instagram automation interfaces,
  Superprofile-style Reel targeting workflows, follower verification gates, and step-by-step
  automation rule execution.
---

# 📱 Mobile-First Instagram Automation Engine & Architecture Guide

This skill specifies the step-by-step execution plan and mobile-first responsive UI architecture for Instagram Reels & DM automation.

---

## 1. Step-by-Step Architecture Pipeline

```
[ User Comments on Instagram Reel ] 
               │
               ▼
[ Meta Webhook Trigger ] ───► /instagram/api/instagram/webhook/
               │
               ▼
[ 1. Check Target Scope ] ───► Matches All Reels OR Specific Reel URL/Media ID?
               │
               ▼
[ 2. Check Trigger Keyword ] ───► Does comment text contain keyword (e.g. "python", "link")?
               │
               ▼
[ 3. Post Public Comment Reply ] ───► e.g. "Thanks @user! 👋 Check your DM."
               │
               ▼
[ 4. Send Private DM & Check Follower Gate ] ───► Is user following @account_username?
               │                                      │
               ├──────► No: Ask to follow & reply "DONE" ─┤
               │                                      │
               └──────► Yes / Upon "DONE" keyword ─────┘
                                       │
                                       ▼
                       [ 5. Deliver Direct Link / Resource ]
```

---

## 2. Mobile-First Component Guidelines

1. **Touch Targets**: Minimum 48px touch height for all buttons, tab items, and dropdowns.
2. **Horizontal Swipeable Tab Navigation**: Touch-optimized smooth scrolling tabs with `scrollbar-width: none`.
3. **Card-Based Stacked Layouts**: On mobile viewports (`<768px`), all statistics grid, automation rules, and API cards stack vertically with responsive padding (`16px`).
4. **Superprofile Theme Colors**:
   - Background: Crisp Obsidian Dark (`#090D16`)
   - Accent Primary: Electric Cyan (`#06B6D4`) & Instagram Gradient (`#E1306C` to `#833AB4`)
   - Surface: Glassmorphic Slate (`rgba(17, 24, 39, 0.85)`)
