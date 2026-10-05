# FuelDrop — Google Play Data Safety Draft

This is the working declaration for the current FuelDrop release. Re-check against the final Play Console wording before submitting.

## Does the app collect or share required user data?

### Precise location
**Collected:** Yes, when the user chooses a location feature such as "Use current location".  
**Required:** No — users can manually select/search an area.  
**Purpose:** App functionality — finding nearby fuel and ranking stations.  
**Processing:** Coordinates are sent to the FuelDrop backend to return nearby fuel data.  
**Background use:** No. FuelDrop is designed for foreground/user-initiated location use.  
**Sale / advertising:** No.

### Approximate location / area
**Collected:** Yes.  
Examples: selected suburb, postcode, state, location label.  
**Purpose:** App functionality and optional alerts.

### App activity / preferences
Fuel type, radius, vehicle type, fill size and economy are used for app functionality. Most preferences are stored locally in browser/app storage. When alerts are enabled, relevant preferences are stored with the push subscription so notifications can be generated.

### Push notification subscription
**Collected when alerts are enabled:** Yes.  
**Purpose:** App functionality.  
**Optional:** Yes.  
Turning alerts off removes the active subscription.

### Saved stations
Stored locally on the user's device/browser in the current release.

### Account / identity data
No FuelDrop account is required in the current release. No name, account username or FuelDrop password is collected.

### Payment / financial data
None in the current release.

### Contacts, SMS, call logs, photos, microphone, camera
Not collected or requested in the current release.

## Sharing

FuelDrop relies on service providers required to deliver the app, including:
- Vercel hosting
- Supabase backend/database services
- mapping/tile services
- browser/device push notification infrastructure
- official fuel-data services

Review Google Play's exact definition of "shared" versus service-provider processing when completing the form. FuelDrop does not sell personal or sensitive data and does not use location for advertising.

## Security practices

- HTTPS in transit
- no public service-role/database credential in the frontend
- public users access backend through controlled API routes
- no native background-location permission
- no app account/password system in version 1.0

## Deletion controls

Users can:
- disable notifications,
- remove saved stations,
- reset app data,
- clear browser/app storage,
- contact FuelDrop regarding privacy/deletion questions.

Privacy Policy:
https://fueldrop-au.vercel.app/privacy.html
