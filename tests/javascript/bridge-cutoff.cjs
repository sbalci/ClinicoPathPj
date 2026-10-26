// Run with NODE_PATH pointing to a separately provisioned jsdom installation.
const assert=require('node:assert/strict'),fs=require('node:fs');
const {JSDOM}=require('jsdom');
const calls=[],errors=[];
const dom=new JSDOM(fs.readFileSync(process.argv[2],'utf8'),{runScripts:'dangerously',pretendToBeVisual:true,beforeParse(w){
 w.setOption=(...args)=>calls.push(args);
 w.addEventListener('error',e=>errors.push(e.message));
}});
const w=dom.window,d=w.document;
assert.deepEqual(errors,[]);
assert.equal(calls.length,0,'render must not rerun backend');
assert.equal(d.querySelector('.direction').disabled,true);
assert.equal(d.querySelector('.criterion').disabled,true);
const input=d.querySelector('.cutoff');input.value='3';input.dispatchEvent(new w.Event('input',{bubbles:true}));
assert.equal(calls.length,0,'preview must stay local');
d.querySelector('.apply').click();assert.deepEqual(calls,[['cutoff','3']]);
d.querySelector('.reset').click();assert.equal(calls.length,1,'restore must stay local');
assert.equal(input.value,'2');
d.querySelector('.apply').click();assert.equal(calls.length,1,'unchanged manual rule need not rerun');
console.log('Bridge preview, explicit native Apply, restore and render isolation PASSED');w.close();
