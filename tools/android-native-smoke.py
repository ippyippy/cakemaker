"""Run only against an isolated CI emulator. Never run on the owner's phone."""
import json, re, subprocess, time, xml.etree.ElementTree as ET
from pathlib import Path
OUT=Path('native-qa');OUT.mkdir(exist_ok=True)
PKG='au.com.fillmenow.app';checks=[]
def adb(*args):
    return subprocess.check_output(['adb',*args],text=True,stderr=subprocess.STDOUT,timeout=30).strip()
def tree():
    adb('shell','uiautomator','dump','/sdcard/fmn-qa.xml')
    return ET.fromstring(adb('shell','cat','/sdcard/fmn-qa.xml'))
def screen(name):
    time.sleep(1);r=tree();(OUT/(name+'.xml')).write_text(ET.tostring(r,encoding='unicode'))
    with (OUT/(name+'.png')).open('wb') as f:subprocess.run(['adb','exec-out','screencap','-p'],stdout=f,check=True,timeout=30)
    return r
def text(r):return ' '.join(n.attrib.get('text','') for n in r.iter('node'))
def bounds(n):return list(map(int,re.findall(r'\d+',n.attrib.get('bounds',''))))
def click_id(r,suffix):
    for n in r.iter('node'):
        if n.attrib.get('resource-id','').endswith(suffix):
            b=bounds(n)
            if len(b)==4 and b[2]>b[0] and b[3]>b[1]:
                adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));return True
    return False
def reveal(suffix,direction='down'):
    for _ in range(6):
        r=tree()
        for n in r.iter('node'):
            if n.attrib.get('resource-id','').endswith(suffix) and len(bounds(n))==4 and bounds(n)[3]>bounds(n)[1]:return r
        scroll=next((n for n in r.iter('node') if n.attrib.get('class')=='android.widget.ScrollView'),None)
        assert scroll is not None,'Native scroll area unavailable: '+text(r)
        b=bounds(scroll);x=(b[0]+b[2])//2;top=b[1]+35;bottom=b[3]-35
        start,end=(bottom,top) if direction=='down' else (top,bottom)
        adb('shell','input','swipe',str(x),str(start),str(x),str(end),'350');time.sleep(.3)
    raise AssertionError('Native control not reachable: '+suffix)
def launch(fresh=True):
    if fresh:adb('shell','am','force-stop',PKG)
    result=adb('shell','am','start','-W','-f','0x14000000','-a','android.intent.action.VIEW','-d','fillmenow://location-settings','-n',PKG+'/.LocationSetupActivity')
    with (OUT/'launch-results.txt').open('a') as f:f.write(result+'\n')
    assert 'Error:' not in result,result
    time.sleep(1)
def is_system_location_notice(r):
    return 'com.google.android.gms' in ET.tostring(r,encoding='unicode') and 'No location access' in text(r)
try:
    adb('shell','cmd','location','set-location-enabled','true')
    adb('shell','pm','clear',PKG)
    launch();initial=screen('01-native-setup');assert 'Set up precise location' in text(initial) and 'not yet allowed' in text(initial),text(initial)
    assert click_id(initial,'native_location_enable');prompt=screen('02-android-permission')
    assert 'location' in text(prompt).lower();assert click_id(prompt,'permission_deny_button'),text(prompt)
    denied=screen('03-denied');assert 'not granted' in text(denied) or 'not yet allowed' in text(denied),text(denied)
    checks.append('Real Android runtime denial returns to setup; manual map remains optional')
    assert click_id(denied,'native_location_enable');prompt=screen('04-retry-permission')
    assert click_id(prompt,'permission_location_accuracy_radio_fine'),text(prompt)
    prompt=screen('04b-precise-selected');assert click_id(prompt,'permission_allow_foreground_only_button'),text(prompt)
    time.sleep(3);grants=adb('shell','dumpsys','package',PKG)
    assert re.search(r'ACCESS_FINE_LOCATION: granted=true',grants)
    assert re.search(r'ACCESS_COARSE_LOCATION: granted=true',grants)
    assert 'ACCESS_BACKGROUND_LOCATION' not in grants
    checks.append('Real precise and while-using approval; no background permission')
    launch();allowed=screen('05-native-granted');assert 'Precise location permission is allowed' in text(allowed),text(allowed)
    assert click_id(allowed,'native_location_permissions');settings=screen('06-app-settings');assert 'FillMeNow' in text(settings) and 'Location' in text(settings),text(settings)
    checks.append('Native app-permission action opens FillMeNow Android settings with Location listed')
    adb('shell','input','keyevent','4');returned=screen('06b-return-from-settings')
    assert 'Set up precise location' in text(returned),text(returned)
    adb('shell','am','force-stop',PKG)
    adb('shell','cmd','location','set-location-enabled','false');time.sleep(1);launch()
    off=screen('07-location-off')
    if is_system_location_notice(off):
        assert click_id(off,'android:id/button2');launch();off=screen('07b-native-location-off')
    assert 'Phone Location is off' in text(off),text(off)
    assert click_id(off,'native_location_enable');resolution=screen('08-system-resolution')
    raw=ET.tostring(resolution,encoding='unicode')
    assert 'location' in text(resolution).lower() and ('com.google.android.gms' in raw or 'com.android.settings' in raw),text(resolution)
    assert click_id(resolution,'android:id/button1'),text(resolution)
    time.sleep(2);assert adb('shell','cmd','location','is-location-enabled')=='true'
    checks.append('App action opens genuine system resolution; a real approval tap turns Location on')
    launch();gps=reveal('native_location_test');screen('09-before-diagnostic');assert click_id(gps,'native_location_test')
    for i in range(8):
        adb('emu','geo','fix',str(153.025+i*.0001),'-27.47');time.sleep(1)
    reveal('native_location_status','up');diagnostic=screen('10-native-gps');v=text(diagnostic)
    assert 'Native GPS: reported' in v,v
    samples=re.search(r'(\d+) updates',v);assert samples and int(samples.group(1))>=2,v
    checks.append('Native fused provider receives multiple fresh simulated movement updates')
    adb('shell','input','keyevent','3');time.sleep(1)
    launch(fresh=False);stopped=reveal('native_location_test');screen('11-foreground-return')
    assert 'Test native GPS for 30 seconds' in text(stopped),text(stopped)
    checks.append('Foreground exit stops the diagnostic; returning does not restart it')
    report={'status':'PASS','checks':checks,'nativeUpdateCount':int(samples.group(1)),'physicalGPS':False,'device':'Android 35 CI emulator','mapDrivingOnPhysicalPhone':'not tested'}
except Exception as e:
    report={'status':'FAIL','checks':checks,'error':str(e),'physicalGPS':False}
    try:
        screen('failure')
        logs=adb('logcat','-d','-t','500')
        (OUT/'runtime-failure.txt').write_text('\n'.join(l for l in logs.splitlines() if any(t in l for t in ['AndroidRuntime','au.com.fillmenow','ActivityTaskManager'])))
    except Exception:pass
finally:
    (OUT/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if report['status']!='PASS':raise SystemExit(1)
