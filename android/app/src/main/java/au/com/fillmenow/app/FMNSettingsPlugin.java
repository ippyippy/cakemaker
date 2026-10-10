package au.com.fillmenow.app;
import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.LocationManager;
import android.net.Uri;
import android.provider.Settings;
import androidx.core.content.ContextCompat;
import androidx.core.location.LocationManagerCompat;
import com.getcapacitor.*;
import com.getcapacitor.annotation.CapacitorPlugin;
@CapacitorPlugin(name="FMNSettings")
public final class FMNSettingsPlugin extends Plugin {
 @PluginMethod public void status(PluginCall c){JSObject r=new JSObject();r.put("fine",ContextCompat.checkSelfPermission(getContext(),Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED);r.put("coarse",ContextCompat.checkSelfPermission(getContext(),Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED);LocationManager m=(LocationManager)getContext().getSystemService(android.content.Context.LOCATION_SERVICE);r.put("enabled",m!=null&&LocationManagerCompat.isLocationEnabled(m));c.resolve(r);}
 @PluginMethod public void ensureEnabled(PluginCall c){getActivity().runOnUiThread(()->((MainActivity)getActivity()).ensureLocation(c));}
 @PluginMethod public void openAppSettings(PluginCall c){open(c,new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,Uri.parse("package:"+getContext().getPackageName())));}
 @PluginMethod public void openLocationSettings(PluginCall c){open(c,new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS));}
 @PluginMethod public void openExternal(PluginCall c){String value=c.getString("url","");Uri u=Uri.parse(value);if(!"https".equals(u.getScheme())&&!"tel".equals(u.getScheme())){c.reject("Unsupported external link");return;}open(c,new Intent(Intent.ACTION_VIEW,u));}
 private void open(PluginCall c,Intent i){getActivity().runOnUiThread(()->{try{getActivity().startActivity(i);c.resolve();}catch(Exception e){c.reject("This settings screen or link is unavailable");}});}
}
