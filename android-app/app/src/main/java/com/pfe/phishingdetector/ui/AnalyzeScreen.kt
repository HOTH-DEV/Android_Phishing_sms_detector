package com.pfe.phishingdetector.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pfe.phishingdetector.ml.ThreatEngine
import com.pfe.phishingdetector.ui.components.ScoreGauge
import com.pfe.phishingdetector.ui.theme.colorForVerdict
import com.pfe.phishingdetector.vm.MainViewModel
import androidx.compose.runtime.collectAsState

@Composable
fun AnalyzeScreen(vm: MainViewModel, prefill: String = "") {
    var input by remember { mutableStateOf(prefill) }
    val ui by vm.ui.collectAsState()

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState())
    ) {
        Text("Analyse manuelle", fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Text("Collez un SMS, un email ou une URL à vérifier.",
            color = Color.Gray, fontSize = 14.sp)
        Spacer(Modifier.height(12.dp))

        OutlinedTextField(
            value = input,
            onValueChange = { input = it },
            modifier = Modifier.fillMaxWidth().height(160.dp),
            label = { Text("Contenu à analyser") }
        )
        Spacer(Modifier.height(12.dp))
        Button(
            onClick = { vm.analyze(input) },
            enabled = input.isNotBlank() && !ui.running,
            modifier = Modifier.fillMaxWidth()
        ) { Text("Analyser") }

        Spacer(Modifier.height(20.dp))
        when {
            ui.running -> CircularProgressIndicator(Modifier.align(Alignment.CenterHorizontally))
            ui.result != null -> ResultCard(ui.result!!)
        }
    }
}

/** Reusable verdict card showing the gauge, verdict, and reasons. */
@Composable
fun ResultCard(result: ThreatEngine.Result) {
    val color = colorForVerdict(result.verdict.label)
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.08f))
    ) {
        Column(Modifier.padding(20.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            ScoreGauge(result.score, color)
            Spacer(Modifier.height(8.dp))
            Text(result.verdict.label, color = color, fontSize = 22.sp,
                fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(12.dp))
            Text("Pourquoi ce verdict :", fontWeight = FontWeight.SemiBold,
                modifier = Modifier.fillMaxWidth())
            Spacer(Modifier.height(4.dp))
            result.reasons.forEach { r ->
                Text("•  $r", modifier = Modifier.fillMaxWidth().padding(vertical = 2.dp))
            }
        }
    }
}
