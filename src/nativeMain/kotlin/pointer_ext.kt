import kotlinx.cinterop.*
import platform.posix.memcpy

/**
 * Converts a Kotlin ByteArray to a null-terminated C-style byte array pointer.
 *
 * This is suitable for text data that needs to be passed to C functions expecting
 * null-terminated strings.
 *
 * Memory layout:
 * ```c
 * uint8_t* ptr = (uint8_t*)malloc(size + 1);
 * memcpy(ptr, data, size);
 * ptr[size] = 0; // Explicit null termination
 * ```
 *
 * @receiver The source ByteArray (text data)
 * @return Non-null pointer to native memory
 * @throws OutOfMemoryError If allocation fails
 * @note Caller MUST free memory using nativeHeap.free()
 */
@Throws(OutOfMemoryError::class)
internal fun ByteArray.toNullTerminatedNativePointer(): CPointer<ByteVar> {
    val ptr = nativeHeap.allocArray<ByteVar>(size + 1)
    usePinned { pinned ->
        memcpy(ptr, pinned.addressOf(0), size.convert())
    }
    ptr[size] = 0
    return ptr
}

/**
 * Converts a Kotlin ByteArray to a C-style unsigned byte array pointer.
 *
 * This is suitable for binary data like protobuf serialization.
 *
 * Memory layout:
 * ```c
 * uint8_t* ptr = (uint8_t*)malloc(size);
 * memcpy(ptr, data, size);
 * ```
 *
 * @receiver The source ByteArray (binary data)
 * @return Non-null pointer to native memory
 * @throws OutOfMemoryError If allocation fails
 * @note Caller MUST free memory using nativeHeap.free()
 */
@Throws(OutOfMemoryError::class)
internal fun ByteArray.toUnsignedNativePointer(): CPointer<UByteVar> {
    val ptr = nativeHeap.allocArray<UByteVar>(size)
    usePinned { pinned ->
        memcpy(ptr, pinned.addressOf(0), size.convert())
    }
    return ptr
}


/**
 * Converts a C-style pointer to a Kotlin ByteArray.
 *
 * Equivalent C code:
 * ```c
 * unsigned char result[size];
 * memcpy(result, ptr, size);
 * ```
 *
 * @receiver CPointer<ByteVar> The source C pointer.
 * @param size Int Number of bytes to copy.
 * @return ByteArray The resulting Kotlin byte array.
 */
internal fun CPointer<ByteVar>.toKByteArray(size: Int): ByteArray {
    return ByteArray(size).apply {
        usePinned { pinned ->
            memcpy(pinned.addressOf(0), this@toKByteArray, size.convert())
        }
    }
}

internal fun CPointer<UByteVar>.toKByteArray(size: Int): ByteArray {
    return ByteArray(size).apply {
        usePinned { pinned ->
            memcpy(
                pinned.addressOf(0),
                this@toKByteArray.reinterpret<ByteVar>(),
                size.convert()
            )
        }
    }
}