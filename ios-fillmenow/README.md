# FillMeNow iOS

Native SwiftUI/MapKit iPhone app for FillMeNow.

## Identity

- App name: FillMeNow
- Bundle ID: au.com.fillmenow.app
- Version: 1.0.0
- Deployment target: iOS 16+
- Build requirement for App Store submission: Xcode 26+ / iOS 26 SDK

## Native functionality

- Native MapKit fuel station map
- Native MapKit annotation clustering
- Foreground Core Location
- Suburb/postcode search
- Best Stop ranking using FillMeNow trip-value logic
- All stations inside the selected radius
- Major petrol-station branding with station-name fallback
- Saved stations stored on-device
- Vehicle/fuel/radius settings
- Apple Maps driving directions
- Native privacy manifest

The app calls the existing FillMeNow production backend:
https://psytztnkeeymavzmpomv.supabase.co/functions/v1/fueldrop

Current launch coverage is NSW, WA and Tasmania.

## Generate project locally

Install XcodeGen and Pillow:

```bash
brew install xcodegen
python3 -m pip install pillow
python3 scripts/generate_app_icon.py
xcodegen generate
open FillMeNow.xcodeproj
```

## Signing

Do not commit Apple signing certificates, provisioning profiles, App Store Connect private keys, or passwords.

Select the developer Team in Xcode, keep bundle ID `au.com.fillmenow.app`, then archive with the App Store distribution profile.

## Public policy

- Privacy: https://fillmenow-au.vercel.app/privacy.html
- Terms: https://fillmenow-au.vercel.app/terms.html
