package com.ji1.assistant.api

import com.ji1.assistant.BuildConfig
import com.ji1.assistant.util.Constants
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

object TelegramApi {
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .build()

    private val baseUrl = "${Constants.TELEGRAM_BASE_URL}${BuildConfig.TELEGRAM_BOT_TOKEN}"
    private val chatId = BuildConfig.TELEGRAM_CHAT_ID

    suspend fun sendMessage(text: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val json = JSONObject().apply {
                put("chat_id", chatId)
                put("text", text)
            }
            val body = json.toString().toRequestBody("application/json".toMediaType())
            val request = Request.Builder()
                .url("$baseUrl/sendMessage")
                .post(body)
                .build()

            val response = client.newCall(request).execute()
            response.use { it.isSuccessful }
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    suspend fun sendSignal(type: String, location: String? = null, extra: Map<String, String>? = null): Boolean {
        val parts = mutableListOf("${Constants.MSG_PREFIX} type=$type")
        location?.let { parts.add("location=$it") }
        extra?.forEach { (k, v) -> parts.add("$k=$v") }
        return sendMessage(parts.joinToString(" "))
    }
}
