export const STATUSES=new Set(['OBSERVED','CONFIG_OBSERVED','REVIEW','NOT_RUN','BLOCKED','HISTORICAL','OPEN_PR']);
export function validateModel(model){
  if(model?.schema!=='homelab-evidence-map-v1'||!/^\d{4}-\d{2}-\d{2}$/.test(model.snapshotDate)||!Array.isArray(model.nodes)||model.nodes.length>40)throw new Error('Unsupported curated snapshot');
  const ids=new Set();
  for(const node of model.nodes){
    if(typeof node.id!=='string'||ids.has(node.id)||!STATUSES.has(node.status)||!Array.isArray(node.claims)||!node.claims.length)throw new Error('Invalid node evidence');
    ids.add(node.id);
    for(const claim of node.claims){
      if(!STATUSES.has(claim.status)||!model.sources?.[claim.source]||!/^\d{4}-\d{2}-\d{2}$/.test(claim.date)||claim.date>model.snapshotDate)throw new Error('Missing or future-dated claim provenance');
    }
  }
  for(const source of Object.values(model.sources)){
    if(source.url?.startsWith('/sources/')&&!/^[0-9a-f]{64}$/.test(source.sha256))throw new Error('Missing source fingerprint');
    if(!/^[0-9a-f]{40}$/.test(source.revision)||typeof source.path!=='string'||!(source.url.startsWith('/sources/')||source.url.startsWith('https://github.com/ajlacabe23-2426/EnterpriseCyberSecHomeLab/blob/'+source.revision+'/')))throw new Error('Invalid source reference');
  }
  for(const view of Object.values(model.views)){
    const placed=new Set();
    for(const node of view.nodes){
      if(!ids.has(node.id)||placed.has(node.id)||!Array.isArray(node.position)||node.position.length!==3||!node.position.every(Number.isFinite))throw new Error('Invalid view placement');
      placed.add(node.id);
    }
    for(const edge of view.edges){
      if(!placed.has(edge.fromNode)||!placed.has(edge.toNode)||!STATUSES.has(edge.status))throw new Error('Invalid evidence connection');
    }
  }
  return model;
}
export function project([x,y,z],{yaw=.16,pitch=-.1,flat=false}={}){
  x*=.82;y*=.82;z*=.82;
  if(flat)return {x:500+x,y:260+y,depth:0};
  const rx=x*Math.cos(yaw)+z*Math.sin(yaw),rz=-x*Math.sin(yaw)+z*Math.cos(yaw);
  const ry=y*Math.cos(pitch)-rz*Math.sin(pitch),depth=y*Math.sin(pitch)+rz*Math.cos(pitch),scale=1200/(1200+depth);
  return {x:500+rx*scale,y:260+ry*scale,depth};
}
export function simulatePort({allowInbound=false,listener=false}={}){
  if(typeof allowInbound!=='boolean'||typeof listener!=='boolean')throw new Error('Simulation expects boolean controls');
  return {status:'SIMULATED',portState:allowInbound?(listener?'OPEN':'CLOSED'):'FILTERED',
    explanation:!allowInbound?'Synthetic firewall drops the probe, even if a service is listening.':listener?'Synthetic firewall allows the probe and a service is listening.':'Synthetic firewall allows the probe, but no service is listening.',
    liveHostAccess:false};
}
