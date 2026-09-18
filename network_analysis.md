# Network Analysis - Schoology APK

> Based on decompiled Java sources from `com.schoology.app` v2026.06.0

## 1. API Configuration

### Server Config
| Field | Value |
|-------|-------|
| Config Key | `A_CONF` (SharedPreferences) |
| Config Class | `ServerConfig` (singleton via `Companion`) |
| Environment Config | `SGYEnvironment` enum (LIVE/STAGING/SANDBOX/DEV/CANADIAN/LOCAL) |

### Server Environments
| Environment | Host |
|------------|------|
| LIVE | `schoology.com` |
| STAGING | `schoologystg.com` |
| SANDBOX | `schoologytest.com` |
| DEV | `qa-mobile.schoologydev.com` |
| CANADIAN | `schoologyca.com` |
| LOCAL | `localenv.ninja` |

## 2. Authentication Flow

```
Step 1: OAuth 1.0a Request Token
  POST /v1/oauth/request_token
  → Returns: request_token + request_token_secret

Step 2: User credentials / QR scan / SSO
  User authenticates (varies by flow type)

Step 3: OAuth 1.0a Access Token
  POST /v1/oauth/access_token
  → Returns: access_token + access_token_secret (AuthToken)

Step 4: JWT Token Acquisition
  POST /jwt/token (OAuth 1.0a signed request)
  → Returns: JWT token string

Step 5: Subsequent API Calls
  Header: Authorization: Bearer <jwt_token>
  Auto-refresh on 401 via JwtSignerInterceptor
```

## 3. JWT Token Management

| Component | Class | Purpose |
|-----------|-------|---------|
| JwtCache | `JwtCache` | Store/retrieve JWT token |
| JwtAuthenticator | `JwtAuthenticator` | Authenticate via `/jwt/token` |
| JwtAuthenticatorApi | `JwtAuthenticatorApi` | Retrofit interface for JWT endpoint |
| JwtSignerInterceptor | `JwtSignerInterceptor` | Add Bearer header, auto-refresh |
| JwtProgressiveBackoffInterceptor | `JwtProgressiveBackoffInterceptor` | Backoff for failed requests |
| JwtAuthenticationFailureHandler | `JwtAuthenticationFailureHandler` | Handle auth failure |
| JwtExpiration | `JwtExpiration` | Token expiry check |
| JwtAuthenticationKt | `JwtAuthenticationKt` | Kotlin extensions |

### JWT Token Lifecycle
1. Stored in JwtCache (in-memory + persistent)
2. `JwtSignerInterceptor.intercept()`:
   - Check cache for non-expired token
   - If expired → `JwtAuthenticator.authenticate()` → POST `/jwt/token`
   - Add `Authorization: Bearer <token>` header
   - Execute request
   - If 401 → invalidate cache, retry once
   - If 401 again → call `authenticationFailureHandler.onAuthenticationFailure()`

## 4. OkHttpClient Configuration

| Property | Source |
|----------|--------|
| Client factory | `OkHttpFactory` |
| Retry interceptor | `JwtSignerInterceptor` |
| Auth failure handler | `JwtAuthenticationFailureHandler` |
| Progressive backoff | `JwtProgressiveBackoffInterceptor` |
| Cache interceptor | `InvalidateCacheInterceptor` |
| Cache response policy | `CacheResponsePolicy` |
| Cache outcome | `CacheOutcome` |
| Credential | `CredentialFactory` (OAuth 1.0a) |

## 5. Retrofit Configuration

| Property | Value |
|----------|-------|
| Factory | `RestAdapterFactory.v1RestAdapter()` |
| Base URL | `ServerConfig.m17431d()` (from environment) |
| Read timeout | 1 minute (from `ApiModule`) |
| Converter | Gson (default Retrofit) |
| Call adapter | RxJava (`Single`, `Observable`, `Completable`) |

### API Interfaces
| Interface | Endpoints |
|-----------|-----------|
| `AssignmentApi` | section/assignment/submission, submissions revisions |
| `FileServiceApi` | File upload/download |
| `JwtAuthenticatorApi` | `/jwt/token` |
| `Credential` | OAuth 1.0a |

## 6. REST API Endpoints

### Auth
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/oauth/request_token` | OAuth request token |
| POST | `/v1/oauth/access_token` | OAuth access token |
| POST | `/jwt/token` | JWT token |
| GET | `/login/school_lookup` | School lookup |
| GET | `/login/school_search` | School search |

### Users
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/users/me` | Current user |
| GET | `/users/{user_id}` | User profile |
| GET | `/users/{user_id}/grades` | Grades |
| GET | `/users/{user_id}/groups` | Groups |
| GET | `/users/{user_id}/sections` | Sections |
| GET | `/users/{user_id}/requests/friends` | Friend requests |

### Schools
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/schools` | List |
| GET | `/schools/{school_id}` | Detail |
| GET | `/schools/{school_id}/buildings` | Buildings |

### Courses
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/courses/{course_id}` | Detail |
| GET | `/courses/{course_id}/folder` | Folder |
| GET | `/courses/{course_id}/metadata` | Metadata |

### Groups
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/groups/{group_id}/albums` | Albums |
| GET | `/groups/{group_id}/albums/{album_id}/content` | Album content |
| GET | `/groups/{group_id}/discussions` | Discussions |
| GET | `/groups/{group_id}/documents` | Documents |
| GET | `/groups/{group_id}/events` | Events |
| GET | `/groups/{group_id}/pages` | Pages |

### Sections
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/sections/{section_id}/assignments` | Assignments |
| GET | `/sections/{section_id}/submissions` | Submissions |
| GET | `/sections/{section_id}/submissions/{sub_id}/{user_id}/revision/{rev_id}` | Revision |
| GET | `/sections/{section_id}/grades` | Grades |
| GET | `/sections/{section_id}/grading_scales` | Grading scales |
| GET | `/sections/{section_id}/materials_hierarchy` | Materials |
| GET | `/sections/{section_id}/folders` | Folders |
| GET | `/sections/{section_id}/enrollments` | Enrollments |
| GET | `/sections/{section_id}/attendance` | Attendance |
| GET | `/sections/accesscode` | Access code |

### Messages
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/messages/inbox` | Inbox |
| GET | `/messages/sent` | Sent |
| GET | `/messages/recipients` | Recipients |

### Files
| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/file` | File operations |
| GET | `/files/{file_id}/annotations` | Annotations |
| GET | `/upload/{upload_id}` | Upload |

### Mobile
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/mobile/me` | Mobile profile |
| GET | `/mobile/enabled_features` | Feature flags |
| GET | `/mobile/notifications` | Notifications |
| GET | `/notifications` | Notifications |
| GET | `/notifications/read` | Mark read |

### Batch
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/multiget` | Multi-get |
| GET | `/multioptions` | Multi-options |

## 9. Parent Portal Endpoints (Burp Capture — 2026-09-18)

Parent portal uses **web session** (`SESS` cookie) + **mobile session** (`s_mobile` cookie) simultaneously.

### Parent Flow

| Endpoint | Method | Status | Purpose |
|----------|--------|--------|---------|
| `/parent` | GET | 302 → `/parent/home` | Entry point; requires `SESS` cookie |
| `/parent/home` | GET | 200 HTML | Parent dashboard (PowerSchool Neon 2.6.1 + PDS 31.0.0 assets) |
| `/iapi/parent/info` | GET | 200 JSON | Parent session info: `session.view_mode=1`, `view_child=<child_uid>`, child profiles, `recent_counts` |
| `/home/feed?page=0&children=<uid>` | GET | 200 JSON | HTML feed of submission notifications per child |
| `/iapi/parent/overdue_submissions/<child_uid>` | GET | 200 JSON | Overdue assignments with course/section context |
| `/course/<course_id>/preview/<child_uid>/parent` | GET | 200 HTML | Parent view of course (deep link) |
| `/parent/grades_attendance/grades` | GET | 200 HTML | Grades/attendance parent view |

### Parent AJAX Headers
- `X-Csrf-Token` + `X-Csrf-Key` headers required for all AJAX requests
- Session cookies: `SESS` (web) + `s_mobile` (mobile API)

### Parent Data Model (from Burp responses)
- `view_mode`: `1` (parent mode)
- `view_child`: `<child_uid>` (active child profile)
- `recent_counts`: Summary counts of recent activity per child
- Child profiles returned by `/iapi/parent/info` include: uid, name, grade_level, school_id

---

## 10. PowerSchool Integration (Burp Capture — 2026-09-18)

### Embedded Assets
| Domain | Version | Purpose | Source |
|--------|---------|---------|--------|
| `assets.powerschool.com/neon/2.6.1` | Neon 2.6.1 | PowerSchool Neon UI components (icons, buttons) | Loaded in parent portal HTML |
| `assets.powerschool.com/pds/31.0.0` | PDS 31.0.0 | PowerSchool design system toolkit + app switcher | Loaded in parent portal HTML |

### Integration Points
- PowerSchool UI is embedded **in the parent portal** (`app.schoology.com/parent/*`)
- App switcher links to PowerSchool PDS (`docs.powerschool.com`)
- No separate PowerSchool APK in scope — integration is via web assets
- Neon/PDS JS bundles loaded as `<script>` tags in parent HTML pages

### Known PowerSchool Pages (via app.schoology.com)
| Page | Notes |
|------|-------|
| `/parent/home` | Main parent dashboard with PowerSchool Neon header |
| `/parent/grades_attendance/grades` | Grades/attendance (PowerSchool data) |
| `/course/{id}/preview/{child}/parent` | Course preview (PowerSchool-backed) |

### API Integration
- PowerSchool data served through Schoology parent API endpoints (`/iapi/parent/*`)
- No direct PowerSchool API endpoints observed in Burp traffic (all proxied through Schoology)
- App switcher transitions Schoology → PowerSchool PDS in browser

---

## 11. Third-Party API Domains

| Domain | Service | Notes |
|--------|---------|-------|
| `*.googleapis.com` | Google APIs (Maps, Sign-In) | |
| `*.firebaseio.com` | Firebase Realtime DB | |
| `*.firebaseapp.com` | Firebase Hosting | |
| `*.crashlytics.com` | Crashlytics | |
| `*.gainsightpx.com` | Gainsight PX | |
| `*.gstatic.com` | Google services | |
| `assets.powerschool.com` | PowerSchool Neon/PDS | Static assets only |
| `app.schoology.com` | Schoology parent portal | Web session (SESS cookie) |
| `files-cdn.schoology.com` | File CDN | Signed CloudFront URLs |

### Analytics (from Burp)
| Domain | Purpose | Notes |
|--------|---------|-------|
| `bam.nr-data.net` | New Relic RUM | 403 Forbidden — rate-limited |
| `firebaseinstallations.googleapis.com` | FCM | Android cert `F3F50D...`, ES256 JWT, expiresIn 604800s |
| `esp-mobile-us2.aptrinsic.com` | Aptrinsic analytics | `SESSION_INITIALIZED`, `IDENTIFY`, `APP_INSTALLED` |

---

## 12. Sync Endpoints

### Download Jobs (from SyncManager)
| Job | Endpoint | Data |
|-----|----------|------|
| AssignmentsDownloadJob | `/sections/{sectionId}/assignments` | Assignments |
| DiscussionsDownloadJob | `/groups/{groupId}/discussions` | Discussions |
| DocumentsDownloadJob | `/groups/{groupId}/documents` | Documents |
| PagesDownloadJob | `/groups/{groupId}/pages` | Pages |
| AlbumsDownloadJob | `/groups/{groupId}/albums` | Albums |
| FoldersDownloadJob | `/courses/{courseId}/folder` | Folders |

## 9. Security Assessment

### Findings
1. **Hardcoded Google API key** - in Firebase config
2. **OAuth 1.0a** - Consumer key/secret in native code
3. **JWT tokens** - Persistent storage (no short-lived tokens)
4. **No certificate pinning** - In OkHttpClient configuration
5. **No mTLS** - Standard TLS only
6. **Deep links** - No authentication required for link opening

### Recommendations
1. Implement certificate pinning
2. Rotate API keys
3. Add mTLS for sensitive endpoints
4. Validate deep link URLs server-side
5. Use short-lived JWT tokens with refresh tokens
