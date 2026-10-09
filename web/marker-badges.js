/* Presentation only. Uses the existing recommendation and checked station data; never ranks, tracks or fetches. */
(function(root,factory){'use strict';const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.FMNMarkerBadges=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){'use strict';
const priorities=Object.freeze({normal:10,truck:20,deal:30,cheapest:40,best:50,selected:60});
function describe(row,context={},now=Date.now()){
 const id=String(row.station_id),eligible=!context.review;
 const best=eligible&&context.bestId!=null&&id===String(context.bestId);
 const cheapest=eligible&&context.cheapestId!=null&&id===String(context.cheapestId);
 // _offers, _access and _facility are supplied by the existing reviewed catalogue rules.
 const offer=eligible&&Array.isArray(row._offers)&&row._offers.some(o=>o.status==='verified'&&Date.parse(o.starts_at)<=now&&Date.parse(o.ends_at)>now);
 const truck=!!context.truck&&(row._access?.status==='match'?'match':row._facility?'facility':null);
 const kind=best?'best':cheapest?'cheapest':offer?'deal':truck?'truck':'normal';
 const primary=best?'★ Best value':cheapest?'Cheapest':offer?'Offer':truck==='match'?'Recorded fit':truck?'Truck facilities':'';
 const secondary=[];
 if(best&&cheapest)secondary.push({kind:'cheapest',text:'Cheapest too'});
 if(offer&&kind!=='deal')secondary.push({kind:'deal',text:'Offer'});
 if(truck&&kind!=='truck')secondary.push({kind:'truck',text:truck==='match'?'Recorded fit':'Truck facilities'});
 return {kind,primary,secondary,best,cheapest,offer,truck,priority:priorities[kind]};
}
function addText(parent,text,cls){const n=parent.ownerDocument.createElement('span');n.className=cls;n.textContent=text;parent.appendChild(n);return n;}
function updateMarker(node,row,context){
 const d=describe(row,context),signature=JSON.stringify(d);
 node.dataset.markerKind=d.kind;node.dataset.markerPriority=String(d.priority);
 node.dataset.bestValue=String(d.best);node.dataset.cheapest=String(d.cheapest);
 node.classList.toggle('best',d.best);node.classList.toggle('cheapest',d.cheapest);
 node.classList.toggle('has-verified-offer',d.offer);node.classList.toggle('has-truck-facilities',!!d.truck);
 if(node.dataset.badgeSignature!==signature||!node.querySelector('.pin-secondary-tags')){
  let primary=node.querySelector('.pin-value-label');if(!primary)primary=addText(node,'','pin-value-label');
  primary.hidden=!d.primary;primary.textContent=d.primary;
  let secondary=node.querySelector('.pin-secondary-tags');if(!secondary)secondary=addText(node,'','pin-secondary-tags');
  secondary.replaceChildren();secondary.hidden=!d.secondary.length;
  d.secondary.forEach(tag=>{const n=addText(secondary,tag.kind==='truck'?'Truck':tag.text,'pin-mini-tag '+tag.kind);n.title=tag.text+(tag.kind==='truck'?' · route and clearance must be checked':'');});
  node.dataset.badgeSignature=signature;
 }
 // MapLibre owns node.transform. CSS changes dimensions, not the geographical anchor.
 return d;
}
function updateCard(main,row,context){
 main.querySelectorAll(':scope > .station-badge-traits').forEach(n=>n.remove());
 const d=describe(row,context),tags=[];
 if(d.cheapest)tags.push({kind:'cheapest',text:d.best?'Cheapest too':'Cheapest'});
 if(d.truck)tags.push({kind:'truck',text:d.truck==='match'?'Matches recorded dimensions · route not checked':'Truck facilities · clearance unconfirmed'});
 if(!tags.length)return d;
 const tray=addText(main,'','station-badge-traits');tags.forEach(t=>addText(tray,t.text,'station-trait '+t.kind));
 const value=main.querySelector(':scope > .value-badge');if(value)value.after(tray);else main.prepend(tray);
 return d;
}
return Object.freeze({priorities,describe,updateMarker,updateCard});
});
