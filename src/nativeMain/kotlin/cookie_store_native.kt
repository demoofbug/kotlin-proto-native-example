@file:OptIn(ExperimentalNativeApi::class)

import com.getiox.cookie.Cookie
import com.getiox.cookie.CookieStore
import kotlinx.cinterop.*
import kotlin.experimental.ExperimentalNativeApi

/**
 * Write an error message string into the provided C char**.
 *
 * @param errMsg Pointer to a C char** for receiving the error message.
 * @param message The Kotlin string to encode and return.
 *
 * Memory:
 *   - Allocates native memory for the null-terminated string.
 *   - The caller must free it using `free_knative_pointer`.
 */
private fun setError(errMsg: CPointer<CPointerVar<ByteVar>>, message: String) {
    errMsg.pointed.value = message.encodeToByteArray().toNullTerminatedNativePointer()
}

/**
 * Convert a COpaquePointer to a CookieStore instance.
 *
 * @throws IllegalStateException if the pointer does not reference a CookieStore.
 */
private fun COpaquePointer.toCookieStore(): CookieStore =
    this.asStableRef<CookieStore>().get()


/**
 * Create a new CookieStore instance.
 *
 * @return A pointer to the new CookieStore (COpaquePointer).
 *
 * Memory:
 *   - Must be freed with `cookie_store_free` when no longer needed.
 */
@CName("cookie_store_new")
fun newCookieStore(): COpaquePointer {
    println("[kotlin-cookie_store_new] Creating new CookieStore instance")
    return StableRef.create(CookieStore()).asCPointer()
}

/**
 * Free a CookieStore instance created by `cookie_store_new`.
 *
 * @param ptr Pointer to the CookieStore to free.
 *
 * Note:
 *   - The pointer must not be used after this call.
 */
@CName("cookie_store_free")
fun freeCookieStore(ptr: COpaquePointer) {
    println("[kotlin-cookie_store_free] Freeing CookieStore instance")
    ptr.asStableRef<CookieStore>().dispose()
}

/**
 * Set (add or update) a cookie in the store.
 *
 * @param ptr        Pointer to CookieStore.
 * @param cookieData Pointer to serialized cookie bytes.
 * @param cookieLen  Length of the serialized data.
 * @param errMsg     Output char** for error message (set only on error).
 *
 * @return COOKIE_SUCCESS or COOKIE_EXCEPTION.
 *
 * Memory:
 *   - If errMsg is set, caller must free with `free_knative_pointer`.
 */
@CName("cookie_store_set")
fun setCookie(
    ptr: COpaquePointer,
    cookieData: CPointer<UByteVar>,
    cookieLen: Int,
    errMsg: CPointer<CPointerVar<ByteVar>>
): Int {
    println("[kotlin-cookie_store_set] Received cookie length=$cookieLen bytes")
    return try {
        val dstData = cookieData.toKByteArray(cookieLen)
        val cookie = Cookie.fromBytes(dstData)
        println("[kotlin-cookie_store_set] Parsed cookie: $cookie")

        ptr.toCookieStore().set(cookie)
        println("[kotlin-cookie_store_set] Cookie stored successfully")
        COOKIE_SUCCESS
    } catch (e: Exception) {
        val msg = "Exception in setCookie: ${e.message}"
        println("[kotlin-cookie_store_set] $msg")
        setError(errMsg, msg)
        COOKIE_EXCEPTION
    }
}

/**
 * Get cookies by domain.
 *
 * @param ptr     Pointer to CookieStore.
 * @param domain  Domain string (const char*).
 * @param outData Output unsigned char** for serialized cookies.
 * @param outLen  Output int* for length of serialized data.
 * @param errMsg  Output char** for error message.
 *
 * @return COOKIE_SUCCESS, COOKIE_NOT_FOUND, or COOKIE_EXCEPTION.
 *
 * Memory:
 *   - If outData is set, caller must free with `free_knative_pointer`.
 *   - If errMsg is set, caller must free with `free_knative_pointer`.
 */
@CName("cookie_store_get_by_domain")
fun getCookiesByDomain(
    ptr: COpaquePointer,
    domain: CPointer<ByteVar>,
    outData: CPointer<CPointerVar<UByteVar>>,
    outLen: CPointer<IntVar>,
    errMsg: CPointer<CPointerVar<ByteVar>>
): Int {
    val domainStr = domain.toKString()
    println("[kotlin-cookie_store_get_by_domain] Querying domain='$domainStr'")
    return try {
        val jar = ptr.toCookieStore().getByDomain(domainStr)
        println("[kotlin-cookie_store_get_by_domain] Found ${jar.cookies.size} cookies")

        if (jar.cookies.isEmpty()) {
            val msg = "No cookies found for domain: $domainStr"
            println("[kotlin-cookie_store_get_by_domain] $msg")
            setError(errMsg, msg)
            return COOKIE_NOT_FOUND
        }

        val bytes = jar.toBytes()
        outData.pointed.value = bytes.toUnsignedNativePointer()
        outLen.pointed.value = bytes.size
        println("[kotlin-cookie_store_get_by_domain] Returning ${bytes.size} bytes")
        COOKIE_SUCCESS
    } catch (e: Exception) {
        val msg = "Exception in getCookiesByDomain: ${e.message}"
        println("[kotlin-cookie_store_get_by_domain] $msg")
        setError(errMsg, msg)
        COOKIE_EXCEPTION
    }
}

/**
 * Remove a cookie by name and domain.
 *
 * @param ptr    Pointer to CookieStore.
 * @param name   Cookie name (const char*).
 * @param domain Domain name (const char*).
 * @param errMsg Output char** for error message.
 *
 * @return COOKIE_SUCCESS or COOKIE_EXCEPTION.
 */
@CName("cookie_store_remove")
fun removeCookie(
    ptr: COpaquePointer,
    name: CPointer<ByteVar>,
    domain: CPointer<ByteVar>,
    errMsg: CPointer<CPointerVar<ByteVar>>
): Int {
    val nameStr = name.toKString()
    val domainStr = domain.toKString()
    println("[kotlin-cookie_store_remove] Removing cookie name='$nameStr' domain='$domainStr'")
    return try {
        ptr.toCookieStore().remove(nameStr, domainStr)
        println("[kotlin-cookie_store_remove] Cookie removed successfully")
        COOKIE_SUCCESS
    } catch (e: Exception) {
        val msg = "Exception in removeCookie: ${e.message}"
        println("[kotlin-cookie_store_remove] $msg")
        setError(errMsg, msg)
        COOKIE_EXCEPTION
    }
}

/**
 * Get all cookies in the store.
 *
 * @param ptr     Pointer to CookieStore.
 * @param outData Output unsigned char** for serialized cookies.
 * @param outLen  Output int* for length of serialized data.
 * @param errMsg  Output char** for error message.
 *
 * @return COOKIE_SUCCESS, COOKIE_NOT_FOUND, or COOKIE_EXCEPTION.
 *
 * Memory:
 *   - If outData is set, caller must free with `free_knative_pointer`.
 *   - If errMsg is set, caller must free with `free_knative_pointer`.
 */
@CName("cookie_store_get_all")
fun getAllCookies(
    ptr: COpaquePointer,
    outData: CPointer<CPointerVar<UByteVar>>,
    outLen: CPointer<IntVar>,
    errMsg: CPointer<CPointerVar<ByteVar>>
): Int {
    println("[kotlin-cookie_store_get_all] Fetching all cookies")
    return try {
        val jar = ptr.toCookieStore().getAll()
        println("[kotlin-cookie_store_get_all] Found ${jar.cookies.size} cookies")

        if (jar.cookies.isEmpty()) {
            val msg = "No cookies found"
            println("[kotlin-cookie_store_get_all] $msg")
            setError(errMsg, msg)
            return COOKIE_NOT_FOUND
        }

        val bytes = jar.toBytes()
        outData.pointed.value = bytes.toUnsignedNativePointer()
        outLen.pointed.value = bytes.size
        println("[kotlin-cookie_store_get_all] Returning ${bytes.size} bytes")
        COOKIE_SUCCESS
    } catch (e: Exception) {
        val msg = "Exception in getAllCookies: ${e.message}"
        println("[kotlin-cookie_store_get_all] $msg")
        setError(errMsg, msg)
        COOKIE_EXCEPTION
    }
}

/**
 * Clear all cookies in the store.
 *
 * @param ptr    Pointer to CookieStore.
 * @param errMsg Output char** for error message.
 *
 * @return COOKIE_SUCCESS or COOKIE_EXCEPTION.
 */
@CName("cookie_store_clear_all")
fun clearAllCookies(
    ptr: COpaquePointer,
    errMsg: CPointer<CPointerVar<ByteVar>>
): Int {
    println("[kotlin-cookie_store_clear_all] Clearing all cookies")
    return try {
        ptr.toCookieStore().clear()
        println("[kotlin-cookie_store_clear_all] All cookies cleared")
        COOKIE_SUCCESS
    } catch (e: Exception) {
        val msg = "Exception in clearAllCookies: ${e.message}"
        println("[kotlin-cookie_store_clear_all] $msg")
        setError(errMsg, msg)
        COOKIE_EXCEPTION
    }
}

/**
 * Free native memory allocated for cookie data or error messages.
 *
 * @param ptr Pointer to memory previously returned from a cookie_* function.
 *
 * Usage:
 *   - Used to free buffers returned by getCookiesByDomain / getAllCookies.
 *   - Used to free error message strings.
 */
@CName("free_knative_pointer")
fun freeKNativePointer(ptr: COpaquePointer?) {
    if (ptr == null) {
        println("[kotlin-free_knative_pointer] Null pointer, nothing to free")
        return
    }
    println("[kotlin-free_knative_pointer] Freeing native memory at address=$ptr")
    nativeHeap.free(ptr)
}

