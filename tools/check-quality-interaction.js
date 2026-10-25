// Small offline DOM harness: verifies display events without depending on a browser package.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(process.argv[2],'utf8');
class Element {
 constructor(tag){this.tag=tag;this.children=[];this.style={};this.events={};this.value='';this.checked=false;}
 appendChild(x){this.children.push(x);if(this.tag==='select'&&this.children.length===1)this.value=x.value;return x;}
 replaceChildren(){this.children=[];}
 setAttribute(k,v){this[k]=v;}
 addEventListener(name,fn){this.events[name]=fn;}
}
const elements={};
for(const [name,tag] of Object.entries({variable:'select',missingOnly:'input',previous:'button',next:'button',scope:'p',page:'p',detail:'p'}))elements['.'+name]=new Element(tag);
elements.thead=new Element('thead');elements.tbody=new Element('tbody');
const root={querySelector:key=>{assert(elements[key],key);return elements[key];}};
const document={getElementById:id=>root,createElement:tag=>new Element(tag)};
const script=html.match(/<script>([\s\S]*)<\/script>/)[1];
vm.runInNewContext(script,{document},{timeout:1000});
assert.equal(elements.tbody.children.length,10);
assert.equal(elements['.next'].disabled,false);
elements['.next'].events.click();assert(elements['.page'].textContent.includes('Page 2'));
let button=elements.tbody.children[0].children[1].children[0];button.events.focus();
assert(elements['.detail'].textContent.includes('Row 32, X: observed'));
elements['.missingOnly'].checked=true;elements['.missingOnly'].events.change();
assert.equal(elements.tbody.children.length,1);
assert(elements['.page'].textContent.includes('1 matching preview rows'));
elements['.variable'].value='1';elements['.variable'].events.change();
assert.equal(elements.tbody.children[0].children.length,2);
button=elements.tbody.children[0].children[1].children[0];button.events.click();
assert.equal(elements['.detail'].textContent,'Row 5, Y: missing');
console.log('Quality preview paging, filtering, keyboard focus and cell inspection passed');
