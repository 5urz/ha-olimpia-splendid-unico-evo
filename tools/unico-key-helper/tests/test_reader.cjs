const fs = require('fs'), vm = require('vm'), assert = require('assert');
const code = fs.readFileSync(require('path').join(__dirname, '..', 'reader.js'), 'utf8');
function run(java) {
  const out = [];
  const context = {Java: java, console: {log: x => out.push(x)}};
  vm.runInNewContext(code, context);
  if (java.available) {
    assert.deepEqual(out, ['UNICO_READER_V1:STARTED']);
    // No timer and no automatic scan. Only this explicit call starts reading.
    context.unicoRead();
    context.unicoRead(); // A double click must not produce a second result.
  }
  const results = out.filter(x => x.startsWith('UNICO_RESULT_V1:'));
  assert.equal(results.length, 1);
  return JSON.parse(results[0].slice('UNICO_RESULT_V1:'.length));
}
const bean = {getName:()=> 'Synthetic', getDevId:()=> 'synthetic123', getLocalKey:()=> '0123456789abcdef', getIp:()=>null};
let visits = [];
let result = run({available:true, perform:f=>f(), use:n=>{if(n.includes('thingclips')) throw Error('absent');}, choose:(n,c)=>{visits.push(n);c.onMatch(bean);c.onComplete();}});
assert.equal(result.devices[0].local_key, '0123456789abcdef');
assert.equal(result.devices[0].host, '');
assert.equal(visits.length, 1);
assert.equal(run({available:false}).error, 'JAVA_UNAVAILABLE');
assert.equal(run({available:true,perform:f=>f(),use:()=>{throw Error('absent');}}).error,'NO_CLASS');
assert.equal(run({available:true,perform:f=>f(),use:()=>{},choose:()=>{throw Error('failure');}}).error,'SCAN_FAILED');
result = run({available:true,perform:f=>f(),use:()=>{},choose:(n,c)=>{for(let i=0;i<600;i++)if(c.onMatch(bean)==='stop')break;c.onComplete();}});
assert.equal(result.devices.length,512);assert.equal(result.truncated,true);
// Java readiness alone must not schedule or run a scan.
const pending = [], output = [];
const context = {Java: {available:true, perform:f=>pending.push(f)}, console:{log:x=>output.push(x)}};
vm.runInNewContext(code, context);
assert.equal(output.length, 0);
pending.shift()();
assert.deepEqual(output, ['UNICO_READER_V1:STARTED']);
assert.equal(pending.length, 0);
context.unicoRead();
assert.equal(pending.length, 1);
context.unicoRead();
assert.equal(pending.length, 1);
console.log('6 reader scenarios passed (manual trigger, synthetic, no Android test).');
