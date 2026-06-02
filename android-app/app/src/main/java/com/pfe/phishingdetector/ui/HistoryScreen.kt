package com.pfe.phishingdetector.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pfe.phishingdetector.ui.theme.colorForVerdict
import com.pfe.phishingdetector.vm.MainViewModel
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun HistoryScreen(vm: MainViewModel) {
    val history by vm.history.collectAsState()
    val dangerous by vm.dangerousCount.collectAsState()
    val fmt = SimpleDateFormat("dd/MM HH:mm", Locale.getDefault())

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("Historique & statistiques", fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(8.dp))

        // Local stats dashboard (bonus).
        Row(Modifier.fillMaxWidth()) {
            StatCard("Analyses", history.size.toString(), Modifier.weight(1f))
            Spacer(Modifier.width(8.dp))
            StatCard("Menaces", dangerous.toString(), Modifier.weight(1f))
        }
        Spacer(Modifier.height(8.dp))
        OutlinedButton(onClick = { vm.clearHistory() }) { Text("Effacer l'historique") }
        Spacer(Modifier.height(8.dp))

        LazyColumn(Modifier.fillMaxSize()) {
            items(history) { item ->
                Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                    Column(Modifier.padding(12.dp)) {
                        Row(Modifier.fillMaxWidth()) {
                            Text(item.verdict, color = colorForVerdict(item.verdict),
                                fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                            Text("${item.score}/100", fontWeight = FontWeight.Bold)
                        }
                        Text(item.content, maxLines = 2, fontSize = 13.sp)
                        Text(fmt.format(Date(item.timestamp)), fontSize = 11.sp)
                    }
                }
            }
        }
    }
}

@Composable
private fun StatCard(label: String, value: String, modifier: Modifier = Modifier) {
    Card(modifier) {
        Column(Modifier.padding(16.dp)) {
            Text(value, fontSize = 28.sp, fontWeight = FontWeight.Bold)
            Text(label, fontSize = 13.sp)
        }
    }
}
