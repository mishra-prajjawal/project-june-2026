# STYLE_GUIDE.md — Write Like a Thoughtful Human

FoodConnect should read like it was written by a careful, slightly opinionated senior developer — not auto-generated. This guide covers **code voice**, **comment voice**, and the **UI/UX bar**.

---

## 1. Code voice (human, not robotic)
- **Name things for intent:** `claim_donation()`, `award_impact_points()`, `nearby_available_donations()` — not `func1`, `do_stuff`, `handle()`.
- **Small, single-purpose functions.** If a view is doing validation + DB writes + notification + scoring, split it: put rules in `services/`, reads in `selectors/`, side-effects behind events.
- **Guard clauses over deep nesting.** Return early on invalid input.
- **No magic numbers/strings.** `DONATION_STATUS.AVAILABLE`, `EXPIRY_WARNING_MINUTES = 60`.
- **Errors are specific and caught deliberately** — no bare `except:` that swallows everything.
- **Consistent formatting:** `black` + `isort` for Python, `prettier` for JS/CSS. Commit the config.
- **No dead code, no commented-out experiments, no leftover `print()` debugging.**

## 2. Comment voice (explain WHY, with a human touch)
Comments should sound like a person who understands the trade-offs. Good comments explain *why*, flag gotchas, and occasionally have a dry human aside — while staying accurate and professional.

**Do:**
```python
# We lock the row before checking status. Two NGOs hitting "Claim" at the same
# instant is the classic race here — without select_for_update the second one
# happily claims an already-taken meal and someone shows up to an empty kitchen.
with transaction.atomic():
    donation = Donation.objects.select_for_update().get(pk=donation_id)
    if donation.status != DonationStatus.AVAILABLE:
        raise AlreadyClaimed("Someone beat you to it — this one's gone.")
```

```python
# Synopsis said MD5 for password hashing. We're deliberately not doing that
# — MD5 is broken for passwords. Django's default (PBKDF2) is the right call.
# DESIGN NOTE: documented this deviation for the report.
```

**Don't:**
```python
# increment i by 1
i += 1
# set status to claimed
donation.status = "Claimed"  # obvious + adds nothing
```

**Rules of thumb**
- Comment the *reasoning*, the *edge case*, or the *decision* — never narrate the obvious line.
- Keep a module-level docstring saying what the file is responsible for.
- Mark intentional spec deviations with `# DESIGN NOTE:` and a one-line reason.
- Mark genuinely-deferred future work with `# FUTURE:` referencing PROJECT_SPEC §13 — but never use TODOs to dodge in-scope work.
- A little personality is welcome; inaccuracy and cleftover noise are not.

## 3. Commit messages (human)
- Imperative, specific: `Add concurrency-safe claim service with row lock`, `Fix leaderboard tie-break so older donor ranks higher`.
- Not: `update`, `fix bug`, `changes`, `wip wip wip`.

## 4. UI/UX bar (this is a graded deliverable — do not compromise)

### Look & feel
- **Mobile-first.** Design the small screen first, enhance up. Test on a phone viewport every phase.
- **Palette as Tailwind tokens:** primary **green** (freshness/eco), **white** (clean, airy), **orange** reserved for urgency/expiring-soon. Define in `tailwind.config.js` (`brand.green`, `brand.orange`, etc.). Don't scatter random hex values.
- **Typography:** Inter / Roboto / Open Sans, generous line-height, strong hierarchy. Self-host or load cleanly.
- **Spacing & rhythm:** consistent scale, breathing room, no cramped forms.
- **Tailwind for layout/utility; thin custom CSS layer** only for things Tailwind is awkward at — keyframe animations (the thank-you checkmark), brand flourishes. Keep custom CSS small and organized.

### Interaction
- **Donate flow ≤ ~30s, 3 steps:** Click Donate → fill ~4 fields (geolocation prefills address) → Post. Large inputs, dropdowns over typing.
- **Visual confirmation:** big animated green ✓ "Thank You" after posting. After a claim, the NGO gets donor contact + a real **"Call Now"** button (tel: link), not plain text.
- **Urgency:** items near expiry glow orange / sort to the top.
- **Live, no-refresh updates:** feed and statuses update via the reactive push layer — it should feel alive.
- **Loading/empty/error states** are designed, not blank. Skeletons or spinners on the live feed.

### Accessibility (required)
- WCAG-level contrast (green/white/orange chosen and tuned for contrast).
- Large hit targets (thumb-friendly), semantic HTML, labels tied to inputs, ARIA on dynamic regions (live feed = `aria-live`).
- Fully keyboard navigable; screen-reader sane.

### Quality smell test (ask before shipping a screen)
- Would this look at home in a polished real product, or does it look like an unstyled assignment?
- Can a restaurant manager on a cheap phone, in a hurry, post a donation without thinking?
- Does anything block, jank, or full-page-reload where it should update live?

If the answer is wrong, it's not done.
