// Offline event harness for the local view; native GUI qualification is separate.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Element {
 constructor(tag){this.tag=tag;this.children=[];this.attributes={};this.events={};this.value='';}
 appendChild(e){this.children.push(e);return e;}
 setAttribute(k,v){this.attributes[k]=String(v);}
 getAttribute(k){return this.attributes[k];}
 addEventListener(k,fn){this.events[k]=fn;}
 querySelectorAll(selector){const found=[];for(const c of this.children){if(selector==='[data-flow]'&&c.attributes['data-flow']!==undefined)found.push(c);found.push(...c.querySelectorAll(selector));}return found;}
}
const html=fs.readFileSync(process.argv[2],'utf8');
const select=new Element('select'),status=new Element('p'),button=new Element('button'),drawing=new Element('div');
const root={querySelector:s=>({select,'.status':status,button,'.drawing':drawing})[s]};
const document={getElementById:()=>root,createElement:t=>new Element(t),createElementNS:(_,t)=>new Element(t)};
vm.runInNewContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],{document},{timeout:1000});
const ribbons=drawing.querySelectorAll('[data-flow]');assert(ribbons.length>=2);
select.value='0';select.events.change();
assert(status.textContent.includes('Flow #0'));
assert(ribbons.filter(p=>p.getAttribute('data-flow')==='0').every(p=>p.getAttribute('fill-opacity')==='0.85'));
assert(ribbons.filter(p=>p.getAttribute('data-flow')!=='0').every(p=>p.getAttribute('fill-opacity')==='0.08'));
const other=ribbons.find(p=>p.getAttribute('data-flow')!=='0');other.events.mouseenter();
assert(status.textContent.includes('Flow #'+other.getAttribute('data-flow')));
other.events.mouseleave();assert(status.textContent.includes('Flow #0'));
button.events.click();assert.equal(select.value,'');assert.equal(status.textContent,'All flows shown.');
assert(ribbons.every(p=>p.getAttribute('fill-opacity')==='0.48'));
console.log('Local selection, linked segments, hover/restore and clearing passed');
