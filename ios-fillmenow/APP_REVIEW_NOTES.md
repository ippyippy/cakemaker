# FillMeNow — App Review Notes

FillMeNow is a native iPhone fuel-comparison utility.

## Core native functionality

The app is not a WebView or repackaged website. Version 1.0 uses:
- SwiftUI interface
- MapKit map and station annotations
- MapKit annotation clustering
- Core Location for optional foreground location
- native suburb/postcode search through MapKit
- on-device Best Stop calculations
- UserDefaults for vehicle preferences and saved stations
- MKMapItem / Apple Maps driving directions

## Purpose and audience

FillMeNow is for Australian drivers who want to compare nearby fuel stations using reported pump price together with estimated trip cost.

## Regional coverage

Version 1.0 supports:
- NSW
- WA
- Tasmania

If testing outside those states, use the suburb/postcode search and select one of the supported states. Suggested review test:
- State: NSW
- Fuel: Diesel
- Search: Sydney NSW
- Radius: 20 km

No login or account is required.

## External services

- FillMeNow backend on Supabase Edge Functions
- NSW Government FuelCheck fuel-price data for NSW/Tasmania
- FuelWatch, Government of Western Australia
- Apple MapKit / Apple Maps
- station brand image endpoints where available

## Location

Location is optional and foreground-only. The app remains usable without granting location permission by searching a suburb or postcode.

## Business model

Version 1.0 is free and contains no in-app purchases, subscriptions or advertising.

## Safety / accuracy

Fuel prices can change after reporting. The app tells users to confirm the displayed pump price before purchase. Estimated distance, time and savings are decision-support estimates only.
