from playwright.sync_api import sync_playwright
from pathlib import Path
import json
URL="https://pedroalread.github.io/laboratorio-de-producto-pedro/"
results=[]
def ck(n,ok):results.append((n,bool(ok)));print(("PASS" if ok else "FAIL"),n,flush=True)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
 for w,h in [(2560,1440),(1440,900),(390,844),(320,700)]:
  ctx=b.new_context(viewport={"width":w,"height":h},accept_downloads=True);page=ctx.new_page();err=[];page.on("pageerror",lambda e:err.append(str(e)))
  response=page.goto(URL,wait_until="domcontentloaded",timeout=60000)
  ck(f"{w} HTTP 200",response.status==200)
  ck(f"{w} five original guides",page.locator(".tool-card").count()==5)
  ck(f"{w} economic evaluator",page.locator("#bc-form").count()==1)
  ck(f"{w} no JS errors",not err)
  ck(f"{w} no overflow",page.evaluate("document.documentElement.scrollWidth<=innerWidth"))
  if w==2560:
   for key,val in [("invest","100"),("revenue","100"),("margin","50"),("cost","0"),("realization","100"),("months","10")]:page.locator("#bc-"+key).fill(val)
   ck("net benefit 50MM",page.locator("#bc-net").inner_text().strip()=="50 MM")
   ck("payback 2 months",page.locator("#bc-payback").inner_text().strip()=="2 meses")
   ck("ROI 400%",page.locator("#bc-roi").inner_text().strip()=="400 %")
   with page.expect_download() as d:page.locator("#bc-export").click()
   ck("export JSON",d.value.suggested_filename.endswith(".json"))
   page.locator("#bc-margin").fill("150")
   ck("invalid assumptions refused","Revisar" in page.locator("#bc-net").inner_text())
   page.locator("#bc-reset").click()
   ck("reset to examples",page.locator("#bc-invest").input_value()=="120")
   page.locator(".tool-card .card-open").first.click()
   ck("legacy guide still opens",page.locator("#guide-dialog").evaluate("(x)=>x.open"))
   page.screenshot(path="qa/roi-qhd.png",full_page=False)
  if w==390:page.screenshot(path="qa/roi-movil.png",full_page=False)
  ctx.close()
 b.close()
n=sum(x[1] for x in results);Path("qa/roi-report.json").write_text(json.dumps({"total":len(results),"passed":n,"tests":results},ensure_ascii=False,indent=2))
print(f"RESULT: {n}/{len(results)} passing",flush=True);assert n==len(results)
