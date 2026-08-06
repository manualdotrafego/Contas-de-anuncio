#!/usr/bin/env python3
"""
Atualiza planilha de ciclos (PT + BR) e o dashboard de criativos.
Roda a cada 6h. Idempotente: pode rodar quantas vezes quiser.

Credenciais (via env ou .env ao lado do script):
  META_ACCESS_TOKEN  token com ads_read em act_615338413578534
  GOOGLE_SA_JSON     caminho do json do service account (ou o proprio json)
  GH_TOKEN           token do GitHub para publicar o dashboard (opcional)

NUNCA sobrescreve numeros confirmados manualmente:
  entrantes no grupo, comparecimento no webinario e calls.
"""
import os, sys, json, time, base64, urllib.request, urllib.parse, datetime, re, io

HERE = os.path.dirname(os.path.abspath(__file__))
ACT = 'act_615338413578534'
API = 'https://graph.facebook.com/v19.0'
SHEET_ID = '1sj_Pw5tHAGUqLzNz696bxFxmbaofWKRF5_vFjPpNDwY'
GID_PT, GID_BR, GID_FUNIL = 1520844617, 2017982781, 557337600
REPO = 'manualdotrafego/devspace-dashboard'
DASH_PATH = 'webinar-criativos/index.html'
PT_C1_START = datetime.date(2026, 3, 25)   # inicio do Ciclo 1 de Portugal
BR_C1_START = datetime.date(2026, 7, 29)   # inicio do Ciclo 1 do Brasil
CACHE = os.path.join(HERE, 'thumb_cache.json')

def log(*a):
    print(datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), *a, flush=True)

# ---------- .env ----------
envf = os.path.join(HERE, '.env')
if os.path.exists(envf):
    for line in open(envf):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

TOKEN = os.environ.get('META_ACCESS_TOKEN', '')
if not TOKEN:
    log('ERRO: META_ACCESS_TOKEN ausente. Nada a fazer.')
    sys.exit(2)

# ---------- Meta ----------
def graph(path, params, tries=6):
    params = dict(params); params['access_token'] = TOKEN
    url = f'{API}/{path}?' + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            if ('limit' in body.lower() or e.code >= 500) and i < tries - 1:
                time.sleep(45); continue
            log('  graph erro', path, body); return {}
        except Exception as ex:
            if i < tries - 1: time.sleep(15); continue
            log('  graph falha', path, str(ex)[:150]); return {}
    return {}

def acts(row):
    return {a['action_type']: float(a['value']) for a in row.get('actions', [])}

def leads_of(a):
    return (a.get('lead') or a.get('offsite_conversion.fb_pixel_lead')
            or a.get('onsite_conversion.lead_grouped') or 0)

def campaigns():
    d = graph(f'{ACT}/campaigns', {'fields': 'id,name,status', 'limit': 300}).get('data', [])
    pt = [c for c in d if 'BRASIL' not in c['name'].upper()]
    br = [c for c in d if 'BRASIL' in c['name'].upper()]
    return pt, br

def daily(cids, since, until, level='campaign', extra=''):
    """insights diarios agregados; devolve lista de linhas com date_start."""
    out = []
    flds = 'spend,impressions,clicks,inline_link_clicks,actions'
    if extra: flds += ',' + extra
    for cid in cids:
        r = graph(f'{cid}/insights', {
            'level': level, 'time_increment': 1,
            'time_range': json.dumps({'since': since, 'until': until}),
            'fields': flds, 'limit': 500})
        for row in r.get('data', []):
            row['_cid'] = cid; out.append(row)
        nxt = (r.get('paging') or {}).get('next')
        while nxt:
            try:
                with urllib.request.urlopen(nxt, timeout=180) as rr: r2 = json.load(rr)
            except Exception: break
            for row in r2.get('data', []):
                row['_cid'] = cid; out.append(row)
            nxt = (r2.get('paging') or {}).get('next')
    return out

def agg(rows):
    t = dict(spend=0.0, impr=0, clk=0, lc=0, lpv=0, lead=0)
    for r in rows:
        a = acts(r)
        t['spend'] += float(r.get('spend') or 0)
        t['impr'] += int(r.get('impressions') or 0)
        t['clk'] += int(r.get('clicks') or 0)
        t['lc'] += int(r.get('inline_link_clicks') or 0)
        t['lpv'] += int(a.get('landing_page_view') or 0)
        t['lead'] += int(leads_of(a))
    return t

# ---------- ciclos ----------
def cycle_bounds(anchor, n):
    s = anchor + datetime.timedelta(days=7 * (n - 1))
    return s, s + datetime.timedelta(days=6)

def cycle_of(anchor, d):
    return (d - anchor).days // 7 + 1

# ---------- Sheets ----------
def sheets():
    import gspread
    from google.oauth2.service_account import Credentials
    raw = os.environ.get('GOOGLE_SA_JSON', '')
    scopes = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive']
    if raw.strip().startswith('{'):
        cr = Credentials.from_service_account_info(json.loads(raw), scopes=scopes)
    else:
        path = raw or os.path.join(HERE, 'sa.json')
        cr = Credentials.from_service_account_file(path, scopes=scopes)
    return gspread.authorize(cr).open_by_key(SHEET_ID)

def col_letter(i):
    s = ''
    while i > 0:
        i, r = divmod(i - 1, 26); s = chr(65 + r) + s
    return s

def num(x):
    """converte '€1.234,56' / '7,85%' / '1.234' em float."""
    if x is None: return 0.0
    s = str(x).strip()
    if not s: return 0.0
    s = re.sub(r'[^\d,.\-]', '', s)
    if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.')
    elif ',' in s: s = s.replace(',', '.')
    try: return float(s)
    except: return 0.0

# ---------- PT ----------
def update_pt(sh, pt_ids, today):
    ws = [w for w in sh.worksheets() if w.id == GID_PT][0]
    vals = ws.get_all_values()
    hdr = vals[0]
    n = cycle_of(PT_C1_START, today)
    s, e = cycle_bounds(PT_C1_START, n)
    label = f'Ciclo {n}'
    if label in hdr:
        ci = hdr.index(label) + 1
    else:                                    # ciclo novo: entra antes do LIFETIME
        li = hdr.index('LIFETIME') + 1 if 'LIFETIME' in hdr else len(hdr) + 1
        ws.insert_cols([[]], li); ci = li
        log(f'  PT: criada coluna do {label}')
    L = col_letter(ci)
    until = min(e, today)
    rows = daily(pt_ids, s.isoformat(), until.isoformat())
    t = agg(rows)
    if t['impr'] == 0:
        log(f'  PT: {label} sem dados ainda'); return
    cpm = t['spend'] / t['impr'] * 1000
    ctr = t['clk'] / t['impr'] * 100
    cpc = t['spend'] / t['lc'] if t['lc'] else 0
    conv = t['lead'] / t['lc'] * 100 if t['lc'] else 0
    cpl = t['spend'] / t['lead'] if t['lead'] else 0
    ws.update(values=[[label], [f"{s.strftime('%d/%m')} → {e.strftime('%d/%m')}"],
                      [(until - s).days + 1],
                      [round(t['spend'], 2)], [t['impr']], [t['clk']],
                      [round(cpm, 2)], [round(ctr, 2)], [round(cpc, 2)],
                      [t['lead']], [round(conv, 2)], [round(cpl, 2)]],
              range_name=f'{L}1:{L}12', value_input_option='RAW')
    # LIFETIME por formula (nao sobrescreve nada manual)
    hdr2 = ws.get_all_values()[0]
    if 'LIFETIME' in hdr2:
        U = col_letter(hdr2.index('LIFETIME') + 1)
        last = col_letter(hdr2.index('LIFETIME'))
        ws.update(values=[[f'=SUM(B4:{last}4)'], [f'=SUM(B5:{last}5)'], [f'=SUM(B6:{last}6)'],
                          [f'=SUM(B4:{last}4)/SUM(B5:{last}5)*1000'],
                          [f'=SUM(B6:{last}6)/SUM(B5:{last}5)*100'],
                          [f'=SUM(B4:{last}4)/SUMPRODUCT(IFERROR(B4:{last}4/B9:{last}9;0))'],
                          [f'=SUM(B10:{last}10)'],
                          [f'=SUM(B10:{last}10)/SUM(B6:{last}6)*100'],
                          [f'=SUM(B4:{last}4)/SUM(B10:{last}10)']],
                  range_name=f'{U}4:{U}12', value_input_option='USER_ENTERED')
    log(f"  PT {label}: EUR {t['spend']:.2f} | {t['lead']} leads | CPL EUR {cpl:.2f}")

# ---------- BR ----------
def update_br(sh, br_ids, today, tx):
    ws = [w for w in sh.worksheets() if w.id == GID_BR][0]
    vals = ws.get_all_values()
    hdr = vals[0]
    n = cycle_of(BR_C1_START, today)
    label = f'Ciclo {n} BR'
    if label in hdr:
        ci = hdr.index(label) + 1
    else:
        li = hdr.index('LIFETIME BR') + 1 if 'LIFETIME BR' in hdr else len(hdr) + 1
        ws.insert_cols([[]], li); ci = li
        vals = ws.get_all_values(); hdr = vals[0]
        log(f'  BR: criada coluna do {label}')
    L = col_letter(ci)
    s, e = cycle_bounds(BR_C1_START, n)
    until = min(e, today)
    rows = daily(br_ids, s.isoformat(), until.isoformat())
    t = agg(rows)
    if t['impr'] == 0:
        log(f'  BR: {label} sem dados ainda'); return
    # preserva entrantes no grupo (linha 16) digitado manualmente
    grupo = 0
    try: grupo = int(num(vals[15][ci - 1])) if len(vals) > 15 and len(vals[15]) >= ci else 0
    except Exception: grupo = 0
    cpm = t['spend'] / t['impr'] * 1000
    ctr = t['clk'] / t['impr']
    cpc = t['spend'] / t['lc'] if t['lc'] else 0
    conv = t['lead'] / t['lc'] if t['lc'] else 0
    cpl = t['spend'] / t['lead'] if t['lead'] else 0
    body = [[label],
            [f"{s.strftime('%d/%m')} a {until.strftime('%d/%m/%Y')}" + (' (em curso)' if until < e else '')],
            [(until - s).days + 1],
            [round(t['spend'], 2)], [round(t['spend'] * tx, 2)],
            [t['impr']], [t['clk']], [t['lc']],
            [round(cpm, 2)], [round(ctr, 6)], [round(cpc, 4)],
            [t['lpv']], [t['lead']], [round(conv, 6)], [round(cpl, 4)]]
    ws.update(values=body, range_name=f'{L}1:{L}15', value_input_option='RAW')
    if grupo:   # so escreve custo por entrante se o numero manual existe
        ws.update(values=[[round(t['spend'] / grupo, 4)],
                          [round(t['spend'] * tx / grupo, 2)]],
                  range_name=f'{L}17:{L}18', value_input_option='RAW')
    ws.update(values=[[round(t['lpv'] / t['lc'], 6) if t['lc'] else 0],
                      [round(t['lead'] / t['lpv'], 6) if t['lpv'] else 0],
                      [round(grupo / t['lead'], 6) if (grupo and t['lead']) else 0],
                      [round(grupo / t['lc'], 6) if (grupo and t['lc']) else 0]],
              range_name=f'{L}21:{L}24', value_input_option='RAW')
    log(f"  BR {label}: EUR {t['spend']:.2f} | {t['lead']} leads | grupo={grupo or 'manual pendente'}")
    # LIFETIME BR por formula, somando todas as colunas de ciclo
    hdr3 = ws.get_all_values()[0]
    if 'LIFETIME BR' in hdr3:
        D = col_letter(hdr3.index('LIFETIME BR') + 1)
        lastc = col_letter(hdr3.index('LIFETIME BR'))
        R = lambda r: f'SUM(B{r}:{lastc}{r})'
        ws.update(values=[[f'={R(3)}'], [f'={R(4)}'], [f'={R(5)}'], [f'={R(6)}'],
                          [f'={R(7)}'], [f'={R(8)}'],
                          [f'={D}4/{D}6*1000'], [f'={D}7/{D}6'], [f'={D}4/{D}8'],
                          [f'={R(12)}'], [f'={R(13)}'], [f'={D}13/{D}8'], [f'={D}4/{D}13'],
                          [f'={R(16)}'], [f'=IFERROR({D}4/{D}16;"")'], [f'=IFERROR({D}5/{D}16;"")']],
                  range_name=f'{D}3:{D}18', value_input_option='USER_ENTERED')
        ws.update(values=[[f'=IFERROR({D}12/{D}8;"")'], [f'=IFERROR({D}13/{D}12;"")'],
                          [f'=IFERROR({D}16/{D}13;"")'], [f'=IFERROR({D}16/{D}8;"")']],
                  range_name=f'{D}21:{D}24', value_input_option='USER_ENTERED')
        ws.update(values=[[f"29/07 a {today.strftime('%d/%m/%Y')}"]],
                  range_name=f'{D}2', value_input_option='RAW')

    return n, t, grupo

# ---------- dashboard ----------
def thumbs(ad_ids_names):
    cache = {}
    if os.path.exists(CACHE):
        try: cache = json.load(open(CACHE))
        except Exception: cache = {}
    novos = 0
    for aid, name in ad_ids_names:
        if name in cache: continue
        d = graph(aid, {'fields': 'creative{thumbnail_url,effective_object_story_id}'})
        cr = d.get('creative') or {}
        url = cr.get('thumbnail_url'); post = cr.get('effective_object_story_id')
        img = ''
        if url:
            try:
                with urllib.request.urlopen(url.replace('p64x64', 'p320x320'), timeout=45) as r:
                    img = 'data:image/jpeg;base64,' + base64.b64encode(r.read()).decode()
            except Exception: img = ''
        cache[name] = {'img': img,
                       'post': f'https://www.facebook.com/{post}' if post else ''}
        novos += 1
    if novos:
        json.dump(cache, open(CACHE, 'w'))
        log(f'  thumbs: {novos} novos, {len(cache)} em cache')
    return cache

def build_dash(pt_ids, br_ids, today):
    data = {}
    for tag, ids, anchor, start in (('PT', pt_ids, PT_C1_START, PT_C1_START),
                                    ('BR', br_ids, BR_C1_START, BR_C1_START)):
        rows = daily(ids, start.isoformat(), today.isoformat(), level='ad', extra='ad_id,ad_name')
        byc = {}
        for r in rows:
            d = datetime.date.fromisoformat(r['date_start'])
            n = cycle_of(anchor, d)
            key = (n, (r.get('ad_name') or '?').strip())
            a = acts(r)
            k = byc.setdefault(key, dict(spend=0.0, impr=0, lc=0, lead=0, aid=r.get('ad_id')))
            k['spend'] += float(r.get('spend') or 0)
            k['impr'] += int(r.get('impressions') or 0)
            k['lc'] += int(r.get('inline_link_clicks') or 0)
            k['lead'] += int(leads_of(a))
        data[tag] = byc
    pares = {(v['aid'], name) for byc in data.values() for (n, name), v in byc.items() if v['aid']}
    cache = thumbs(sorted(pares))
    out = {}
    for tag, byc in data.items():
        cy = {}
        for (n, name), v in byc.items():
            if v['spend'] <= 0: continue
            t = cache.get(name, {})
            cy.setdefault(n, []).append({
                'name': name, 'spend': round(v['spend'], 2), 'imp': v['impr'],
                'lc': v['lc'], 'leads': v['lead'],
                'ctr': round(v['lc'] / v['impr'] * 100, 2) if v['impr'] else 0,
                'cpl': round(v['spend'] / v['lead'], 2) if v['lead'] else None,
                'img': t.get('img', ''), 'post': t.get('post', '')})
        anchor = PT_C1_START if tag == 'PT' else BR_C1_START
        lst = []
        for n in sorted(cy):
            crs = sorted(cy[n], key=lambda x: (-x['leads'], x['cpl'] or 9999))
            s, e = cycle_bounds(anchor, n)
            sp = sum(c['spend'] for c in crs); ld = sum(c['leads'] for c in crs)
            lc = sum(c['lc'] for c in crs)
            lst.append({'num': n, 'period': f"{s.strftime('%d/%m')} → {e.strftime('%d/%m')}",
                        'creatives': crs, 'spend': round(sp, 2), 'leads': ld,
                        'cpl': round(sp / ld, 2) if ld else 0,
                        'conv': round(ld / lc * 100, 1) if lc else 0, 'n': len(crs)})
        out[tag] = lst
    return out

HTML = '''<!DOCTYPE html><html lang="pt"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Criativos por Ciclo - Webinar 2026</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0a0a;color:#fff;padding:24px}
.head{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;margin-bottom:18px;border-bottom:3px solid #FFE500;padding-bottom:18px}
.head h1{font-size:22px;font-weight:800}.head .sub{color:#9a9a9a;font-size:13px;margin-top:4px}
.kpis{display:flex;gap:14px;flex-wrap:wrap}
.kpi{background:#161616;border-radius:12px;padding:12px 18px;border-left:3px solid #FFE500}
.kpi .v{font-size:20px;font-weight:800;color:#FFE500}.kpi .l{font-size:10px;color:#9a9a9a;text-transform:uppercase;letter-spacing:.5px}
.tabs{display:flex;gap:10px;margin-bottom:6px}
.tab{background:#161616;border:2px solid #2a2a2a;color:#999;padding:11px 26px;border-radius:11px;cursor:pointer;font-size:15px;font-weight:800}
.tab.on{background:#FFE500;border-color:#FFE500;color:#0a0a0a}
.warn{background:#2a1a1a;border-left:3px solid #ef4444;border-radius:8px;padding:11px 15px;margin:14px 0;font-size:12px;color:#e5b4b4}
.cycle{background:#141414;border-radius:14px;margin-bottom:14px;overflow:hidden;border:1px solid #222}
.chead{display:flex;align-items:center;gap:18px;padding:16px 20px;cursor:pointer;user-select:none}
.chead:hover{background:#1c1c1c}
.cnum{background:#FFE500;color:#0a0a0a;font-weight:800;font-size:15px;width:46px;height:46px;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-direction:column;line-height:1;flex-shrink:0}
.cnum small{font-size:8px;font-weight:600}
.cper{font-weight:700;font-size:15px}.cper small{display:block;color:#9a9a9a;font-size:11px;font-weight:400;margin-top:2px}
.cstats{margin-left:auto;display:flex;gap:22px;align-items:center;flex-wrap:wrap}
.cstat{text-align:right}.cstat .v{font-weight:800;font-size:16px}.cstat .l{font-size:9px;color:#9a9a9a;text-transform:uppercase}
.cstat .v.g{color:#22c55e}.cstat .v.y{color:#FFE500}
.arrow{font-size:13px;color:#666;transition:.2s;margin-left:6px}
.cycle.open .arrow{transform:rotate(90deg)}
.cbody{display:none;padding:6px 20px 20px}.cycle.open .cbody{display:block}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(185px,1fr));gap:12px}
.card{background:#1a1a1a;border-radius:11px;overflow:hidden;border:1px solid #2a2a2a;display:flex;flex-direction:column}
.card:hover{border-color:#FFE500}
.thumb{width:100%;aspect-ratio:1/1;object-fit:cover;background:#000;display:block}
.nothumb{width:100%;aspect-ratio:1/1;background:#222;display:flex;align-items:center;justify-content:center;color:#555;font-size:11px}
.cardb{padding:10px 12px;flex:1;display:flex;flex-direction:column}
.cname{font-weight:700;font-size:12px;margin-bottom:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.metrics{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.m{background:#0e0e0e;border-radius:6px;padding:5px 8px}
.m .v{font-weight:800;font-size:13px}.m .l{font-size:8px;color:#888;text-transform:uppercase}
.m.lead .v{color:#FFE500}.m.cpl .v{color:#22c55e}.m.cpl.bad .v{color:#ef4444}
.prev{display:block;margin-top:9px;text-align:center;background:#FFE500;color:#0a0a0a;font-weight:800;font-size:11px;padding:7px;border-radius:7px;text-decoration:none}
.prev.off{background:#2a2a2a;color:#666;pointer-events:none}
.badge{position:absolute;top:8px;left:8px;background:#FFE500;color:#000;font-weight:800;font-size:11px;padding:2px 8px;border-radius:20px}
.cardwrap{position:relative}
.foot{text-align:center;color:#555;font-size:11px;margin-top:20px;font-family:monospace}
.controls{margin:14px 0 16px;display:flex;gap:10px}
.btn{background:#161616;border:1px solid #333;color:#ccc;padding:8px 16px;border-radius:8px;cursor:pointer;font-size:12px;font-weight:600}
</style></head><body>
<div class="head"><div><h1>Criativos por Ciclo - Webinar 2026</h1>
<div class="sub">Joao Mafra Lancamento (EUR) - atualizado __UPD__</div></div>
<div class="kpis" id="kpis"></div></div>
<div class="tabs"><button class="tab on" id="tPT" onclick="setPais('PT')">PORTUGAL</button>
<button class="tab" id="tBR" onclick="setPais('BR')">BRASIL</button></div>
<div id="aviso"></div>
<div class="controls">
<button class="btn" onclick="document.querySelectorAll('.cycle').forEach(c=>c.classList.add('open'))">Expandir todos</button>
<button class="btn" onclick="document.querySelectorAll('.cycle').forEach(c=>c.classList.remove('open'))">Recolher todos</button></div>
<div id="app"></div><div class="foot" id="foot"></div>
<script>
const DATA=__DATA__;
const eur=v=>'EUR '+v.toFixed(2).replace('.',',');
let pais='PT';
function setPais(p){pais=p;
 document.getElementById('tPT').classList.toggle('on',p==='PT');
 document.getElementById('tBR').classList.toggle('on',p==='BR');render();}
function render(){
 const cy=DATA[pais];
 const sp=cy.reduce((a,c)=>a+c.spend,0), ld=cy.reduce((a,c)=>a+c.leads,0);
 document.getElementById('kpis').innerHTML=`
  <div class="kpi"><div class="v">${eur(sp)}</div><div class="l">Gasto total</div></div>
  <div class="kpi"><div class="v">${ld}</div><div class="l">Leads</div></div>
  <div class="kpi"><div class="v">${eur(ld?sp/ld:0)}</div><div class="l">CPL medio</div></div>
  <div class="kpi"><div class="v">${cy.length}</div><div class="l">Ciclos</div></div>`;
 document.getElementById('aviso').innerHTML = pais==='BR'
  ? '<div class="warn"><b>Atencao:</b> no Brasil os leads sao CLIQUES NO BOTAO da LP, nao entradas no grupo. O numero real de entrantes esta na planilha, aba Ciclo Brasil.</div>' : '';
 document.getElementById('foot').textContent='manualdotrafego - atualizacao automatica a cada 6h';
 const app=document.getElementById('app'); app.innerHTML='';
 cy.forEach((c,idx)=>{
  const cards=c.creatives.map(x=>{
   const bad=x.cpl&&x.cpl>6;
   const th=x.img?`<img class="thumb" src="${x.img}" loading="lazy">`:'<div class="nothumb">sem thumb</div>';
   const bg=x.leads>=10?`<div class="badge">${x.leads} leads</div>`:'';
   const cp=x.cpl!=null?`<div class="m cpl ${bad?'bad':''}"><div class="v">${eur(x.cpl)}</div><div class="l">CPL</div></div>`
                       :'<div class="m cpl"><div class="v">-</div><div class="l">CPL</div></div>';
   const pv=x.post?`<a class="prev" href="${x.post}" target="_blank">Ver previa</a>`:'<span class="prev off">sem previa</span>';
   return `<div class="card"><div class="cardwrap">${th}${bg}</div><div class="cardb">
    <div class="cname" title="${x.name}">${x.name}</div><div class="metrics">
    <div class="m lead"><div class="v">${x.leads}</div><div class="l">Leads</div></div>${cp}
    <div class="m"><div class="v">${eur(x.spend)}</div><div class="l">Gasto</div></div>
    <div class="m"><div class="v">${x.ctr.toFixed(2)}%</div><div class="l">CTR</div></div>
    </div>${pv}</div></div>`;}).join('');
  app.insertAdjacentHTML('beforeend',`<div class="cycle ${idx>=cy.length-2?'open':''}">
   <div class="chead" onclick="this.parentNode.classList.toggle('open')">
    <div class="cnum"><small>CICLO</small>${c.num}</div>
    <div class="cper">${c.period}<small>${c.n} criativos</small></div>
    <div class="cstats">
     <div class="cstat"><div class="v">${eur(c.spend)}</div><div class="l">Gasto</div></div>
     <div class="cstat"><div class="v y">${c.leads}</div><div class="l">Leads</div></div>
     <div class="cstat"><div class="v g">${eur(c.cpl)}</div><div class="l">CPL</div></div>
     <div class="cstat"><div class="v">${c.conv.toFixed(1)}%</div><div class="l">Conv</div></div>
     <span class="arrow">&#9654;</span></div></div>
   <div class="cbody"><div class="grid">${cards}</div></div></div>`);});
}
render();
</script></body></html>'''

def publish(html):
    tok = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    content = base64.b64encode(html.encode()).decode()
    if tok:
        base = f'https://api.github.com/repos/{REPO}/contents/{DASH_PATH}'
        def call(url, method='GET', payload=None):
            rq = urllib.request.Request(url, method=method,
                data=json.dumps(payload).encode() if payload else None,
                headers={'Authorization': f'Bearer {tok}', 'Accept': 'application/vnd.github+json',
                         'User-Agent': 'webauto'})
            with urllib.request.urlopen(rq, timeout=120) as r: return json.load(r)
        sha = None
        try: sha = call(base + '?ref=gh-pages').get('sha')
        except Exception: pass
        p = {'message': 'auto: atualizacao 6h do dashboard de criativos',
             'content': content, 'branch': 'gh-pages'}
        if sha: p['sha'] = sha
        call(base, 'PUT', p)
        log('  dashboard publicado via API'); return True
    # fallback: git + chave de deploy
    import subprocess, tempfile, shutil
    tmp = tempfile.mkdtemp()
    try:
        env = dict(os.environ, GIT_SSH_COMMAND='ssh -i /root/.ssh/webinar_deploy -o StrictHostKeyChecking=no')
        subprocess.run(['git', 'clone', '--depth', '1', '-b', 'gh-pages',
                        f'git@github.com:{REPO}.git', tmp], check=True, env=env,
                       capture_output=True, timeout=180)
        p = os.path.join(tmp, DASH_PATH); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w').write(html)
        subprocess.run(['git', '-C', tmp, 'config', 'user.email', 'bot@manualdotrafego'], check=True)
        subprocess.run(['git', '-C', tmp, 'config', 'user.name', 'webauto'], check=True)
        subprocess.run(['git', '-C', tmp, 'add', '-A'], check=True)
        r = subprocess.run(['git', '-C', tmp, 'commit', '-m', 'auto: atualizacao 6h'],
                           capture_output=True)
        if r.returncode == 0:
            subprocess.run(['git', '-C', tmp, 'push'], check=True, env=env,
                           capture_output=True, timeout=180)
            log('  dashboard publicado via git')
        else:
            log('  dashboard sem mudancas')
        return True
    except Exception as e:
        log('  ERRO publicar dashboard:', str(e)[:200]); return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

# ---------- cotacao ----------
def cotacao():
    fontes = [
        ('https://economia.awesomeapi.com.br/json/last/EUR-BRL',
         lambda d: float(d['EURBRL']['bid'])),
        ('https://api.frankfurter.dev/v1/latest?base=EUR&symbols=BRL',
         lambda d: float(d['rates']['BRL'])),
        ('https://open.er-api.com/v6/latest/EUR',
         lambda d: float(d['rates']['BRL'])),
    ]
    for url, pick in fontes:
        try:
            rq = urllib.request.Request(url, headers={'User-Agent': 'webauto/1.0'})
            with urllib.request.urlopen(rq, timeout=25) as r:
                v = pick(json.load(r))
            if 3 < v < 12:
                log(f'  cotacao de {urllib.parse.urlparse(url).netloc}'); return v
        except Exception:
            continue
    log('  nenhuma fonte de cotacao respondeu, usando 5.9175')
    return 5.9175

# ---------- main ----------
def main():
    t0 = time.time()
    log('=== inicio ===')
    today = datetime.date.today()
    pt, br = campaigns()
    pt_ids = [c['id'] for c in pt]; br_ids = [c['id'] for c in br]
    log(f'  {len(pt_ids)} campanhas PT, {len(br_ids)} campanhas BR')
    tx = cotacao(); log(f'  cotacao EUR/BRL {tx:.4f}')
    try:
        sh = sheets()
        update_pt(sh, pt_ids, today)
        update_br(sh, br_ids, today, tx)
    except Exception as e:
        log('  ERRO planilha:', str(e)[:300])
    try:
        d = build_dash(pt_ids, br_ids, today)
        html = (HTML.replace('__DATA__', json.dumps(d, ensure_ascii=False))
                    .replace('__UPD__', today.strftime('%d/%m/%Y')))
        publish(html)
    except Exception as e:
        log('  ERRO dashboard:', str(e)[:300])
    log(f'=== fim em {time.time()-t0:.0f}s ===')

if __name__ == '__main__':
    main()
