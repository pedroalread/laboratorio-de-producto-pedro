from pathlib import Path
from playwright.sync_api import sync_playwright
import json, os, tempfile

SITE = os.environ.get("PORTAL_URL", "https://pedroalread.github.io/laboratorio-de-producto-pedro/")
results = []

def ck(name, ok):
    print(("PASS " if ok else "FAIL ") + name, flush=True)
    results.append({"name":name, "passed":bool(ok)})

Path("qa/screenshots").mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
    for width,height in [(2560,1440),(1920,1080),(1440,900),(768,1024),(390,844),(320,700)]:
        context=browser.new_context(viewport={"width":width,"height":height},accept_downloads=True)
        page=context.new_page()
        errors=[]
        page.on("pageerror",lambda err:errors.append(str(err)))
        response=page.goto(SITE,wait_until="load",timeout=60000)
        ck(f"{width}px no JS errors",len(errors)==0 and response.status==200)
        ck(f"{width}px no horizontal overflow",page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
        ck(f"{width}px five guides present",page.locator(".tool-card").count()==5)
        if width==2560:
            ck("Main headline",page.locator(".hero-intro h1").is_visible())
            ck("Original landscape",page.locator(".mountain-svg path").count()>=5)
            ck("Main product demo",page.locator(".product-window").is_visible())
            page.screenshot(path="qa/screenshots/produccion-qhd.png",full_page=True)
        if width==390: page.screenshot(path="qa/screenshots/produccion-movil.png",full_page=True)
        context.close()

    context=browser.new_context(accept_downloads=True)
    page=context.new_page()
    errors=[]
    page.on("pageerror",lambda err:errors.append(str(err)))
    response=page.goto(SITE,wait_until="load",timeout=60000)
    ck("Production HTTPS responds HTTP 200",response.status==200 and page.url.startswith("https://"))
    page.locator(".tool-card .card-open").first.click()
    ck("Guide opens",page.locator("#guide-dialog").evaluate("(e)=>e.open"))
    ck("Import button available",page.locator("#import-data").is_visible())
    with page.expect_download() as download_info:page.locator("#export-data").click()
    download=download_info.value
    with tempfile.TemporaryDirectory() as d:
        exported=Path(d)/"producto.json"
        download.save_as(str(exported))
        obj=json.loads(exported.read_text(encoding="utf-8"))
        ck("Export correct tool",obj["herramienta"]=="presupuesto100")
        edited=dict(obj)
        edited["datos"]=[
            {"name":"Reducir fraude","points":50},
            {"name":"Simplificar onboarding","points":20},
            {"name":"Activacion de tarjetas","points":20},
            {"name":"Acelerar transferencias","points":10}
        ]
        good=Path(d)/"correcto.json"
        good.write_text(json.dumps(edited,ensure_ascii=False),encoding="utf-8")
        page.locator("#import-file").set_input_files(str(good))
        page.wait_for_function("document.querySelector('#tool-message').textContent.includes('restaurado')")
        ck("Import restores edited data",page.evaluate("toolState[0].points") == 50 and "100 / 100" in page.locator("#budget-status").inner_text())
        wrong=Path(d)/"otra-herramienta.json"
        wrong.write_text(json.dumps({"herramienta":"raci","datos":[]}),encoding="utf-8")
        page.locator("#import-file").set_input_files(str(wrong))
        page.wait_for_function("document.querySelector('#tool-message').textContent.includes('otra herramienta')")
        ck("Wrong-tool JSON rejected","otra herramienta" in page.locator("#tool-message").inner_text())
        invalid=Path(d)/"invalido.json"
        invalid.write_text("{not json",encoding="utf-8")
        page.locator("#import-file").set_input_files(str(invalid))
        page.wait_for_function("document.querySelector('#tool-message').textContent.includes('No se pudo leer')")
        ck("Invalid JSON rejected","No se pudo leer" in page.locator("#tool-message").inner_text())
        page.locator("#close-guide").click()
        page.locator(".tool-card .card-open").first.click()
        ck("Guide reopens",page.locator("#guide-dialog").evaluate("(e)=>e.open"))
        ck("No execution errors",len(errors)==0 and page.evaluate("typeof initImport==='function' && typeof validateImportedData==='function'"))
        page.locator("#close-guide").click()
        page.reload(wait_until="load")
        page.locator(".tool-card .card-open").first.click()
        ck("Data survive HTTPS page reload",page.evaluate("toolState[0].points")==50)
        ck("Same-origin localStorage saved",page.evaluate("JSON.parse(localStorage.getItem('po-lab:presupuesto100'))[0].points")==50)
        ck("Portfolio navigation points to production",page.locator("a[href*='pedro-navarrete-portfolio.vercel.app']").count()>=1)
    context.close()
    browser.close()
passed=sum(1 for t in results if t["passed"])
report={"url":SITE,"passed":passed,"total":len(results),"tests":results}
Path("qa/resultado-produccion.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print(f"RESULT: {passed}/{len(results)} passing")
assert passed==len(results), "Production QA failed"