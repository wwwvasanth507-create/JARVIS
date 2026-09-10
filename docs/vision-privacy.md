# Vision Privacy Architecture

## Privacy Exclusions
`ScreenPrivacyPolicy` maintains a configurable blacklist of sensitive active window titles and application names:
- Password managers (1Password, KeePass, Bitwarden, LastPass)
- Banking & Financial software
- Security & Credential applications
- Lock screens & login screens

## Rules & Enforcements
- Capture Requests targeting blacklisted applications raise `ScreenPrivacyDeniedError`.
- Screenshots are NEVER saved to persistent disk by default.
- Screenshots are stored as transient in-memory objects or brief temporary cache files destroyed immediately after processing.
- Zero external transmissions: No image bytes or visual metadata leave the local machine.
