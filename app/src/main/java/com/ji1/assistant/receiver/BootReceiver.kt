package com.ji1.assistant.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.ji1.assistant.service.WifiMonitorService

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            Log.i("BootReceiver", "Boot completed, starting WifiMonitorService")
            val serviceIntent = Intent(context, WifiMonitorService::class.java)
            context.startForegroundService(serviceIntent)
        }
    }
}
