package com.pfe.phishingdetector.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Risk palette (also used by the score gauge & badges).
val RiskGreen = Color(0xFF2E7D32)
val RiskOrange = Color(0xFFEF6C00)
val RiskRed = Color(0xFFC62828)

private val Primary = Color(0xFF1565C0)

private val LightColors = lightColorScheme(primary = Primary)
private val DarkColors = darkColorScheme(primary = Primary)

@Composable
fun PhishingTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        content = content
    )
}

/** Map a verdict label to its colour. */
fun colorForVerdict(verdict: String): Color = when (verdict) {
    "Dangereux" -> RiskRed
    "Suspect" -> RiskOrange
    else -> RiskGreen
}
