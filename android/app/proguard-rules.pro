-keep class au.com.fillmenow.app.MainActivity { *; }
-keep class au.com.fillmenow.app.FMNSettingsPlugin { *; }
-keep class com.getcapacitor.** { *; }
-keep @com.getcapacitor.annotation.CapacitorPlugin class * { *; }
-keepclassmembers class * { @com.getcapacitor.PluginMethod <methods>; }
# The separate instrumentation APK calls these shared dependency APIs. Preserve them in the actual delivered release too.
-keep class androidx.** { *; }
-keep class kotlin.** { *; }
