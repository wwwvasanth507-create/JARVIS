# Notification Manager & Fallback Delivery Architecture

## Notification Channels
1. **TEXT**: Standard output / UI notification stream.
2. **DESKTOP**: OS toast notifications (`win10toast` / `plyer`) with text fallback.
3. **VOICE**: Speech synthesis (`VoiceManager` / `TTSEngine`) with text fallback.

## Fallback Guarantees
If voice synthesis or desktop notifications fail, `NotificationManager` automatically falls back to text delivery, ensuring reminders are never lost.
