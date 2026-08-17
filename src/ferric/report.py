"""Generate Ferric's self-contained offline drift report."""

from __future__ import annotations

import html
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from ferric.schema import DriftClassification, DriftResult


def _event_lines(result: DriftResult, target: bool) -> list[str]:
    events = result.target_events if target else result.baseline_events
    return [
        f"{event.index:02d}  {event.role.value:<11} "
        f"{json.dumps(event.payload.model_dump(mode='json'), ensure_ascii=True, sort_keys=True)}"
        for event in events
    ]


def render_drift_report(
    results: list[DriftResult],
    *,
    baseline_model: str,
    target_model: str,
    generated_at: datetime | None = None,
) -> str:
    """Render validated drift results as one dependency-free HTML document."""

    generated = generated_at or datetime.now(UTC)
    counts = {
        state.value: sum(result.classification is state for result in results)
        for state in DriftClassification
    }
    rows = [
        {
            "baseline": _event_lines(result, False),
            "cassette": result.cassette_id,
            "classification": result.classification.value,
            "dimension": result.dimension.value.replace("_", " ")
            if result.dimension
            else "",
            "events": len(result.baseline_events),
            "target": _event_lines(result, True),
            "tokens": result.tokens_spent,
        }
        for result in results
    ]
    data_json = json.dumps(rows, ensure_ascii=True, separators=(",", ":")).replace(
        "</", "<\\/"
    )
    baseline = html.escape(baseline_model)
    target = html.escape(target_model)
    generated_text = html.escape(
        generated.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")
    )
    total_tokens = sum(result.tokens_spent for result in results)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ferric drift report</title>
<style>
:root{{--bg:#0b0b0c;--surface:#121214;--raised:#17171a;--accent:#ffb020;--text:#ededea;--secondary:#9a9a94;--muted:#5c5c57;--border:rgba(255,255,255,.11);--subtle:rgba(255,255,255,.06);--fail:#ff5c46;--display:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;--mono:ui-monospace,"SFMono-Regular","Cascadia Mono","Liberation Mono",monospace}}
*{{box-sizing:border-box}}html{{background:var(--bg);color:var(--text)}}body{{margin:0;font:13px/1.55 var(--mono);background:var(--bg)}}header{{padding:32px;border-bottom:1px solid var(--border)}}h1{{margin:0;font:700 22px var(--display);letter-spacing:.04em}}.meta{{display:flex;flex-wrap:wrap;gap:12px 32px;margin-top:12px;color:var(--muted);font-size:11px;letter-spacing:.16em;text-transform:uppercase}}.summary{{display:grid;grid-template-columns:repeat(3,1fr);border-bottom:1px solid var(--border)}}.metric{{padding:24px 32px;border-right:1px solid var(--subtle)}}.metric:last-child{{border:0}}.label{{color:var(--muted);font-size:10px;letter-spacing:.2em;text-transform:uppercase}}.value{{margin-top:8px;color:var(--secondary);font-size:32px;font-variant-numeric:tabular-nums}}.metric.fail .value{{color:var(--fail)}}.filters{{position:sticky;top:0;z-index:200;display:flex;gap:8px;padding:12px 32px;background:rgba(11,11,12,.88);border-bottom:1px solid var(--border);box-shadow:0 8px 24px -12px rgba(0,0,0,.6);backdrop-filter:blur(12px)}}button{{padding:6px 14px;border:1px solid var(--border);border-radius:0;background:transparent;color:var(--muted);font:11px var(--mono);letter-spacing:.16em;text-transform:uppercase;cursor:pointer;transition:color 240ms,border-color 240ms}}button:hover{{color:var(--text)}}button.active{{border-color:var(--accent);background:var(--accent);color:var(--bg)}}.table-wrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px 32px;text-align:left}}th{{border-bottom:1px solid var(--border);color:var(--muted);font-size:10px;letter-spacing:.2em}}tbody tr.result{{border-bottom:1px solid var(--subtle);cursor:pointer}}tbody tr.result:hover{{background:var(--raised)}}td{{color:var(--secondary);font-size:12px}}td.state-unchanged{{color:var(--muted)}}td.state-diverged{{color:var(--fail)}}tr.result.diverged{{border-left:2px solid var(--fail);background:rgba(255,92,70,.05)}}tr[hidden]{{display:none}}tr.detail{{display:none;background:var(--surface)}}tr.detail.open{{display:table-row}}.detail-cell{{padding:0 32px 24px}}.diff{{display:grid;grid-template-columns:1fr 1fr;gap:1px;border:1px solid var(--border);background:var(--border)}}.side{{min-width:0;padding:16px;background:var(--bg)}}pre{{margin:10px 0 0;overflow:auto;white-space:pre-wrap;color:var(--secondary);font:12px/1.7 var(--mono)}}.target.changed pre{{padding-left:8px;border-left:2px solid var(--fail);background:rgba(255,92,70,.06);color:var(--text)}}footer{{display:flex;justify-content:space-between;padding:24px 32px;border-top:1px solid var(--subtle);color:var(--muted);font-size:10px;letter-spacing:.2em;text-transform:uppercase}}
tr.detail .diff{{max-height:0;overflow:hidden;opacity:0;transition:max-height 320ms cubic-bezier(.16,1,.3,1),opacity 320ms cubic-bezier(.16,1,.3,1)}}tr.detail.open .diff{{max-height:600px;opacity:1}}
@media(max-width:767px){{header,.metric,th,td,.filters,.detail-cell,footer{{padding-left:16px;padding-right:16px}}.summary{{grid-template-columns:1fr}}.metric{{border-right:0;border-bottom:1px solid var(--subtle)}}.events-column{{display:none}}.diff{{grid-template-columns:1fr}}footer{{gap:16px;flex-direction:column}}}}
@media print{{html,body{{background:white;color:black}}.filters{{display:none}}tr.detail{{display:table-row!important}}tr.result.diverged{{border-left:2px solid black;background:white}}.side,.diff{{background:white;color:black}}}}
</style>
</head>
<body>
<header><h1>DRIFT REPORT</h1><div class="meta"><span>BASELINE / {baseline}</span><span>TARGET / {target}</span><span>CASSETTES / {len(results)}</span><span>GENERATED / {generated_text}</span></div></header>
<section class="summary" aria-label="Drift summary"><div class="metric"><div class="label">UNCHANGED</div><div class="value">{counts["unchanged"]}</div></div><div class="metric"><div class="label">REWORDED</div><div class="value">{counts["reworded"]}</div></div><div class="metric fail"><div class="label">DIVERGED</div><div class="value">{counts["diverged"]}</div></div></section>
<nav class="filters" aria-label="Result filters"><button class="active" data-filter="all">ALL</button><button data-filter="diverged">DIVERGED</button><button data-filter="reworded">REWORDED</button><button data-filter="unchanged">UNCHANGED</button></nav>
<div class="table-wrap"><table><thead><tr><th>CASSETTE</th><th class="events-column">EVENTS</th><th>CLASSIFICATION</th><th>DIMENSION</th></tr></thead><tbody id="results"></tbody></table></div>
<footer><span>generated by ferric</span><span>{total_tokens} total tokens spent</span></footer>
<script id="report-data" type="application/json">{data_json}</script>
<script>
const rows=JSON.parse(document.getElementById('report-data').textContent);const body=document.getElementById('results');
function escapeText(value){{const node=document.createElement('span');node.textContent=value;return node.innerHTML}}
rows.forEach((row,index)=>{{const result=document.createElement('tr');result.className='result '+row.classification;result.dataset.state=row.classification;result.tabIndex=0;result.innerHTML=`<td>${{escapeText(row.cassette.slice(0,12))}}</td><td class="events-column">${{row.events}}</td><td class="state-${{row.classification}}">${{row.classification}}</td><td>${{escapeText(row.dimension)}}</td>`;const detail=document.createElement('tr');detail.className='detail';detail.dataset.state=row.classification;detail.innerHTML=`<td class="detail-cell" colspan="4"><div class="diff"><section class="side"><div class="label">BASELINE</div><pre>${{escapeText(row.baseline.join('\n'))}}</pre></section><section class="side target ${{row.classification==='diverged'?'changed':''}}"><div class="label">TARGET</div><pre>${{escapeText(row.target.join('\n'))}}</pre></section></div></td>`;const toggle=()=>{{document.querySelectorAll('tr.detail.open').forEach(open=>{{if(open!==detail)open.classList.remove('open')}});detail.classList.toggle('open')}};result.addEventListener('click',toggle);result.addEventListener('keydown',event=>{{if(event.key==='Enter'||event.key===' '){{event.preventDefault();toggle()}}}});body.append(result,detail)}});
document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{{document.querySelectorAll('[data-filter]').forEach(item=>item.classList.remove('active'));button.classList.add('active');const filter=button.dataset.filter;document.querySelectorAll('tbody tr').forEach(row=>{{row.hidden=filter!=='all'&&row.dataset.state!==filter;if(row.hidden)row.classList.remove('open')}})}}));
</script>
</body>
</html>
"""


def write_drift_report(
    path: Path | str,
    results: list[DriftResult],
    *,
    baseline_model: str,
    target_model: str,
    generated_at: datetime | None = None,
) -> Path:
    """Atomically write a self-contained drift report."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    document = render_drift_report(
        results,
        baseline_model=baseline_model,
        target_model=target_model,
        generated_at=generated_at,
    )
    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent, prefix=f".{destination.name}.", suffix=".tmp", text=True
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(document)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, destination)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return destination
