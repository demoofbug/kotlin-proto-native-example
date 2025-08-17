#ifndef COOKIE_STORE_H
#define COOKIE_STORE_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h> // for size_t

// ============================================================
// Error Codes
// ============================================================
#define COOKIE_SUCCESS              0   // Operation successful
#define COOKIE_NOT_FOUND            1   // No matching cookie found
#define COOKIE_ALLOCATION_FAILED    2   // Memory allocation failed
#define COOKIE_EXCEPTION           -1   // Unexpected exception

// ============================================================
// Type Definitions
// ============================================================

// Opaque pointer type representing a CookieStore instance.
// This is returned by cookie_store_new and used in all store functions.
typedef void* cookie_store_t;

// ============================================================
// API Functions
// ============================================================

/**
 * Create a new CookieStore instance.
 *
 * @return A pointer to the new CookieStore.
 *
 * Memory:
 *   - Must be freed with cookie_store_free() when no longer needed.
 */
cookie_store_t cookie_store_new(void);

/**
 * Free a CookieStore instance created by cookie_store_new().
 *
 * @param store Pointer to the CookieStore to free.
 *
 * Note:
 *   - The pointer must not be used after this call.
 */
void cookie_store_free(cookie_store_t store);

/**
 * Set (add or update) a cookie in the store.
 *
 * @param store      Pointer to CookieStore.
 * @param cookieData Pointer to serialized cookie bytes.
 * @param cookieLen  Length of the serialized data.
 * @param errMsg     Output parameter for error message string (set only on error).
 *                   Caller must free with free_knative_pointer().
 *
 * @return COOKIE_SUCCESS or COOKIE_EXCEPTION.
 */
int cookie_store_set(
    cookie_store_t store,
    const unsigned char* cookieData,
    int cookieLen,
    char** errMsg
);

/**
 * Get cookies by domain.
 *
 * @param store   Pointer to CookieStore.
 * @param domain  Domain string (null-terminated).
 * @param outData Output parameter for serialized cookies (unsigned char*).
 *                Caller must free with free_knative_pointer().
 * @param outLen  Output parameter for length of serialized data.
 * @param errMsg  Output parameter for error message (char*).
 *                Caller must free with free_knative_pointer().
 *
 * @return COOKIE_SUCCESS, COOKIE_NOT_FOUND, or COOKIE_EXCEPTION.
 */
int cookie_store_get_by_domain(
    cookie_store_t store,
    const char* domain,
    unsigned char** outData,
    int* outLen,
    char** errMsg
);

/**
 * Remove a cookie by name and domain.
 *
 * @param store  Pointer to CookieStore.
 * @param name   Cookie name (null-terminated).
 * @param domain Domain name (null-terminated).
 * @param errMsg Output parameter for error message (char*).
 *               Caller must free with free_knative_pointer().
 *
 * @return COOKIE_SUCCESS or COOKIE_EXCEPTION.
 */
int cookie_store_remove(
    cookie_store_t store,
    const char* name,
    const char* domain,
    char** errMsg
);

/**
 * Get all cookies in the store.
 *
 * @param store   Pointer to CookieStore.
 * @param outData Output parameter for serialized cookies (unsigned char*).
 *                Caller must free with free_knative_pointer().
 * @param outLen  Output parameter for length of serialized data.
 * @param errMsg  Output parameter for error message (char*).
 *                Caller must free with free_knative_pointer().
 *
 * @return COOKIE_SUCCESS, COOKIE_NOT_FOUND, or COOKIE_EXCEPTION.
 */
int cookie_store_get_all(
    cookie_store_t store,
    unsigned char** outData,
    int* outLen,
    char** errMsg
);

/**
 * Clear all cookies in the store.
 *
 * @param store  Pointer to CookieStore.
 * @param errMsg Output parameter for error message (char*).
 *               Caller must free with free_knative_pointer().
 *
 * @return COOKIE_SUCCESS or COOKIE_EXCEPTION.
 */
int cookie_store_clear_all(
    cookie_store_t store,
    char** errMsg
);

/**
 * Free native memory allocated by cookie_store_* functions.
 *
 * @param ptr Pointer to memory previously returned from a cookie_* function.
 *
 * Usage:
 *   - Used to free buffers returned by getCookiesByDomain / getAllCookies.
 *   - Used to free error message strings.
 */
void free_knative_pointer(void* ptr);

#ifdef __cplusplus
}
#endif

#endif // COOKIE_STORE_H