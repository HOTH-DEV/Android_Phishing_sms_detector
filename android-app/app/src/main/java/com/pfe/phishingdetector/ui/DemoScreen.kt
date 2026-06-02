package com.pfe.phishingdetector.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pfe.phishingdetector.vm.MainViewModel

/**
 * "Attack" demo tab (bonus): curated, anonymised example messages that show the
 * detector working live in a presentation. Tapping a card runs the analysis.
 */
@Composable
fun DemoScreen(vm: MainViewModel, onAnalyzed: () -> Unit) {
    val examples = remember {
        listOf(
            "URGENT: votre compte bancaire a ete suspendu. Confirmez vos identifiants ici: http://cihbank-login.online/verify",
            "You won a 500 EUR Amazon gift card! Claim within 24h: http://192.168.43.12/claim",
            "تنبيه: تم تعليق حسابك. تحقق من هويتك هنا: http://secure-verify.xyz/login",
            "Salut, tu es dispo pour dejeuner demain a midi ?",
            "Votre colis La Poste est en attente. Reglez 1,99 EUR de frais: http://laposte-colis.info/pay",
            "Your monthly Netflix invoice is available in the app."
        )
    }

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("Mode demo (attaque)", fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Text("Touchez un exemple pour lancer la detection en direct.", fontSize = 14.sp)
        Spacer(Modifier.height(12.dp))
        LazyColumn {
            items(examples) { ex ->
                Card(Modifier.fillMaxWidth().padding(vertical = 5.dp)) {
                    Text(
                        ex,
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { vm.analyze(ex); onAnalyzed() }
                            .padding(14.dp),
                        fontSize = 14.sp
                    )
                }
            }
        }
    }
}
