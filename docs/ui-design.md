# UI design direction

## Subject, audience and single job

- Subject: a pharmacy operations evidence console, not a consumer health app.
- Audience: a pharmacy buyer or interviewer checking whether each recommendation is supported by data.
- Single job: move from source evidence to an auditable purchasing decision without hiding uncertainty.

## Token system

### Color

- `Porcelain` `#F3F6F4`: main working surface, recalling pharmacy paper and labels without using generic pure white.
- `Dispensary ink` `#152A32`: headings and high-contrast text.
- `Trace blue` `#1F6F8B`: source lineage, links and active navigation.
- `Verified moss` `#5E755E`: valid checkpoints and accepted evidence.
- `Expiry amber` `#C98224`: warnings and incomplete inputs.
- `Recall red` `#B4473F`: errors only, never decoration.

### Type

- Display and body: `Source Han Sans SC`, `Microsoft YaHei`, sans-serif.
- Data and audit labels: `IBM Plex Mono`, `Cascadia Mono`, monospace.
- Large typography is reserved for a conclusion or forecast horizon, not generic vanity metrics.

### Layout

The page behaves like an evidence file. A narrow left rail records the stages of the decision; the main pane holds the currently inspected table, chart or calculation.

```text
┌─────────────────────────────────────────────────────────┐
│ 药采智析                 REAL DATA · LOCAL PROCESSING   │
├──────────────┬──────────────────────────────────────────┤
│ SOURCE       │  Current checkpoint title                │
│ QUALITY      │  What was observed, not what we hope     │
│ ANALYSIS     │                                          │
│ BACKTEST     │  table / chart / formula evidence        │
│ BAD CASE     │  coverage / warning / limitation         │
│ PROCUREMENT  │                                          │
│ EXPORT       │  limitation note and next action         │
└──────────────┴──────────────────────────────────────────┘
```

### Signature

The persistent **evidence rail** is the memorable element. Every stage receives one of four states: `未开始`, `有证据`, `有警告`, `输入不足`. Users can always see whether a conclusion is derived from source data, user inputs or an unavailable field.

## Self-critique and revision

An early direction used the familiar green medical dashboard with floating KPI cards. That visual language would make this project indistinguishable from generic AI health mockups and would overstate certainty. The revised direction uses an audit-file structure, square-edged table surfaces, restrained motion and explicit evidence states. The only expressive risk is the vertical evidence rail; all other elements remain quiet and operational.

## Interaction constraints

- No decorative gradients or animated health graphics.
- Keyboard focus must be visible.
- Red is reserved for actionable data errors.
- Empty states explain which file or field unlocks the next stage.
- Every forecast view shows its holdout window and error metric nearby.
- Every procurement row exposes its calculation inputs.
- Reduced-motion users receive no animated transitions.

