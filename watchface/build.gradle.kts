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
        versionCode = 1
        versionName = "0.1.0"
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            isShrinkResources = false // WFF references resources from raw XML.
        }
    }
}
