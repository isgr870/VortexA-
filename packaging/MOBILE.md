# Vortexa mobile packaging (GitHub Actions)

## Architecture
Phone/desktop apps are a **WebView shell** around the existing UI, plus a local
Python bridge (`server.py`) where the platform allows it.

| Target | Strategy |
|--------|----------|
| Web / PWA | `index.html` + `manifest.webmanifest` + `sw.js` (this repo) |
| Android APK | Capacitor WebView → load UI; bridge via localhost or embedded termux-like service later |
| iOS | Capacitor on **macOS** runner (Apple certs required for device install) |
| Windows EXE | PyInstaller workflow `build-desktop.yml` |
| Linux | Same PyInstaller workflow |

## Android (Capacitor) — run on GitHub or locally
```bash
npm create capacitor@latest vortexa-app -- --template=blank-typescript
# copy dist-web into capacitor www/
npx cap add android
npx cap sync android
npx cap open android   # or ./gradlew assembleDebug
```
GitHub: use `macos-latest` / `ubuntu-latest` with Android SDK for debug APK artifacts.
Signing a Play release needs your keystore (GitHub Secrets).

## iOS
Requires Apple Developer account + certificates.
```bash
npx cap add ios
npx cap sync ios
# Xcode archive on macOS runner
```

## Reality check
- Full offline robotics bridge inside APK/iOS needs an embedded Python runtime
  (e.g. Chaquopy on Android) or a companion Termux session — not a single click yet.
- Near-term investor demo: **desktop EXE/Linux bundle** + **phone browser to Termux** + **PWA icon**.
