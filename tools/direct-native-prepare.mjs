// Build-only migration on the reviewed candidate branch. Production web/backend are never modified.
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
const write=(p,s)=>{fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,s);};
write('native/package.json',JSON.stringify({name:'fillmenow-native',private:true,version:'1.2.0',type:'module',dependencies:{'@capacitor/core':'8.5.3','@capacitor/android':'8.5.3','@capacitor/cli':'8.5.3','@capacitor/geolocation':'8.2.3','@capacitor/app':'8.1.2',esbuild:'0.25.12'}},null,2));
execFileSync('npm',[fs.existsSync('native/package-lock.json')?'ci':'install','--ignore-scripts','--no-audit','--no-fund'],{cwd:'native',stdio:'inherit'});
write('native/capacitor.config.json',JSON.stringify({appId:'au.com.fillmenow.app',appName:'FillMeNow',webDir:'www',android:{path:'../android',allowMixedContent:false,webContentsDebuggingEnabled:false},server:{hostname:'localhost',androidScheme:'https',cleartext:false},loggingBehavior:'none'},null,2));
write('android/build.gradle',`buildscript { repositories { google(); mavenCentral() }; dependencies { classpath 'com.android.tools.build:gradle:8.13.0' } }
ext { minSdkVersion=24; compileSdkVersion=36; targetSdkVersion=36; androidxActivityVersion='1.11.0'; androidxAppCompatVersion='1.7.1'; androidxCoreVersion='1.17.0'; androidxWebkitVersion='1.14.0' }
allprojects { repositories { google(); mavenCentral() } }
`);
write('android/settings.gradle',`include ':app'
include ':capacitor-cordova-android-plugins'
project(':capacitor-cordova-android-plugins').projectDir = new File('./capacitor-cordova-android-plugins/')
apply from: 'capacitor.settings.gradle'
`);
write('android/app/build.gradle',`apply plugin: 'com.android.application'
android {
 namespace 'au.com.fillmenow.app'
 compileSdk 36
 defaultConfig { applicationId 'au.com.fillmenow.app'; minSdk 24; targetSdk 36; versionCode 3; versionName '1.2.0-direct-gps-test'; testInstrumentationRunner 'androidx.test.runner.AndroidJUnitRunner' }
 buildTypes { release { minifyEnabled true; proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro' } }
 testBuildType 'release'
 compileOptions { sourceCompatibility JavaVersion.VERSION_21; targetCompatibility JavaVersion.VERSION_21 }
}
dependencies {
 implementation project(':capacitor-android')
 implementation project(':capacitor-cordova-android-plugins')
 implementation 'androidx.appcompat:appcompat:1.7.1'
 implementation 'androidx.core:core:1.17.0'
 implementation 'com.google.android.gms:play-services-location:21.3.0'
 androidTestImplementation 'androidx.test:runner:1.7.0'
 androidTestImplementation 'androidx.test:rules:1.7.0'
 androidTestImplementation 'androidx.test.ext:junit:1.3.0'
 androidTestImplementation 'androidx.test.uiautomator:uiautomator:2.3.0'
}
apply from: 'capacitor.build.gradle'
`);
write('android/app/proguard-rules.pro',`-keep class au.com.fillmenow.app.MainActivity { *; }
-keep class au.com.fillmenow.app.FMNSettingsPlugin { *; }
-keep class com.getcapacitor.** { *; }
-keep @com.getcapacitor.annotation.CapacitorPlugin class * { *; }
-keepclassmembers class * { @com.getcapacitor.PluginMethod <methods>; }
# The separate instrumentation APK calls these shared dependency APIs. Preserve them in the actual delivered release too.
-keep class androidx.** { *; }
-keep class kotlin.** { *; }
`);
write('android/app/src/main/AndroidManifest.xml',`<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
 <uses-permission android:name="android.permission.INTERNET"/>
 <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
 <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
 <uses-feature android:name="android.hardware.location.gps" android:required="false"/>
 <application android:allowBackup="false" android:icon="@drawable/ic_launcher" android:roundIcon="@drawable/ic_launcher" android:label="FillMeNow" android:supportsRtl="true" android:usesCleartextTraffic="false" android:theme="@style/AppTheme.NoActionBar">
  <activity android:name=".MainActivity" android:exported="true" android:launchMode="singleTask" android:configChanges="orientation|keyboardHidden|keyboard|screenSize|locale|smallestScreenSize|screenLayout|uiMode|navigation|density" android:theme="@style/AppTheme.NoActionBar">
   <intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter>
  </activity>
 </application>
</manifest>`);
write('android/app/src/main/res/values/styles.xml',`<resources><style name="AppTheme" parent="Theme.AppCompat.Light.NoActionBar"><item name="colorPrimary">#087532</item><item name="colorAccent">#087532</item><item name="android:windowLightStatusBar">true</item><item name="android:statusBarColor">#FFFFFF</item><item name="android:navigationBarColor">#FFFFFF</item></style><style name="AppTheme.NoActionBar" parent="AppTheme"><item name="windowActionModeOverlay">true</item><item name="windowNoTitle">true</item></style></resources>`);
for(const p of ['android/app/src/main/java/au/com/fillmenow/app/LocationSetupActivity.java','android/app/src/main/java/au/com/fillmenow/app/LocationDelegationService.java'])fs.rmSync(p,{force:true});
write('android/app/src/main/java/au/com/fillmenow/app/MainActivity.java',`package au.com.fillmenow.app;
import android.os.Bundle;
import android.app.Activity;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.IntentSenderRequest;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.PluginCall;
import com.google.android.gms.common.api.ResolvableApiException;
import com.google.android.gms.location.*;
public final class MainActivity extends BridgeActivity {
 private PluginCall pendingSettings;
 private final ActivityResultLauncher<IntentSenderRequest> resolution=registerForActivityResult(new ActivityResultContracts.StartIntentSenderForResult(),r->{PluginCall p=pendingSettings;pendingSettings=null;if(p!=null){if(r.getResultCode()==Activity.RESULT_OK)p.resolve();else p.reject("Phone Location was not enabled","LOCATION_SETTINGS_DECLINED");}});
 @Override public void onCreate(Bundle b){registerPlugin(FMNSettingsPlugin.class);super.onCreate(b);if(getBridge()!=null){android.view.View view=getBridge().getWebView();ViewCompat.setOnApplyWindowInsetsListener(view,(v,insets)->{androidx.core.graphics.Insets i=insets.getInsets(WindowInsetsCompat.Type.systemBars()|WindowInsetsCompat.Type.displayCutout());v.setPadding(i.left,i.top,i.right,i.bottom);return insets;});ViewCompat.requestApplyInsets(view);}}
 public void ensureLocation(PluginCall call){
  if(pendingSettings!=null){call.reject("Location setup already in progress","SETTINGS_BUSY");return;}
  pendingSettings=call;
  LocationRequest q=new LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY,1000L).build();
  LocationServices.getSettingsClient(this).checkLocationSettings(new LocationSettingsRequest.Builder().addLocationRequest(q).setAlwaysShow(true).build())
   .addOnSuccessListener(this,r->{if(pendingSettings==call){pendingSettings=null;call.resolve();}})
   .addOnFailureListener(this,e->{if(pendingSettings!=call)return;if(e instanceof ResolvableApiException){try{resolution.launch(new IntentSenderRequest.Builder(((ResolvableApiException)e).getResolution()).build());}catch(Exception x){pendingSettings=null;call.reject("Open phone Location settings","LOCATION_SETTINGS_ERROR");}}else{pendingSettings=null;call.reject("Location settings unavailable","LOCATION_SETTINGS_ERROR");}});
 }
 @Override public void onDestroy(){if(pendingSettings!=null){pendingSettings.reject("App closed during location setup","CANCELLED");pendingSettings=null;}super.onDestroy();}
}
`);
write('android/app/src/main/java/au/com/fillmenow/app/FMNSettingsPlugin.java',`package au.com.fillmenow.app;
import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.LocationManager;
import android.net.Uri;
import android.provider.Settings;
import androidx.core.content.ContextCompat;
import androidx.core.location.LocationManagerCompat;
import com.getcapacitor.*;
import com.getcapacitor.annotation.CapacitorPlugin;
@CapacitorPlugin(name="FMNSettings")
public final class FMNSettingsPlugin extends Plugin {
 @PluginMethod public void status(PluginCall c){JSObject r=new JSObject();r.put("fine",ContextCompat.checkSelfPermission(getContext(),Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED);r.put("coarse",ContextCompat.checkSelfPermission(getContext(),Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED);LocationManager m=(LocationManager)getContext().getSystemService(android.content.Context.LOCATION_SERVICE);r.put("enabled",m!=null&&LocationManagerCompat.isLocationEnabled(m));c.resolve(r);}
 @PluginMethod public void ensureEnabled(PluginCall c){getActivity().runOnUiThread(()->((MainActivity)getActivity()).ensureLocation(c));}
 @PluginMethod public void openAppSettings(PluginCall c){open(c,new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,Uri.parse("package:"+getContext().getPackageName())));}
 @PluginMethod public void openLocationSettings(PluginCall c){open(c,new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS));}
 @PluginMethod public void openExternal(PluginCall c){String value=c.getString("url","");Uri u=Uri.parse(value);if(!"https".equals(u.getScheme())&&!"tel".equals(u.getScheme())){c.reject("Unsupported external link");return;}open(c,new Intent(Intent.ACTION_VIEW,u));}
 private void open(PluginCall c,Intent i){getActivity().runOnUiThread(()->{try{getActivity().startActivity(i);c.resolve();}catch(Exception e){c.reject("This settings screen or link is unavailable");}});}
}
`);
// Package a copy of the single existing interface. Never fetch executable UI from a remote server.
fs.rmSync('native/www',{recursive:true,force:true});fs.cpSync('web','native/www',{recursive:true});
const files=['index.html','journey.js','live-location.js'];
for(const name of files){const p='native/www/'+name;let s=fs.readFileSync(p,'utf8');s=s.replaceAll('navigator.geolocation','window.FMNNativeLocation.geolocation');
 if(name==='index.html'){
  s=s.replace('</head>','<meta http-equiv="Content-Security-Policy" content="default-src \'self\' data: blob: https:; script-src \'self\' \'unsafe-inline\'; style-src \'self\' \'unsafe-inline\'; object-src \'none\'; frame-src \'none\'; base-uri \'self\'; form-action \'none\';"><script src="/native-entry.js"></script></head>');
  s=s.replace('async function swreg(){','async function swreg(){throw Error("Push is not enabled in this native GPS test");');
 }
 if(name==='live-location.js'||name==='journey.js')s=s.replace('function help(){','function help(){if(window.FMNNativeLocation){window.FMNPermissionUI.open();return;}');
 if(name==='live-location.js')s=s.replaceAll('Following · reported accuracy','Following · Android GPS ±').replace('GPS ± ±','GPS ±');
 fs.writeFileSync(p,s);
}
// This package uses Android permission, never the browser geolocation element or browser permission-query UI.
write('native/www/gps-permission.js','/* Permission handling is supplied by the direct native entry bundle. */\n');
const {build}=await import('../native/node_modules/esbuild/lib/main.js');
await build({entryPoints:['native/entry.mjs'],bundle:true,format:'iife',platform:'browser',target:'chrome100',outfile:'native/www/native-entry.js',logLevel:'warning'});
execFileSync('npx',['cap','sync','android'],{cwd:'native',stdio:'inherit'});
console.log('Direct Android assets prepared; production web, backend, prices and artwork unchanged.');
