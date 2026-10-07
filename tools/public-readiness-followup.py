from pathlib import Path
import re
p=Path('web/index.html');s=p.read_text()
assert 'fillmenow-public-readiness-2026-10-07' in s
# Match the existing JS desktop-detail cutoff instead of retaining a broken hybrid layout.
s=re.sub(r'max-width:\s*900px', 'max-width:1024px', s)
s=re.sub(r'min-width:\s*901px', 'min-width:1025px', s)
s=s.replace('max-height:calc(100dvh - 142px - var(--fmn-nav));overflow-y:auto!important', 'max-height:calc(100dvh - 142px - var(--fmn-nav));overflow:visible!important')
# Keep the original artwork outside the scrollable content, so a short display can still scroll.
art=re.search(r'\.sheet-main:before\{[\s\S]*?background-image:(url\("data:image/webp;base64,[^\"]+"\))',s)
assert art, 'Original Dash artwork not found'
extra='''
@media(max-width:1024px){
 body .topbar.app-topbar{display:flex!important;justify-content:space-between!important;gap:12px!important;padding:10px 16px!important}
 body .topbar.app-topbar .brand{min-width:0!important;justify-self:start!important}
 body .topbar.app-topbar .top-area{position:static!important;flex:0 0 48px!important;width:48px!important;height:48px!important}
 body .brand-copy strong{font-size:clamp(22px,6.4vw,27px)!important;letter-spacing:-1px!important}
 body #page-explore .sheet-main:before{content:none!important;display:none!important}
 body #page-explore .mobile-sheet:not(.is-collapsed):before{content:"";position:absolute;z-index:9;right:16px;top:-36px;width:96px;height:76px;background-image:DASH_ART;background-size:contain;background-repeat:no-repeat;background-position:center;pointer-events:none;filter:drop-shadow(0 5px 6px #0002)}
 body #page-explore .sheet-main{overflow-y:auto!important;overscroll-behavior:contain}
 body #page-explore .map-station-count{font-size:11px!important}
 body #page-explore .maplibregl-ctrl-bottom-right{right:8px!important;bottom:102px!important}
 body #page-explore .maplibregl-ctrl-attrib{max-width:calc(100vw - 32px)!important;white-space:normal!important;font-size:10px!important}
 body #page-alerts .switch{flex-shrink:0}
 body #page-saved .saved-card .btn{min-width:76px!important;padding:8px!important}
}
'''.replace('DASH_ART',art.group(1))
marker='</style>\n\n</head>'
assert marker in s
s=s.replace(marker,extra+marker,1)
p.write_text(s)
print('Unified mobile/tablet breakpoint and preserved original Dash outside the scrollable sheet.')
