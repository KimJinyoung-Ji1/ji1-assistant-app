package com.ji1.assistant.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import android.net.wifi.WifiInfo
import android.os.IBinder
import android.util.Log
import com.ji1.assistant.MainActivity
import com.ji1.assistant.api.TelegramApi
import com.ji1.assistant.util.Constants
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class WifiMonitorService : Service() {
    private val tag = "WifiMonitorService"
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private var lastSsid: String? = null
    private var networkCallback: ConnectivityManager.NetworkCallback? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(Constants.NOTIFICATION_ID, buildNotification("서비스 시작됨"))
        registerNetworkCallback()
        Log.i(tag, "WifiMonitorService started")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        networkCallback?.let {
            val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            cm.unregisterNetworkCallback(it)
        }
        super.onDestroy()
    }

    private fun registerNetworkCallback() {
        val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val request = NetworkRequest.Builder()
            .addTransportType(NetworkCapabilities.TRANSPORT_WIFI)
            .build()

        networkCallback = object : ConnectivityManager.NetworkCallback() {
            override fun onCapabilitiesChanged(network: Network, caps: NetworkCapabilities) {
                val wifiInfo = caps.transportInfo as? WifiInfo
                val ssid = wifiInfo?.ssid?.removeSurrounding("\"") ?: return
                if (ssid == lastSsid || ssid == "<unknown ssid>") return
                lastSsid = ssid
                handleWifiChange(ssid)
            }

            override fun onLost(network: Network) {
                if (lastSsid != null) {
                    lastSsid = null
                    handleWifiDisconnect()
                }
            }
        }
        cm.registerNetworkCallback(request, networkCallback!!)
    }

    private fun handleWifiChange(ssid: String) {
        Log.i(tag, "WiFi connected: $ssid")
        updateNotification("WiFi: $ssid")

        when (ssid) {
            Constants.WIFI_OFFICE -> {
                scope.launch { TelegramApi.sendSignal("arrive", "office") }
            }
            Constants.WIFI_HOME -> {
                scope.launch { TelegramApi.sendSignal("arrive", "home") }
            }
            else -> {
                Log.d(tag, "Unknown WiFi: $ssid (ignored)")
            }
        }
    }

    private fun handleWifiDisconnect() {
        Log.i(tag, "WiFi disconnected")
        updateNotification("WiFi 연결 해제")
        scope.launch { TelegramApi.sendSignal("leave", "moving") }
    }

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            Constants.CHANNEL_ID,
            Constants.CHANNEL_NAME,
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "지일 비서 백그라운드 서비스"
        }
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(channel)
    }

    private fun buildNotification(text: String): Notification {
        val intent = Intent(this, MainActivity::class.java)
        val pi = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE)

        return Notification.Builder(this, Constants.CHANNEL_ID)
            .setContentTitle("지일 비서")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentIntent(pi)
            .setOngoing(true)
            .build()
    }

    private fun updateNotification(text: String) {
        val nm = getSystemService(NotificationManager::class.java)
        nm.notify(Constants.NOTIFICATION_ID, buildNotification(text))
    }
}
