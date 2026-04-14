# ji1-assistant-app

Android 네이티브 앱 (Kotlin). PM 전용 Galaxy S23 비서 앱.

## 빌드
- 로컬: `./gradlew assembleDebug`
- CI: GitHub Actions -> APK artifact 다운로드
- Android SDK 없는 PC: CI 빌드만 사용

## 핵심 기능
1. WiFi 감지 -> 텔레그램 출퇴근 신호
2. 카톡 알림 -> 텔레그램 전달
3. ForegroundService 상시 실행
4. 부팅 시 자동 시작

## 설계서
docs/DESIGN.md
