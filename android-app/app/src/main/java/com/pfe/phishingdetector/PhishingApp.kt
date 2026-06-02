package com.pfe.phishingdetector

import android.app.Application
import androidx.room.Room
import com.pfe.phishingdetector.data.AppDatabase
import com.pfe.phishingdetector.ml.TextClassifier

/**
 * Holds app-wide singletons: the Room database and the TFLite classifier.
 * The classifier is created lazily and may be null if the model asset is
 * missing (so the app still runs in URL-only / heuristic mode during dev).
 */
class PhishingApp : Application() {

    val database: AppDatabase by lazy {
        Room.databaseBuilder(this, AppDatabase::class.java, "phishing.db").build()
    }

    val classifier: TextClassifier? by lazy {
        runCatching { TextClassifier(this) }.getOrNull()
    }

    companion object {
        lateinit var instance: PhishingApp
            private set
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
    }
}
