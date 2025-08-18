# Kotlin/Native Dynamic Library: Cookie Store Demo

## Overview

This project demonstrates **how to build a Kotlin/Native dynamic library**.
The example implements an in-memory **cookie store**, showcasing safe memory management and cross-language data exchange with **C** and **Python**.

## Features

* **C ABI Export**: Kotlin functions exposed via `@CName` + manual header (`include/cookie_store.h`)
* **Memory Safety**: Kotlin-allocated resources must be released using `free_knative_pointer`
* **Protobuf Serialization**: Shared `.proto` schema for language bindings and data exchange
* **Example Clients**: Ready-to-run demo clients in **C** and **Python**

## Project Structure

```
├── src
│   ├── commonMain/kotlin            # Common code
│   └── nativeMain/kotlin            # Kotlin/Native implementation
│       ├── cookie_store_native.kt   # Native API implementation
│       ├── cookie_error_codes.kt    # Error codes
│       └── pointer_ext.kt           # Pointer helpers
├── include/cookie_store.h           # Manually written C header matching Kotlin/Native interface
├── proto/cookie_store.proto         # Protobuf schema
├── bindings/c                       # C demo client
├── bindings/python                  # Python demo client
├── build.gradle.kts                 # Gradle build config
└── README.md                        # Project documentation
```

## C-Compatible API

> ⚠️ Note: All API functions that return buffers or error messages allocate memory on the native heap. **Always release with `free_knative_pointer`.**

| Function                     | Description                                                                  |
| ---------------------------- | ---------------------------------------------------------------------------- |
| `cookie_store_new`           | Create a new `CookieStore` instance. Must be freed with `cookie_store_free`. |
| `cookie_store_free`          | Free a `CookieStore` instance created by `cookie_store_new`.                 |
| `cookie_store_set`           | Insert or update a cookie from serialized ProtoBuf bytes.                    |
| `cookie_store_get_by_domain` | Get cookies by domain. Returns serialized ProtoBuf data.                     |
| `cookie_store_remove`        | Remove a cookie by name and domain.                                          |
| `cookie_store_get_all`       | Get all cookies in the store. Returns serialized ProtoBuf data.              |
| `cookie_store_clear_all`     | Remove all cookies from memory.                                              |
| `free_knative_pointer`       | Free memory allocated by the above functions (buffers or error messages).    |

### Memory Handling

```c
// Kotlin-allocated resources MUST be released via:
free_knative_pointer(ptr);
// Never use system free() directly
```

Applies to:

* Protobuf data buffers (`unsigned char** outData`)
* Error message strings (`char** errMsg`)

### Error Codes

| Code                       | Meaning                       |
| -------------------------- | ----------------------------- |
| COOKIE\_SUCCESS            | Operation successful          |
| COOKIE\_NOT\_FOUND         | No matching cookie found      |
| COOKIE\_ALLOCATION\_FAILED | Memory allocation failed      |
| COOKIE\_EXCEPTION          | Unexpected exception occurred |

## Build & Run

### Prerequisites

* Kotlin/Native + Gradle + JDK 17
* CMake 4.1.0+ (for C demo)
* Python 3.12.8 with `protobuf 3.20.1`

### Steps

> ⚠️ Note: Protobuf files are already generated. No need to run `protoc`.

#### 1. Build Kotlin/Native dynamic library

* **Linux (x64):**

```bash
  ./gradlew linkReleaseSharedLinuxX64
```

* **Linux (ARM64):**

```bash
  ./gradlew linkReleaseSharedLinuxArm64
```

* **macOS (Intel):**

```bash
  ./gradlew linkReleaseSharedMacosX64
```

* **macOS (Apple Silicon):**

```bash
  ./gradlew linkReleaseSharedMacosArm64
```

* **Windows (x64):**

```bash
  ./gradlew linkReleaseSharedMingwX64
```

The resulting `.so` / `.dylib` / `.dll` will be under:

```
build/bin/<target>/releaseShared/
```

Where `<target>` ∈ { `linuxX64`, `linuxArm64`, `macosX64`, `macosArm64`, `mingwX64` }.

#### 2. Run C demo

```bash
cd bindings/c
mkdir build && cd build
cmake ..
make
./cookie_store_demo
```

#### 3. Run Python demo

```bash
cd bindings/python
python3 cookie_store_demo.py
```

## Notes

* Protobuf introduces at least one memory copy between Kotlin and C.
* Direct C structs would be faster but less portable.
* This project is for **demonstration only** — production use requires additional safety and error handling.
