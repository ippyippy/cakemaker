package au.com.fillmenow.app;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.location.Location;
import android.location.LocationManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.view.View;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import androidx.core.location.LocationManagerCompat;
import com.google.android.gms.common.ConnectionResult;
import com.google.android.gms.common.GoogleApiAvailability;
import com.google.android.gms.common.api.ResolvableApiException;
import com.google.android.gms.location.LocationCallback;
import com.google.android.gms.location.LocationRequest;
import com.google.android.gms.location.LocationResult;
import com.google.android.gms.location.LocationServices;
import com.google.android.gms.location.LocationSettingsRequest;
import com.google.android.gms.location.Priority;
import com.google.androidbrowserhelper.trusted.LauncherActivity;
import java.util.Locale;

/** Native permission/setup UI. Coordinates are neither logged nor persisted here. */
public final class LocationSetupActivity extends Activity {
    private static final int PERMISSION = 2001, SETTINGS = 2002;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private TextView status;
    private Button enable, diagnostic;
    private LocationCallback locationCallback;
    private boolean busy, launching;
    private int samples;

    private boolean precise() {
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }
    private boolean enabled() {
        LocationManager manager = (LocationManager)getSystemService(LOCATION_SERVICE);
        return manager != null && LocationManagerCompat.isLocationEnabled(manager);
    }
    private boolean servicesAvailable() {
        return GoogleApiAvailability.getInstance().isGooglePlayServicesAvailable(this) == ConnectionResult.SUCCESS;
    }
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle("FillMeNow location setup");
        buildScreen();
        boolean settingsLink = getIntent().getData() != null;
        if (state == null && !settingsLink && precise() && enabled()) openMap();
    }
    private void buildScreen() {
        LinearLayout frame = new LinearLayout(this);
        frame.setOrientation(LinearLayout.VERTICAL);
        frame.setBackgroundColor(Color.WHITE);
        frame.setOnApplyWindowInsetsListener((view, insets) -> {
            view.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                    insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets;
        });
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(24), dp(24), dp(24), dp(24));
        scroll.addView(body);
        frame.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        ImageView icon = new ImageView(this);
        icon.setImageResource(R.drawable.ic_launcher);
        icon.setContentDescription("FillMeNow");
        body.addView(icon, new LinearLayout.LayoutParams(dp(56), dp(56)));
        text(body, "FillMeNow", 30, true);
        text(body, "Set up precise location", 24, true);
        text(body, "While parked, allow precise location so the map can follow you. Android controls this permission under FillMeNow, not your home-screen shortcut.", 17, false);
        status = text(body, "Checking permission…", 17, true);
        status.setId(R.id.native_location_status);
        status.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);
        enable = button(body, "Enable precise location", R.id.native_location_enable, this::requestPrecise);
        button(body, "FillMeNow app permissions", R.id.native_location_permissions, () -> {
            stopDiagnostic();
            openSettings(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getPackageName()));
        });
        button(body, "Phone location settings", R.id.native_location_phone, () -> {
            stopDiagnostic();
            openSettings(Settings.ACTION_LOCATION_SOURCE_SETTINGS, null);
        });
        diagnostic = button(body, "Test native GPS for 30 seconds", R.id.native_location_test, this::testGps);
        text(body, "The GPS test displays accuracy and update count only. A precise permission does not guarantee reception. No test position is logged or saved.", 15, false);
        text(body, "Live following works while FillMeNow is visible. No background-location permission is requested. The existing map, station prices, Dash and vehicle settings are used.", 15, false);
        LinearLayout footer = new LinearLayout(this);
        footer.setOrientation(LinearLayout.VERTICAL);
        footer.setPadding(dp(24), dp(8), dp(24), dp(12));
        button(footer, "Open map / continue without GPS", R.id.native_location_open_map, this::openMap);
        frame.addView(footer);
        setContentView(frame);
        frame.requestApplyInsets();
    }
    private TextView text(LinearLayout parent, String value, int size, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value); view.setTextSize(size); view.setTextColor(Color.rgb(17, 34, 24));
        view.setPadding(0, dp(10), 0, dp(10));
        if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        parent.addView(view, new LinearLayout.LayoutParams(-1, -2));
        return view;
    }
    private Button button(LinearLayout parent, String title, int id, Runnable action) {
        Button view = new Button(this);
        view.setId(id); view.setText(title); view.setAllCaps(false); view.setTextSize(16);
        view.setTextColor(Color.WHITE); view.setMinHeight(dp(52));
        view.setPadding(dp(14), dp(8), dp(14), dp(8));
        GradientDrawable background = new GradientDrawable();
        background.setColor(Color.rgb(8, 117, 50)); background.setCornerRadius(dp(12));
        view.setBackground(background);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.topMargin = dp(10); parent.addView(view, params);
        view.setOnClickListener(v -> action.run());
        return view;
    }
    private void refresh() {
        if (busy || locationCallback != null) return;
        String permission = precise() ? "Precise location permission is allowed." : "Precise location permission is not yet allowed.";
        status.setText(permission + (enabled() ? " Phone Location is on." : " Phone Location is off."));
        enable.setText(precise() ? "Check location settings and open map" : "Enable precise location");
    }
    private void requestPrecise() {
        if (busy) return;
        stopDiagnostic();
        if (precise()) { checkSettings(); return; }
        busy = true;
        boolean asked = getPreferences(MODE_PRIVATE).getBoolean("asked_location", false);
        if (asked && !shouldShowRequestPermissionRationale(Manifest.permission.ACCESS_FINE_LOCATION)) {
            busy = false;
            new AlertDialog.Builder(this).setTitle("Allow precise location")
                .setMessage("Open FillMeNow permissions, choose Location → Allow while using the app, then turn on Use precise location. Manual search remains available.")
                .setPositiveButton("Open app settings", (d, w) -> openSettings(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getPackageName())))
                .setNegativeButton("Not now", null).show();
            return;
        }
        getPreferences(MODE_PRIVATE).edit().putBoolean("asked_location", true).apply();
        requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION}, PERMISSION);
    }
    @Override public void onRequestPermissionsResult(int request, String[] permissions, int[] grants) {
        super.onRequestPermissionsResult(request, permissions, grants);
        if (request != PERMISSION) return;
        busy = false;
        if (precise()) checkSettings();
        else status.setText("Precise location was not granted. You can use manual area search, or change FillMeNow's Location permission. No tracking has started.");
    }
    private void checkSettings() {
        if (!precise()) return;
        busy = true;
        if (!servicesAvailable()) {
            busy = false;
            if (enabled()) openMap();
            else openSettings(Settings.ACTION_LOCATION_SOURCE_SETTINGS, null);
            return;
        }
        LocationRequest request = new LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 1000L).build();
        LocationSettingsRequest needs = new LocationSettingsRequest.Builder().addLocationRequest(request).setAlwaysShow(true).build();
        LocationServices.getSettingsClient(this).checkLocationSettings(needs)
            .addOnSuccessListener(this, result -> { busy = false; openMap(); })
            .addOnFailureListener(this, error -> {
                if (error instanceof ResolvableApiException) {
                    try { ((ResolvableApiException)error).startResolutionForResult(this, SETTINGS); }
                    catch (android.content.IntentSender.SendIntentException ignored) { busy = false; openSettings(Settings.ACTION_LOCATION_SOURCE_SETTINGS, null); }
                } else {
                    busy = false;
                    status.setText("Android could not confirm the requested settings. Open Phone location settings, then retry. Manual search remains available.");
                }
            });
    }
    @Override public void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == SETTINGS) {
            busy = false;
            if (result == RESULT_OK && precise() && enabled()) openMap();
            else status.setText("Location setup was not completed. Nothing was enabled without your approval. Retry or open the map for manual search.");
        }
    }
    private void openSettings(String action, Uri uri) {
        try { startActivity(new Intent(action, uri)); }
        catch (android.content.ActivityNotFoundException e) { status.setText("This device cannot open that screen directly. Open phone Settings → Apps → FillMeNow → Permissions → Location."); }
    }
    private void openMap() {
        if (launching) return;
        launching = true; stopDiagnostic();
        try {
            // Fixed app-owned HTTPS URL is supplied by the manifest; incoming URL/extras are not forwarded.
            startActivity(new Intent(this, LauncherActivity.class));
            finish();
        } catch (RuntimeException e) {
            launching = false;
            status.setText("The map could not open. Install or update Chrome, then try again. Your settings have not been cleared.");
        }
    }
    private void testGps() {
        if (locationCallback != null) { stopDiagnostic(); refresh(); return; }
        if (!precise() || !enabled()) { status.setText("First allow precise location and turn on phone Location using the buttons above."); return; }
        if (!servicesAvailable()) { status.setText("This diagnostic uses Google Play services, which are unavailable. The delegated map can use Android's alternative provider; actual reception still needs checking."); return; }
        samples = 0; diagnostic.setText("Stop native GPS test");
        status.setText("Waiting for native GPS… Try outdoors while parked.");
        locationCallback = new LocationCallback() {
            @Override public void onLocationResult(LocationResult result) {
                if (locationCallback != this || isFinishing()) return;
                Location point = result.getLastLocation();
                if (point == null) return;
                long age = Math.max(0, (android.os.SystemClock.elapsedRealtimeNanos() - point.getElapsedRealtimeNanos()) / 1000000);
                if (age > 10000 || !point.hasAccuracy()) return;
                samples++;
                status.setText(String.format(Locale.US, "Native GPS: reported ±%.0f m · %d updates · %.1f seconds old. %s", point.getAccuracy(), samples, age / 1000.0,
                    point.getAccuracy() <= 50 ? "Precise enough for the app's follow threshold; not a lane-accuracy guarantee." : "Waiting for a more precise reading."));
            }
        };
        LocationRequest request = new LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 1000L)
            .setMinUpdateIntervalMillis(500L).setMinUpdateDistanceMeters(0).setMaxUpdateAgeMillis(0).build();
        try {
            LocationServices.getFusedLocationProviderClient(this).requestLocationUpdates(request, locationCallback, Looper.getMainLooper())
                .addOnFailureListener(this, e -> { stopDiagnostic(); status.setText("Native GPS could not start. Check permission and Location settings, then retry outdoors."); });
            handler.postDelayed(() -> { if (locationCallback != null) { stopDiagnostic(); status.append(" Test stopped after 30 seconds."); } }, 30000);
        } catch (SecurityException e) { stopDiagnostic(); refresh(); }
    }
    private void stopDiagnostic() {
        handler.removeCallbacksAndMessages(null);
        if (locationCallback != null) {
            LocationServices.getFusedLocationProviderClient(this).removeLocationUpdates(locationCallback);
            locationCallback = null;
        }
        if (diagnostic != null) diagnostic.setText("Test native GPS for 30 seconds");
    }
    @Override public void onResume() { super.onResume(); if (status != null) refresh(); }
    @Override public void onPause() { stopDiagnostic(); super.onPause(); }
    @Override public void onDestroy() { stopDiagnostic(); super.onDestroy(); }
}
