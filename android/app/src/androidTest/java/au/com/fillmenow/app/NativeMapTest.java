package au.com.fillmenow.app;
import static org.junit.Assert.*;
import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.SystemClock;
import android.webkit.WebView;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.uiautomator.*;
import androidx.lifecycle.Lifecycle;
import org.json.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
import java.util.regex.Pattern;
@RunWith(AndroidJUnit4.class)
public class NativeMapTest {
 private ActivityScenario<MainActivity> scenario;
 private final UiDevice device=UiDevice.getInstance(InstrumentationRegistry.getInstrumentation());
 private String json(String expression)throws Exception{
  ArrayBlockingQueue<String> result=new ArrayBlockingQueue<>(1);
  scenario.onActivity(a->a.getBridge().getWebView().evaluateJavascript("JSON.stringify("+expression+")",v->result.offer(v)));
  String s=result.poll(10,TimeUnit.SECONDS);assertNotNull("WebView did not respond",s);
  Object decoded=new JSONTokener(s).nextValue();return decoded==JSONObject.NULL?"null":decoded.toString();
 }
 private void run(String statements)throws Exception{json("(()=>{"+statements+";return true})()");}
 private void waitFor(String expression,int seconds)throws Exception{long end=SystemClock.elapsedRealtime()+seconds*1000L;String last="";do{try{last=json(expression);if("true".equals(last))return;}catch(Exception ignored){}SystemClock.sleep(300);}while(SystemClock.elapsedRealtime()<end);fail("Condition not reached: "+expression+" ("+last+")");}
 private void reload()throws Exception{
  run("window.__fmnReloadPending=true;location.reload()");
  waitFor("!window.__fmnReloadPending&&document.readyState==='complete'&&!!(window.FMNNativeLocation&&window.FMNJourneyApp&&window.FMNLiveLocation&&document.getElementById('recenterBtn'))",45);
 }
 private void tap(String selector)throws Exception{
  waitFor("!!document.querySelector("+JSONObject.quote(selector)+")",15);
  JSONObject r=new JSONObject(json("(()=>{const e=document.querySelector("+JSONObject.quote(selector)+");if(!e)return {};e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,w:innerWidth}})()"));
  assertTrue("Missing control "+selector,r.has("x"));final int[] point=new int[2];
  scenario.onActivity(a->{WebView w=a.getBridge().getWebView();int[] p=new int[2];w.getLocationOnScreen(p);try{double scale=(w.getWidth()-w.getPaddingLeft()-w.getPaddingRight())/r.getDouble("w");point[0]=(int)(p[0]+w.getPaddingLeft()+r.getDouble("x")*scale);point[1]=(int)(p[1]+w.getPaddingTop()+r.getDouble("y")*scale);}catch(Exception e){throw new RuntimeException(e);}});
  assertTrue("Control outside screen",point[0]>=0&&point[0]<device.getDisplayWidth()&&point[1]>=0&&point[1]<device.getDisplayHeight());device.click(point[0],point[1]);
 }
 private File dir(){File d=new File(InstrumentationRegistry.getInstrumentation().getTargetContext().getExternalFilesDir(null),"native-map-qa");d.mkdirs();return d;}
 private void screen(String name){device.takeScreenshot(new File(dir(),name+".png"));}
 private void grantDialog(boolean allow)throws Exception{
  UiObject2 choice=device.wait(Until.findObject(By.res(Pattern.compile(".*:id/permission_"+(allow?"allow_foreground_only":"deny")+"_button"))),20000);assertNotNull("Expected the actual Android permission dialog",choice);
  if(allow){UiObject2 precise=device.findObject(By.text("Precise"));if(precise!=null)precise.click();}
  screen(allow?"02-android-precise-allow":"01-android-permission-deny");choice.click();
 }
 @Test public void nativePositionsMoveTheExistingMap()throws Exception{
  assertTrue("CI emulator only",android.os.Build.FINGERPRINT.contains("generic")||android.os.Build.MODEL.contains("sdk")||android.os.Build.PRODUCT.contains("sdk"));device.executeShellCommand("cmd location set-location-enabled true");scenario=ActivityScenario.launch(MainActivity.class);
  try{
   waitFor("document.readyState==='complete'&&!!(window.FMNNativeLocation&&window.FMNJourneyApp&&window.FMNLiveLocation)",40);
   run("localStorage.setItem('fmnOnboarded','1');localStorage.setItem('fdPrefs',JSON.stringify({state:'QLD',fuel:'Diesel',radius:10,alertRadius:25,tank:250,economy:35,vehicle:'truck',truck:{height:4.2,width:2,length:12,weight:12,configuration:'rigid'},frequency:'off'}));localStorage.setItem('fdLoc',JSON.stringify({lat:-27.47,lng:153.025,state:'QLD',label:'Isolated emulator test'}))");
   reload();
   waitFor("!!(window.FMNJourneyApp.getMap()&&document.getElementById('followToggle'))&&!document.querySelector('#fmnOnboard.open')&&Number(document.getElementById('statCount').textContent)>0",45);
   assertEquals("\"https://localhost\"",json("location.origin"));assertEquals("\"android\"",json("Capacitor.getPlatform()"));
   run("Object.defineProperty(navigator,'geolocation',{configurable:true,value:{watchPosition(){throw Error('Browser GPS forbidden in native test')},getCurrentPosition(){throw Error('Browser GPS forbidden in native test')},clearWatch(){throw Error('Browser GPS forbidden in native test')}}})");
   screen("00-map-before-location");tap("#recenterBtn");grantDialog(false);
   waitFor("!!document.querySelector('#nativeLocationDialog[open]')",15);assertFalse(Boolean.parseBoolean(json("FMNLiveLocation.getState().following")));
   tap("#nativeLocationDialog footer button");tap("#recenterBtn");grantDialog(true);
   Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();assertEquals(PackageManager.PERMISSION_GRANTED,c.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION));
   waitFor("FMNLiveLocation.getState().following&&FMNNativeLocation.diagnostics().updates>=3",60);
   JSONObject before=new JSONObject(json("({updates:FMNNativeLocation.diagnostics().updates,lng:FMNJourneyApp.getLocation().lng,camera:FMNJourneyApp.getMap().getCenter().lng})"));
   waitFor("FMNNativeLocation.diagnostics().updates>="+(before.getInt("updates")+3)+"&&Math.abs(FMNJourneyApp.getLocation().lng-"+before.getDouble("lng")+")>0.00002",25);
   JSONObject after=new JSONObject(json("({updates:FMNNativeLocation.diagnostics().updates,lng:FMNJourneyApp.getLocation().lng,camera:FMNJourneyApp.getMap().getCenter().lng,accuracy:FMNNativeLocation.diagnostics().accuracy,following:FMNLiveLocation.getState().following})"));
   assertTrue(after.getDouble("accuracy")<=50);assertTrue(after.getBoolean("following"));assertNotEquals(before.getDouble("camera"),after.getDouble("camera"),0.000005);
   waitFor("(()=>{const m=FMNJourneyApp.getMap(),l=FMNJourneyApp.getLocation(),p=m.project([l.lng,l.lat]),r=m.getContainer().getBoundingClientRect();return p.x>0&&p.x<r.width&&p.y>0&&p.y<r.height})()",10);screen("03-native-gps-moving-real-map");
   tap("#followToggle");waitFor("!FMNNativeLocation.diagnostics().watching&&FMNNativeLocation.diagnostics().subscribers===0&&!FMNLiveLocation.getState().following",10);
   int stopped=new JSONObject(json("FMNNativeLocation.diagnostics()")).getInt("updates");SystemClock.sleep(2000);assertEquals(stopped,new JSONObject(json("FMNNativeLocation.diagnostics()")).getInt("updates"));
   tap("#topArea");tap("#areaGps");waitFor("!document.querySelector('#areaModal.open')&&FMNNativeLocation.diagnostics().updates>"+stopped,35);waitFor("FMNNativeLocation.diagnostics().subscribers===0",10);assertFalse(Boolean.parseBoolean(json("FMNLiveLocation.getState().following")));
   tap("#recenterBtn");waitFor("FMNLiveLocation.getState().following",30);
   scenario.moveToState(Lifecycle.State.CREATED);SystemClock.sleep(2000);scenario.moveToState(Lifecycle.State.RESUMED);waitFor("!FMNLiveLocation.getState().following&&FMNNativeLocation.diagnostics().subscribers===0",15);
   reload();assertEquals("250",json("JSON.parse(localStorage.getItem('fdPrefs')).tank"));assertEquals("4.2",json("JSON.parse(localStorage.getItem('fdPrefs')).truck.height"));screen("04-return-and-preferences");
   System.out.println("PASS: actual Android denial/precise approval; browser GPS disabled; native updates move both map origin and camera; Stop and one-shot Search use same provider; foreground stop; preferences retained. Emulator positions, not physical reception.");
  }catch(Throwable t){screen("failure");try(FileOutputStream f=new FileOutputStream(new File(dir(),"failure-state.json"))){f.write(json("({ready:document.readyState,page:document.body?.dataset.page,onboarded:localStorage.getItem('fmnOnboarded'),controls:!!document.getElementById('recenterBtn'),native:window.FMNNativeLocation?.diagnostics(),follow:window.FMNLiveLocation?.getState(),onboarding:!!document.querySelector('#fmnOnboard.open')})").getBytes(StandardCharsets.UTF_8));}catch(Exception ignored){}throw t;}finally{if(scenario!=null)scenario.close();}
 }
}
