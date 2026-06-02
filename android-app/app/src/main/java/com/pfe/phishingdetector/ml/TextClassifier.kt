package com.pfe.phishingdetector.ml

import android.content.Context
import org.tensorflow.lite.Interpreter
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel
import kotlin.math.exp

/**
 * On-device DistilBERT text classifier (TensorFlow Lite).
 * Loads model.tflite from assets/ and returns P(phishing) in [0,1].
 *
 * All inference is local — no network call is ever made.
 */
class TextClassifier(context: Context, private val maxLen: Int = 128) {

    private val interpreter: Interpreter
    private val tokenizer = WordpieceTokenizer(context)

    init {
        val model = loadModelFile(context, "model.tflite")
        val options = Interpreter.Options().apply { numThreads = 2 }
        interpreter = Interpreter(model, options)
    }

    private fun loadModelFile(context: Context, name: String): MappedByteBuffer {
        val fd = context.assets.openFd(name)
        fd.createInputStream().channel.use { channel ->
            return channel.map(FileChannel.MapMode.READ_ONLY,
                fd.startOffset, fd.declaredLength)
        }
    }

    /** Returns the phishing probability for [text]. */
    fun phishingProbability(text: String): Float {
        val (ids, mask) = tokenizer.encode(text, maxLen)

        val inputIds = arrayOf(ids)        // shape [1, maxLen]
        val attention = arrayOf(mask)      // shape [1, maxLen]
        val logits = Array(1) { FloatArray(2) }  // [legitimate, phishing]

        val inputs = mapOf("input_ids" to inputIds, "attention_mask" to attention)
        val outputs = mutableMapOf<Int, Any>(0 to logits)
        // Signature-based call keeps us robust to input ordering.
        interpreter.runForMultipleInputsOutputs(arrayOf(inputIds, attention), outputs)

        return softmax(logits[0])[1]
    }

    private fun softmax(z: FloatArray): FloatArray {
        val max = z.max()
        val exps = z.map { exp((it - max).toDouble()) }
        val sum = exps.sum()
        return FloatArray(z.size) { (exps[it] / sum).toFloat() }
    }

    fun close() = interpreter.close()
}
