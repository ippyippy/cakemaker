# FillMeNow 1.1.0 native GPS test

This is an Android APK, not an Add to Home Screen shortcut. It uses the existing FillMeNow interface with Android Browser Helper location delegation. Chrome/a compatible trusted-activity browser still renders the interface; Android supplies the delegated location using FillMeNow's own foreground permission. This is not a complete rewrite of the web interface and does not provide offline/background navigation.

## Install
1. Keep the existing home-screen shortcut. Do not uninstall it or clear browser/app storage.
2. Download/open `FillMeNow-1.1.0-GPS-test.apk` on the Android phone. Approve installation from the chosen download app only if needed, then turn that install-source permission off afterwards. Do not disable Play Protect. This build has not been published to Google Play.
3. Launch the newly installed FillMeNow app. The first-run native screen says `Set up precise location`.
4. While parked, tap `Enable precise location`, select `Precise` and `While using the app`, and approve Android's location-setting resolution if offered. The app never grants itself permission or turns Location on without approval.
5. Open the map and tap `My location`. If another web permission prompt appears, allow the matching FillMeNow site. Use the same Chrome/browser profile as the old app where possible.

The APK keeps the established package name and is signed with the existing private FillMeNow upload key. Its signing fingerprint must match the already published Digital Asset Links before the package is released by the test build. A Play-installed app may use a different Play signing certificate: do not uninstall or force-replace an existing signed app if Android reports a conflict. A home-screen WebAPK is separate and may result in two similar icons.

## Native GPS diagnostics
Long-press the NEW native FillMeNow icon and choose `Location settings`. It opens the app's native permission/setup screen, not Chrome settings. `Test native GPS for 30 seconds` shows actual device-reported accuracy, fresh update count and age. It stops after 30 seconds or when the screen loses foreground. Coordinates are not shown, logged or saved by this diagnostic.

Check Location off/on, denied/allowed, approximate/precise, fresh outdoor acquisition, multiple movement updates, return from background, map follow/pause/recentre, and stop. A passenger should inspect map movement, or compare readings while stopped; do not operate the phone while driving. No physical GPS or road/lane accuracy is certified by an emulator test. Actual trusted-browser delegation and map following must be checked on the phone.

## Existing preferences
The trusted app launches the existing `fillmenow-au.vercel.app` origin. When hosted by the same browser/profile as the old AU shortcut, it can use that browser's existing origin-local saved settings. A different origin or browser has separate storage. This release does not clear storage, silently copy private data between browsers, or promise cross-origin/account sync. Check the truck fill size/dimensions and Saved list before relying on recommendations. Leave the old shortcut intact until this is confirmed.

## Preserved and still incomplete
All current web/UI, Dash artwork, station coordinates, green Best Value hierarchy, prices, preference logic, saved stations, filters and backend are unchanged by the native-only branch. Location delegation follows the browser's requests. No ACCESS_BACKGROUND_LOCATION permission or location foreground service was added. The map's existing foreground-only precision checks remain in place.

Measured truck-clearance records, real along-road detours and confirmed promotions remain independent tasks; this package does not invent them or solve them. No store release, account migration, credential rotation, database/cron update or customer-report action is part of this build.

## Sources
- Google Android Browser Helper location delegation demo: https://github.com/GoogleChrome/android-browser-helper/tree/main/demos/twa-location-delegation
- Android precise permission: https://developer.android.com/codelabs/approximate-location
- Location settings resolution: https://developers.google.com/android/reference/com/google/android/gms/location/SettingsClient
