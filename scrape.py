import re,json,html,urllib.request,concurrent.futures as cf
B="https://www.americar-llc.com"
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 AmericarFeedBot"}),timeout=30).read().decode("utf-8","ignore")
def urls():
    s=set(re.findall(r'Inventory/Details/[a-f0-9-]{36}',get(B+"/sitemap.xml")))
    s|=set(re.findall(r'Inventory/Details/[a-f0-9-]{36}',get(B+"/Inventory")))
    return sorted(B+"/"+x for x in s)
def info(h,label):
    m=re.search(r'info__label[^>]*>\s*'+re.escape(label)+r'\s*</div>\s*<div[^>]*>([^<]*)<',h)
    return html.unescape(m.group(1).strip()) if m else ""
def parse(u):
    h=get(u); r={"link":u,"errors":[]}
    lds=[]
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>',h,re.S):
        try: lds.append(json.loads(m))
        except: pass
    car=next((d for d in lds if "vehicleIdentificationNumber" in d),None)
    imgs=next((d["Image"] for d in lds if "Image" in d),[])
    if not car: r["errors"].append("no vehicle data (page sold/removed?)"); return r
    o=car.get("offers",{})
    r.update(vin=car.get("vehicleIdentificationNumber",""),year=str(car.get("modelDate","")),
      make=car.get("brand",{}).get("name",""),model=car.get("model",""),trim=car.get("vehicleConfiguration","") or "",
      price=o.get("price",""),availability=o.get("availability",""),
      mileage=int(car.get("mileageFromOdometer",{}).get("value") or 0),
      condition="used" if "Used" in o.get("itemCondition",car.get("itemCondition","")) else "new",
      body=car.get("bodyType",""),color=car.get("color","") or info(h,"Exterior Color"),
      interior=car.get("vehicleInteriorColor",""),transmission=car.get("vehicleTransmission",""),
      fuel=car.get("fuelType",""),drivetrain=car.get("driveWheelConfiguration","").split("/")[-1].replace("Configuration",""),
      stock=info(h,"Stock#"),site_description=html.unescape(re.sub(r'<br\s*/?>',"\n",car.get("description",""))),
      images=[i.get("url") for i in imgs if i.get("url")])
    m=re.search(r'price-allin-value[^>]*>(.*?)</div>',h,re.S)
    r["displayed_price"]=re.sub(r'\D','',re.sub(r'<[^>]+>','',m.group(1))) if m else ""
    return r
def scrape():
    with cf.ThreadPoolExecutor(6) as ex: return list(ex.map(parse,urls()))
if __name__=="__main__":
    d=scrape(); json.dump(d,open("data/inventory.json","w"),indent=1); print(len(d))
