package com.pfe.phishingdetector.ml

import kotlin.math.roundToInt

/**
 * Fusion engine — Kotlin mirror of model/threat_score.py.
 * Combines the text probability (DistilBERT) and the URL risk into a single
 * Threat Score (0-100), assigns a verdict, and produces readable reasons.
 */
object ThreatEngine {

    private const val W_TEXT = 0.6
    private const val W_URL = 0.4

    private val URL_REGEX = Regex(
        """(https?://[^\s]+|www\.[^\s]+|\b[a-z0-9.-]+\.[a-z]{2,}(/[^\s]*)?)""",
        RegexOption.IGNORE_CASE
    )
    private val URGENCY = listOf("urgent", "immédiat", "immediately", "now",
        "maintenant", "24h", "expire", "suspendu", "suspended", "locked",
        "bloqué", "dernier", "avertissement", "عاجل", "فورا")
    private val CREDENTIAL = listOf("password", "mot de passe", "login",
        "identifiant", "verify", "vérifier", "confirm", "confirmer", "code",
        "pin", "تحقق")
    private val MONEY = listOf("refund", "remboursement", "gagné", "won", "prize",
        "cadeau", "gift", "eur", "€", "facture", "payer", "pay", "bonus")

    enum class Verdict(val label: String) {
        SAFE("Sûr"), SUSPICIOUS("Suspect"), DANGEROUS("Dangereux")
    }

    data class Result(
        val score: Int,
        val verdict: Verdict,
        val reasons: List<String>,
        val urls: List<String>
    )

    fun findUrls(text: String): List<String> =
        URL_REGEX.findAll(text).map { it.value.trimEnd('.', ',', ')', ';') }.toList()

    private fun textSignals(text: String): MutableList<String> {
        val t = text.lowercase()
        val reasons = mutableListOf<String>()
        if (URGENCY.any { t.contains(it) }) reasons.add("Ton d'urgence / pression temporelle détecté")
        if (CREDENTIAL.any { t.contains(it) }) reasons.add("Demande d'identifiants / code de vérification")
        if (MONEY.any { t.contains(it) }) reasons.add("Promesse de gain ou pression financière")
        return reasons
    }

    fun verdictFor(score: Int): Verdict = when {
        score >= 70 -> Verdict.DANGEROUS
        score >= 40 -> Verdict.SUSPICIOUS
        else -> Verdict.SAFE
    }

    /**
     * @param text   raw message/URL to analyse
     * @param pText  phishing probability from DistilBERT in [0,1]
     */
    fun analyze(text: String, pText: Float): Result {
        val urls = findUrls(text)
        val reasons = textSignals(text)

        val fused: Double
        if (urls.isNotEmpty()) {
            val risky = urls.maxByOrNull { UrlFeatures.urlRisk(it) }!!
            val pUrl = UrlFeatures.urlRisk(risky)
            fused = W_TEXT * pText + W_URL * pUrl
            if (pUrl >= 0.5) {
                val f = UrlFeatures.extract(risky)
                val flags = buildList {
                    if (f.hasIp) add("adresse IP brute")
                    if (f.suspiciousTld) add("extension suspecte")
                    if (f.hasSuspiciousWord) add("mot-clé sensible")
                    if (!f.hasHttps) add("absence de HTTPS")
                }
                val detail = if (flags.isNotEmpty()) " (${flags.joinToString(", ")})" else ""
                reasons.add("URL à risque : $risky$detail")
            }
        } else {
            fused = pText.toDouble()
        }

        val score = (100 * fused).roundToInt().coerceIn(0, 100)
        if (reasons.isEmpty()) {
            reasons.add(
                if (score < 40) "Aucun signal fort ; contenu probablement légitime"
                else "Score élevé du modèle de langage"
            )
        }
        return Result(score, verdictFor(score), reasons, urls)
    }
}
