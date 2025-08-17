package com.getiox.cookie

import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.Serializable
import kotlinx.serialization.decodeFromByteArray
import kotlinx.serialization.encodeToByteArray
import kotlinx.serialization.protobuf.ProtoBuf
import kotlinx.serialization.protobuf.ProtoNumber

/**
 * Represents a single HTTP cookie.
 * Serialized using kotlinx.serialization with ProtoBuf format.
 */
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
) {
    /** Serialize this Cookie to ProtoBuf binary format */
    fun toBytes(): ByteArray = ProtoBuf.encodeToByteArray(this)

    companion object {
        /** Deserialize a Cookie from ProtoBuf binary format */
        fun fromBytes(bytes: ByteArray): Cookie =
            ProtoBuf.decodeFromByteArray(bytes)
    }

    override fun toString(): String = buildString {
        appendLine("Cookie(")
        appendLine("  name = '$name',")
        appendLine("  value = '$value',")
        appendLine("  domain = '$domain',")
        appendLine("  path = '$path',")
        appendLine("  secure = $secure,")
        appendLine("  httpOnly = $httpOnly,")
        appendLine("  expirationTime = $expirationTime")
        append(")")
    }
}

/**
 * Represents a collection of cookies.
 * Serialized using kotlinx.serialization with ProtoBuf format.
 */
@Serializable
@OptIn(ExperimentalSerializationApi::class)
internal data class CookieJar(
    @ProtoNumber(1) val cookies: List<Cookie> = listOf()
) {
    /** Serialize this CookieJar to ProtoBuf binary format */
    fun toBytes(): ByteArray = ProtoBuf.encodeToByteArray(this)

    companion object {
        /** Deserialize a CookieJar from ProtoBuf binary format */
        fun fromBytes(bytes: ByteArray): CookieJar =
            ProtoBuf.decodeFromByteArray(bytes)
    }

    override fun toString(): String = buildString {
        appendLine("CookieJar(")
        if (cookies.isEmpty()) {
            appendLine("  cookies = []")
        } else {
            appendLine("  cookies = [")
            cookies.forEach { cookie ->
                appendLine("    ${cookie.toString().replace("\n", "\n    ")},")
            }
            appendLine("  ]")
        }
        append(")")
    }
}
