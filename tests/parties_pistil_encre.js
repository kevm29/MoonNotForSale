// Parties au hasard avec Pistil, route de la Nuit d'encre (on prend l'entrée dès qu'elle est proposée)
const {chromium}=require('playwright');
(async()=>{
const dir=process.argv[2], runs=+(process.argv[3]||25);const b=await chromium.launch();
const p=await b.newPage({viewport:{width:1100,height:860},reducedMotion:"reduce"});
const errs=[];p.on('pageerror',e=>errs.push('PE '+e.message));p.on('console',m=>{if(m.type()==='error')errs.push('C '+m.text())});
const ends={};let bad=[];let ink=0;
for(let run=0;run<runs;run++){
  await p.goto('file://'+dir+'/out/la-lune-vendue.html');await p.evaluate(()=>{localStorage.clear();localStorage.setItem('lune.parties','1');});await p.reload();await p.waitForTimeout(100);
  await p.click('#tabCommencer'); await p.click('.pc[data-pc="pistil"]'); await p.click('#sheetGo'); await p.waitForTimeout(80);
  for(let steps=0;steps<250;steps++){
    if(await p.$('#again'))break;
    const txt=await p.$eval('#scene',e=>e.innerText);
    if(/(^|\n)\s*\?[!a-z]/.test(txt)||/\?(comp|flag|pc|last):/.test(txt)||/undefined|NaN/.test(txt)) bad.push(txt.slice(0,200));
    const cs=await p.$$('.choice'); if(!cs.length){bad.push('BLOCKED '+txt.slice(0,100));break;}
    let pick=null;for(const c of cs){const t=await c.innerText();if(/Ne pas partir\. Rester|Te retenir au bord du rêve/.test(t))pick=c;}
    if(await p.$('.gauge.ink'))ink++;
    await (pick||cs[Math.floor(Math.random()*cs.length)]).click();
    await p.waitForSelector('#next:not([hidden])',{timeout:5000});
    await p.click('#next');
  }
  const e=await p.evaluate(()=>N[S.node].end); ends[e]=(ends[e]||0)+1;
}
console.log('ink',ink,'ends',JSON.stringify(ends),'bad',bad.length,bad.slice(0,3),'errs',errs);
await b.close();})();
