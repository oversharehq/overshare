# Overshare frontend

Next.js 16 (App Router), TypeScript, Tailwind v4. System-level context is in `../OVERVIEW.md` §3.3;
this file is about working on the UI.

> **Read `AGENTS.md` first.** This is not the Next.js you may remember — check
> `node_modules/next/dist/docs/` before writing routing or metadata code.

```bash
npm run dev     # http://localhost:3000
npm run build   # must run before tsc: PageProps/RouteContext are generated into .next/types
npx tsc --noEmit
npx eslint .
```

With no `OVERSHARE_API_URL` set, the app serves fixture scans so you can work without running
Python — `lib/mock/`. A banner marks every fixture report, and `lib/mock/guard.ts` returns 503 in a
production build rather than ever serving fabricated results as real ones. To see a report locally:

```bash
ID=$(curl -s -X POST localhost:3000/api/v1/scans \
  -H 'content-type: application/json' \
  -d '{"url":"https://myapp.lovable.app"}' | grep -oE 'scn_[a-z0-9]+')
open "http://localhost:3000/scan/$ID"          # ~12s to complete
```

A hostname matching `clean|secure|safe` returns the passing fixture instead, which is the only way
to exercise the A-grade styling.

## The design language

The interface is a **technical document, not a dashboard**: warm paper ground, Newsreader serif for
prose, IBM Plex Mono for every label and datum, hairline rules instead of cards, numbered sections,
notes floated into the right margin, captioned figures. This is a positioning decision — the product
sells published calibration, so the site should look like something measured and written down.
The reasoning, and the two rejected alternatives, are in `../OVERVIEW.md` §4.

| Where | What |
|---|---|
| `app/globals.css` | The `@theme` block: the entire palette and both font stacks. Also the `.label` class used for every mono micro-label. |
| `components/Paper.tsx` | `Shell`, `Section`, `Block`, `Note`, `Figure`, `Prose`, `Code`. |
| `lib/severity.ts` | Severity and grade styling. |
| `lib/docs.ts` | Headings and numbers shared with the root markdown docs. |
| `components/Mark.tsx` | The logo: three redacted lines, the last one unredacted. |

Colour names are semantic, not literal — `paper`, `ink`, `ink-soft`, `mute`, `faint`, `rule`,
`rule-firm`, `inset`, `plate`, and `flag` / `ochre` / `pass` for the three states. Use those.

### Rules

- **No `slate-*`, `rounded-*` or `shadow-*`.** If you reach for one, the answer is a rule
  (`border-t border-rule`) or a plate (`bg-plate`). `grep -rE "slate-|rounded-|shadow-" app components`
  should stay empty.
- **Anything global in `globals.css` goes inside `@layer base`.** Unlayered CSS outranks Tailwind
  v4's layered utilities at *any* specificity, so a bare `:focus-visible { outline: ... }` silently
  beats `focus-visible:outline-none` at every call site. This cost a debugging session.
- **Severity is weight plus a rule in two hues** — vermilion for critical/high, ochre for medium,
  plain ink for low/info. Not a five-colour pill scale: that trains people to read the palette
  instead of the finding. See the comment in `lib/severity.ts`.
- **Give grid and flex children `min-w-0` when they contain a `<pre>`.** Automatic minimum sizing
  makes the track as wide as the unwrappable command line, which overflows the whole page on mobile
  even though the `pre` itself has `overflow-x-auto`.
- **The report at `/scan/[id]` has to print.** It is the artifact people hand to a customer. The
  print rules in `globals.css` hide site chrome, expand every collapsed `<details>` so a printed
  report cannot omit a finding, and invert the ink plates so evidence is not a block of toner.

### Copy

`../marketing/04-landing-page.md` is the spec the landing page is built from, and
`../marketing/02-messaging.md` §5 is the voice. Two standing constraints: no fake trust signals, and
**no placeholder statistics** — if a number is not measured, the sentence is omitted. The `<Todo>`
component marks copy that depends on something that does not exist yet, and is written so the
surrounding sentence stays true when the marker is deleted.

`/methodology` and `/acceptable-use` restate `../METHODOLOGY.md` and `../ACCEPTABLE_USE.md`, because
the Docker build context here is `web/` alone and the pages cannot read those files. Headings and
load-bearing numbers therefore live once, in `lib/docs.ts`, and `../tests/test_docs_sync.py` fails
CI if the copies drift from each other or from the scanner. Editing prose is free; editing a
heading, a penalty or the retention window means updating `lib/docs.ts` too.

## Checking your work

There is no browser automation configured. Chrome headless over CDP is enough:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --remote-debugging-port=9333 about:blank &
```

Then drive it with `Emulation.setDeviceMetricsOverride` before screenshotting — passing
`--window-size=390,...` does **not** give you a 390px layout, because headless clamps the window to
roughly 485px and you get a clipped capture of a wider page, which looks exactly like a CSS bug.
Emulate the width, then assert nothing overflows:

```js
document.documentElement.scrollWidth <= document.documentElement.clientWidth
```

That check is what caught the only real responsive bug in the redesign. Verify at 1280 and 390, and
use `Emulation.setEmulatedMedia({media:"print"})` for the report.
