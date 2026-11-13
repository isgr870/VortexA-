# Mobile packaging

## Goal
One-tap APK / IPA for Vortexa UI. Full offline Python bridge on mobile still needs an
embedded runtime (Chaquopy / Pyodide / companion service). That is phased work.

## Near-term Android (Capacitor WebView + Termux bridge)
```bash
npm create @capacitor/app vortexa-cap -- --template=blank
cd vortexa-cap
# copy index.html, vendor, assets into dist/
npx cap add android
npx cap sync android
cd android && ./gradlew assembleDebug
# APK: android/app/build/outputs/apk/debug/app-debug.apk
```

Point the WebView at http://127.0.0.1:8080 when Termux runs texup, or ship static
assets offline (compute via desktop bridge).

## iOS
Requires Apple Developer account and macOS.
```bash
npx cap add ios
npx cap sync ios
# Xcode -> Archive
```
