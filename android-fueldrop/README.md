# FuelDrop Android / Google Play package

Package ID: `au.com.fueldrop.app`

Production origin: `https://fueldrop-au.vercel.app`

This project wraps the FuelDrop PWA in a Trusted Web Activity using Google's Android Browser Helper.

## Android / Play configuration

- compileSdk: 36
- targetSdk: 36
- minSdk: 24
- Android Browser Helper: 2.7.3
- No native background-location permission is requested.
- Location remains a foreground web feature initiated by the user.

## Build

Use JDK 17, Android SDK Platform 36 and Build Tools 36.0.0.

```bash
gradle :app:bundleRelease
```

The release AAB must be signed with the permanent FuelDrop upload key before Play upload.

## Digital Asset Links

A Trusted Web Activity requires:

`https://fueldrop-au.vercel.app/.well-known/assetlinks.json`

The file must contain the package ID and SHA-256 certificate fingerprint. For Play-distributed builds, add the **Google Play App Signing certificate** SHA-256 fingerprint after the app is created in Play Console. The upload-key fingerprint may also be included for local/direct signed builds.

Do not commit a keystore or keystore passwords to this public repository.

## Public policy URLs

- Privacy: https://fueldrop-au.vercel.app/privacy.html
- Terms: https://fueldrop-au.vercel.app/terms.html
