package com.pfe.phishingdetector.vm

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pfe.phishingdetector.PhishingApp
import com.pfe.phishingdetector.data.AnalysisEntity
import com.pfe.phishingdetector.ml.ThreatEngine
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** UI state for a single analysis result. */
data class AnalysisUiState(
    val running: Boolean = false,
    val result: ThreatEngine.Result? = null
)

class MainViewModel : ViewModel() {

    private val app = PhishingApp.instance
    private val dao = app.database.analysisDao()

    private val _ui = MutableStateFlow(AnalysisUiState())
    val ui: StateFlow<AnalysisUiState> = _ui

    val history: StateFlow<List<AnalysisEntity>> =
        dao.observeAll().stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val dangerousCount: StateFlow<Int> =
        dao.countByVerdict("Dangereux")
            .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), 0)

    /** Analyse free text (SMS / email / URL) on a background thread. */
    fun analyze(text: String, persist: Boolean = true) {
        if (text.isBlank()) return
        _ui.value = AnalysisUiState(running = true)
        viewModelScope.launch {
            val result = withContext(Dispatchers.Default) {
                // DistilBERT probability if the model is loaded, else neutral 0.5
                // so the URL signal still drives the verdict.
                val pText = app.classifier?.phishingProbability(text) ?: 0.5f
                ThreatEngine.analyze(text, pText)
            }
            _ui.value = AnalysisUiState(running = false, result = result)
            if (persist) {
                dao.insert(
                    AnalysisEntity(
                        content = text.take(500),
                        score = result.score,
                        verdict = result.verdict.label,
                        reasons = result.reasons.joinToString(" | ")
                    )
                )
            }
        }
    }

    fun clearHistory() = viewModelScope.launch { dao.clear() }
}
