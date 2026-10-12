import {validateModel,project,simulatePort} from './core.mjs';
const $=id=>document.getElementById(id),ns='http://www.w3.org/2000/svg';
const colors={OBSERVED:'#b5dcaa',CONFIG_OBSERVED:'#9bc8de',REVIEW:'#e4c88b',NOT_RUN:'#95a6b0',BLOCKED:'#d9a0a0',HISTORICAL:'#bbb1dc',OPEN_PR:'#98ceca'};
const descriptions={
  OBSERVED:'A named user-observed result at its recorded date; not a whole-system health PASS.',
  CONFIG_OBSERVED:'An adapter or rule was configured as shown. Actual traffic behavior remains a separate check.',
  REVIEW:'A specific configuration or evidence concern needs review; no automatic remediation.',
  NOT_RUN:'No current behavioral verification is recorded for this gate.',
  BLOCKED:'The role or prerequisite is absent. Historical results do not close this gap.',
  HISTORICAL:'Dated checkpoint retained as history; not current machine status.',
  OPEN_PR:'Source exists in an independent open candidate. Installation/integration is not implied.'
};
let model=null,viewId='topology',selected='lab',yaw=.16,pitch=-.1,flat=false,trace=false,drag=null,suppressClick=false;
const svg=$('map');
const element=(tag,cls,text)=>{const el=document.createElement(tag);if(cls)el.className=cls;if(text!==undefined)el.textContent=text;return el;};
const add=(parent,tag,attrs={},text)=>{const el=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))el.setAttribute(k,String(v));if(text!==undefined)el.textContent=text;parent.append(el);return el;};
const label=status=>status.replaceAll('_',' ');
function detail(){
  const node=model?.nodes.find(n=>n.id===selected);if(!node)return;
  $('detail-title').textContent=node.title;$('detail-status').textContent=label(node.status);$('detail-role').textContent=node.role;$('next-check').textContent=node.nextCheck;
  $('skills').replaceChildren(...node.skills.map(s=>element('span','',s)));$('claims').replaceChildren();
  for(const claim of node.claims){
    const card=element('div','claim'),head=element('div','claim-head'),source=model.sources[claim.source];
    head.append(element('strong','',claim.title),element('span','badge',label(claim.status)));
    const link=element('a','',source.label+' ↗');link.href=source.url;link.target='_blank';link.rel='noopener noreferrer';
    card.append(head,element('p','',claim.detail),link,element('small','',claim.date+' · '+source.path),element('small','',source.kind+' · revision '+source.revision));
    if(source.prUrl){const pr=element('a','',`Open PR #${source.pr} · separate candidate`);pr.href=source.prUrl;pr.target='_blank';pr.rel='noopener noreferrer';card.append(pr);}
    $('claims').append(card);
  }
  for(const button of $('node-list').querySelectorAll('button'))button.setAttribute('aria-pressed',String(button.dataset.node===selected));
  for(const group of svg.querySelectorAll('[data-node]')){
    group.setAttribute('opacity',group.dataset.node===selected?'1':'.82');
    group.querySelector('rect').setAttribute('stroke-width',group.dataset.node===selected?'2.8':'1.3');
  }
}
function select(id){selected=id;detail();}
function draw(){
  if(!model)return;svg.replaceChildren();const view=model.views[viewId];
  const defs=add(svg,'defs');
  for(const [state,color]of Object.entries(colors)){
    const marker=add(defs,'marker',{id:'arrow-'+state,viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:5,markerHeight:5,orient:'auto-start-reverse'});
    add(marker,'path',{d:'M 0 0 L 10 5 L 0 10 z',fill:color});
  }
  const points=new Map(view.nodes.map(n=>[n.id,project(n.position,{yaw,pitch,flat})]));
  for(const edge of view.edges){
    const a=points.get(edge.fromNode),b=points.get(edge.toNode),dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy),offset=Math.min(83,d*.35),active=trace&&model.trace.includes(edge.id),color=active?colors.OBSERVED:colors[edge.status];
    const line=add(svg,'line',{'data-edge':edge.id,x1:a.x+dx/d*offset,y1:a.y+dy/d*offset,x2:b.x-dx/d*offset,y2:b.y-dy/d*offset,stroke:color,'stroke-width':active?3:1.3,'stroke-dasharray':['OBSERVED','CONFIG_OBSERVED'].includes(edge.status)?'none':'5 6',opacity:trace&&!active?.25:.65,'marker-end':'url(#arrow-'+(active?'OBSERVED':edge.status)+')'});
    add(line,'title',{},edge.label+' · '+label(edge.status));
  }
  for(const placement of [...view.nodes].sort((a,b)=>points.get(b.id).depth-points.get(a.id).depth)){
    const node=model.nodes.find(n=>n.id===placement.id),p=points.get(node.id),g=add(svg,'g',{'data-node':node.id,transform:'translate('+p.x+' '+p.y+')',class:'node'});
    add(g,'title',{},node.title+' · '+label(node.status));
    add(g,'rect',{x:-78,y:-29,width:156,height:58,rx:9,fill:'#142d35',stroke:colors[node.status]});
    add(g,'text',{x:0,y:-5,'text-anchor':'middle',fill:'#edf1e8','font-size':13},node.title);
    const subtitle=viewId==='tools'&&node.kind==='tool'?model.sources[node.claims[0].source].path.split('/').at(-1):label(node.status);
    add(g,'text',{x:0,y:14,'text-anchor':'middle',fill:colors[node.status],'font-size':9},subtitle);
  }
  detail();
}
function showView(id){
  viewId=id;const view=model.views[id];if(!view.nodes.some(n=>n.id===selected))selected=view.nodes[0].id;
  $('view-title').textContent=view.title;$('view-subtitle').textContent=view.subtitle;
  for(const button of document.querySelectorAll('[data-view]'))button.setAttribute('aria-pressed',String(button.dataset.view===id));
  $('node-list').replaceChildren();$('connections').replaceChildren();
  for(const placement of view.nodes){const node=model.nodes.find(n=>n.id===placement.id),button=element('button','',node.title);button.dataset.node=node.id;button.addEventListener('click',()=>select(node.id));$('node-list').append(button);}
  for(const edge of view.edges){const row=element('div','connection');row.append(element('b','',edge.fromNode+' → '+edge.toNode+' '),element('span','',edge.label+' · '+label(edge.status)));$('connections').append(row);}
  draw();
}
svg.addEventListener('click',event=>{if(suppressClick){suppressClick=false;return;}const id=event.target.closest('[data-node]')?.dataset.node;if(id)select(id);});
svg.addEventListener('pointerdown',event=>{if(flat||event.button!==0)return;suppressClick=false;drag={x:event.clientX,y:event.clientY,yaw,pitch,moved:false,node:event.target.closest('[data-node]')?.dataset.node};svg.setPointerCapture(event.pointerId);});
svg.addEventListener('pointermove',event=>{if(!drag||!svg.hasPointerCapture(event.pointerId))return;const dx=event.clientX-drag.x,dy=event.clientY-drag.y;if(Math.abs(dx)+Math.abs(dy)<5)return;drag.moved=true;yaw=Math.max(-.6,Math.min(.6,drag.yaw+dx*.003));pitch=Math.max(-.3,Math.min(.3,drag.pitch+dy*.003));draw();});
svg.addEventListener('pointerup',()=>{if(drag&&!drag.moved&&drag.node)select(drag.node);suppressClick=!!drag;drag=null;});
svg.addEventListener('pointercancel',()=>{drag=null;suppressClick=false;});
svg.addEventListener('keydown',event=>{if(flat)return;if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home'].includes(event.key)){event.preventDefault();if(event.key==='Home'){yaw=.16;pitch=-.1;}else if(event.key==='ArrowLeft')yaw=Math.max(-.6,yaw-.08);else if(event.key==='ArrowRight')yaw=Math.min(.6,yaw+.08);else pitch=Math.max(-.3,Math.min(.3,pitch+(event.key==='ArrowUp'?-.06:.06)));draw();}});
$('rotate-left').addEventListener('click',()=>{yaw=Math.max(-.6,yaw-.12);draw();});$('rotate-right').addEventListener('click',()=>{yaw=Math.min(.6,yaw+.12);draw();});
$('reset').addEventListener('click',()=>{yaw=.16;pitch=-.1;draw();});
$('flat').addEventListener('click',()=>{flat=!flat;drag=null;suppressClick=false;$('flat').setAttribute('aria-pressed',String(flat));$('flat').textContent=flat?'Switch to 3D':'Flat view';for(const id of ['rotate-left','rotate-right','reset'])$(id).disabled=flat;draw();});
for(const button of document.querySelectorAll('[data-view]'))button.addEventListener('click',()=>{trace=false;$('trace').setAttribute('aria-pressed','false');showView(button.dataset.view);});
$('trace').addEventListener('click',()=>{trace=!trace;$('trace').setAttribute('aria-pressed',String(trace));selected='logs';showView('telemetry');});
function simulation(){const result=simulatePort({allowInbound:$('allow-inbound').checked,listener:$('listener').checked});$('port-state').textContent=result.portState;$('port-explanation').textContent=result.explanation;}
for(const id of ['allow-inbound','listener'])$(id).addEventListener('change',simulation);
$('sim-reset').addEventListener('click',()=>{$('allow-inbound').checked=false;$('listener').checked=false;simulation();});simulation();
for(const [status,description]of Object.entries(descriptions)){const card=element('div','');card.append(element('span','badge',label(status)),element('p','',description));$('legend').append(card);}
fetch('/data.json').then(response=>{if(!response.ok)throw new Error('Curated snapshot unavailable');return response.json();}).then(data=>{
  model=validateModel(data);$('snapshot-label').textContent='Recorded through '+model.snapshotDate+' · curated evidence snapshot';showView('topology');$('load-status').textContent='Snapshot loaded · no VM access';
}).catch(error=>{$('load-status').textContent='Map unavailable: '+error.message;$('snapshot-label').textContent='Snapshot could not be verified';for(const button of document.querySelectorAll('.views button,.controls button'))button.disabled=true;});
