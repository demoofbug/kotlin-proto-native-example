package com.getiox.cookie

internal class CookieStore {

    // Use name@domain as the unique key
    private val store: MutableMap<String, Cookie> = mutableMapOf()

    /** Add or update a cookie */
    fun set(cookie: Cookie) {
        store[key(cookie.name, cookie.domain)] = cookie
    }

    /** Remove a specific cookie */
    fun remove(cookie: Cookie) {
        store.remove(key(cookie.name, cookie.domain))
    }

    /** Remove a cookie by name and domain */
    fun remove(name: String, domain: String) {
        store.remove(key(name, domain))
    }

    /** Get a specific cookie */
    fun get(name: String, domain: String): Cookie? {
        return store[key(name, domain)]
    }

    /** Get all cookies */
    fun getAll(): CookieJar {
        return CookieJar(store.values.toList())
    }

    /** Get all cookies by domain */
    fun getByDomain(domain: String): CookieJar {
        return CookieJar(store.values.filter { it.domain == domain })
    }

    /** Remove all cookies */
    fun clear() {
        store.clear()
    }

    /** Build the unique key */
    private fun key(name: String, domain: String) = "$name@$domain"
}