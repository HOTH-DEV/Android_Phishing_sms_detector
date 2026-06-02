package com.pfe.phishingdetector.ml

import android.content.Context
import java.io.BufferedReader
import java.io.InputStreamReader

/**
 * Minimal WordPiece tokenizer compatible with DistilBERT multilingual (cased).
 * Loads vocab.txt from assets/ and reproduces the BERT tokenization needed to
 * feed the TFLite model: [CLS] tokens [SEP] padded to maxLen.
 *
 * This is a teaching-grade implementation (greedy longest-match) sufficient for
 * the PFE; it intentionally keeps case (the model is "cased").
 */
class WordpieceTokenizer(context: Context, vocabAsset: String = "vocab.txt") {

    private val vocab = HashMap<String, Int>()
    private val unkToken = "[UNK]"
    private val clsId: Int
    private val sepId: Int
    private val padId: Int
    private val unkId: Int

    init {
        context.assets.open(vocabAsset).use { stream ->
            BufferedReader(InputStreamReader(stream, Charsets.UTF_8)).useLines { lines ->
                var index = 0
                lines.forEach { token -> vocab[token] = index++ }
            }
        }
        clsId = vocab["[CLS]"] ?: 101
        sepId = vocab["[SEP]"] ?: 102
        padId = vocab["[PAD]"] ?: 0
        unkId = vocab[unkToken] ?: 100
    }

    /** Returns input_ids and attention_mask, both of length [maxLen]. */
    fun encode(text: String, maxLen: Int = 128): Pair<IntArray, IntArray> {
        val pieces = ArrayList<Int>()
        pieces.add(clsId)
        for (word in basicTokenize(text)) {
            pieces.addAll(wordpiece(word))
            if (pieces.size >= maxLen - 1) break
        }
        pieces.add(sepId)

        val ids = IntArray(maxLen) { padId }
        val mask = IntArray(maxLen) { 0 }
        for (i in pieces.indices) {
            if (i >= maxLen) break
            ids[i] = pieces[i]
            mask[i] = 1
        }
        return Pair(ids, mask)
    }

    /** Split on whitespace and isolate punctuation as separate tokens. */
    private fun basicTokenize(text: String): List<String> {
        val out = ArrayList<String>()
        val sb = StringBuilder()
        for (ch in text.trim()) {
            when {
                ch.isWhitespace() -> { if (sb.isNotEmpty()) { out.add(sb.toString()); sb.clear() } }
                isPunct(ch) -> {
                    if (sb.isNotEmpty()) { out.add(sb.toString()); sb.clear() }
                    out.add(ch.toString())
                }
                else -> sb.append(ch)
            }
        }
        if (sb.isNotEmpty()) out.add(sb.toString())
        return out
    }

    private fun isPunct(ch: Char): Boolean =
        !ch.isLetterOrDigit() && !ch.isWhitespace()

    /** Greedy longest-match WordPiece over a single word. */
    private fun wordpiece(word: String): List<Int> {
        if (word.isEmpty()) return emptyList()
        val tokens = ArrayList<Int>()
        var start = 0
        val chars = word
        while (start < chars.length) {
            var end = chars.length
            var curId: Int? = null
            while (start < end) {
                var sub = chars.substring(start, end)
                if (start > 0) sub = "##$sub"
                val id = vocab[sub]
                if (id != null) { curId = id; break }
                end--
            }
            if (curId == null) { return listOf(unkId) } // whole word -> [UNK]
            tokens.add(curId)
            start = end
        }
        return tokens
    }
}
