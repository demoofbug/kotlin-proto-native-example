pluginManagement {
    repositories {
        //maven("https://maven.aliyun.com/repository/public")
        gradlePluginPortal()
        google()
        mavenCentral()
    }
}
plugins {
    id("org.gradle.toolchains.foojay-resolver-convention") version ("0.8.0")
}

dependencyResolutionManagement {
    repositories {
       // maven("https://maven.aliyun.com/repository/public")
        mavenCentral()
        google()
    }
}

rootProject.name = "kotlin-proto-native-example"