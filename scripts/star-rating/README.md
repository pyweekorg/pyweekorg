# STAR rating preview

From the repository root, with the project's Python dependencies installed:

```sh
PYTHONPATH=. python scripts/star-rating/serve_demo.py
```

Open http://127.0.0.1:8766/p/1/. This server binds only to loopback and uses
an in-memory SQLite database, synthetic themes and a synthetic voter session.
It does not connect to production. Stop it to discard the data.

With `playwright` available to Node and its Chromium browser installed, run in
another terminal:

```sh
node scripts/star-rating/check.mjs
```

This checks keyboard selection, clicking zero, required ratings, saving and
restoring scores, mobile overflow and the no-JavaScript fallback. It also writes
`star-rating-desktop.png` and `star-rating-mobile.png` in the current directory.
Restart the demo before rerunning so that its original unrated option is restored.

Manual accessibility checks: Tab moves between rating groups; arrow keys move
between scores; Space selects a score. A screen reader should announce the theme,
score, required state and checked state. Check a narrow viewport, browser zoom,
forced-colours mode, and hovering without changing a saved score. The unselected
state must remain distinct from an explicitly chosen zero.
