# Agent instructions

## Browser checks and UI pull requests

- Use the Playwright skill in `.agents/skills/playwright-cli/SKILL.md` for browser checks.
- Always install a browser when setting up this repository: follow the Installation section of `.agents/skills/playwright-cli/SKILL.md`, using `npm ci` and the documented mirror download command. Do not regenerate the committed skill during normal setup.
- Use `npx playwright-cli` to run the locally installed CLI.
- For every PR that introduces UI changes, run the affected pages in the browser, inspect the result, and include screenshots in the PR description. Capture the changed UI and relevant states with `npx playwright-cli screenshot --filename=...` and embed the images where reviewers can see them.
