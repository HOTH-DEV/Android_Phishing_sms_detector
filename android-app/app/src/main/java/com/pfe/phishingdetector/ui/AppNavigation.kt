package com.pfe.phishingdetector.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Sms
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.lifecycle.viewmodel.compose.viewModel
import com.pfe.phishingdetector.vm.MainViewModel

private data class Tab(val label: String, val icon: ImageVector)

@Composable
fun AppNavigation(sharedText: String?) {
    val vm: MainViewModel = viewModel()
    var selected by remember { mutableIntStateOf(if (sharedText != null) 0 else 0) }
    var prefill by remember { mutableStateOf(sharedText ?: "") }

    val tabs = listOf(
        Tab("Analyser", Icons.Filled.Search),
        Tab("SMS", Icons.Filled.Sms),
        Tab("Démo", Icons.Filled.PlayArrow),
        Tab("Historique", Icons.Filled.History),
    )

    Scaffold(
        bottomBar = {
            NavigationBar {
                tabs.forEachIndexed { i, tab ->
                    NavigationBarItem(
                        selected = selected == i,
                        onClick = { selected = i },
                        icon = { Icon(tab.icon, contentDescription = tab.label) },
                        label = { Text(tab.label) }
                    )
                }
            }
        }
    ) { padding ->
        androidx.compose.foundation.layout.Box(Modifier.padding(padding)) {
            when (selected) {
                0 -> AnalyzeScreen(vm, prefill)
                1 -> SmsScreen()
                2 -> DemoScreen(vm) { selected = 0 }
                3 -> HistoryScreen(vm)
            }
        }
    }
}
