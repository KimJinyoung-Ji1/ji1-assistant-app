package com.ji1.assistant.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class WifiReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        // NetworkCallback in WifiMonitorService handles the real work.
        // This receiver is kept for legacy broadcast compatibility.
        Log.d("WifiReceiver", "WiFi state change broadcast: ${intent.action}")
    }
}
