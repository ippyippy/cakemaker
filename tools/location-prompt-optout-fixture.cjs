'use strict';
// Test harness only: existing non-permission suites represent a user who selected Not now.
// The dedicated location-prompt suite tests startup, refusal and recovery WITHOUT this preloader.
// No application feature flag, forced browser clicks, or changed coordinate assertions.
const pw=require('playwright');
for(const type of [pw.chromium,pw.webkit]){
 const launch=type.launch.bind(type);
 type.launch=async function(options){const browser=await launch(options),create=browser.newContext.bind(browser);
  browser.newContext=async function(opts){const context=await create(opts);await context.addInitScript(()=>{try{sessionStorage.setItem('fmnLocationPromptDismissed','1');}catch{}});return context;};
  return browser;
 };
}
