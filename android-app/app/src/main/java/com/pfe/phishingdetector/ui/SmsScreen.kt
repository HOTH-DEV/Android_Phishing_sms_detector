package com.pfe.phishingdetector.ui

import android.Manifest
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.Telephony
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pfe.phishingdetector.ml.ThreatEngine
import com.pfe.phishingdetector.PhishingApp
import com.pfe.phishingdetector.ui.theme.colorForVerdict

private data class ScoredSms(val body: String, val score: Int, val verdict: String)

/**
 * Lists recent SMS with a coloured risk badge. READ_SMS is requested only on
 * explicit user action (privacy by design); nothing leaves the device.
 */
@Composable
fun SmsScreen() {
    val context = LocalContext.current
    var granted by remember {
        mutableStateOf(
            context.checkSelfPermission(Manifest.permission.READ_SMS)
                    == PackageManager.PERMISSION_GRANTED
        )
    }
    var messages by remember { mutableStateOf<List<ScoredSms>>(emptyList()) }

    val launcher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { ok ->
        granted = ok
        if (ok) messages = readAndScoreSms(context)
    }

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("SMS récents", fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(8.dp))

        if (!granted) {
            Text("L'accès aux SMS nécessite votre consentement. " +
                    "Les messages sont analysés localement et ne quittent jamais le téléphone.",
                fontSize = 14.sp)
            Spacer(Modifier.height(8.dp))
            Button(onClick = { launcher.launch(Manifest.permission.READ_SMS) }) {
                Text("Autoriser la lecture des SMS")
            }
        } else {
            if (messages.isEmpty()) messages = readAndScoreSms(context)
            LazyColumn {
                items(messages) { m ->
                    Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Row(Modifier.padding(12.dp)) {
                            Surface(
                                color = colorForVerdict(m.verdict),
                                shape = CircleShape,
                                modifier = Modifier.size(14.dp)
                            ) {}
                            Spacer(Modifier.size(10.dp))
                            Column {
                                Text(m.body, maxLines = 3, fontSize = 14.sp)
                                Text("${m.verdict} (${m.score}/100)",
                                    color = colorForVerdict(m.verdict),
                                    fontSize = 12.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }
        }
    }
}

/** Query the SMS inbox and score each message with the on-device engine. */
private fun readAndScoreSms(context: android.content.Context, limit: Int = 30): List<ScoredSms> {
    val app = context.applicationContext as PhishingApp
    val out = ArrayList<ScoredSms>()
    val cursor = context.contentResolver.query(
        Uri.parse("content://sms/inbox"),
        arrayOf(Telephony.Sms.BODY),
        null, null, "${Telephony.Sms.DATE} DESC"
    )
    cursor?.use {
        val bodyIdx = it.getColumnIndexOrThrow(Telephony.Sms.BODY)
        var count = 0
        while (it.moveToNext() && count < limit) {
            val body = it.getString(bodyIdx) ?: continue
            val pText = app.classifier?.phishingProbability(body) ?: 0.5f
            val r: ThreatEngine.Result = ThreatEngine.analyze(body, pText)
            out.add(ScoredSms(body, r.score, r.verdict.label))
            count++
        }
    }
    return out
}
