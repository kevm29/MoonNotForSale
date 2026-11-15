const {chromium}=require('playwright');
(async()=>{
const dir=process.argv[2];const b=await chromium.launch();
for(const w of [1400,390]){
const p=await b.newPage({viewport:{width:w,height:900}});
await p.route('**/cytoscape.min.js',r=>r.fulfill({path:dir+'/vendor_cytoscape.min.js',contentType:'application/javascript'}));
const errs=[];p.on('pageerror',e=>errs.push('PE '+e.message));p.on('console',m=>{if(m.type()==='error')errs.push('C '+m.text())});
await p.goto('file://'+dir+'/out/arbre-de-decision.html');await p.waitForTimeout(2500);
await p.screenshot({path:dir+`/../t_${w}.png`});
const info=await p.evaluate(()=>({cy:typeof cytoscape, canv:document.querySelectorAll("canvas").length, sw:document.documentElement.scrollWidth, tabs:[...document.querySelectorAll('button')].map(b=>b.textContent.trim()).slice(0,40)}));
console.log(w,JSON.stringify(info),errs);
if(w===1400){
  const tabs=await p.$$('[role=tab], .tab');
  for(let i=0;i<tabs.length;i++){await tabs[i].click();await p.waitForTimeout(300);await p.screenshot({path:dir+`/../t_tab${i}.png`});}
}
await p.close();}
await b.close();})();
