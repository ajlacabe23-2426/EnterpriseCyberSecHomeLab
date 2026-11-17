import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp,readFile,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function eventually(fn,label){const until=Date.now()+15000;let last;while(Date.now()<until){try{if(await fn())return;}catch(e){last=e;}await pause(100);}throw new Error('Timed out: '+label+(last?' / '+last.message:''));}
async function connect(port){
  let target;await eventually(async()=>{target=(await(await fetch('http://127.0.0.1:'+port+'/json/list')).json()).find(t=>t.type==='page');return !!target?.webSocketDebuggerUrl;},'Chrome target');
  const ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
  let seq=0;const pending=new Map(),errors=[],requests=[];
  ws.addEventListener('message',event=>{const item=JSON.parse(String(event.data));if(item.method==='Runtime.exceptionThrown')errors.push(item.params.exceptionDetails.text);if(item.method==='Network.requestWillBeSent')requests.push({url:item.params.request.url,method:item.params.request.method});if(!item.id)return;const handler=pending.get(item.id);if(!handler)return;pending.delete(item.id);if(item.error)handler.reject(new Error(JSON.stringify(item.error)));else handler.resolve(item.result);});
  const command=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
  const js=async expression=>{const result=await command('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(result.exceptionDetails)throw new Error(result.exceptionDetails.text);return result.result.value;};
  await command('Runtime.enable');await command('Network.enable');
  return {command,js,errors,requests,close:()=>ws.close()};
}
test('actual Chromium explores evidence, topology and simulation without host requests or mutations',
 {skip:process.env.RUN_BROWSER_ACCEPTANCE!=='1',timeout:90000},async()=>{
  const dir=await mkdtemp(join(tmpdir(),'homelab-map-browser-')),port=45500+Math.floor(Math.random()*1000),base='http://127.0.0.1:'+port;
  const before=await readFile(join(root,'labmap/public/data.json'));
  let server,chrome,cdp;try{
    server=spawn(process.env.PYTHON_BIN||'python3',['-B','-m','labmap','--port',String(port)],{cwd:root,stdio:['ignore','pipe','pipe']});
    let output='';server.stdout.on('data',d=>output+=d);server.stderr.on('data',d=>output+=d);server.once('error',e=>output+=e.message);
    await eventually(async()=>server.exitCode===null&&(await fetch(base)).ok,'read-only local server: '+output);
    chrome=spawn(process.env.CHROME_BIN||'google-chrome',['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--no-first-run','--no-default-browser-check','--user-data-dir='+join(dir,'chrome'),'--remote-debugging-port=0','about:blank'],{stdio:'ignore'});
    let chromePort;await eventually(async()=>{try{chromePort=Number((await readFile(join(dir,'chrome/DevToolsActivePort'),'utf8')).split('\n')[0]);return chromePort>0;}catch{return false;}},'Chrome port');
    cdp=await connect(chromePort);const {js,command}=cdp;
    await command('Emulation.setDeviceMetricsOverride',{width:1500,height:1100,deviceScaleFactor:1,mobile:false});
    await command('Page.navigate',{url:base});
    await eventually(()=>js("document.querySelector('#load-status')?.textContent.includes('Snapshot loaded')"),'snapshot render');
    assert.equal(await js("document.querySelectorAll('#map [data-node]').length"),8);
    assert.equal(await js("document.querySelector('#snapshot-label').textContent.includes('2026-10-11')"),true);
    await js("document.querySelector('#node-list [data-node=sec]').click()");
    assert.equal(await js("document.querySelector('#detail-status').textContent"),'REVIEW');
    assert.equal(await js("document.querySelector('#claims').textContent.includes('Anywhere')"),true);
    await js("document.querySelector('#node-list [data-node=dc]').click()");
    assert.equal(await js("document.querySelector('#detail-status').textContent"),'BLOCKED');
    const initial=await js("document.querySelector('#map [data-node=kali]').getAttribute('transform')");
    await js("document.querySelector('#rotate-right').click()");
    assert.notEqual(await js("document.querySelector('#map [data-node=kali]').getAttribute('transform')"),initial);
    await js("document.querySelector('#map').scrollIntoView({block:'center',behavior:'instant'})");
    const hit=await js("(() => {const r=document.querySelector('#map [data-node=ubuntu] rect').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()");
    for(const type of ['mousePressed','mouseReleased'])await command('Input.dispatchMouseEvent',{type,x:hit.x,y:hit.y,button:'left',clickCount:1});
    assert.equal(await js("document.querySelector('#detail-title').textContent"),'UBUNTU01');
    const beforeDrag=await js("document.querySelector('#map [data-node=kali]').getAttribute('transform')");
    await command('Input.dispatchMouseEvent',{type:'mousePressed',x:hit.x,y:hit.y,button:'left',clickCount:1});
    await command('Input.dispatchMouseEvent',{type:'mouseMoved',x:hit.x+60,y:hit.y+10,button:'left',buttons:1});
    await command('Input.dispatchMouseEvent',{type:'mouseReleased',x:hit.x+60,y:hit.y+10,button:'left',clickCount:1});
    assert.notEqual(await js("document.querySelector('#map [data-node=kali]').getAttribute('transform')"),beforeDrag);
    await js("document.querySelector('#flat').click();document.querySelector('#map [data-node=win] rect').dispatchEvent(new MouseEvent('click',{bubbles:true}))");
    assert.equal(await js("document.querySelector('#detail-title').textContent"),'Win11-Client01');
    await js("document.querySelector('#flat').click();document.querySelector('#map').focus()");
    const beforeKey=await js("document.querySelector('#map [data-node=kali]').getAttribute('transform')");
    await command('Input.dispatchKeyEvent',{type:'keyDown',key:'ArrowLeft',code:'ArrowLeft',windowsVirtualKeyCode:37});
    await command('Input.dispatchKeyEvent',{type:'keyUp',key:'ArrowLeft',code:'ArrowLeft',windowsVirtualKeyCode:37});
    assert.notEqual(await js("document.querySelector('#map [data-node=kali]').getAttribute('transform')"),beforeKey);
    await js("document.querySelector('#trace').click()");
    assert.equal(await js("document.querySelector('#view-title').textContent"),'Telemetry & evidence path');
    assert.equal(await js("document.querySelector('#detail-title').textContent"),'Centralized logs');
    assert.equal(await js("document.querySelector('#claims').textContent.includes('2026-10-11')"),true);
    assert.equal(await js("document.querySelector('#map [data-edge=ubuntu-sec]').getAttribute('stroke-width')"),'3');
    await js("document.querySelector('[data-view=tools]').click();document.querySelector('#node-list [data-node=soc]').click()");
    assert.equal(await js("document.querySelector('#detail-status').textContent"),'OPEN PR');
    assert.equal(await js("document.querySelector('#claims a').href.includes('4b5a9e894504814ec661bcfe6a99dd64d1e65130')"),true);
    assert.equal(await js("document.querySelector('#map [data-node=soc]').textContent.includes('detect.py')"),true);
    assert.equal(await js("document.querySelector('#port-state').textContent"),'FILTERED');
    await js("document.querySelector('#listener').click()");assert.equal(await js("document.querySelector('#port-state').textContent"),'FILTERED');
    await js("document.querySelector('#allow-inbound').click()");assert.equal(await js("document.querySelector('#port-state').textContent"),'OPEN');
    await js("document.querySelector('#listener').click()");assert.equal(await js("document.querySelector('#port-state').textContent"),'CLOSED');
    await js("document.querySelector('#sim-reset').click()");assert.equal(await js("document.querySelector('#port-state').textContent"),'FILTERED');
    await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
    assert.equal(await js("document.documentElement.scrollWidth<=document.documentElement.clientWidth"),true,'mobile overflow contained');
    assert.equal(await js("document.querySelector('#node-list [data-node=ir]').getBoundingClientRect().width>0"),true);
    assert.deepEqual(await readFile(join(root,'labmap/public/data.json')),before,'exploration never persists');
    assert.deepEqual(cdp.errors,[],'no renderer exceptions');
    assert.ok(cdp.requests.every(r=>r.url.startsWith(base+'/')&&r.method==='GET'),'no VM, external or mutation request');
    assert.ok(cdp.requests.some(r=>r.url===base+'/data.json'));
    if(process.env.HOMELAB_MAP_SCREENSHOT){
      await command('Emulation.setDeviceMetricsOverride',{width:1500,height:1100,deviceScaleFactor:1,mobile:false});
      await js("document.querySelector('[data-view=topology]').click();document.querySelector('#node-list [data-node=sec]').click();window.scrollTo(0,0)");
      const shot=await command('Page.captureScreenshot',{format:'png'});await writeFile(process.env.HOMELAB_MAP_SCREENSHOT,Buffer.from(shot.data,'base64'));
    }
  }finally{cdp?.close();chrome?.kill('SIGTERM');server?.kill('SIGTERM');await rm(dir,{recursive:true,force:true,maxRetries:3,retryDelay:200});}
 });
