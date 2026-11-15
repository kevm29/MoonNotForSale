const {chromium}=require('playwright');
(async()=>{
const dir=process.argv[2];const b=await chromium.launch();
const p=await b.newPage({viewport:{width:1100,height:860},reducedMotion:"reduce"});
const errs=[];p.on('pageerror',e=>errs.push('PE '+e.message));p.on('console',m=>{if(m.type()==='error')errs.push('C '+m.text())});
const ends={};let bad=[];
for(let run=0;run<8;run++){
  await p.goto('file://'+dir+'/out/la-lune-vendue.html');await p.evaluate(()=>localStorage.clear());await p.reload();await p.waitForTimeout(150);
  const pcs=await p.$$('.pc'); await pcs[run%pcs.length].click(); await p.waitForTimeout(100);
  let steps=0;
  for(;steps<250;steps++){
    if(await p.$('#again'))break;
    const txt=await p.$eval('#scene',e=>e.innerText);
    if(/(^|\n)\s*\?[!a-z]/.test(txt)||/undefined|NaN/.test(txt)) bad.push(txt.slice(0,200));
    const cs=await p.$$('.choice'); if(!cs.length){bad.push('BLOCKED '+txt.slice(0,100));break;}
    await cs[Math.floor(Math.random()*cs.length)].click();
    await p.waitForSelector('#next:not([hidden])',{timeout:5000});
    await p.click('#next');
  }
  const st=await p.evaluate(()=>({end:N[S.node].end,prev:S.prev,last:S.last,xp:S.xp,vars:S.vars}));
  ends[st.end]=(ends[st.end]||0)+1;
  if(run<2) console.log(JSON.stringify(st));
}
console.log('ends',JSON.stringify(ends),'bad',bad.length,bad.slice(0,3),'errs',errs);
await b.close();})();
