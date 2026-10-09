"""Run only against an isolated CI emulator. Never run on the owner's phone."""
import json, os, re, subprocess, time, xml.etree.ElementTree as ET
from pathlib import Path
OUT = Path('native-qa'); OUT.mkdir(exist_ok=True)
PKG = 'au.com.fillmenow.app'
checks = []

def adb(*args):
    return subprocess.check_output(['adb', *args], text=True, stderr=subprocess.STDOUT).strip()

def screen(name):
    time.sleep(1)
    adb('shell', 'uiautomator', 'dump', '/sdcard/fmn-qa.xml')
    xml = adb('shell', 'cat', '/sdcard/fmn-qa.xml')
    (OUT / (name + '.xml')).write_text(xml)
    with (OUT / (name + '.png')).open('wb') as f:
        subprocess.run(['adb', 'exec-out', 'screencap', '-p'], stdout=f, check=True)
    return ET.fromstring(xml)

def click_id(tree, suffix):
    for node in tree.iter('node'):
        if node.attrib.get('resource-id', '').endswith(suffix):
            b = list(map(int, re.findall(r'\d+', node.attrib['bounds'])))
            adb('shell', 'input', 'tap', str((b[0] + b[2])//2), str((b[1] + b[3])//2))
            return True
    return False

def text(tree): return ' '.join(n.attrib.get('text','') for n in tree.iter('node'))
def launch():
    adb('shell', 'am', 'start', '-W', '-a', 'android.intent.action.VIEW', '-d', 'fillmenow://location-settings', '-n', PKG + '/.LocationSetupActivity')

try:
    adb('shell', 'cmd', 'location', 'set-location-enabled', 'true')
    # This data belongs exclusively to the disposable emulator installation.
    adb('shell', 'pm', 'clear', PKG)
    launch(); initial = screen('01-native-setup')
    assert 'Set up precise location' in text(initial), text(initial)
    assert 'not yet allowed' in text(initial)
    assert click_id(initial, 'native_location_enable')
    prompt = screen('02-android-permission')
    assert 'location' in text(prompt).lower(), text(prompt)
    # Real Android permission dialog, not a HTML imitation or auto-granted fixture.
    assert click_id(prompt, 'permission_deny_button'), text(prompt)
    denied = screen('03-denied')
    assert 'not granted' in text(denied) or 'not yet allowed' in text(denied), text(denied)
    checks.append('Android runtime denial returns to native setup; map remains optional')
    assert click_id(denied, 'native_location_enable')
    prompt = screen('04-retry-permission')
    precise = next((n for n in prompt.iter('node') if n.attrib.get('text') == 'Precise'), None)
    if precise is not None:
        b=list(map(int,re.findall(r'\d+',precise.attrib['bounds']))); adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2))
        prompt=screen('04b-precise-selected')
    assert click_id(prompt, 'permission_allow_foreground_only_button'), text(prompt)
    time.sleep(3)
    grants = adb('shell','dumpsys','package',PKG)
    assert re.search(r'ACCESS_FINE_LOCATION: granted=true',grants), 'Fine permission not granted'
    assert re.search(r'ACCESS_COARSE_LOCATION: granted=true',grants), 'Coarse permission not granted'
    assert 'ACCESS_BACKGROUND_LOCATION' not in grants, 'Unexpected background location permission'
    checks.append('Real Android precise + foreground approval; no background permission declared')
    launch(); allowed = screen('05-native-granted')
    assert 'Precise location permission is allowed' in text(allowed), text(allowed)
    assert click_id(allowed, 'native_location_permissions')
    settings = screen('06-app-settings')
    assert 'FillMeNow' in text(settings), text(settings)
    checks.append('App permission button opens Android settings for FillMeNow itself')
    launch(); adb('shell','cmd','location','set-location-enabled','false'); launch()
    off = screen('07-location-off'); assert 'Phone Location is off' in text(off), text(off)
    assert click_id(off,'native_location_enable')
    resolution = screen('08-system-resolution')
    assert 'location' in text(resolution).lower(), text(resolution)
    assert 'com.google.android.gms' in ET.tostring(resolution,encoding='unicode') or 'com.android.settings' in ET.tostring(resolution,encoding='unicode'), 'Expected Android/Google settings UI'
    checks.append('Location-off opens a system location-settings resolution, not a web help popup')
    # Do not confuse the simulated location check below with physical GPS reception.
    adb('shell','input','keyevent','4'); adb('shell','cmd','location','set-location-enabled','true')
    launch(); gps=screen('09-before-diagnostic'); assert click_id(gps,'native_location_test')
    for i in range(8):
        adb('emu','geo','fix',str(153.025+i*.0001),'-27.47'); time.sleep(1)
    diagnostic=screen('10-native-gps'); diagnostic_text=text(diagnostic)
    assert 'Native GPS: reported' in diagnostic_text, diagnostic_text
    samples=re.search(r'(\d+) updates',diagnostic_text); assert samples and int(samples.group(1))>=2, diagnostic_text
    checks.append('Native fused GPS receives multiple fresh emulator positions; no kilometre distance gate')
    adb('shell','input','keyevent','3'); time.sleep(1); launch()
    stopped=screen('11-foreground-return')
    assert 'Test native GPS for 30 seconds' in text(stopped), text(stopped)
    checks.append('Native diagnostic stops when backgrounded; it does not restart without a tap')
    report={'status':'PASS','checks':checks,'physicalGPS':False,'device':'Android 35 CI emulator','mapDrivingOnPhysicalPhone':'not tested'}
except Exception as e:
    report={'status':'FAIL','checks':checks,'error':str(e),'physicalGPS':False}
    screen('failure')
finally:
    (OUT/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
if report['status']!='PASS': raise SystemExit(1)
