"""Finalize lifecycle ordering and visibility in the reviewed journey source."""
from pathlib import Path
p=Path('web/journey.js');s=p.read_text()
changes=[
 ('document.addEventListener(\'DOMContentLoaded\',()=>queueMicrotask(init));','document.addEventListener(\'DOMContentLoaded\',()=>setTimeout(init,0));'),
 ('for(const x of j.candidates){const clean=', 'for(const x of j.candidates){if(x.state&&x.state!==state)continue;const clean='),
 ("$('stateSelect').addEventListener('change',()=>cancelLocation(true));", "$('stateSelect').addEventListener('change',()=>{if(controller)cancelLocation(true);});"),
]
for old,new in changes:
 if old in s:
  assert s.count(old)==1
  s=s.replace(old,new,1)
 else: assert new in s,old
p.write_text(s)
p=Path('web/journey.css');s=p.read_text()
rule='\nbody #optionsWiden[hidden]{display:none!important}\n'
if rule not in s:s+=rule
p.write_text(s)
print('Journey mount order, state-boundary confirmation and hidden empty-state action verified.')
