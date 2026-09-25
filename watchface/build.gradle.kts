plugins { id("com.android.application") }

android {
    enableKotlin = false
    namespace = "io.github.dconsoli.modular"
    compileSdk = 36
    buildToolsVersion = "36.0.0"

    defaultConfig {
        applicationId = "io.github.dconsoli.modular"
        minSdk = 34 // WFF 2: Wear OS 5+, including Pixel Watch 4.
        targetSdk = 36
        versionCode = 3
        versionName = "0.3.0"
    }
    buildTypes {
        debug {
            // Strip AGP-generated resource classes as well: a WFF APK must contain no DEX.
            isMinifyEnabled = true
            isShrinkResources = false
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = false // WFF references resources from raw XML.
        }
    }
}
