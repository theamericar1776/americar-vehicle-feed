import json,datetime,scrape,build
run_at=datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p CT")
inv=scrape.scrape(); json.dump(inv,open("data/inventory.json","w"),indent=1)
rows,rep=build.build(inv,run_at); build.dashboard(rep,run_at,len(rows))
print(run_at,"site:",len(inv),"feed:",len(rows))
for r in rep:
    if r["errors"] or r["warnings"]: print(r["stock"],r["title"],r["errors"],r["warnings"])
