const {chromium}=require('playwright');
(async()=>{
const dir=process.argv[2];const b=await chromium.launch();
for(const [ci,w] of [[0,1200],[3,390]]){
const p=await b.newPage({viewport:{width:w,height:860},reducedMotion:"reduce"});
const errs=[];p.on('pageerror',e=>errs.push('PE '+e.message));p.on('console',m=>{if(m.type()==='error')errs.push('C '+m.text())});
await p.goto('file://'+dir+'/out/la-lune-vendue.html');await p.waitForTimeout(300);
const bs=await p.$$('.pc');await bs[ci].click();
await p.waitForTimeout(300);
await p.screenshot({path:dir+`/../g_scene_${w}.png`});
let steps=0,ended=false;
for(;steps<300;steps++){
  if(await p.$('#again')){ended=true;break;}
  const cs=await p.$$('.choice'); if(!cs.length){console.log('no choice at step',steps);break;}
  await cs[Math.floor(Math.random()*cs.length)].click();
  await p.waitForSelector('#next:not([hidden])',{timeout:5000});
  if(steps==2) await p.screenshot({path:dir+`/../g_roll_${w}.png`});
  await p.click('#next');
}
const sw=await p.evaluate(()=>document.documentElement.scrollWidth);
await p.screenshot({path:dir+`/../g_end_${w}.png`});
console.log(w,'steps',steps,'ended',ended,'scrollW',sw,errs);
await p.close();}
await b.close();})();
