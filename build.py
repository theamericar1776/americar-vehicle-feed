import json,re,csv,html,datetime,urllib.request
from xml.sax.saxutils import escape
STORE="RAL-NE-1776"; DEALER="AMERICAR LLC"; PHONE="(402) 279-1999"
BANNED=re.compile(r'in-house|in house|bhph|buy here|pay here|bad credit|good credit / bad credit',re.I)
def vin_ok(v):
    if not re.fullmatch(r'[A-HJ-NPR-Z0-9]{17}',v or ""): return False
    tr={**{str(i):i for i in range(10)},**dict(zip("ABCDEFGH",range(1,9))),**dict(zip("JKLMN",range(1,6))),"P":7,"R":9,**dict(zip("STUVWXYZ",range(2,10)))}
    w=[8,7,6,5,4,3,2,10,0,9,8,7,6,5,4,3,2]; s=sum(tr[c]*w[i] for i,c in enumerate(v))%11
    return v[8]==("X" if s==10 else str(s))
def desc(c):
    t=f"{c['year']} {c['make']} {c['model']} {c['trim']}".strip()
    p=[f"{t} for sale at {DEALER}, 7216 Main St, Ralston NE."]
    p.append(f"{c['mileage']:,} miles. {c['color']} exterior, {c['interior']} interior. {c['transmission']}, {c['fuel']}.")
    keep=[l.strip("-–•✅ \t") for l in c["site_description"].split("\n") if re.match(r'\s*(-|✅)',l) and not re.search(r'financ|warrant|price',l,re.I) and not BANNED.search(l)]
    if keep: p.append("Highlights: "+"; ".join(keep[:8])+".")
    p.append(f"Trade-ins welcome. Call {PHONE} to schedule a test drive.")
    return " ".join(p)[:5000]
def validate(c,live_check=False):
    e,w=list(c["errors"]),[]
    for f in ("vin","year","make","model","price","mileage","link"):
        if not c.get(f): e.append(f"missing {f}")
    if c.get("vin") and not vin_ok(c["vin"]): e.append("VIN fails check digit")
    if not c.get("stock"): w.append("no stock # on site")
    if c.get("displayed_price") and c.get("price")!=c["displayed_price"]: e.append(f"price mismatch: structured ${c['price']} vs shown ${c['displayed_price']}")
    if c.get("price") and int(c["price"])<500: e.append("price looks placeholder")
    if not c.get("images"): e.append("no photos (skipped)")
    elif len(c["images"])<3: w.append("fewer than 3 photos")
    if c.get("availability") and c["availability"]!="InStock": e.append(f"availability {c['availability']}")
    sd=c.get("site_description","")
    if BANNED.search(sd): w.append("website description mentions in-house/BHPH financing (excluded from feed; fix on site)")
    m=re.findall(r'\$\s?([\d,]{4,})',sd)
    other=[x.replace(",","") for x in m if x.replace(",","")!=c.get("price")]
    if other: w.append("website description shows a different price ($"+", $".join(other)+"): Google price-consistency risk")
    if c.get("mileage",0)==0: w.append("mileage 0")
    if live_check and c.get("images"):
        try: urllib.request.urlopen(urllib.request.Request(c["images"][0],method="HEAD"),timeout=15)
        except Exception as x: e.append(f"main image unreachable: {x}")
    return e,w
COLS=["id","store_code","title","description","link","link_template","image_link","additional_image_link","price","condition","vin","brand","model","year","trim","mileage","color","body_style","vehicle_fulfillment(option:store_code)","google_product_category","availability"]
def row(c):
    return {"id":c["vin"],"store_code":STORE,"title":f"{c['year']} {c['make']} {c['model']} {c['trim']}".strip()[:150],"description":desc(c),"link":c["link"],"link_template":c["link"]+("&" if "?" in c["link"] else "?")+"store={store_code}",
     "image_link":c["images"][0],"additional_image_link":",".join(c["images"][1:11]),"price":f"{c['price']}.00 USD","condition":c["condition"],"vin":c["vin"],
     "brand":c["make"],"model":c["model"],"year":c["year"],"trim":c["trim"],"mileage":f"{c['mileage']} miles","color":c["color"],"body_style":c["body"],
     "vehicle_fulfillment(option:store_code)":f"in_store:{STORE}","google_product_category":"916","availability":"in_stock"}
def build(inv,run_at):
    rows,report=[],[]
    for c in inv:
        e,w=validate(c,True); ok=not e
        if ok: rows.append(row(c))
        report.append({"stock":c.get("stock",""),"vin":c.get("vin",""),"title":f"{c.get('year','')} {c.get('make','')} {c.get('model','')} {c.get('trim','')}".strip(),
          "price":c.get("price",""),"mileage":c.get("mileage",""),"photos":len(c.get("images",[])),"link":c["link"],"thumb":(c.get("images") or [""])[0],
          "status":"IN FEED" if ok else "EXCLUDED","errors":e,"warnings":w})
    with open("out/vehicle_feed.tsv","w",newline="") as f:
        x=csv.DictWriter(f,COLS,delimiter="\t"); x.writeheader(); x.writerows(rows)
    with open("out/vehicle_feed.xml","w") as f:
        f.write('<?xml version="1.0"?>\n<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0"><channel><title>Americar LLC vehicles</title><link>https://www.americar-llc.com</link>\n')
        for r in rows:
            f.write("<item>"+"".join(
              "".join(f"<g:additional_image_link>{escape(u)}</g:additional_image_link>" for u in v.split(",") if u) if k=="additional_image_link" else
              f"<g:vehicle_fulfillment><g:option>in_store</g:option><g:store_code>{STORE}</g:store_code></g:vehicle_fulfillment>" if k.startswith("vehicle_fulfillment") else
              f"<g:{k}>{escape(str(v))}</g:{k}>" for k,v in r.items())+"</item>\n")
        f.write("</channel></rss>\n")
    json.dump({"run_at":run_at,"cars":report},open("out/report.json","w"),indent=1)
    return rows,report
def dashboard(report,run_at,n_rows):
    trs="".join(f"<tr class='{'bad' if r['errors'] else 'warn' if r['warnings'] else 'ok'}'><td><img src='{html.escape(r['thumb'])}'></td><td><a href='{html.escape(r['link'])}'>{html.escape(r['title'])}</a><br><small>Stock {html.escape(r['stock'])} · VIN {html.escape(r['vin'])}</small></td><td>${int(r['price'] or 0):,}</td><td>{r['mileage']:,}</td><td>{r['photos']}</td><td><b>{r['status']}</b></td><td>{'<br>'.join('❌ '+html.escape(x) for x in r['errors'])}{'<br>'.join('⚠️ '+html.escape(x) for x in r['warnings'])}</td></tr>" for r in report)
    open("out/dashboard.html","w").write(f"""<!doctype html><meta charset=utf-8><title>Americar Feed</title><style>body{{font-family:sans-serif;margin:20px}}td,th{{border-bottom:1px solid #ddd;padding:6px;vertical-align:top}}img{{width:110px}}tr.bad{{background:#fde8e8}}tr.warn{{background:#fff8e1}}</style>
<h1>Americar LLC: Google vehicle-ads feed (shadow mode)</h1><p>Last run: <b>{run_at}</b> · On website: {len(report)} · In feed: {n_rows} · Excluded: {len(report)-n_rows} · With warnings: {sum(1 for r in report if r['warnings'])} · DMC baseline: 35 inventory / 38 live on Google</p>
<p><a href=vehicle_feed.tsv>vehicle_feed.tsv</a> · <a href=vehicle_feed.xml>vehicle_feed.xml</a> · NOT pushed to Google.</p><table><tr><th></th><th>Vehicle</th><th>Price</th><th>Miles</th><th>Photos</th><th>Status</th><th>Issues</th></tr>{trs}</table>""")
