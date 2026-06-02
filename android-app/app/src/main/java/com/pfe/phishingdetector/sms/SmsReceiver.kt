package com.pfe.phishingdetector.sms

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.provider.Telephony
import androidx.core.app.NotificationCompat
import com.pfe.phishingdetector.PhishingApp
import com.pfe.phishingdetector.R
import com.pfe.phishingdetector.ml.ThreatEngine

/**
 * Real-time detection (bonus): on each incoming SMS, runs the on-device engine
 * and raises a local notification if the message looks dangerous. All analysis
 * is local; nothing is transmitted.
 */
class SmsReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return

        val body = Telephony.Sms.Intents.getMessagesFromIntent(intent)
            ?.joinToString("") { it.messageBody ?: "" } ?: return
        if (body.isBlank()) return

        val app = context.applicationContext as PhishingApp
        val pText = app.classifier?.phishingProbability(body) ?: 0.5f
        val result = ThreatEngine.analyze(body, pText)

        if (result.verdict == ThreatEngine.Verdict.DANGEROUS) {
            notifyDanger(context, result.score, result.reasons.firstOrNull() ?: "")
        }
    }

    private fun notifyDanger(context: Context, score: Int, reason: String) {
        val channelId = "phishing_alerts"
        val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            nm.createNotificationChannel(
                NotificationChannel(channelId, "Alertes phishing",
                    NotificationManager.IMPORTANCE_HIGH)
            )
        }
        val notif = NotificationCompat.Builder(context, channelId)
            .setSmallIcon(android.R.drawable.stat_sys_warning)
            .setContentTitle("⚠️ SMS suspect détecté ($score/100)")
            .setContentText(reason)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .build()
        nm.notify(System.currentTimeMillis().toInt(), notif)
    }
}
