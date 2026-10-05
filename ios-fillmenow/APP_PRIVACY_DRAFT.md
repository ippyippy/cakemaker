# FillMeNow — App Store Privacy Draft

Use these answers as the working App Store Connect privacy declaration for version 1.0. Re-check the final binary and Apple form wording before submission.

## Tracking

**Does this app use data to track users across apps or websites owned by other companies?**  
No.

## Data linked to the user

None. FillMeNow version 1.0 has no user account and does not collect a name, email address, phone number or advertising identifier.

## Data not linked to the user

### Precise Location

**Collected:** Yes, when the user chooses the current-location feature.  
**Linked to identity:** No.  
**Used for tracking:** No.  
**Purpose:** App Functionality.

The coordinates are sent to the FillMeNow backend to return nearby fuel stations. Users can instead search a suburb or postcode.

### Approximate / selected area

The selected search area is used for app functionality. Search and preference values are stored locally on the device.

## Data stored only on the device

The following are stored locally using app-scoped UserDefaults and are not treated as off-device collection by FillMeNow:
- selected state and fuel type
- search radius
- vehicle profile
- tank / fill size
- fuel economy
- selected location label
- saved stations

## No collection in version 1.0

- Contact info
- Health data
- Financial information
- Contacts
- User content
- Browsing history
- Advertising data
- Purchases
- Photos or videos
- Audio
- Messages
- Sensitive information

## Privacy manifest

The binary includes:
- NSPrivacyCollectedDataTypePreciseLocation for App Functionality
- NSPrivacyAccessedAPICategoryUserDefaults with reason CA92.1
- NSPrivacyTracking = false
