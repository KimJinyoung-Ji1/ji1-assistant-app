package com.ji1.assistant.service

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import com.ji1.assistant.api.TelegramApi
import com.ji1.assistant.util.Constants
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class KakaoNotificationService : NotificationListenerService() {
    private val tag = "KakaoNotifService"
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private var lastNotifKey: String? = null
    private var lastNotifTime: Long = 0

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        if (sbn == null) return
        if (sbn.packageName != Constants.KAKAO_PACKAGE) return

        val extras = sbn.notification.extras
        val sender = extras.getCharSequence("android.title")?.toString() ?: return
        val text = extras.getCharSequence("android.text")?.toString() ?: return

        // 중복 방지 (같은 sender+text가 1초 이내면 무시)
        val key = "$sender:$text"
        val now = System.currentTimeMillis()
        if (key == lastNotifKey && now - lastNotifTime < 1000) return
        lastNotifKey = key
        lastNotifTime = now

        Log.i(tag, "KakaoTalk: $sender -> $text")

        scope.launch {
            TelegramApi.sendSignal(
                type = "katalk",
                extra = mapOf("sender" to sender, "text" to text)
            )
        }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification?) {
        // no-op
    }
}
