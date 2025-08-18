# CookieStore Kotlin/Native Project

## Overview

This project demonstrates an **in-memory cookie management system** implemented in Kotlin/Native.
It exposes **C-compatible functions** and leverages **Protocol Buffers (Protobuf)** for cross-language data serialization.
All C API functions that return data or error messages allocate memory on the native heap and **must be freed with `free_knative_pointer`**.
Sample clients in **C** and **Python** showcase practical usage and interoperability.

## Features

* In-memory cookie storage implemented in Kotlin.
* Protobuf-based serialization/deserialization of cookies and cookie jars.
* C-compatible API exposed via `@CName` functions.
* Logging of all operations using `println`.
* Query, insert, remove, and clear cookies through the C API.


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

## Data Structures

### Cookie

Represents a single HTTP cookie:

```kotlin
@Serializable
@OptIn(ExperimentalSerializationApi::class)
internal data class Cookie(
    @ProtoNumber(1) val name: String = "",
    @ProtoNumber(2) val value: String = "",
    @ProtoNumber(3) val domain: String = "",
    @ProtoNumber(4) val path: String = "",
    @ProtoNumber(5) val secure: Boolean = false,
    @ProtoNumber(6) val httpOnly: Boolean = false,
    @ProtoNumber(7) val expirationTime: Long = 0,
)
```

### CookieJar

Represents a collection of cookies:

```kotlin
@Serializable
@OptIn(ExperimentalSerializationApi::class)
internal data class CookieJar(
    @ProtoNumber(1) val cookies: List<Cookie> = listOf()
) 
```

## C-Compatible API

### Functions

> ⚠️ Note: The C header files in `include/` are **manually written** to match the exported Kotlin/Native functions.

The library exposes the following C API for native consumption:

| Function                       | Description                                                                                  |
| ------------------------------- | -------------------------------------------------------------------------------------------- |
| `cookie_store_new`              | Create a new `CookieStore` instance. Must be freed with `cookie_store_free`.                 |
| `cookie_store_free`             | Free a `CookieStore` instance created by `cookie_store_new`.                                 |
| `cookie_store_set`              | Insert or update a cookie from serialized ProtoBuf bytes.                                    |
| `cookie_store_get_by_domain`    | Get cookies by domain. Returns serialized ProtoBuf data.                                     |
| `cookie_store_remove`           | Remove a cookie by name and domain.                                                          |
| `cookie_store_get_all`          | Get all cookies in the store. Returns serialized ProtoBuf data.                              |
| `cookie_store_clear_all`        | Remove all cookies from memory.                                                              |
| `free_knative_pointer`          | Free memory allocated by any of the above functions (buffers or error messages).            |

---

### Memory Handling

- All functions that return serialized data (`unsigned char** outData`) or error messages (`char** errMsg`) allocate memory on the native heap.
- **Caller must free memory** using:

```c
free_knative_pointer(ptr);
```
This applies to:
   - cookie_store_get_by_domain  
   - cookie_store_get_all 
   - Error message strings (char** errMsg) returned by any function

### Example Usage (C)
> ⚠️ Always free both returned buffers and error messages with `free_knative_pointer`.
```c
unsigned char* data;
int len;
char* err;
int ret = cookie_store_get_by_domain(store, "example.com", &data, &len, &err);
if (ret == COOKIE_SUCCESS) {
    // Process ProtoBuf data...
    free_knative_pointer(data);
} else {
    printf("Error: %s\n", err);
    free_knative_pointer(err);
}   
``` 
### Error Codes

| Code                     | Meaning                           |
| ------------------------ | --------------------------------- |
| COOKIE_SUCCESS            | Operation successful              |
| COOKIE_NOT_FOUND          | No matching cookie found          |
| COOKIE_ALLOCATION_FAILED  | Memory allocation failed          |
| COOKIE_EXCEPTION          | Unexpected exception occurred     |


### Type Definitions

- `cookie_store_t`: Opaque pointer representing a `CookieStore` instance.
    - Must be created with `cookie_store_new` and freed with `cookie_store_free`.
    - Do not access the internal structure directly; use API functions only.
> ⚠️ Do not cast or dereference this pointer. Always use API functions.


## Build & Run

### Prerequisites

* Kotlin/Native + Gradle + JDK 17
* CMake 4.1.0 (for C demo)
* Python 3.12.8 with `protobuf 3.20.1` package

### Steps

> ⚠️ Note: Protobuf files have already been generated. No need to run `protoc` again.

#### 1. Build Kotlin/Native dynamic library

- **Linux (x64):**. 
```bash
  ./gradlew linkReleaseSharedLinuxX64
```
- **Linux (ARM64):**
```bash
  ./gradlew linkReleaseSharedLinuxArm64
```

- **macOS (Intel):**
```bash
  ./gradlew linkReleaseSharedMacosX64
```

- **macOS (Apple Silicon):**
```bash
  ./gradlew linkReleaseSharedMacosArm64
```
- **Windows (x64):**
```bash
  ./gradlew linkReleaseSharedMingwX64
```

The resulting `.so` / `.dylib` / `.dll` will be located under:
```bash
   build/bin/<target>/releaseShared/
```
Where `<target>` is one of: `linuxX64`, `linuxArm64`, `macosX64`, `macosArm64`, `mingwX64`.


#### 2. Run C demo 
> Make sure the dynamic library from `build/bin/<target>/releaseShared/` is in your library path.
```bash
cd bindings/c
mkdir build && cd build
cmake ..
make
./cookie_store_demo   # runs the C demo program
```

#### 3. Run Python demo
> Make sure the dynamic library from `build/bin/<target>/releaseShared/` is in your library path.
```bash
cd bindings/python
python3 cookie_store_demo.py
```

## Cross-Language Bindings

This project includes sample bindings for multiple languages (currently C and Python). The structure allows easy extension to others:

| Language | Directory Path    | Description                           |
| -------- | ----------------- | ------------------------------------- |
| C        | `bindings/c`      | Example C client with CMake build.    |
| Python   | `bindings/python` | Example Python client using Protobuf. |

Planned (not yet implemented): Go, Rust, C++.

## Notes

* Protobuf introduces at least one memory copy between Kotlin and C memory.
* Direct C structs would be faster but less portable.
* This project is for demonstration purposes; production use requires extra safety and error handling.
