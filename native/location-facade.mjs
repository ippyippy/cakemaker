/* One native subscription shared by Search and Follow; never falls back to browser GPS. */
export function createLocationFacade(plugin, settings, visible = () => true) {
  const listeners = new Map();
  let next = 1, generation = 0, pending = null, nativeId = null;
  let updates = 0, accuracy = null, timestamp = null, lastError = null;
  const diagnostics = () => ({source:'Android native',subscribers:listeners.size,watching:nativeId!==null,starting:!!pending,updates,accuracy,ageMs:timestamp===null?null:Date.now()-timestamp,error:lastError});
  function errorValue(error) {
    const value=String(error?.code||'');
    if(value==='OS-PLUG-GLOC-0003'||value==='PRECISE_REQUIRED') return {code:1,message:'Allow precise location for FillMeNow.',nativeCode:value};
    if(value==='OS-PLUG-GLOC-0010') return {code:3,message:'Waiting for a fresh GPS reading.',nativeCode:value};
    return {code:2,message:'Android location is unavailable. Check Location settings or try outdoors.',nativeCode:value};
  }
  function clearNative(id) { if(id!==null) return Promise.resolve(plugin.clearWatch({id})).catch(()=>{}); return Promise.resolve(); }
  function stop() {
    generation++; listeners.clear(); const old=nativeId;nativeId=null;
    accuracy=null;timestamp=null; return clearNative(old);
  }
  function clearWatch(id) {
    listeners.delete(id);
    if(!listeners.size){generation++;const old=nativeId;nativeId=null;void clearNative(old);}
  }
  function deliverError(error,fatal=false) {
    const e=errorValue(error);lastError=e.nativeCode||String(e.code);
    const callbacks=[...listeners.values()];
    if(fatal)void stop();
    for(const cb of callbacks)try{cb.error?.(e);}catch{}
  }
  function start() {
    if(pending||nativeId!==null||!listeners.size||!visible())return;
    const own=generation;
    pending=(async()=>{
      await settings.ensureEnabled();
      if(own!==generation||!listeners.size||!visible())return;
      const permission=await plugin.requestPermissions({permissions:['location']});
      if(own!==generation||!listeners.size||!visible())return;
      if(permission.location!=='granted')throw {code:'PRECISE_REQUIRED'};
      const id=await plugin.watchPosition({enableHighAccuracy:true,maximumAge:0,timeout:20000,interval:1000,minimumUpdateInterval:500},(point,error)=>{
        if(own!==generation||!listeners.size||!visible())return;
        if(error){const code=String(error.code||'');deliverError(error,['OS-PLUG-GLOC-0003','OS-PLUG-GLOC-0007','OS-PLUG-GLOC-0009','OS-PLUG-GLOC-0017'].includes(code));return;}
        if(!point?.coords)return;
        updates++;accuracy=point.coords.accuracy;timestamp=point.timestamp;lastError=null;
        // Keep device coordinates/accuracy/time unmodified. Existing map validation rejects coarse/stale readings.
        for(const cb of [...listeners.values()])try{cb.success(point);}catch{}
      });
      if(own!==generation||!listeners.size||!visible())await clearNative(id);else nativeId=id;
    })().catch(error=>{if(own===generation&&listeners.size)deliverError(error,true);}).finally(()=>{
      pending=null;
      // A new user action may have started while an earlier async registration was being cancelled.
      if(listeners.size&&nativeId===null&&visible())start();
    });
  }
  function watchPosition(success,error) {
    if(typeof success!=='function')throw new TypeError('A location callback is required');
    const id=next++;
    if(!visible()){queueMicrotask(()=>error?.({code:2,message:'Open FillMeNow to use location.'}));return id;}
    listeners.set(id,{success,error});start();return id;
  }
  function getCurrentPosition(success,error,options={}) {
    let done=false,id,timer;
    const finish=(e,p)=>{if(done)return;done=true;clearTimeout(timer);if(id!==undefined)clearWatch(id);if(e)error?.(e);else success(p);};
    id=watchPosition(p=>finish(null,p),e=>finish(e));
    if(done)clearWatch(id);else timer=setTimeout(()=>finish({code:3,message:'Location request timed out.'}),options.timeout||25000);
  }
  return Object.freeze({geolocation:{watchPosition,clearWatch,getCurrentPosition},stop,diagnostics});
}
