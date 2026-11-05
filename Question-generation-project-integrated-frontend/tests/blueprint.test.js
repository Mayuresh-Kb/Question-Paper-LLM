import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildPayload, initialDraft } from '../src/lib/blueprint.js';
const units=[{id:'unit-a',name:'Trees',questions:Array.from({length:8},()=>({enabled:true}))},{id:'unit-b',name:'Graphs',questions:Array.from({length:8},()=>({enabled:true}))}];
test('canonical payload supports unequal unit marks and authoritative total',()=>{
 const draft=initialDraft(units);draft.paper_format='custom';draft.plans['unit-a'].marks=15;draft.plans['unit-b'].marks=20;
 const result=buildPayload('upload',draft,units);
 assert.equal(result.total_marks,35);assert.equal(result.units[1].marks,20);
 assert.equal(result.header.max_marks,undefined);assert.equal(result.mode,'balanced');
});
test('only explicitly selected units are sent',()=>{
 const draft=initialDraft(units);draft.paper_format='custom';draft.plans['unit-a'].selected=false;
 assert.deepEqual(buildPayload('upload',draft,units).units.map(u=>u.unit_id),['unit-b']);
});
test('impossible marks are rejected before requesting generation',()=>{
 const draft=initialDraft(units);draft.paper_format='custom';draft.plans['unit-a'].marks=1;
 assert.throws(()=>buildPayload('upload',draft,units),/at least one mark/);
});
test('enough questions must exist for BOTH alternatives',()=>{
 const draft=initialDraft(units);draft.plans['unit-a'].count=5;
 assert.throws(()=>buildPayload('upload',draft,units),/needs 10/);
});
test('missing upload and fractional inputs are rejected',()=>{
 const draft=initialDraft(units);assert.throws(()=>buildPayload('',draft,units),/uploaded unit/);
 draft.paper_format='custom';
 draft.plans['unit-a'].marks='2.5';assert.throws(()=>buildPayload('upload',draft,units),/whole number/);
});
test('unit test is exactly two units and sixteen marks',()=>{
 const five=Array.from({length:5},(_,i)=>({id:`unit-${i}`,name:`Unit ${i+1}`,questions:Array.from({length:8},()=>({enabled:true}))}));
 const draft=initialDraft(five);const result=buildPayload('upload',draft,five);
 assert.equal(result.paper_format,'unit_test');assert.equal(result.total_marks,16);assert.equal(result.units.length,2);
 assert.deepEqual(result.units.map(unit=>unit.marks),[8,8]);
 draft.plans['unit-2'].selected=true;
 assert.throws(()=>buildPayload('upload',draft,five),/exactly two units/);
});
