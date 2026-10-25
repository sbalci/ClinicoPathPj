// Unit harness for the view's event logic, not a browser or jamovi integration test.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
class Element {
  constructor() { this.handlers={}; this.attributes={}; this.children=[]; this.value=''; }
  setAttribute(k,v) { this.attributes[k]=v; }
  appendChild(e) { this.children.push(e); }
  addEventListener(k,fn) { this.handlers[k]=fn; }
}
const selectors = Object.fromEntries(['svg','.cut','.status','.metrics','.reset','.apply'].map(k=>[k,new Element()]));
const svg=selectors.svg;
svg.createSVGPoint=()=>({matrixTransform(){return {y:this.y}}});
svg.getScreenCTM=()=>({inverse(){return {}}});
svg.setPointerCapture=()=>{};
const root={querySelector:k=>selectors[k]};
const applied=[];
const payload={values:[1,2,2,4,5,6],truth:[0,0,1,0,1,1],rows:[1,2,3,4,5,6],
  marker:'Ki-67',positive:'P',negative:'N',cutoff:2,automatic:5,direction:'high',log:false};
const source=fs.readFileSync(path.join(__dirname,'../../inst/python/templates/dotdecision.html'),'utf8')
  .split('<script>')[1].split('</script>')[0].replace('__PAYLOAD__',JSON.stringify(payload));
vm.runInNewContext(source, {document:{getElementById:()=>root,createElementNS:()=>new Element()},
  window:{setOption:(...args)=>applied.push(args)},console});
assert.match(selectors['.metrics'].textContent,/TP 3 \| FP 2 \| FN 0 \| TN 1/);
selectors['.cut'].value='5.00'; selectors['.cut'].handlers.input();
assert.equal(selectors['.cut'].value,'5.00'); // preserve decimal editing
assert.match(selectors['.metrics'].textContent,/TP 2 \| FP 0 \| FN 1 \| TN 3/);
selectors['.apply'].handlers.click(); assert.deepEqual(applied,[['cutoff','5']]);
svg.handlers.pointerdown({clientX:400,clientY:200,pointerId:1});
svg.handlers.pointermove({clientX:400,clientY:100,pointerId:1});
svg.handlers.pointerup(); assert.notEqual(selectors['.cut'].value,'5');
selectors['.reset'].handlers.click();assert.equal(selectors['.cut'].value,'5');
console.log('Dotplot event logic: preview counts, decimal editing, Apply binding, drag, reset passed.');
