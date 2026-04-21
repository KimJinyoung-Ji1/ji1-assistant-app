package com.ji1.assistant

import android.Manifest
import android.content.ComponentName
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.lifecycle.lifecycleScope
import com.ji1.assistant.api.TelegramApi
import com.ji1.assistant.service.KakaoNotificationService
import com.ji1.assistant.service.WifiMonitorService
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    private val PERMISSION_REQUEST = 100

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        requestPermissions()
        checkNotificationAccess()

        findViewById<Button>(R.id.btnStartService).setOnClickListener {
            startForegroundService(Intent(this, WifiMonitorService::class.java))
            updateStatus("서비스 시작됨")
        }

        findViewById<Button>(R.id.btnStopService).setOnClickListener {
            stopService(Intent(this, WifiMonitorService::class.java))
            updateStatus("서비스 중지됨")
        }

        findViewById<Button>(R.id.btnTestTelegram).setOnClickListener {
            lifecycleScope.launch {
                val ok = TelegramApi.sendSignal("test", extra = mapOf("message" to "앱 테스트"))
                updateStatus(if (ok) "텔레그램 전송 성공" else "텔레그램 전송 실패")
            }
        }

        findViewById<Button>(R.id.btnNotifSettings).setOnClickListener {
            startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
        }

        // Auto-start service
        startForegroundService(Intent(this, WifiMonitorService::class.java))
    }

    private fun requestPermissions() {
        val perms = arrayOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
            Manifest.permission.POST_NOTIFICATIONS,
        )
        val needed = perms.filter {
            ActivityCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (needed.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, needed.toTypedArray(), PERMISSION_REQUEST)
        }
    }

    private fun checkNotificationAccess() {
        val cn = ComponentName(this, KakaoNotificationService::class.java)
        val flat = Settings.Secure.getString(contentResolver, "enabled_notification_listeners")
        val enabled = flat?.contains(cn.flattenToString()) == true
        val tv = findViewById<TextView>(R.id.tvNotifStatus)
        tv.text = if (enabled) "알림 접근: 허용됨 ✓" else "알림 접근: 허용 필요 ✗"
    }

    private fun updateStatus(msg: String) {
        findViewById<TextView>(R.id.tvStatus).text = msg
    }
}
