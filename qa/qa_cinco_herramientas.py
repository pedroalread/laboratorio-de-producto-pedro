from pathlib import Path
from playwright.sync_api import sync_playwright
import os, json
URL=os.environ.get('PORTAL_URL','https://pedroalread.github.io/laboratorio-de-producto-pedro/')
results=[]
def ck(label,ok):
 ok=bool(ok);print(('PASS ' if ok else 'FAIL ')+label,flush=True);results.append({'name':label,'passed':ok})
with sync_playwright() as pw:
 options={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
 if os.environ.get('QA_LOCAL_HTML'): options['executable_path']='/usr/bin/chromium'
 browser=pw.chromium.launch(**options)
 ctx=browser.new_context(viewport={'width':1440,'height':1000})
 page=ctx.new_page()
 if os.environ.get('QA_LOCAL_HTML'):
  page.set_content(Path(os.environ['QA_LOCAL_HTML']).read_text(encoding='utf-8'),wait_until='load')
 else:
  page.goto(URL,wait_until='load',timeout=60000)
 def open_tool(n):
  page.locator('.tool-card .card-open').nth(n).click()
  assert page.locator('#guide-dialog').evaluate('(e)=>e.open')
 def close_tool(): page.locator('#close-guide').click()
 open_tool(0)
 inp=page.locator('#tool-content .tool-row input').first
 inp.fill('40')
 ck('PRESUPUESTO: input actualiza los puntos',page.evaluate('toolState[0].points')==40)
 ck('PRESUPUESTO: total recalculado 105', '105 / 100' in page.locator('#budget-status').inner_text())
 page.locator('#reset-tool').click()
 ck('PRESUPUESTO: restaurar recupera 100 puntos', '100 / 100' in page.locator('#budget-status').inner_text() and page.evaluate('toolState[0].points')==35)
 close_tool()
 open_tool(1)
 choice=page.locator('#tool-content select').first
 choice.select_option('2')
 ck('MATRIZ: selector actualiza impacto',page.evaluate('toolState[0].impact')==2)
 ck('MATRIZ: cuadrante cambia', 'Corregir acceso' in page.locator('[data-quadrant="fill"]').inner_text())
 choice.select_option('5')
 ck('MATRIZ: cuadrante se recalcula', 'Corregir acceso' in page.locator('[data-quadrant="win"]').inner_text())
 close_tool()
 open_tool(2)
 page.locator('#tool-content input').first.fill('Aumentar activaciones digitales un 20 %')
 ck('ARBOL: editar resultado actualiza modelo',page.evaluate("toolState.outcome")=='Aumentar activaciones digitales un 20 %')
 ck('ARBOL: representa resultado visual', 'Aumentar activaciones digitales un 20 %' in page.locator('#tree-preview').inner_text())
 close_tool()
 open_tool(3)
 page.locator('#tool-content textarea').first.fill('Aumentar ventas digitales un 10 %')
 ck('IMPACT MAP: editar objetivo actualiza modelo',page.evaluate('toolState.objective')=='Aumentar ventas digitales un 10 %')
 ck('IMPACT MAP: representa cadena causal', 'Aumentar ventas digitales un 10 %' in page.locator('#impact-preview').inner_text())
 close_tool()
 open_tool(4)
 selector=page.locator('#tool-content table select').first
 selector.select_option('–')
 ck('RACI: valida ausencia de accountable', 'por revisar' in page.locator('#raci-status').inner_text())
 selector.select_option('A')
 ck('RACI: restaurar accountable corrige advertencia','responsable A único' in page.locator('#raci-status').inner_text())
 close_tool()
 page.locator('#search').fill('RACI')
 ck('BUSCADOR: filtra por RACI',page.locator('.tool-card').count()==1)
 page.locator('#search').fill('')
 ck('BUSCADOR: limpiar restaura cinco',page.locator('.tool-card').count()==5)
 page.locator('[data-filter="discovery"]').click()
 ck('FILTROS: Discovery muestra dos',page.locator('.tool-card').count()==2)
 ctx.close();browser.close()
passed=sum(x['passed'] for x in results)
print(f'RESULT: {passed}/{len(results)} passing',flush=True)
Path('qa/resultado-cinco-herramientas.json').parent.mkdir(parents=True,exist_ok=True)
Path('qa/resultado-cinco-herramientas.json').write_text(json.dumps({'url':URL,'total':len(results),'passed':passed,'tests':results},indent=2,ensure_ascii=False),encoding='utf-8')
assert passed==len(results)