# Schoology APK Reverse Engineering — Clean-Room Analysis

This repository contains a clean-room reverse engineering analysis of the Schoology mobile application (`com.schoology.app`, v2026.06.0). The goal is to document **observable behavior, API contracts, and architecture** without redistributing copyrighted application code, APK binaries, or proprietary session data.

---

## What's Here (Most Important First)

| File | Priority | What It Tells You |
|------|----------|-------------------|
| `SCHOOLYOGY_APK_REVERSE_ENGINEERING.md` | ★★★★★ | **Main report.** Full architecture, auth flow, API endpoints, security findings, Burp results |
| `GAP_ANALYSIS.md` | ★★★★☆ | **What's complete vs. missing.** Status of every reverse-engineering area, including remaining gaps |
| `network_analysis.md` | ★★★★☆ | **API endpoint reference.** REST paths, auth, third-party domains, parent portal endpoints |
| `ui_analysis.md` | ★★★☆☆ | **UI architecture.** Activities, fragments, ViewModels, deep-link routing |
| `mermaid-diagrams.md` | ★★★☆☆ | **Visual diagrams.** System architecture, auth flow, data flow |

---

## Supporting Files

| File / Dir | Purpose |
|------------|---------|
| `analyze_schoology.py` | Androguard-based static analysis script that generated `analysis_data.json` |
| `api_endpoints.txt` | Extracted endpoint strings from the APK |
| `deep_links.txt` | Deep-link intent filters and routing targets |
| `domains.txt` | Network domains found in the APK |
| `burp_project_settings.json` | Burp Suite project configuration (no raw traffic) |
| `manifest_clean.json` / `manifest_detailed.txt` | Parsed AndroidManifest (permissions, activities, services) |
| `mise.toml` / `mise-tasks/bootstrap` | Reproducible build environment (Java 17, JADX, dex2jar, Vineflower) |

---

## Deliberately Excluded (See `.gitignore`)

These are **not** committed to avoid copyright and security issues:

- `apk/` — original APK binary
- `dex/` — DEX bytecode
- `decompiled_java/` — decompiled source code
- `extracted/` — raw APK extraction (DEX, resources, native libs)
- `strings.txt` — raw string dump (may contain proprietary data)
- `secret_dex2.txt` — dex2jar output
- `firebase_keys.txt` / `google_api_keys.txt` — extracted keys
- `urls.txt` — raw URL extraction
- `ssl_pinning.txt` — empty, no pinning found
- `oauth_tokens.txt` — empty, no tokens

**Why:** These contain copyrighted material or sensitive data that should not be redistributed.

---

## Clean-Room & Legal

- See `NOTICE.md` for the full clean-room methodology and disclaimer
- See `LICENCE` — this work is licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**
- Documentation describes **interfaces and behavior**, not copied implementation
- No session tokens, packet captures, or live user data are published

---

## Key Findings (TL;DR)

1. **Two auth layers:** OAuth 1.0a token exchange → JWT Bearer tokens (`POST /jwt/token`)
2. **Two sessions:** mobile API (`s_mobile` cookie) + web portal (`SESS` cookie) + FCM token
3. **Parent portal:** `/parent/*` and `/iapi/parent/*` endpoints — not visible in static analysis
4. **PowerSchool integration:** Neon 2.6.1 + PDS 31.0.0 assets embedded in parent HTML
5. **No certificate pinning** — Burp interception possible with APK patching
6. **Attendance is teacher-only** — permission-gated, hidden for student/parent roles
7. **Batch API:** `/v1/multioptions` and `/v1/multiget` reveal endpoint methods

---

## Reproduce the Analysis

```bash
mise install
mise run bootstrap
python3 analyze_schoology.py
```

The script uses Androguard to extract classes, strings, endpoints, and manifest data.

---

## Remaining Gaps

See `GAP_ANALYSIS.md` → "Remaining Gaps" section. Highest priority:
- `/parent/grades_attendance/attendance` (parent view)
- PowerSchool PDS app-switcher behavior
- Multi-child profile switching

---

## Contact / Attribution

Licensed under CC BY 4.0 — attribution required for reuse. See `LICENCE` for full terms.
