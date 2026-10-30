from pathlib import Path
from playwright.sync_api import sync_playwright
import json, os
p=Path(__file__).with_name('index.html')
URL=os.environ.get('PORTAL_URL','https://pedroalread.github.io/laboratorio-de-producto-pedro/')
Path('qa/screenshots').mkdir(parents=True,exist_ok=True)
results=[]
def ck(label, passed):
 results.append((label,bool(passed)));print(('PASS' if passed else 'FAIL')+' '+label,flush=True)
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 for w,h in [(2560,1440),(1920,1080),(1440,900),(900,800),(768,1024),(390,844),(320,700)]:
  ctx=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=1)
  page=ctx.new_page();errs=[]
  page.on('pageerror',lambda e:errs.append(str(e)))
  response=page.goto(URL,wait_until='load',timeout=60000)
  ck(f'{w}px - HTTP 200',response.status==200)
  ck(f'{w}px - five guides',page.locator('.tool-card').count()==5)
  ck(f'{w}px - no horizontal scroll',page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
  ck(f'{w}px - no JS error',not errs)
  ck(f'{w}px - authorship section',page.get_by_text('Una iniciativa impulsada por').count()>=1)
  ck(f'{w}px - links',page.locator('a[href^="mailto:pedro18@gmail.com"]').count()>=2 and page.locator('a[href^="https://pedro-navarrete-portfolio.vercel.app"]').count()>=2)
  if w==2560:page.screenshot(path='qa/screenshots/v22-qhd.png',full_page=True)
  if w==390:
   page.screenshot(path='qa/screenshots/v22-movil.png',full_page=True)
   page.locator('#nav-toggle').click()
   ck('Mobile menu shows Sala de Decisiones',page.locator('#mobile-navigation a[href="#sala-de-decisiones"]').is_visible())
  ctx.close()
 ctx=browser.new_context(viewport={'width':1440,'height':900});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));response=page.goto(URL,wait_until='load',timeout=60000)
 for ch,txt in [('onboarding','Funnel por etapa'),('riesgo','Severidad y obligatoriedad'),('producto','Evidencia de demanda')]:
  page.locator('input[name=decision-choice][value='+ch+']').check()
  ck('Room resets when choice changes '+ch,page.locator('#decision-feedback').is_hidden())
  page.locator('#evaluate-decision').click()
  ck('Room analyzes '+ch,page.locator('#decision-feedback').is_visible() and txt in page.locator('#feedback-evidence').inner_text())
 page.locator('#reset-decision').click();ck('Room resets',page.locator('#decision-feedback').is_hidden());ck('Room JS clean',not errors)
 page.locator('.tool-card .card-open').first.click();ck('Existing guide opens',page.locator('#guide-dialog').evaluate('(e)=>e.open'));page.locator('#close-guide').click()
 ck('Scenario label hypothetical',page.get_by_text('ESCENARIO HIPOTÉTICO').count()>0)
 browser.close()
out={'total':len(results),'passed':sum(1 for _,ok in results if ok),'tests':[{'test':a,'passed':b} for a,b in results]}
Path('qa/qa-v22-production.json').write_text(json.dumps(out,indent=2,ensure_ascii=False))
print('RESULT',out['passed'],'/',out['total'])
assert out['passed']==out['total']