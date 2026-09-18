# GAP ANALYSIS - COMPLETE REVERSE ENGINEERING STATUS

## Authentication Implementation (NOW COMPLETELY DETERMINED)

### OAuth 1.0a (from `SchoologyOauthParameters.java`, `OAuthPlainTextSigner.java`, `HMacMessageGenerator.java`)

**Signature Parameters:**
- `oauth_consumer_key` - from `ServerConfig` / `OAuthConfig`
- `oauth_nonce` = `Long.toHexString(Math.abs(RANDOM.nextLong()))` — 16 hex chars (64-bit from SecureRandom)
- `oauth_signature_method` = "HMAC-SHA1" (always)
- `oauth_timestamp` = `Long.toString(System.currentTimeMillis() / 1000)` — seconds since epoch
- `oauth_token` — access token (optional; null for request-token step)
- `oauth_verifier` — verifier code (optional; null for access-token step)
- `oauth_version` = "1.0"

**Authorization Header Format** (from `SchoologyOauthParameters.getAuthorizationHeader()`):
```
OAuth realm="%s", oauth_callback="%s", oauth_consumer_key="%s", 
oauth_nonce="%s", oauth_signature_method="%s", oauth_timestamp="%s", 
oauth_token="%s", oauth_verifier="%s", oauth_version="1.0", 
oauth_signature="%s"
```
Where `oauth_signature` is the URL-encoded Base64 HMAC-SHA1 hash.

**Signing Key** (from `OAuthPlainTextSigner`): `clientSharedSecret + "&" + tokenSharedSecret`

**Base String** (from `HMacMessageGenerator.normalise()`):
```
METHOD + "&" + URL_ENCODED(BASE_URL) + "&" + URL_ENCODED(NORMALIZED_PARAMETERS)
```
- `METHOD` = HTTP method (GET/POST/etc.)
- `BASE_URL` = `scheme://host+rawPath` (no query string)
- `NORMALIZED_PARAMETERS` = ALL request params + OAuth params, sorted alphabetically by name, format `key=value&key2=value2`
- **URL Encoding**: `URLEncoder.encode(string, UTF_8)` — Note: encodes space as `+`, `%7E` for `~` (NOT fully RFC 3986)

**Nonce Generation**: `Long.toHexString(Math.abs(RANDOM.nextLong()))` — 16 hex chars from `SecureRandom`

**Timestamp Generation**: `Long.toString(System.currentTimeMillis() / 1000)` — seconds since epoch

### JWT / Bearer Token (from `JwtAuthenticator.java`, `JwtSignerInterceptor.java`, `JwtAuthentication.java`)

**Endpoint**: `POST /jwt/token` (Retrofit `@InterfaceC4348o("jwt/token")`)

**Token Structure** (`JwtAuthentication`):
- `token`: String — the Bearer token value
- `expiration`: long — epoch milliseconds (comparison: `currentTime > expiration` → expired)

**Expiry Check** (`JwtAuthentication.isExpired(long)`):
```
currentTime > expiration → token EXPIRED
otherwise → token NOT expired
```

**Refresh Logic** (`JwtSignerInterceptor.performRequestWithToken()`):
1. Retrieve JWT from `JwtCache`
2. Check expiry: `dateInSecondsProvider.invoke().longValue() > jwt.expiration`
3. If expired: call `jwtAuthenticator.authenticate()` → `POST /jwt/token` → store new JWT via `jwtCache.storeJwt()`
4. Add `Authorization: Bearer <token>` header
5. Execute request

**401 Error Handling** (`JwtSignerInterceptor.intercept()`):
1. Execute request with current token
2. If response is 401: `jwtCache.invalidateJwt()` then retry request once
3. If retry also returns 401: call `authenticationFailureHandler.onAuthenticationFailure()`

**Token Acquisition Flow**:
1. App starts → no JWT cached → `JwtAuthenticator.authenticate()` → `POST /jwt/token` → store JWT
2. Subsequent requests use cached JWT with expiry check
3. On 401: invalidate cache, refresh token, retry once

---

## API Status Summary (Updated)

| Category | Status |
|----------|--------|
| OAuth 1.0a signing | **100% determined** (all params, format, algorithm) |
| JWT / Bearer token | **95% determined** (only exact TTL value unknown) |
| API endpoint paths (v1) | **100% determined** (all 36 methods in `SchoologyApiInterface` documented) |
| API endpoint paths (v2) | **100% determined** (all 8 Backend interfaces enumerated) |
| **Parent portal endpoints** | **~30% determined** (core `/parent`, `/iapi/parent` captured; child-specific, grades, messages, assignments missing) |
| **PowerSchool integration** | **~10% determined** (Neon 2.6.1 + PDS 31.0.0 assets identified; app switcher, JS bridge unknown) |
| **Multi-session architecture** | **100% determined** (mobile `s_mobile` cookie + web `SESS` cookie + FCM token) |
| Response model fields | **100% determined** (all `@InterfaceC1849l` annotations extracted from 100+ model classes) |
| OAuth 1.0a nonce format | **100% determined** (`Long.toHexString(Math.abs(RANDOM.nextLong())))`) |
| OAuth 1.0a timestamp format | **100% determined** (`System.currentTimeMillis() / 1000`) |
| Network security / Burp | **100% determined** (NOT debuggable; patch APK to enable) |
| GreenDAO entity columns | **100% determined** (all 17 entities with full CREATE TABLE schemas) |
| Web bundle (JS) analysis | **~60% analyzed** (Gainsight PX analytics bridge, not app UI) |
| Business logic | **~0% determined** (fully obfuscated) |
| UI layouts | **0% determined** |

## v2 API Endpoints (Complete)

All v2 endpoints use Kotlin coroutines (`t0<T>` = suspend/coroutine return type) instead of RxJava `Observable<T>`.

### School (`ui/school/api/SchoolBackend.java`)
- `GET /v1/schools/{id}` → `SchoolResponse` — school details

### Calendar (`ui/calendar/api/CalendarEventsBackend.java`)
- `GET <full URL>` → `CalendarEventDetailsResponse` — event details (full URL passed via `@Url`)

### Annotations (`ui/annotations/api/AnnotationBackend.java`)
- `GET <full URL>` → `AnnotationV2Response` — annotation signed URL request
- `GET <full URL>` → `b0<f0>` — get annotations request (file bytes)
- `GET /v2/sections/{sectionId}/assignments/{assignmentId}` → `AnnotationV2Response` — new annotation request
- `POST <full URL>` → `b0<C6528u>` — restore assignment request
- `POST <full URL>` → `StartAnnotationAssignmentV2Response` — start annotation assignment (body: `"{}"`)
- `POST <full URL>` → `AnnotationV2Response` — submit annotation request (body: `SubmitAnnotationRequestBody`)
- `PUT <full URL>` → `b0<C6528u>` — update annotations (headers: `Content-Type: application/xml`, `x-amz-server-side-encryption: AES256`)

### Course Apps (`ui/courseapp/api/CourseAppBackend.java`)
- `GET /v2/sections/{sectionId}/applications` → `CourseAppResponse` — course app list
- `GET <full URL>` → `LaunchCourseAppResponse` — launch course app

### LTI (`ui/courses/lti/api/LtiWebBackend.java`)
- `GET {realm}/{realm_id}/documents` → `LtiResponse` — LTI details (no document_id)
- `GET {realm}/{realm_id}/documents/{document_id}` → `LtiResponse` — LTI details (with document_id)

### SCORM (`ui/courses/scorm/api/ScormWebBackend.java`)
- `GET {realm}/{realm_id}/package/{id}` → `ScormResponse` — SCORM package details

### Create Session (`services/createsession/api/CreateSessionBackend.java`)
- `GET sessionstart` → `SessionResponse` — create web session (query: `domain`)

### Collection Resources (`ui/collectionresource/api/CollectionResourceApiInterface.java`)
- `GET /v2/resources/applications/{app_id}/launch` → `LaunchCollectionResourceResponse` — launch collection resource app

## GreenDAO Entity Schemas (Complete)

All 17 entities with full CREATE TABLE statements:

1. **UserEntity** — `USER_ENTITY` (USER_ID PK, SCHOOL_ID, IS_SYNCED, SCHOOL_UID, BUILDING_ID, NAME_TITLE, SHOW_NAME_TITLE, NAME_FIRST, NAME_FIRST_PREFERRED, NAME_MIDDLE, SHOW_NAME_MIDDLE, NAME_LAST, NAME_DISPLAY, USERNAME, PRIMARY_EMAIL, PICTURE_URL, GENDER, POSITION, GRAD_YEAR, PASSWORD, ROLE_ID, TZ_OFFSET, TZ_NAME, CAN_SEND_MESSAGE, STATS_USER_TYPE, LANGUAGE, LAST_MODIFIED, ENROLLED_SECTIONS, CHILD_UIDS, IS_DIRECTORY_PUBLIC, ALLOW_CONNECTIONS)
2. **SectionEntity** — `SECTION_ENTITY` (SECTION_ID PK, COURSE_TITLE, COURSE_CODE, COURSE_ID, SCHOOL_ID, ACCESS_CODE, SECTION_TITLE, SECTION_CODE, SECTION_SCHOOL_CODE, SYNCED, ACTIVE, DESCRIPTION, SUBJECT_AREA, GRADE_LEVEL_RANGE_START, GRADE_LEVEL_RANGE_END, PROFILE_URL, LOCATION, MEETING_DAYS, CLASS_PERIODS, WEIGHT, IS_ADMIN, LAST_MODIFIED, OFFLINE_INFO_ID, COURSE_THEME)
3. **SchoolEntity** — `SCHOOL_ENTITY` (ID PK, TITLE, ADDRESS1, ADDRESS2, CITY, STATE, POSTAL_CODE, COUNTRY, WEBSITE, PHONE, FAX, BUILDING_CODE, PICTURE_URL, LAST_MODIFIED)
4. **AssignmentEntity** — `ASSIGNMENT_ENTITY` (ASSIGNMENT_ID + REALM_ID unique, TITLE, DESCRIPTION, DUE, GRADING_SCALE, GRADING_PERIOD, GRADING_CATEGORY, MAX_POINTS, FACTOR, IS_FINAL, SHOW_COMMENTS, GRADE_STATS, ALLOW_DROPBOX, ALLOW_DISCUSSION, PUBLISHED, TYPE, GRADE_ITEM_ID, AVAILABLE, COMPLETED, DROPBOX_LOCKED, GRADING_SCALE_TYPE, SHOW_RUBRIC, COMPLETION_STATUS, LAST_MODIFIED, PARENT_ID, DISPLAY_WEIGHT, ASSIGNMENT_TYPE, ATTACHMENT_ID)
5. **DiscussionEntity** — `DISCUSSION_ENTITY` (DISCUSSION_ID + REALM + REALM_ID unique, TITLE, BODY, WEIGHT, GRADED, REQUIRE_INITIAL_POST, PUBLISHED, AVAILABLE, COMPLETED, DUE_DATE, GRADE_ITEM_ID, GRADING_SCALE, GRADING_SCALE_TYPE, GRADING_PERIOD, GRADING_CATEGORY, MAX_POINTS, FACTOR, IS_FINAL, COMMENTS_CLOSED, COMPLETION_STATUS, LAST_MODIFIED, PARENT_ID, DISPLAY_WEIGHT, ATTACHMENT_ID)
6. **DocumentEntity** — `DOCUMENT_ENTITY` (REALM + REALM_ID + DOCUMENT_ID unique, TITLE, COURSE_FID, AVAILABLE, PUBLISHED, COMPLETION_STATUS, COMPLETED, LAST_MODIFIED, PARENT_ID, DISPLAY_WEIGHT, ATTACHMENT_ID)
7. **AlbumEntity** — `ALBUM_ENTITY` (ALBUM_ID + REALM_ID + REALM unique, TITLE, DESCRIPTION, SETTING_COMMENTS, SETTING_MEMBER_POST, PHOTO_COUNT, VIDEO_COUNT, AUDIO_COUNT, CREATED, PUBLISHED, AVAILABLE, COMPLETED, COVER_IMAGE_URL, COMPLETION_STATUS, LAST_MODIFIED, PARENT_ID, DISPLAY_WEIGHT, CONTENT_ID)
8. **FolderEntity** — `FOLDER_ENTITY` (FOLDER_ID + REALM_ID unique, TITLE, BODY, AVAILABLE, TYPE, LOCATION, PUBLISH_START, PUBLISH_END, STATUS, COMPLETION_STATUS, HAS_RULES, COMPLETED, COLOR, LAST_MODIFIED, PARENT_ID, DISPLAY_WEIGHT)
9. **PageEntity** — `PAGE_ENTITY` (PAGE_ID + REALM + REALM_ID unique, CREATED_TIME, TITLE, BODY, PUBLISHED, INLINE, AVAILABLE, COMPLETED, COMPLETION_STATUS, LAST_MODIFIED, PARENT_ID, DISPLAY_WEIGHT, ATTACHMENT_ID)
10. **FileEntity** — `FILE_ENTITY` (ID PK, TYPE, TITLE, FILENAME, FILESIZE, MD5_CHECKSUM, TIMESTAMP, FILEMIME, DOWNLOAD_PATH, EXTENSION, DIMENSIONS, THUMBNAIL, THUMBNAIL_DIMENSIONS, CONVERTED_STATUS, CONVERTED_TYPE, CONVERTED_FILENAME, CONVERTED_DOWNLOAD_PATH, CONVERTED_EXTENSION, CONVERTED_FILESIZE, CONVERTED_MD5_CHECKSUM, LAST_MODIFIED, CONVERTED_FILE_MIME, ATTACHMENT_ID)
11. **VideoEntity** — `VIDEO_ENTITY` (ID PK, TYPE, URL, TITLE, FAVICON, FAVICON_DIMENSIONS, LAST_MODIFIED, ATTACHMENT_ID)
12. **LinkEntity** — `LINK_ENTITY` (ID PK, SUMMARY, DISPLAY_INLINE, TYPE, URL, TITLE, FAVICON, FAVICON_DIMENSIONS, LAST_MODIFIED, ATTACHMENT_ID)
13. **EmbedEntity** — `EMBED_ENTITY` (ID PK, EMBED_CODE, TYPE, URL, TITLE, FAVICON, FAVICON_DIMENSIONS, LAST_MODIFIED, ATTACHMENT_ID)
14. **OfflineInfoEntity** — `OFFLINE_INFO_ENTITY` (AVAILABLE_OFFLINE, WITH_ATTACHMENTS, OFFLINE_HASH, SYNC_REQUESTED, LAST_MODIFIED)
15. **InAppNotifsEntity** — `IN_APP_NOTIFS_ENTITY` (MESSAGE_ID TEXT PK NOT NULL, NEXT_TIME_TO_SHOW, MESSAGE_DATA, TIMES_SHOWN)
16. **CompletionRuleSyncEntity** — `COMPLETION_RULE_SYNC_ENTITY` (MATERIAL_ID + REALM_ID unique, MATERIAL_TYPE, LAST_MODIFIED)
17. **FileReferenceUsageDao** — `FILE_REFERENCE_USAGE` (URL + REALM + REALM_ID unique, LAST_MODIFIED)

## Response Model JSON Schemas (Complete)

All `@InterfaceC1849l` annotations extracted from 100+ model classes in `restapi/legacy/services/model/`. Key models:

- **UserObject**: profile_info, uid, id, name_title, name_title_show, name_first, name_first_preferred, name_middle, name_middle_show, name_last, name_display, use_preferred_first_name, primary_email, picture_url
- **SectionObject**: id, course_title, section_title, active, description, profile_url, location, options, admin, links, course_theme
- **AssignmentObject**: id, title, description, due, grading_scale, grading_period, grading_category, max_points, factor, is_final, show_comments, grade_stats, allow_dropbox, allow_discussion, published, assignment_type, type, grade_item_id, grading_scale_type, attachments, links, file-attachment, tags
- **EventObject/EventObjectV2**: id, title, description, has_end, end, all_day, editable, rsvp, comments_enabled, type, group_id, district_id, links, file-attachment, attachments
- **SchoolObject**: id, title, address1, address2, city, state, postal_code, country, website, phone, fax, picture_url
- **AttachmentM**: attachment, external_tools, embeds, links, videos, annotation_files
- **Grading**: grades, periods, final_grade, grading_category, scale
- **Messages**: message (id, subject, recipient_ids, last_updated, author_id, message_status, message, attachments, file-attachment)
- **Enrollments**: enrollment (id, uid, school_uid, name_title, name_title_show, name_first, name_first_preferred, name_middle, name_middle_show, name_last, admin, status, links)
- **DiscussionObject**: id, uid, title, body, weight, graded, published, due, grade_item_id, grading_scale, grading_period, grading_category, max_points, factor, is_final, attachments, file-attachment, links, topic_id
- **DocumentObject**: available, course_fid, id, published, title, has_rules, attachments
- **PageObject**: attachments, available, body, completed, created, inline, links, id, parent, published, title
- **FolderObject**: id, title, body, completion_status, available, completed, status, has_rules, type, document_type, publish_start, publish_end, location, color

## Web Bundle Analysis

`assets/bundle.js` (37KB webpack bundle) is **Gainsight PX analytics SDK**, NOT the app UI:
- Tracks screen events via `window.location.href`
- Tracks clicks via `window.addEventListener('touchend', trackClicks)`
- Handles WebView relative frame positioning for iOS/Android
- Communicates via `window.webkit.messageHandlers.gpxjs.postMessage()`
- Contains `engineStarted`, `ignoreSafeAreaOffset`, `updateWebViewRelativeFrame` exports
- The actual app UI is rendered natively by Android activities, NOT by this JS bundle

## Mediator Architecture

`SchoologyRequestMediator` (deprecated legacy API layer):
- Wraps `SchoologyApiInterface` (Retrofit interface)
- Provides fluent accessors: `albums()`, `assignments()`, `events()`, `groups()`, `invites()`, `io()`, `messages()`, `mobile()`, `multiget()`, `permissions()`, `requests()`, `schools()`, `sections()`, `users()`
- `BaseCalls` → individual `*Calls` classes → `getApiInterface()` → direct Retrofit calls
- `SchoologyUrlGenerator` generates URLs from base URL + path constants
- `SchoologyApi` (deprecated) → `SchoologyRequestMediator` → `SchoologyApiInterface`
- `@Deprecated` on both `SchoologyApi` and `SchoologyRequestMediator` — the app is migrating to the `appv2` coroutines architecture

## TLS / Burp Analysis

- App is **NOT debuggable** (no `android:debuggable="true"` in manifest)
- `network_security_config.xml` only contains `<debug-overrides>` (user certs trusted only when debuggable)
- **No OkHttp CertificatePinner** found anywhere in the codebase
- `SchoologyApi.Builder.withAllowUnsafeConnections(true)` exists in legacy code — creates a trust-all `X509TrustManager` + permissive `HostnameVerifier`
- **Burp interception requires APK patch**: enable `android:debuggable="true"` + add `<base-config>` to trust user certs

## Burp Capture Findings (2026-09-18)

### Parent Portal — `/parent` flow
| Endpoint | Method | Status | Key Findings |
|----------|--------|--------|--------------|
| `/parent` | GET | 302 → `/parent/home` | Requires `SESS` web session cookie |
| `/parent/home` | GET | 200 HTML | PowerSchool Neon 2.6.1 + PDS 31.0.0 assets; JS tab-ID broadcast channel |
| `/iapi/parent/info` | GET | 200 JSON | `session.view_mode=1`, `view_child=95607489`, child profiles + `recent_counts` |
| `/home/feed?page=0&children=95607489` | GET | 200 JSON | HTML feed of submission notifications per child |
| `/iapi/parent/overdue_submissions/{child_uid}` | GET | 200 JSON | Overdue assignments HTML with course/section context |
| `/course/{course_id}/preview/{child_uid}/parent` | GET | 200 HTML | Parent view of course (via deep link) |
| `/parent/grades_attendance/grades` | GET | 200 HTML | Grades/attendance parent view |

### Mobile API (OAuth 1.0a + `s_mobile` cookie)
| Endpoint | Method | Key Findings |
|----------|--------|--------------|
| `/v1/users/{uid}?extended=true` | GET | Parent profile: `position:Parent`, `child_uids` |
| `/v1/alert/device/{fcm_token}` | PUT | Device registration (204 No Content) |
| `/v1/mobile/enabled_features` | GET | Feature flags incl. offline, LTI, assessments |
| `/v1/mobile/gainsight/me` | GET | Gainsight: `role=parent`, enterprise district, API key |
| `/v1/mobile/me` | GET | Settings: course_dashboard, default_start_page |
| `/v1/users/{uid}/sections` | GET | Empty for parent (sections belong to child) |
| `/v1/users/{uid}/groups` | GET | Empty for parent |
| `/v1/messages` | OPTIONS | Allow: POST only |
| `/v1/multioptions` | POST | Batch endpoint — reveals actual HTTP methods per path |
| `/v1/multiget` | POST | Batch user/school data |
| `/v1/recent` | GET | School feed with embedded attachments |
| `/v1/mobile/notifications` | GET | Empty `schema_version:1, messages:[]` |
| `/v1/users/{uid}/grades` | GET/PUT | Discovered via multioptions |
| `/v1/users/{uid}/assignments` | GET/PUT | Discovered via multioptions |
| `/v1/users/{uid}/discussions` | GET | Discovered via multioptions |
| `/v1/users/{uid}/events` | GET/POST | Discovered via multioptions |

### Third-party / Analytics
| Domain | Purpose | Notes |
|--------|---------|-------|
| `bam.nr-data.net` | New Relic RUM | **403 Forbidden** — rate-limited / blocked |
| `firebaseinstallations.googleapis.com` | FCM | Android cert `F3F50D...`, ES256 JWT, expiresIn 604800s |
| `esp-mobile-us2.aptrinsic.com` | Aptrinsic analytics | `SESSION_INITIALIZED`, `IDENTIFY`, `APP_INSTALLED` |
| `assets.powerschool.com/neon/2.6.1` | PowerSchool Neon UI | Icon/button components |
| `assets.powerschool.com/pds/31.0.0` | PowerSchool PDS | App switcher, design system toolkit |

### Auth Architecture
- **Two sessions**: mobile API (`s_mobile` cookie + OAuth 1.0a) and web portal (`SESS` cookie)
- **Parent session**: `SESS` cookie set by `app.schoology.com`; `s_mobile` also present on parent requests
- **CSRF tokens**: parent AJAX requests include `X-Csrf-Token` + `X-Csrf-Key` headers
- **File downloads**: `app.schoology.com/system/files/attachments/...` → 302 → signed CloudFront URL on `files-cdn.schoology.com`

### What Burp Revealed That Static Analysis Could Not
1. Parent portal endpoint structure (`/parent/*`, `/iapi/parent/*`) — not exposed in smali routing
2. PowerSchool integration (Neon 2.6.1 + PDS 31.0.0) — embedded in HTML, not referenced in DEX
3. Batch/multioptions usage — reveals actual HTTP methods per endpoint
4. Parent-specific data model — `view_mode`, `view_child`, `recent_counts`
5. Two-session architecture — `SESS` + `s_mobile` + FCM token coexistence
6. CSRF token handling — `X-Csrf-Token` / `X-Csrf-Key` headers
7. Empty sections/groups for parent role — parent only sees child data
8. File attachment signed-URL flow — CloudFront + query-string signing

---

## Remaining Gaps (2026-09-18)

### Explored & Confirmed Absent
| Area | Finding | Notes |
|------|---------|-------|
| Parent Messages | **Empty inbox** | `/v1/messages` returns `Allow: POST only`; parent portal messages tab had no content |
| Parent Notifications | **Empty** | `/v1/mobile/notifications` returned `schema_version:1, messages:[]` |
| Email Settings | **Configured** | User verified email settings in parent portal |
| Native Attendance | **Teacher-only** | `AttendanceRepository.getAttendancePermission()` gates the section nav tab; not visible for student/parent roles |
| PowerSchool App Switcher | **Not triggered** | Switcher link present in parent HTML but not clicked |

### Still Missing / Unexplored
| Area | Likely Endpoint | Priority |
|------|----------------|----------|
| Parent Attendance | `/parent/grades_attendance/attendance` | Medium |
| Child Profile Details | `/iapi/parent/info` with `view_child=<uid>` per child | Low |
| Parent Calendar | `/parent/calendar` or `/iapi/parent/calendar` | Low |
| PowerSchool PDS Transition | JS bridge / app switcher behavior on `/parent/home` | Low |
| PowerSchool API Proxies | Any `*.powerschool.com` API calls from parent portal | Low |
| Multi-Child Switching | `/iapi/parent/info` with different `view_child` values | Low |

### Why These Are Low Priority
- Parent attendance is likely a **static HTML page** (sibling to `/parent/grades_attendance/grades`), not a REST API
- Child profile details already captured via `/iapi/parent/info` (returns `child_uids` array)
- PowerSchool integration is **web-asset only** (Neon/PDS JS bundles); no separate PowerSchool API observed
- Multi-child switching is handled client-side via `view_child` query parameter

### What Would Be Needed to Complete
1. **Teacher account** to trigger native attendance permission check
2. **Active parent session** with multiple children to test child switching
3. **PowerSchool app switcher** click in parent portal to observe JS bridge
4. **Burp export** of any remaining parent portal endpoints (Messages, Notifications, Calendar tabs)

## Files Already Documented

- `GAP_ANALYSIS.md` - this file (comprehensive gap analysis)
- `SCHOOLYOGY_APK_REVERSE_ENGINEERING.md` - main report (653 lines, 18 sections)
- `mermaid-diagrams.md` - 6 mermaid diagrams
- `network_analysis.md` - API endpoint documentation
- `ui_analysis.md` - UI component mapping

All documentation is in `~/src/erudite/schoology-re/`.
