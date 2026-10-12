import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {validateModel,project,simulatePort} from './labmap/public/core.mjs';
const fixture=JSON.parse(await readFile(new URL('./labmap/public/data.json',import.meta.url),'utf8'));
test('every diagram node and connection resolves to a dated, revision-bound source',()=>{
  assert.equal(validateModel(fixture),fixture);
  assert.ok(fixture.views.tools.edges.every(e=>e.status==='NOT_RUN'));
  assert.deepEqual(fixture.trace,['ubuntu-sec','sec-logs']);
});
test('missing provenance and accidental future evidence cannot be silently shown as verified',()=>{
  const fingerprint=structuredClone(fixture);delete fingerprint.sources.current.sha256;assert.throws(()=>validateModel(fingerprint));
  const unknown=structuredClone(fixture);unknown.nodes[0].claims[0].source='absent';assert.throws(()=>validateModel(unknown));
  const future=structuredClone(fixture);future.nodes[0].claims[0].date='2027-01-01';assert.throws(()=>validateModel(future));
  const status=structuredClone(fixture);status.nodes[0].status='SECURE';assert.throws(()=>validateModel(status));
  const duplicate=structuredClone(fixture);duplicate.nodes.push(duplicate.nodes[0]);assert.throws(()=>validateModel(duplicate));
  const url=structuredClone(fixture);url.sources.current.url='javascript:alert(1)';assert.throws(()=>validateModel(url));
});
test('simulation separates a dropped probe, an absent listener and a listening service',()=>{
  for(const [allowInbound,listener,expected]of [[false,false,'FILTERED'],[false,true,'FILTERED'],[true,false,'CLOSED'],[true,true,'OPEN']]){
    const result=simulatePort({allowInbound,listener});assert.equal(result.portState,expected);assert.equal(result.status,'SIMULATED');assert.equal(result.liveHostAccess,false);
  }
  assert.throws(()=>simulatePort({allowInbound:'true'}));
});
test('rotatable and flat views keep component centers inside the diagram',()=>{
  for(const view of Object.values(fixture.views))for(const placement of view.nodes){
    assert.equal(project(placement.position,{flat:true}).depth,0);
    for(const yaw of [-.6,0,.6])for(const pitch of [-.3,0,.3]){
      const point=project(placement.position,{yaw,pitch});assert.ok(Number.isFinite(point.depth));assert.ok(point.x>0&&point.x<1000&&point.y>0&&point.y<560);
    }
  }
});
