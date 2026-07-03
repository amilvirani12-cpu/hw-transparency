# HW Fiscal Dashboard — Design System

Anchor: the "Budget at a Glance" pages (`Budget/budget_visualizer.py`). Every page on
the site — home page and all generated dashboards — follows this language. When
restyling a dashboard, change ONLY presentation (CSS tokens, header, nav, fonts,
chart colors). Never change data logic, numbers, table contents, or wording of
analytical text.

## Core tokens (put in `:root`)

```css
:root{
  --ink:#16202e;        /* primary text */
  --mut:#5c6c81;        /* secondary text */
  --line:#e2e8f0;       /* card borders, strong rules */
  --linesoft:#eaeff5;   /* row separators */
  --bg:#eef2f7;         /* page background base */
  --card:#fff;
  --good:#22794c;       /* positive / money in / OK status */
  --info:#1f5da0;       /* neutral emphasis / money out */
  --warn:#b45309;       /* caution */
  --bad:#b4451f;        /* negative / exception / urgent */
  --capacc:#7c3aed;     /* capital purple accent */
  --saacc:#0d9488;      /* teal accent */
  --shadow:0 1px 2px rgba(15,40,68,.05),0 10px 30px -22px rgba(15,40,68,.35);
}
```

## Page fundamentals

- Font: `'Segoe UI Variable Text','Segoe UI',-apple-system,Roboto,Helvetica,Arial,sans-serif`
  (display sizes use `'Segoe UI Variable Display'` first). No serif fonts anywhere.
- Body background: `linear-gradient(180deg,#eaeff6 0%,var(--bg) 260px)`; `line-height:1.5`.
- Font sizing (two readability bumps applied Jul 2026): body/table/paragraph/list text
  is ~16–16.5px; section body and hero subtitle ~19px; section `h2` ~22px; small
  uppercase labels, pills, table-header `th`, meta pills, and nav sit at ~13–14px; large
  display numbers (~26–27px) and hero `h1` (~31–32px) are unchanged. This is the current
  target — generated pages should render at these sizes. When touching an existing page,
  match these; never change non-font px values.
- Content wrapper: `max-width:980px;margin:0 auto;padding:26px 24px`
  (wider dashboards may use up to 1240px, keep the same padding).
- Numbers always `font-variant-numeric:tabular-nums`.

## Site nav (every page, first thing in the wrapper)

```html
<nav class="sitenav">
  <a class="brand" href="../">HW Fiscal Dashboard</a>
  <a href="../budget/">Budget</a>
  <a href="../treasurer/">Treasurer</a>
  <a href="../facilities/tours/">Facilities Tours</a>
  <a href="../facilities/bcs/">Building Condition</a>
</nav>
```

(Adjust the relative prefix to each page's depth: home page uses no `../`; pages two
levels deep, e.g. `facilities/tours/`, use `../../`. Mark the current section's link
with `class="on"`.)

```css
.sitenav{display:flex;flex-wrap:wrap;gap:4px 18px;align-items:baseline;
  font-size:13px;margin-bottom:14px}
.sitenav .brand{font-weight:700;color:var(--ink);text-decoration:none;
  letter-spacing:-.01em;margin-right:8px}
.sitenav a{color:var(--mut);text-decoration:none}
.sitenav a:hover{color:var(--ink)}
.sitenav a.on{color:var(--info);font-weight:650}
@media print{.sitenav{display:none}}
```

## Page header (the blue hero)

```css
header.page{position:relative;overflow:hidden;color:#fff;border-radius:18px;
  padding:30px 34px;margin-bottom:24px;
  background:radial-gradient(130% 180% at 0% 0%,#20558a 0%,#16406f 48%,#0e2c52 100%);
  box-shadow:0 2px 4px rgba(10,30,55,.18),0 18px 44px -24px rgba(10,30,55,.55)}
header.page:before{content:'';position:absolute;inset:0;border-radius:inherit;
  pointer-events:none;box-shadow:inset 0 1px 0 rgba(255,255,255,.18)}
header.page:after{content:'';position:absolute;right:-70px;top:-90px;width:300px;
  height:300px;border-radius:50%;
  background:radial-gradient(circle,rgba(122,178,235,.22),transparent 65%);pointer-events:none}
header.page h1{margin:0 0 5px;font-size:31px;font-weight:700;letter-spacing:-.015em}
header.page .sub{font-size:17px;opacity:.9;margin:0;font-weight:350}
.meta{margin-top:16px;display:flex;flex-wrap:wrap;gap:9px;position:relative}
.meta span{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.22);
  border-radius:999px;padding:5px 14px;font-size:12.5px;backdrop-filter:blur(2px)}
```

Header contents: `h1` = page name (e.g. "Treasurer's Reports"), `.sub` =
one plain-language sentence, `.meta` pills = key facts (period covered, source,
last updated).

## Sections and cards

- Section: `background:var(--card);border:1px solid var(--line);border-radius:16px;
  padding:22px 26px;margin-bottom:20px;box-shadow:var(--shadow)`
- `h2`: 20px, 700, `letter-spacing:-.012em`, with a 13px rounded color chip
  (`.ico`, border-radius 4.5px, gradient fill in the section's accent, soft glow
  `box-shadow:0 0 0 3.5px <accent at 14% alpha>`).
- `h3`: 12.5px uppercase, `color:var(--mut)`, `letter-spacing:.09em`, weight 650.
- Stat cards: white→#fafcfe gradient, 1px var(--line), radius 13px, centered,
  big tabular number + small muted label.

## Tables

- `th`: left-aligned, 11.5px uppercase, letterspacing .07em, `color:var(--mut)`,
  `border-bottom:2px solid var(--line)`, weight 650. Right-align numeric columns.
- `td`: padding 8.5px 8px, `border-bottom:1px solid var(--linesoft)`.
- Row hover: `background:#f6f9fc`. Totals row: `border-top:2px solid var(--line)`.

## Notes / callouts

`font-size:13px;color:var(--mut);background:#f6f9fc;border:1px solid var(--linesoft);
border-left:3px solid #c9d6e4;padding:9px 13px;border-radius:0 9px 9px 0`.
For warnings use `border-left-color:var(--warn)`; exceptions `var(--bad)`.

## Charts (Plotly or CSS bars)

- Use the token palette: series in `#2565ab` blues and `#22794c` greens first;
  `--bad` red strictly for flagged/exception data, never decoration.
- Plotly: `font.family` matching the body font, `paper_bgcolor`/`plot_bgcolor`
  transparent or white, no gridline clutter (light `#eaeff5` gridlines),
  no Plotly logo (`displaylogo:false`).

## Status colors (facilities/BCS)

good → `var(--good)`, monitor/caution → `var(--warn)`, urgent/poor → `var(--bad)`.
Tint backgrounds at low alpha of the same hue, e.g. `rgba(180,69,31,.07)`.

## Never

- Serif fonts, gold/brass accents (#c8a24b, #c9a227 are retired), pure black text,
  boxy sharp corners, heavy drop shadows, more than one hero header per page.
- Removing the source-citation / drill-down features any dashboard already has.
