package com.pfe.phishingdetector.ml

import java.net.URI
import kotlin.math.ln

/**
 * Lexical URL features — Kotlin mirror of model/url_features.py (same 15
 * features, same order). Pure on-device, no network.
 *
 * Because the trained URL RandomForest is not embedded, the app uses a
 * transparent weighted heuristic (urlRisk) built from these features. The
 * Python project can export the RF if higher accuracy is desired.
 */
object UrlFeatures {

    private val SHORTENERS = setOf("bit.ly", "tinyurl.com", "t.co", "goo.gl",
        "ow.ly", "is.gd", "buff.ly")
    private val SUSPICIOUS_TLDS = setOf("xyz", "top", "info", "online", "support",
        "click", "country", "co", "tk", "ml", "ga", "cf", "gq", "work", "zip")
    private val SUSPICIOUS_WORDS = listOf("login", "verify", "secure", "account",
        "update", "confirm", "bank", "signin", "password", "billing", "unlock",
        "webscr", "wp-admin", "paypal", "free", "bonus", "gift")
    private val IP_REGEX = Regex("""^\d{1,3}(\.\d{1,3}){3}$""")

    data class Features(
        val urlLength: Int, val numDots: Int, val numHyphens: Int,
        val numDigits: Int, val numSpecial: Int, val hasIp: Boolean,
        val hasAt: Boolean, val numSubdomains: Int, val hasHttps: Boolean,
        val usesShortener: Boolean, val hasSuspiciousWord: Boolean,
        val suspiciousTld: Boolean, val digitRatio: Double, val entropy: Double,
        val hasPort: Boolean
    )

    fun extract(rawUrl: String): Features {
        val url = rawUrl.trim()
        val full = if (url.contains("://")) url else "http://$url"
        val uri = runCatching { URI(full) }.getOrNull()
        val host = uri?.host ?: ""
        val tld = if (host.contains(".")) host.substringAfterLast(".").lowercase() else ""
        val labels = host.split(".").filter { it.isNotEmpty() }

        val digits = url.count { it.isDigit() }
        val specials = url.count { it in "@%?=&_~+" }

        return Features(
            urlLength = url.length,
            numDots = url.count { it == '.' },
            numHyphens = url.count { it == '-' },
            numDigits = digits,
            numSpecial = specials,
            hasIp = IP_REGEX.matches(host),
            hasAt = url.contains("@"),
            numSubdomains = maxOf(0, labels.size - 2),
            hasHttps = uri?.scheme == "https",
            usesShortener = host in SHORTENERS,
            hasSuspiciousWord = SUSPICIOUS_WORDS.any { url.lowercase().contains(it) },
            suspiciousTld = tld in SUSPICIOUS_TLDS,
            digitRatio = if (url.isNotEmpty()) digits.toDouble() / url.length else 0.0,
            entropy = shannonEntropy(url),
            hasPort = (uri?.port ?: -1) > 0
        )
    }

    /** Transparent risk score in [0,1] from the lexical features. */
    fun urlRisk(rawUrl: String): Double {
        val f = extract(rawUrl)
        var score = 0.0
        if (f.hasIp) score += 0.30
        if (f.suspiciousTld) score += 0.20
        if (f.hasSuspiciousWord) score += 0.20
        if (!f.hasHttps) score += 0.15
        score += 0.15 * minOf(f.numHyphens / 3.0, 1.0)
        if (f.usesShortener) score += 0.10
        if (f.hasAt) score += 0.10
        return score.coerceIn(0.0, 1.0)
    }

    private fun shannonEntropy(s: String): Double {
        if (s.isEmpty()) return 0.0
        val counts = HashMap<Char, Int>()
        for (c in s) counts[c] = (counts[c] ?: 0) + 1
        val n = s.length.toDouble()
        return -counts.values.sumOf { val p = it / n; p * (ln(p) / ln(2.0)) }
    }
}
