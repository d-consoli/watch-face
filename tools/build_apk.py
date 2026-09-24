"""Fast, offline, resource-only APK build with official Android SDK tools.

Python 3.10+, JDK 17+, Android platform 36 and Build Tools 36.0.0.
No third-party Python dependencies. Generated output and debug key stay untracked.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "io.github.dconsoli.modular"
ANDROID = "{http://schemas.android.com/apk/res/android}"


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def find_sdk():
    candidates = [os.getenv("ANDROID_HOME"), os.getenv("ANDROID_SDK_ROOT")]
    local = ROOT / "local.properties"
    if local.exists():
        for line in local.read_text().splitlines():
            if line.startswith("sdk.dir="):
                candidates.append(line.split("=", 1)[1].replace("\\:", ":").replace("\\\\", "\\"))
    candidates.extend([str(Path.home()/"AppData/Local/Android/Sdk"),
                       str(Path.home()/"Android/Sdk"), str(Path.home()/"Library/Android/sdk")])
    for path in candidates:
        if path and (Path(path)/"platforms/android-36/android.jar").is_file(): return Path(path)
    raise SystemExit("Set ANDROID_HOME to an Android SDK containing platforms;android-36.")


def java_tool(name):
    suffix = ".exe" if os.name == "nt" else ""
    if os.getenv("JAVA_HOME"):
        tool = Path(os.environ["JAVA_HOME"])/"bin"/(name+suffix)
        if tool.is_file(): return str(tool)
    tool = shutil.which(name)
    if tool: return tool
    raise SystemExit(f"Missing {name}; install JDK 17+ and set JAVA_HOME.")


def build():
    sdk = find_sdk()
    bt = sdk / "build-tools/36.0.0"
    suffix = ".exe" if os.name == "nt" else ""
    aapt = bt/("aapt2"+suffix)
    align = bt/("zipalign"+suffix)
    signer = bt/"lib/apksigner.jar"
    for path in (aapt, align, signer):
        if not path.is_file(): raise SystemExit(f"Missing {path}; install build-tools;36.0.0.")
    out = ROOT / "build/fast"
    out.mkdir(parents=True, exist_ok=True)
    # Work on a copy: Gradle adds these attributes itself to the source manifest.
    E.register_namespace("android", ANDROID[1:-1])
    manifest = E.parse(ROOT/"watchface/src/main/AndroidManifest.xml")
    manifest.getroot().set("package", PACKAGE)
    manifest.getroot().set(ANDROID+"versionCode", "1")
    manifest.getroot().set(ANDROID+"versionName", "0.1.0")
    manifest.find("application").set(ANDROID+"debuggable", "true")
    manifest.write(out/"AndroidManifest.xml", encoding="utf-8", xml_declaration=True)
    run(aapt, "compile", "--dir", ROOT/"watchface/src/main/res", "-o", out/"resources.zip")
    run(aapt, "link", "-o", out/"unsigned.apk", "--manifest", out/"AndroidManifest.xml",
        "-I", sdk/"platforms/android-36/android.jar", "--min-sdk-version", "34",
        "--target-sdk-version", "36", out/"resources.zip")
    run(align, "-f", "-p", "4", out/"unsigned.apk", out/"aligned.apk")
    # Same standard debug identity as Android Studio/Gradle on this machine.
    key = Path.home()/".android/debug.keystore"
    if not key.exists():
        key.parent.mkdir(parents=True, exist_ok=True)
        run(java_tool("keytool"), "-genkeypair", "-keystore", key, "-storepass", "android",
            "-keypass", "android", "-alias", "androiddebugkey", "-dname", "CN=Android Debug,O=Android,C=US",
            "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000")
    apk = out/"modular-lab-debug.apk"
    run(java_tool("java"), "-jar", signer, "sign", "--ks", key, "--ks-key-alias", "androiddebugkey",
        "--ks-pass", "pass:android", "--key-pass", "pass:android", "--out", apk, out/"aligned.apk")
    run(java_tool("java"), "-jar", signer, "verify", "--verbose", apk)
    print(f"\nAPK: {apk}")
    return apk, sdk


def select_watch(sdk, serial):
    adb = sdk/"platform-tools"/("adb.exe" if os.name == "nt" else "adb")
    if not serial:
        listing = subprocess.check_output([str(adb), "devices"], text=True)
        devices = [line.split()[0] for line in listing.splitlines() if line.endswith("\tdevice")]
        if len(devices) != 1:
            raise SystemExit("Connect one watch/emulator, or pass --serial from 'adb devices'.")
        serial = devices[0]
    prefix = [str(adb), "-s", serial]
    characteristics = subprocess.check_output(prefix+["shell", "getprop", "ro.build.characteristics"], text=True)
    if "watch" not in characteristics:
        raise SystemExit(f"{serial} is not reporting a Wear OS watch; installation stopped.")
    return prefix


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Update one connected Wear OS target")
    parser.add_argument("--serial", help="adb device ID, e.g. emulator-5554 or watch IP:connection-port")
    args = parser.parse_args()
    apk, sdk = build()
    if args.install:
        run(*select_watch(sdk, args.serial), "install", "-r", apk)
        print("Installed. On the watch: long-press face > Add watch face > Modular Lab.")
