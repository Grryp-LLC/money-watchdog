#!/usr/bin/env python3
"""Money Watchdog poster generator.

Renders Wild-West 'MOST WANTED' posters, a monthly 'Rap Sheet' and a weekly 'Bounty Board'
from a small JSON spec to PNG at X-friendly sizes (1200x675 landscape, 1080x1350 portrait).

  python render.py spec.json --out ./out [--sizes landscape,portrait] [--anonymous] [--html]

Every string passes through privacy.scrub() and the final text is linted before rendering;
a lint failure aborts the render (exit 2) so nothing sensitive can reach a shareable image.
"""
import argparse, hashlib, html, json, math, os, random, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from icons import icon  # noqa: E402
import privacy  # noqa: E402

FONTS = HERE / "fonts"
SIZES = {"landscape": (1200, 675), "portrait": (1080, 1350)}
INK, RED = "#2a1709", "#7c1a12"

def esc(s):
    return html.escape(str(s if s is not None else ""))

def money(n):
    return f"${round(float(n)):,}"

# ---------------------------------------------------------------- shared chrome
def font_css():
    missing = [f for f in ("Rye-Regular.ttf", "Sancreek-Regular.ttf", "SpecialElite-Regular.ttf",
               "IMFellEnglishSC-Regular.ttf", "IMFellDWPica-Regular.ttf", "IMFellDWPica-Italic.ttf") if not (FONTS / f).exists()]
    if missing:
        sys.exit("fonts missing in poster/fonts: " + ", ".join(missing) + "  (run ./install.sh)")
    faces = {"Rye": "Rye-Regular.ttf", "Sancreek": "Sancreek-Regular.ttf",
             "Elite": "SpecialElite-Regular.ttf", "FellSC": "IMFellEnglishSC-Regular.ttf",
             "Fell": "IMFellDWPica-Regular.ttf"}
    out = [f"@font-face{{font-family:'{k}';src:url('{(FONTS / v).as_uri()}');}}" for k, v in faces.items()]
    out.append("@font-face{font-family:'FellI';src:url('%s');}" % (FONTS / "IMFellDWPica-Italic.ttf").as_uri())
    return "\n".join(out)

def svg_defs(seed):
    return f"""
<svg width="0" height="0" style="position:absolute">
 <defs>
  <filter id="distress" x="-5%" y="-5%" width="110%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="3" seed="{seed}" result="warp"/>
    <feDisplacementMap in="SourceGraphic" in2="warp" scale="3.2" xChannelSelector="R" yChannelSelector="G" result="rough"/>
    <feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="3" seed="{seed+7}" result="grain"/>
    <feColorMatrix in="grain" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -11 0 0 0 7.45" result="mask"/>
    <feComposite in="rough" in2="mask" operator="in"/>
  </filter>
  <filter id="paperGrain"><feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="4" seed="{seed+3}"/>
    <feColorMatrix type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.22  0 0 0 0 0.1  0 0 0 -1.1 0.95"/></filter>
  <filter id="paperBlotch"><feTurbulence type="fractalNoise" baseFrequency="0.006" numOctaves="4" seed="{seed+11}"/>
    <feColorMatrix type="matrix" values="0 0 0 0 0.45  0 0 0 0 0.26  0 0 0 0 0.08  1.6 0 0 0 -0.62"/></filter>
  <filter id="woodGrain"><feTurbulence type="fractalNoise" baseFrequency="0.003 0.09" numOctaves="4" seed="{seed+5}"/>
    <feColorMatrix type="matrix" values="0 0 0 0 0.12  0 0 0 0 0.06  0 0 0 0 0.02  0 1.3 0 0 -0.35"/></filter>
  <pattern id="hatch" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">
    <line x1="0" y1="0" x2="0" y2="9" stroke="{INK}" stroke-width="1.4" opacity=".35"/></pattern>
 </defs>
</svg>"""

def torn_clip(seed, jag=1.1, n=26):
    """Irregular polygon (percent units) so every sheet has its own torn edges."""
    r = random.Random(seed)
    pts = []
    for side in range(4):
        for i in range(n):
            t = i / n * 100
            d = r.uniform(0, jag) + (r.random() < .12) * r.uniform(0, jag * 1.4)
            pts.append({0: (t, d), 1: (100 - d, t), 2: (100 - t, 100 - d), 3: (d, 100 - t)}[side])
    return "polygon(" + ",".join(f"{x:.2f}% {y:.2f}%" for x, y in pts) + ")"

def badge_svg(size=120, label="MONEY WATCHDOG"):
    pts = []
    for i in range(12):
        a = -math.pi / 2 + i * math.pi / 6
        rad = 96 if i % 2 == 0 else 50
        pts.append(f"{100 + rad * math.cos(a):.1f},{100 + rad * math.sin(a):.1f}")
    balls = "".join(
        f'<circle cx="{100 + 96 * math.cos(-math.pi/2 + k*math.pi/3):.1f}" cy="{100 + 96 * math.sin(-math.pi/2 + k*math.pi/3):.1f}" r="9"/>'
        for k in range(6))
    paw = ('<ellipse cx="100" cy="112" rx="15" ry="12"/><ellipse cx="83" cy="92" rx="6" ry="8"/>'
           '<ellipse cx="95" cy="85" rx="6" ry="8"/><ellipse cx="107" cy="85" rx="6" ry="8"/><ellipse cx="119" cy="92" rx="6" ry="8"/>')
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs><path id="ring" d="M100,100 m-36,0 a36,36 0 1,1 72,0 a36,36 0 1,1 -72,0"/></defs>
  <g fill="none" stroke="{INK}" stroke-width="5"><polygon points="{' '.join(pts)}"/></g>
  <g fill="{INK}">{balls}</g>
  <circle cx="100" cy="100" r="46" fill="none" stroke="{INK}" stroke-width="3"/>
  <text font-family="FellSC" font-size="12.5" fill="{INK}" letter-spacing="1.4"><textPath href="#ring" startOffset="0">★ {esc(label)} ★ SHERIFF ★</textPath></text>
  <g fill="{INK}" transform="translate(100 100) scale(.62) translate(-100 -100)">{paw}</g>
</svg>"""

BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:%(W)dpx;height:%(H)dpx;overflow:hidden;background:#2b1a0f}
.stage{position:relative;width:%(W)dpx;height:%(H)dpx;overflow:hidden}
.wood{position:absolute;inset:0;background:
  repeating-linear-gradient(90deg,rgba(0,0,0,.55) 0 3px,transparent 3px 180px),
  linear-gradient(90deg,#5a3719,#6d4322 20%%,#5b381b 35%%,#734826 55%%,#5e3a1c 75%%,#6a4121);}
.wood svg{position:absolute;inset:0;width:100%%;height:100%%;mix-blend-mode:multiply}
.wood:after{content:"";position:absolute;inset:0;box-shadow:inset 0 0 160px rgba(0,0,0,.75)}
.sheet{position:absolute;filter:drop-shadow(0 18px 22px rgba(0,0,0,.55)) drop-shadow(0 2px 3px rgba(0,0,0,.6))}
.paper{position:absolute;inset:0;overflow:hidden;
  background:radial-gradient(ellipse at 50%% 42%%,#f3e2b6 0%%,#ead094 45%%,#d7ad6c 78%%,#a8753c 96%%,#7c4f22 100%%);}
.paper svg.tex{position:absolute;inset:0;width:100%%;height:100%%}
.paper .grain{mix-blend-mode:multiply;opacity:.55}
.paper .blotch{mix-blend-mode:multiply;opacity:.8}
.paper .fold{position:absolute;inset:0;background:
  linear-gradient(180deg,transparent 33.1%%,rgba(90,55,20,.18) 33.3%%,rgba(255,245,220,.35) 33.5%%,transparent 33.9%%),
  linear-gradient(180deg,transparent 66.3%%,rgba(90,55,20,.16) 66.5%%,rgba(255,245,220,.3) 66.7%%,transparent 67.1%%),
  linear-gradient(90deg,transparent 49.7%%,rgba(90,55,20,.13) 49.9%%,rgba(255,245,220,.28) 50.1%%,transparent 50.5%%);}
.paper .burn{position:absolute;inset:0;box-shadow:inset 0 0 70px rgba(92,48,12,.65),inset 0 0 14px rgba(60,30,5,.7)}
.ink{position:absolute;inset:0;color:%(INK)s;filter:url(#distress)}
.nail{position:absolute;width:22px;height:22px;border-radius:50%%;z-index:5;
  background:radial-gradient(circle at 35%% 30%%,#d9d2c4 0,#8d8578 30%%,#3b352c 70%%,#1b1712 100%%);
  box-shadow:2px 4px 5px rgba(0,0,0,.6)}
.rule{height:0;border-top:3px solid %(INK)s;border-bottom:1px solid %(INK)s;padding-top:3px}
.fit{white-space:nowrap;display:block}
.stamp{position:absolute;z-index:9;font-family:Elite;color:#9b1c14;border:3px solid #9b1c14;
  padding:3px 10px 1px;letter-spacing:2px;transform:rotate(-8deg);opacity:.85;background:rgba(255,240,210,.12)}
.hole{position:absolute;width:26px;height:26px;border-radius:50%%;z-index:6;
  background:radial-gradient(circle,#1a0f06 0 38%%,#4a2a10 45%%,rgba(120,70,25,.55) 62%%,transparent 72%%)}
"""

FIT_JS = """
async function fitAll(){
  await document.fonts.ready;
  for (const el of document.querySelectorAll('.fit')){
    const max = parseFloat(el.dataset.max || getComputedStyle(el).fontSize);
    let s = max; el.style.fontSize = s+'px';
    const w = el.parentElement.clientWidth;
    while (el.scrollWidth > w && s > 8){ s -= 1; el.style.fontSize = s+'px'; }
  }
  for (const el of document.querySelectorAll('.clamp')){
    const maxH = parseFloat(el.dataset.h); let s = parseFloat(getComputedStyle(el).fontSize);
    while (el.scrollHeight > maxH && s > 10){ s -= 1; el.style.fontSize = s+'px'; }
  }
  document.body.dataset.ready = '1';
}
fitAll();
"""

def page(W, H, seed, body, extra_css=""):
    css = BASE_CSS % {"W": W, "H": H, "INK": INK}
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{font_css()}{css}{extra_css}</style></head>
<body><div class="stage">{svg_defs(seed)}
<div class="wood"><svg><rect width="100%" height="100%" filter="url(#woodGrain)"/></svg></div>
{body}</div><script>{FIT_JS}</script></body></html>"""

def paper(seed, jag=1.0):
    return f"""<div class="paper" style="clip-path:{torn_clip(seed, jag)}">
  <svg class="tex blotch"><rect width="100%" height="100%" filter="url(#paperBlotch)"/></svg>
  <svg class="tex grain"><rect width="100%" height="100%" filter="url(#paperGrain)"/></svg>
  <div class="fold"></div><div class="burn"></div></div>"""

def sample_stamp(data, pos="right:34px;bottom:30px", size=15):
    if not data.get("sample"):
        return ""
    return f'<div class="stamp" style="{pos};font-size:{size}px">SAMPLE · DEMO DATA</div>'

def mug(category, logo=None, anonymous=False, w=300, h=240, initial="?"):
    inner = (f'<img src="{Path(logo).resolve().as_uri()}" style="max-width:78%;max-height:78%;'
             f'filter:grayscale(1) sepia(.9) contrast(1.35) brightness(.8);mix-blend-mode:multiply">'
             if logo and not anonymous else
             f'<div style="width:{int(min(w,h)*.8)}px;height:{int(min(w,h)*.8)}px;color:{INK}">{icon(category)}</div>')
    return f"""<div style="position:relative;width:{w}px;height:{h}px;border:4px solid {INK};padding:7px;margin:0 auto">
  <div style="position:relative;width:100%;height:100%;border:2px solid {INK};display:flex;align-items:center;justify-content:center;overflow:hidden">
   <svg style="position:absolute;inset:0;width:100%;height:100%"><rect width="100%" height="100%" fill="url(#hatch)"/></svg>
   <div style="position:absolute;inset:14%;border-radius:50%;background:radial-gradient(circle,rgba(243,226,182,.95) 0,rgba(243,226,182,.85) 55%,rgba(243,226,182,0) 72%)"></div>
   <div style="position:relative;display:flex;align-items:center;justify-content:center;width:100%;height:100%">{inner}</div>
   <div style="position:absolute;left:8px;bottom:4px;font-family:Elite;font-size:{max(12,int(h*.07))}px;letter-spacing:1px">No. {esc(initial)}</div>
  </div></div>"""

# ---------------------------------------------------------------- data prep
def prep_wanted(d, anonymous, deny):
    anon = anonymous or d.get("anonymous", False)
    cat = d.get("category", "generic")
    out = {
        "merchant": privacy.display_merchant(d["merchant"], cat, anon, deny).upper(),
        "merchant_disp": privacy.display_merchant(d["merchant"], cat, anon, deny),
        "alias": privacy.scrub(d.get("alias", ""), deny),
        "crimes": [privacy.scrub(c, deny) for c in d.get("crimes", [])][:4],
        "reward": float(d["reward_per_year"]),
        "basis": privacy.scrub(d.get("reward_basis", ""), deny),
        "period": privacy.scrub(d.get("period", ""), deny),
        "category": cat, "logo": d.get("logo"), "anon": anon, "sample": d.get("sample", False),
        "case": privacy.scrub(d.get("case", ""), deny),
    }
    out["initial"] = out["case"] or ("?" if anon else out["merchant"][:1])
    return out

def lint_or_die(texts, deny):
    probs = []
    for t in texts:
        probs += [f"{p} in: {t!r}" for p in privacy.lint(str(t), deny)]
    if probs:
        sys.stderr.write("PRIVACY LINT FAILED — refusing to render:\n  " + "\n  ".join(probs) + "\n")
        sys.exit(2)

# ---------------------------------------------------------------- WANTED
def wanted_html(p, size, seed):
    W, H = SIZES[size]
    crimes = "".join(f'<li><span class="cn">COUNT {i+1}.</span> {esc(c)}</li>' for i, c in enumerate(p["crimes"]))
    reward = money(p["reward"])
    alias = f'<div class="alias">alias &ldquo;{esc(p["alias"])}&rdquo;</div>' if p["alias"] else ""
    foot_l = f'WANTED IN {esc(p["period"]).upper()}' if p["period"] else "WANTED"
    if size == "portrait":
        css = """
.sheet{left:46px;top:40px;right:46px;bottom:40px}
.col{position:absolute;inset:44px 66px 40px;display:flex;flex-direction:column;align-items:stretch;text-align:center}
.top{font-family:FellSC;font-size:25px;letter-spacing:6px;display:flex;align-items:center;gap:16px}
.top:before,.top:after{content:"";flex:1;border-top:2px solid;border-bottom:1px solid;height:5px}
.wanted{font-family:Rye;font-size:236px;line-height:.95;letter-spacing:4px;margin-top:6px}
.sub{font-family:FellSC;font-size:37px;letter-spacing:3px;padding:8px 0 6px;margin:4px 0 20px;border-top:3px double;border-bottom:3px double}
.name{font-family:Sancreek;margin-top:16px;line-height:1.05}
.alias{font-family:FellI;font-size:34px;margin-top:0}
.charge{font-family:FellSC;font-size:25px;letter-spacing:5px;margin-top:14px}
ol{list-style:none;text-align:left;font-family:Elite;font-size:27px;line-height:1.28;margin:8px 6px 8px;flex:1;display:flex;flex-direction:column;justify-content:center}
ol li{margin:4px 0;padding-left:128px;text-indent:-128px}
.cn{display:inline-block;width:128px;text-indent:0;font-size:22px;letter-spacing:1px}
.rewardbox{border-top:3px double;padding-top:6px;display:flex;align-items:center;justify-content:center;gap:24px}
.rw{font-family:Rye;font-size:62px;letter-spacing:3px}
.amt{font-family:Rye;font-size:150px;color:%(RED)s;line-height:1}
.per{font-family:Rye;font-size:48px;color:%(RED)s}
.est{font-family:Elite;font-size:19px;letter-spacing:.5px;margin-top:0}
.foot{display:flex;justify-content:space-between;align-items:flex-end;font-family:Rye;font-size:19px;letter-spacing:2px;margin-top:10px}
""" % {"RED": RED}
        body = f"""
<div class="sheet">{paper(seed)}
 <div class="ink"><div class="col">
  <div class="top">BY ORDER OF THE MONEY WATCHDOG</div>
  <div style="width:100%"><span class="wanted fit" data-max="236">WANTED</span></div>
  <div class="sub">FOR CRIMES AGAINST YOUR WALLET</div>
  {mug(p['category'], p['logo'], p['anon'], 400, 280, p['initial'])}
  <div style="width:100%"><span class="name fit" data-max="118">{esc(p['merchant'])}</span></div>
  {alias}
  <div class="charge">— CHARGED WITH —</div>
  <ol>{crimes}</ol>
  <div class="rewardbox"><span class="rw">REWARD</span><span class="amt">{reward}</span><span class="per">/YR</span></div>
  <div style="width:100%"><span class="est fit" data-max="19">ESTIMATED POTENTIAL SAVINGS{(' · ' + esc(p['basis'])) if p['basis'] else ''}</span></div>
  <div class="foot"><span>{foot_l}</span>{badge_svg(92)}<span>HANDS OFF MY WALLET</span></div>
 </div></div>
</div>
<div class="nail" style="left:70px;top:58px"></div><div class="nail" style="right:70px;top:58px"></div>
<div class="nail" style="left:72px;bottom:56px"></div><div class="nail" style="right:74px;bottom:58px"></div>
<div class="hole" style="right:130px;top:350px"></div>
{sample_stamp(p, 'right:86px;bottom:130px')}"""
    else:
        css = """
.sheet{left:36px;top:28px;right:36px;bottom:28px}
.grid{position:absolute;inset:30px 46px 26px;display:grid;grid-template-columns:400px 1fr;gap:34px}
.left{display:flex;flex-direction:column;text-align:center}
.right{display:flex;flex-direction:column;min-width:0}
.top{font-family:FellSC;font-size:17px;letter-spacing:4px}
.wanted{font-family:Rye;font-size:124px;line-height:.95;margin:2px 0 10px}
.name{font-family:Sancreek;line-height:1.05;margin-top:10px}
.alias{font-family:FellI;font-size:26px}
.sub{font-family:FellSC;font-size:30px;letter-spacing:3px;padding:6px 0 4px;border-top:3px double;border-bottom:3px double;text-align:center}
.charge{font-family:FellSC;font-size:19px;letter-spacing:5px;margin-top:10px;text-align:center}
ol{list-style:none;font-family:Elite;font-size:27px;line-height:1.28;margin-top:10px;flex:1;display:flex;flex-direction:column;justify-content:center}
ol li{margin:10px 0;padding-left:122px;text-indent:-122px}
.cn{display:inline-block;width:122px;text-indent:0;font-size:20px;letter-spacing:1px}
.rewardbox{border-top:3px double;padding-top:4px;display:flex;align-items:center;justify-content:center;gap:18px}
.rw{font-family:Rye;font-size:44px}
.amt{font-family:Rye;font-size:104px;color:%(RED)s;line-height:1}
.per{font-family:Rye;font-size:36px;color:%(RED)s}
.est{font-family:Elite;font-size:16px;text-align:center}
.foot{display:flex;justify-content:space-between;align-items:center;font-family:Rye;font-size:15px;letter-spacing:2px;margin-top:4px}
""" % {"RED": RED}
        body = f"""
<div class="sheet">{paper(seed, .8)}
 <div class="ink"><div class="grid">
  <div class="left">
   <div style="width:100%"><span class="top fit" data-max="17">BY ORDER OF THE MONEY WATCHDOG</span></div>
   <div style="width:100%"><span class="wanted fit" data-max="124">WANTED</span></div>
   {mug(p['category'], p['logo'], p['anon'], 340, 236, p['initial'])}
   <div style="width:100%"><span class="name fit" data-max="80">{esc(p['merchant'])}</span></div>
   {alias}
  </div>
  <div class="right">
   <div class="sub"><span class="fit" data-max="30">FOR CRIMES AGAINST YOUR WALLET</span></div>
   <div class="charge">— CHARGED WITH —</div>
   <ol>{crimes}</ol>
   <div class="rewardbox"><span class="rw">REWARD</span><span class="amt">{reward}</span><span class="per">/YR</span></div>
   <div style="width:100%"><span class="est fit" data-max="16">ESTIMATED POTENTIAL SAVINGS{(' · ' + esc(p['basis'])) if p['basis'] else ''}</span></div>
   <div class="foot"><span>{foot_l}</span>{badge_svg(64)}<span>HANDS OFF MY WALLET</span></div>
  </div>
 </div></div>
</div>
<div class="nail" style="left:54px;top:44px"></div><div class="nail" style="right:54px;top:44px"></div>
<div class="nail" style="left:56px;bottom:42px"></div><div class="nail" style="right:56px;bottom:44px"></div>
<div class="hole" style="left:462px;top:300px"></div>
{sample_stamp(p, 'left:128px;bottom:52px', 13)}"""
    return page(W, H, seed, body, css)

def wanted_caption(p):
    who = p["merchant_disp"] if not p["anon"] else p["merchant_disp"].lower()
    lead = p["crimes"][0].rstrip(".") if p["crimes"] else "sneaking charges past me"
    return (f"My inbox sheriff just slapped a WANTED poster on {who}. "
            f"Crime: {lead[0].lower() + lead[1:] if lead else lead}. "
            f"Bounty: ~{money(p['reward'])}/yr in potential savings (estimate). "
            f"Posse up. #MoneyWatchdog")

# ---------------------------------------------------------------- RAP SHEET (monthly)
STATUS = {"caught": ("CAUGHT", "#2f5d2a"), "at_large": ("AT LARGE", RED), "pardoned": ("PARDONED", "#5a4a32"),
          "watching": ("WATCHING", "#6b4a12")}

def prep_rap(d, anonymous, deny):
    anon = anonymous or d.get("anonymous", False)
    rows = []
    for r in d.get("rows", []):
        rows.append({"merchant": privacy.display_merchant(r["merchant"], r.get("category"), anon, deny),
                     "category": r.get("category", "generic"), "crime": privacy.scrub(r.get("crime", ""), deny),
                     "bounty": float(r.get("bounty_per_year", r.get("bounty_once", 0))), "once": "bounty_once" in r,
                     "status": r.get("status", "at_large")})
    at_large = sum(r["bounty"] for r in rows if r["status"] in ("at_large", "watching") and not r["once"])
    caught = sum(r["bounty"] for r in rows if r["status"] == "caught")
    top = max((r for r in rows if r["status"] in ("at_large", "watching")), key=lambda r: r["bounty"], default=None)
    return {"period": privacy.scrub(d.get("period", ""), deny), "rows": rows, "anon": anon, "sample": d.get("sample"),
            "spotted": d.get("spotted", len(rows)), "at_large": at_large, "caught": caught, "top": top,
            "one_off": float(d.get("one_off_recovered", 0))}

def rap_html(p, size, seed):
    W, H = SIZES[size]
    port = size == "portrait"
    maxrows = 7 if port else 5
    rows = p["rows"][:maxrows]
    trs = ""
    for r in rows:
        label, color = STATUS.get(r["status"], STATUS["at_large"])
        trs += f"""<tr><td class="ic"><div style="width:100%;height:100%">{icon(r['category'])}</div></td>
<td class="mc"><div class="mn">{esc(r['merchant'])}</div><div class="cr">{esc(r['crime'])}</div></td>
<td class="bt">{(money(r['bounty']) + ('<small> once</small>' if r['once'] else '<small>/yr</small>')) if r['bounty'] else '&mdash;'}</td>
<td class="st"><span style="color:{color};border-color:{color}">{label}</span></td></tr>"""
    top = p["top"]
    mw = (f'<div class="mw"><b>MOST WANTED:</b> {esc(top["merchant"])} &mdash; {money(top["bounty"])}/yr bounty</div>'
          if top else '<div class="mw"><b>ALL QUIET:</b> no outlaws at large this month</div>')
    stats = f"""<div class="stats">
 <div class="sb"><div class="n">{p['spotted']}</div><div class="l">OUTLAWS SPOTTED</div></div>
 <div class="sb"><div class="n" style="color:{RED}">{money(p['at_large'])}</div><div class="l">STILL AT LARGE<br><i>est. potential /yr</i></div></div>
 <div class="sb"><div class="n" style="color:#2f5d2a">{money(p['caught'] + p['one_off'])}</div><div class="l">BOUNTIES COLLECTED<br><i>you acted · est.</i></div></div>
</div>"""
    k = 1.0 if port else .78
    css = f"""
.sheet{{left:{46 if port else 34}px;top:{40 if port else 26}px;right:{46 if port else 34}px;bottom:{40 if port else 26}px}}
.col{{position:absolute;inset:{'46px 62px 40px' if port else '26px 44px 22px'};display:flex;flex-direction:column}}
.hdr>div:last-child{{flex:1;min-width:0}}
.hdr{{display:flex;align-items:center;gap:{int(22*k)}px}}
.ttl{{font-family:Rye;font-size:{int(128*k) if port else 92}px;line-height:1}}
.ttl2{{font-family:FellSC;font-size:{int(26*k)}px;letter-spacing:4px;margin-top:6px}}
.stats{{display:flex;gap:{int(16*k)}px;margin:{int(20*k)}px 0 {int(14*k)}px}}
.sb{{flex:1;border:3px double {INK};text-align:center;padding:{int(10*k)}px 6px}}
.sb .n{{font-family:Rye;font-size:{int(62*k)}px;line-height:1.05}}
.sb .l{{font-family:FellSC;font-size:{int(18*k)}px;letter-spacing:2px;margin-top:2px}}
.sb i{{font-family:Elite;font-style:normal;font-size:{int(14*k)}px;letter-spacing:0}}
.lineup{{font-family:FellSC;font-size:{int(22*k)}px;letter-spacing:6px;text-align:center;border-top:3px double;border-bottom:1px solid;padding:4px 0}}
table{{width:100%;border-collapse:collapse;margin-top:4px}}
td{{border-bottom:1px dashed rgba(42,23,9,.55);padding:{int(9*k)}px 6px;vertical-align:middle}}
td.ic{{width:{int(64*k)}px;height:{int(64*k)}px;color:{INK}}}
.mn{{font-family:Sancreek;font-size:{int(34*k)}px;line-height:1.05}}
.cr{{font-family:Elite;font-size:{int(19*k)}px;line-height:1.2}}
td.bt{{font-family:Rye;font-size:{int(36*k)}px;text-align:right;white-space:nowrap}}
td.bt small{{font-size:.5em}}
td.st{{width:{int(170*k)}px;text-align:center}}
td.st span{{display:inline-block;font-family:Elite;font-size:{int(18*k)}px;letter-spacing:2px;border:2px solid;padding:3px 8px 1px;transform:rotate(-5deg)}}
.mw{{font-family:Elite;font-size:{int(24*k)}px;text-align:center;margin-top:auto;padding-top:{int(10*k)}px}}
.mw b{{font-family:FellSC;font-weight:normal;letter-spacing:3px;color:{RED}}}
.fine{{font-family:Elite;font-size:{int(14*k) if port else 12}px;text-align:center;margin-top:4px;opacity:.9}}
"""
    if port:
        inner = f"""<div class="hdr">{badge_svg(150)}<div><div style="width:100%"><span class="ttl fit" data-max="150">RAP SHEET</span></div>
<div class="ttl2">SHERIFF'S MONTHLY REPORT</div><div class="ttl2" style="margin-top:2px;font-family:Rye;letter-spacing:3px">{esc(p['period']).upper()}</div></div></div>
{stats}<div class="lineup">THE LINEUP</div><table>{trs}</table>{mw}
<div class="fine">Bounties are estimates from amounts in the emails, annualized. Collected = items you marked handled.</div>"""
    else:
        css += """.two{display:grid;grid-template-columns:300px 1fr;gap:30px;flex:1;min-height:0}
.two .stats{flex-direction:column;margin:10px 0 0;gap:8px}
.two .sb{padding:5px 6px;display:flex;align-items:center;gap:10px;text-align:left}
.two .sb .n{font-size:40px;min-width:118px;text-align:center}
.two .sb .l{font-size:14px;letter-spacing:1px}
.two .mn{font-size:30px}.two .cr{font-size:17px}.two td.bt{font-size:30px}.two td{padding:13px 6px}
.two td.ic{width:52px;height:52px}.two td.st span{font-size:15px}
.two .mw{font-size:20px}"""
        inner = f"""<div class="two"><div style="display:flex;flex-direction:column">
<div style="text-align:center">{badge_svg(92)}</div><div style="width:100%;text-align:center"><span class="ttl fit" data-max="64" style="text-align:center">RAP SHEET</span></div>
<div class="ttl2" style="text-align:center;font-size:15px;letter-spacing:2px;margin-top:4px;white-space:nowrap">SHERIFF'S MONTHLY REPORT</div><div style="text-align:center;font-family:Rye;font-size:18px;letter-spacing:3px">{esc(p['period']).upper()}</div>{stats}</div>
<div style="display:flex;flex-direction:column;min-width:0"><div class="lineup">THE LINEUP</div><table>{trs}</table>{mw}
<div class="fine">Bounties are estimates from amounts in the emails, annualized. Collected = items you marked handled.</div></div></div>"""
    body = f"""<div class="sheet">{paper(seed, .8)}<div class="ink"><div class="col">{inner}</div></div></div>
<div class="nail" style="left:{70 if port else 52}px;top:{58 if port else 40}px"></div><div class="nail" style="right:{70 if port else 52}px;top:{58 if port else 40}px"></div>
{sample_stamp(p, '%s' % ('right:90px;top:84px' if port else 'left:96px;bottom:60px'), 15 if port else 12)}"""
    return page(W, H, seed, body, css)

def rap_caption(p):
    if p["top"]:
        return (f"Monthly rap sheet from my inbox sheriff: {p['spotted']} outlaws spotted, "
                f"~{money(p['at_large'])}/yr still at large (estimated potential savings). "
                f"Most wanted: {p['top']['merchant']}. #MoneyWatchdog")
    return f"Monthly rap sheet: {p['spotted']} outlaws spotted, none still at large. Quiet month in town. #MoneyWatchdog"

# ---------------------------------------------------------------- BOUNTY BOARD (weekly)
def board_html(p, size, seed):
    W, H = SIZES[size]
    port = size == "portrait"
    at_large = [r for r in p["rows"] if r["status"] in ("at_large", "watching")]
    items = at_large[: (3 if port else 3)] or p["rows"][:3]
    r = random.Random(seed)
    cw, ch = (440, 500) if port else (318, 400)
    positions = ([(64, 250), (576, 262), (64, 800)] if port else [(58, 168), (420, 158), (782, 172)])
    notes = ""
    for i, it in enumerate(items):
        x, y = positions[i]
        rot = r.uniform(-3.5, 3.5)
        unit = " ONCE" if it["once"] else "/YR"
        notes += f"""<div class="sheet" style="left:{x}px;top:{y}px;width:{cw}px;height:{ch}px;transform:rotate({rot:.1f}deg)">{paper(seed + i * 17, 1.4)}
<div class="ink" style="padding:{int(ch*.07)}px {int(cw*.1)}px {int(ch*.11)}px;display:flex;flex-direction:column;text-align:center">
 <div style="width:100%"><span class="fit" data-max="{int(cw*.2)}" style="font-family:Rye;line-height:1">WANTED</span></div>
 <div style="border-top:2px solid;border-bottom:2px solid;margin-top:4px;padding:2px 0"><span class="fit" data-max="{int(cw*.05)}" style="font-family:FellSC;letter-spacing:1px">FOR CRIMES AGAINST YOUR WALLET</span></div>
 <div style="width:{int(ch*.22)}px;height:{int(ch*.22)}px;margin:{int(ch*.03)}px auto 0;color:{INK}">{icon(it['category'])}</div>
 <div style="width:100%"><span class="fit" data-max="{int(cw*.12)}" style="font-family:Sancreek">{esc(it['merchant'])}</span></div>
 <div class="clamp" data-h="{int(ch*.16)}" style="font-family:Elite;font-size:{int(cw*.056)}px;line-height:1.2;margin-top:4px">{esc(it['crime'])}</div>
 <div style="margin-top:auto;border-top:3px double;padding-top:6px;font-family:Rye;color:{RED};font-size:{int(cw*.15)}px;line-height:1">{money(it['bounty'])}<span style="font-size:.4em">{unit}</span></div>
 <div style="font-family:Elite;font-size:{int(cw*.038)}px">est. potential savings</div>
</div></div><div class="nail" style="left:{x + cw//2 - 11}px;top:{y + 10}px"></div>"""
    total = sum(i["bounty"] for i in at_large if not i["once"])
    extra = len(at_large) - len(items)
    if port:  # sheriff's notice fills the 4th slot
        x, y = 576, 812
        notes += f"""<div class="sheet" style="left:{x}px;top:{y}px;width:{cw}px;height:{ch-40}px;transform:rotate(2deg)">{paper(seed + 99, 1.4)}
<div class="ink" style="padding:34px 40px;display:flex;flex-direction:column;align-items:center;text-align:center">
 {badge_svg(130)}
 <div style="font-family:Rye;font-size:40px;margin-top:6px">SHERIFF'S NOTICE</div>
 <div style="font-family:Elite;font-size:24px;line-height:1.3;margin-top:10px">{len(at_large)} outlaw{'s' if len(at_large)!=1 else ''} at large{f' ({extra} more in the ledger)' if extra>0 else ''}</div>
 <div style="font-family:Rye;font-size:70px;color:{RED};margin-top:auto;line-height:1">{money(total)}<span style="font-size:.4em">/YR</span></div>
 <div style="font-family:Elite;font-size:17px">total bounty · est. potential savings</div>
</div></div><div class="nail" style="left:{x + cw//2 - 11}px;top:{y + 10}px"></div>"""
    css = """.plank{position:absolute;left:0;right:0;text-align:center;color:#f1dcae;
font-family:Rye;text-shadow:0 2px 0 #1c0f05,0 -1px 0 rgba(255,230,180,.25);white-space:nowrap}
.plank small{display:block;font-family:Rye;letter-spacing:4px}"""
    title = (f'<div class="plank" style="top:44px;font-size:118px">BOUNTY BOARD<small style="font-size:30px">WEEK OF {esc(p["period"]).upper()}</small></div>'
             if port else
             f'<div class="plank" style="top:22px;font-size:84px">BOUNTY BOARD<small style="font-size:22px">WEEK OF {esc(p["period"]).upper()}</small></div>')
    foot = ("" if port else
            f'<div class="plank" style="bottom:18px;font-size:24px;letter-spacing:2px">'
            f'TOTAL ON THE BOARD: ~{money(total)}/YR · ESTIMATED POTENTIAL SAVINGS</div>')
    body = title + notes + foot + sample_stamp(p, "right:34px;top:%dpx" % (18 if port else 14), 14 if port else 12)
    return page(W, H, seed, body, css)

def board_caption(p):
    items = [r for r in p["rows"] if r["status"] in ("at_large", "watching")]
    total = sum(i["bounty"] for i in items if not i["once"])
    return (f"This week's bounty board from my inbox sheriff: {len(items)} outlaws at large, "
            f"~{money(total)}/yr in estimated potential savings on the board. #MoneyWatchdog")

# ---------------------------------------------------------------- render
async def shoot(html_path, png_path, W, H):
    from playwright.async_api import async_playwright
    exe = os.environ.get("CHROME_PATH") or next((p for p in ["/usr/bin/google-chrome", "/usr/bin/chromium",
                                                            "/usr/bin/chromium-browser"] if os.path.exists(p)), None)
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=exe, args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        await pg.goto(Path(html_path).resolve().as_uri())
        await pg.wait_for_selector("body[data-ready='1']", timeout=20000)
        await pg.wait_for_timeout(250)
        await pg.screenshot(path=str(png_path), clip={"x": 0, "y": 0, "width": W, "height": H})
        await b.close()

def main():
    import asyncio
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec"); ap.add_argument("--out", default="out")
    ap.add_argument("--sizes", default="landscape,portrait"); ap.add_argument("--anonymous", action="store_true")
    ap.add_argument("--deny", default="", help="comma-separated names that must never appear (user's own name etc.)")
    ap.add_argument("--html", action="store_true", help="keep the intermediate HTML")
    ap.add_argument("--sample", action="store_true", help="stamp 'SAMPLE · DEMO DATA' (use for any demo/fictional data)")
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text())
    if a.sample: spec["sample"] = True
    deny = [s.strip() for s in (a.deny.split(",") + spec.get("deny_names", [])) if s.strip()]
    kind = spec.get("type", "wanted")
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    stem = spec.get("slug") or Path(a.spec).stem
    seed = int(hashlib.md5(stem.encode()).hexdigest()[:6], 16) % 997
    if kind == "wanted":
        p = prep_wanted(spec, a.anonymous, deny)
        lint_or_die([p["merchant"], p["alias"], p["basis"], p["period"], *p["crimes"]], deny)
        builder, caption = wanted_html, wanted_caption(p)
    elif kind in ("rapsheet", "bountyboard"):
        p = prep_rap(spec, a.anonymous, deny)
        lint_or_die([p["period"]] + [x for r in p["rows"] for x in (r["merchant"], r["crime"])], deny)
        builder = rap_html if kind == "rapsheet" else board_html
        caption = rap_caption(p) if kind == "rapsheet" else board_caption(p)
    else:
        sys.exit(f"unknown type {kind}")
    lint_or_die([caption], deny)
    results = []
    for size in [s.strip() for s in a.sizes.split(",") if s.strip()]:
        W, H = SIZES[size]
        hp = out / f"{stem}-{W}x{H}.html"; pp = out / f"{stem}-{W}x{H}.png"
        hp.write_text(builder(p, size, seed))
        asyncio.run(shoot(hp, pp, W, H))
        if not a.html: hp.unlink()
        results.append(str(pp))
    (out / f"{stem}-caption.txt").write_text(caption + "\n")
    print(json.dumps({"pngs": results, "caption": caption}, indent=2))

if __name__ == "__main__":
    main()
