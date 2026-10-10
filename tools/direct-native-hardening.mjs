// Idempotent source-recipe correction, committed only after the native map acceptance test passes.
import fs from 'node:fs';
const file='tools/direct-native-prepare.mjs';let s=fs.readFileSync(file,'utf8');
const old="script-src \\'self\\' \\'unsafe-inline\\'; style-src";
const next="script-src \\'self\\' \\'unsafe-inline\\'; worker-src \\'self\\' blob:; style-src";
if(!s.includes(next)){
 if(!s.includes(old))throw Error('Unexpected native content policy: review before changing it');
 s=s.replace(old,next);fs.writeFileSync(file,s);
}
console.log('Native content policy permits packaged map workers; remote scripts, frames and objects remain blocked.');
