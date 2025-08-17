plugins {
    alias(libs.plugins.kotlin.multiplatform)
    alias(libs.plugins.kotlin.serialization)
}

kotlin {
    jvmToolchain(17)
}

kotlin {
    val nativeTargets = listOf(macosX64(),macosArm64(),linuxArm64(), linuxX64(), mingwX64())

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation("org.jetbrains.kotlinx:kotlinx-serialization-protobuf:1.9.0")
            }
        }
        val nativeMain by creating {
            dependsOn(commonMain)
            dependencies {
                api(libs.kotlin.stdlib)
            }
        }
        nativeTargets.forEach {
            it.compilations["main"].defaultSourceSet {
                dependsOn(nativeMain)
            }
        }
    }

    nativeTargets.forEach {
        it.binaries {
            sharedLib {
                baseName = "kcookie_store"
            }
        }
    }
}

kotlin.sourceSets.all {
    languageSettings.optIn("kotlinx.cinterop.ExperimentalForeignApi")
}