# 지일 AI 비서 앱 — 설계서 v1.0

## 1. 프로젝트 개요

### 목적
PM(김진영)의 폰에서 위치/알림 기반으로 자동 브리핑+업무 자동화를 수행하는 Android 앱.
오케스트레이터(사무실 PC)와 텔레그램 봇을 통해 양방향 통신.

### 대상
- 기기: Galaxy S23 (Android 14+)
- 사용자: 1명 (PM 전용)
- 배포: APK 직접 설치 (Play Store 불필요)

## 2. 핵심 기능

### F1. 위치 기반 자동 브리핑
| 트리거 | 동작 |
|--------|------|
| jiil_5G WiFi 연결 (출근) | 텔레그램 봇에 "출근" 신호 전송 → 오케스트레이터가 오늘 할일/세션상태 브리핑 |
| JIN's HOME_5G WiFi 연결 (퇴근) | 텔레그램 봇에 "퇴근" 신호 전송 → 하루 성과 요약 + 야간 작업 시작 |
| WiFi 연결 해제 (이동 중) | 텔레그램 봇에 "이동중" 신호 |

### F2. 카카오톡 알림 분석
- Android NotificationListenerService로 카톡 알림 수신
- 알림 텍스트(발신자 + 메시지 미리보기)를 텔레그램 봇에 전달
- 오케스트레이터가 AI 분석:
  - 일정이면 → 대시보드 tasks에 자동 등록
  - 업무 지시면 → directive 생성
  - 일반 대화면 → 무시

### F3. 자동 일정/할일 등록
- 카톡/텔레그램에서 감지된 일정 → Supabase tasks 테이블에 INSERT
- 감지된 할일 → shared_context에 directive 등록
- 매일 오전 9시 → 오늘 일정 요약 push 알림

### F4. 상태 알림
- 세션 완료 시 push 알림 (텔레그램 봇 경유)
- blocker 발생 시 긴급 알림
- 10분 이상 idle 세션 감지 시 알림

## 3. 아키텍처

```
[Galaxy S23 앱]
    │
    ├─ WiFi 감지 (BroadcastReceiver)
    ├─ 카톡 알림 수신 (NotificationListenerService)
    ├─ Push 알림 수신 (Firebase FCM)
    │
    ▼
[텔레그램 봇 API]
    │
    ▼
[오케스트레이터 (사무실 PC)]
    ├─ AI 분석 (일정/할일 분류)
    ├─ Supabase tasks INSERT
    ├─ directive 생성
    └─ 브리핑 메시지 생성 → 텔레그램 봇 → 앱 push
```

## 4. 기술 스택

| 구분 | 기술 | 이유 |
|------|------|------|
| 앱 프레임워크 | Android Native (Kotlin) | 백그라운드 서비스 안정성, NotificationListener 필수 |
| 빌드 | Gradle + AGP | 표준 Android 빌드 |
| WiFi 감지 | WifiManager + BroadcastReceiver | 네이티브 API, 배터리 효율적 |
| 알림 읽기 | NotificationListenerService | 카톡 알림 텍스트 추출 |
| 통신 | Telegram Bot API (HTTPS) | 기존 인프라 활용, 추가 서버 불필요 |
| Push 알림 | Firebase Cloud Messaging (FCM) | 무료, 안정적 |
| 최소 SDK | API 33 (Android 13) | Galaxy S23 기본 |

### 대안 검토 후 탈락
| 대안 | 탈락 이유 |
|------|-----------|
| Flutter/React Native | NotificationListener 네이티브 브리지 필요 → 복잡도만 증가 |
| Tasker | 앱이 아닌 자동화 도구, 커스터마이징 한계 |
| Expo | 백그라운드 서비스 제약, 알림 읽기 불가 |

## 5. 파일 구조 (예상)

```
ji1-assistant-app/
  app/
    src/main/
      java/com/ji1/assistant/
        MainActivity.kt              — 메인 화면 (상태 표시)
        service/
          WifiMonitorService.kt      — WiFi 변경 감지 + 텔레그램 전송
          NotificationService.kt     — 카톡 알림 읽기 + 텔레그램 전송
          DailyBriefingService.kt    — 매일 오전 9시 브리핑
        receiver/
          WifiReceiver.kt            — WiFi 연결/해제 BroadcastReceiver
          BootReceiver.kt            — 부팅 시 서비스 자동 시작
        api/
          TelegramApi.kt             — 텔레그램 봇 API 클라이언트
        util/
          Constants.kt               — WiFi SSID, 봇 토큰 등
      res/
        layout/activity_main.xml
      AndroidManifest.xml
    build.gradle.kts
  docs/
    DESIGN.md                        — 이 파일
  build.gradle.kts
  settings.gradle.kts
```

## 6. 권한 (AndroidManifest)

| 권한 | 용도 |
|------|------|
| ACCESS_WIFI_STATE | WiFi SSID 읽기 |
| ACCESS_FINE_LOCATION | WiFi SSID 접근 (Android 13+ 필수) |
| CHANGE_WIFI_STATE | WiFi 상태 변경 감지 |
| INTERNET | 텔레그램 API 호출 |
| FOREGROUND_SERVICE | 백그라운드 서비스 유지 |
| RECEIVE_BOOT_COMPLETED | 부팅 시 자동 시작 |
| BIND_NOTIFICATION_LISTENER_SERVICE | 카톡 알림 읽기 |
| POST_NOTIFICATIONS | push 알림 표시 |

## 7. 보안

- 텔레그램 봇 토큰: BuildConfig에 저장 (APK 내부, Play Store 배포 안 하므로 OK)
- 카톡 알림 내용: 텔레그램 DM으로만 전송 (그룹 아님)
- 위치 데이터: WiFi SSID만 사용 (GPS 좌표 수집 안 함)
- 데이터 저장: 로컬 저장 없음 (모든 처리는 오케스트레이터에서)

## 8. 구현 단계

### Phase 1: 기본 (1~2일)
- [ ] Android 프로젝트 생성 (Kotlin, API 33)
- [ ] WiFi 감지 서비스 (jiil_5G / JIN's HOME_5G)
- [ ] 텔레그램 봇 API 연동 (출근/퇴근 신호)
- [ ] 부팅 시 자동 시작
- [ ] APK 빌드 + 텔레그램으로 전송

### Phase 2: 카톡 연동 (1~2일)
- [ ] NotificationListenerService 구현
- [ ] 카톡 알림 필터링 (발신자 + 메시지)
- [ ] 텔레그램 전달 + 오케스트레이터 분석 연동

### Phase 3: 브리핑 (1일)
- [ ] 매일 오전 9시 브리핑 (AlarmManager)
- [ ] Firebase FCM push 알림
- [ ] 세션 상태 알림

## 9. 오케스트레이터 연동

앱에서 텔레그램으로 전송하는 메시지 포맷:
```
[JI1-APP] type=arrive location=office
[JI1-APP] type=leave location=office  
[JI1-APP] type=arrive location=home
[JI1-APP] type=katalk sender=이운봉 text=내일 회의 10시로 변경
```

오케스트레이터가 수신 후 처리:
- arrive/office → 오늘 할일 + 세션상태 브리핑 생성 → 텔레그램 DM 발송
- arrive/home → 하루 성과 요약 → 텔레그램 DM 발송
- katalk → AI 분석 → 일정이면 tasks INSERT, 할일이면 directive 생성

## 10. 테스트 계획

| 항목 | 방법 |
|------|------|
| WiFi 트리거 | WiFi 켜기/끄기로 시뮬레이션 |
| 카톡 알림 | 테스트 카톡 메시지 전송 |
| 텔레그램 통신 | 봇 API 직접 호출 |
| 배터리 소모 | 24시간 백그라운드 실행 후 확인 |
| 부팅 자동시작 | 폰 재시작 후 서비스 확인 |
