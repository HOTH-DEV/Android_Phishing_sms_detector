package com.pfe.phishingdetector.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** Circular gauge showing the threat score 0-100 in the verdict colour. */
@Composable
fun ScoreGauge(score: Int, color: Color, modifier: Modifier = Modifier) {
    Box(modifier = modifier.size(160.dp), contentAlignment = Alignment.Center) {
        Canvas(modifier = Modifier.size(160.dp)) {
            val stroke = Stroke(width = 18f)
            val arcSize = Size(size.width - 18f, size.height - 18f)
            drawArc(
                color = Color(0x22000000), startAngle = 135f, sweepAngle = 270f,
                useCenter = false, style = stroke, size = arcSize,
                topLeft = androidx.compose.ui.geometry.Offset(9f, 9f)
            )
            drawArc(
                color = color, startAngle = 135f,
                sweepAngle = 270f * (score / 100f),
                useCenter = false, style = stroke, size = arcSize,
                topLeft = androidx.compose.ui.geometry.Offset(9f, 9f)
            )
        }
        Text("$score", color = color, fontSize = 40.sp, fontWeight = FontWeight.Bold)
    }
}
