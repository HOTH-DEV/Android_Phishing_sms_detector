package com.pfe.phishingdetector

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.pfe.phishingdetector.ui.AppNavigation
import com.pfe.phishingdetector.ui.theme.PhishingTheme

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // If launched via "Share to", prefill the analysis field.
        val shared: String? =
            if (intent?.action == Intent.ACTION_SEND && intent.type == "text/plain")
                intent.getStringExtra(Intent.EXTRA_TEXT)
            else null

        setContent {
            PhishingTheme {
                AppNavigation(sharedText = shared)
            }
        }
    }
}
