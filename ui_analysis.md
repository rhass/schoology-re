# UI Architecture Analysis - Schoology APK

> Based on decompiled sources from `com.schoology.app` v2026.06.0

## 1. UI Layer Overview

| Layer | Components |
|-------|-----------|
| Activities | 52 declared in manifest |
| Fragments | SlidingMenuSectionFragment + many feature fragments |
| ViewModels | SectionNavViewModel, feature-specific VMs |
| Domain Models | AssignmentDomainModel, UserDomainModel, SectionDomainModel, etc. |
| Hybrid | HybridPushActivity (WebView + JS bridge) |

## 2. Main Flow

```
ApplicationUtil.onCreate()
    │
    └── MenuActivity (Main)
            │
            ├── SlidingMenuDrawer (sidebar)
            │   ├── Home
            │   ├── Courses
            │   ├── Grades
            │   ├── Groups
            │   ├── Messages
            │   ├── Notifications
            │   ├── People
            │   ├── Requests
            │   ├── Resources
            │   ├── Settings
            │   ├── Calendar
            │   └── Logout
            │
            ├── Native Fragments
            │   └── SlidingMenuSectionFragment (per section)
            │
            ├── Hybrid Screens
            │   └── HybridPushActivity (WebView + JS Bridge)
            │
            └── Deep Links
                └── RouterActivity → DeepLinkHost → Handler
```

## 3. Login Flow

Multiple login methods supported (AbstractLoginFlow subclasses):
- **LoginNativeActivity** - Email/password
- **LoginExternalActivity** - External browser (WebView)
- **LoginOAuthManagementActivity** - OAuth account management
- **LoginSearchActivity** - School search
- **QRCodeCameraActivity** - QR code scan login
- **SSOLoginActivity** - App SSO
- **ExternalLoginSelectionActivity** - Choose login method
- **LoginNativeActivity** - Standard native login

Login result managed via `BehaviorSubject<LoginResult>` in `LoginManager`.

## 4. Hybrid Architecture (WebView)

```
assets/bundle.js (webpack bundle, 36KB)
    │
    ├── GainsightPX (analytics engine)
    ├── JS Bridge
    │   ├── window.gpxjs.postMessage(JSON.stringify(body))
    │   │   → Android: tsWindow.gpxjs.postMessage()
    │   │   → iOS: window.webkit.messageHandlers.gpxjs.postMessage()
    │   └── sendMessage(body) → platform-specific bridge
    └── engineStarted/startEngine()

HybridPushActivity
    ├── WebView (loads hybrid screens)
    ├── JSBridge (native ↔ web communication)
    ├── HybridPresenter / HybridViewModel
    ├── HybridInteractor
    ├── HybridWebSession management
    └── Renderers (content rendering)
```

## 5. Deep Link Routing

All deep links route through:
```
RouterActivity → DeeplinkUrlValidator → DeepLinkHost → Handler
```

| Handler | Purpose |
|---------|---------|
| ExternalLoginHandler | Login flow |
| ExternalDocumentHandler | Open document in WebView |
| ExternalLinkHandler | Link to course material |
| LtiHandler | LTI content |
| ScormHandler | SCORM content |
| ExternalToolHandler | External tools (LTI/SCORM) |
| LTIAssignmentHandler | LTI assignment |
| GainsightDeepLinkHandler | Gainsight links |
| CourseMaterialRouter | Navigate to assignment/section |
| ParentRouter | Parent-specific material/submission |
| StudentDocumentRouter | Student document |
| SubmissionDocumentLink | Submission doc links |
| OpenSubmissionLink | Open submission |
| MyChildren | My Children screen |

## 6. UI Packages

| Package | Contents |
|---------|----------|
| `ui.login` | Login screens |
| `ui.login.appsso` | App SSO + interceptor |
| `ui.courses` | Course screens, LTI, SCORM, WebViews |
| `ui.courses.viewmodel` | Course ViewModels |
| `ui.courses.scorm` | SCORM content |
| `ui.courses.lti` | LTI content |
| `ui.courses.createSession` | Session creation |
| `ui.album.gallery` | Photo albums |
| `ui.grades` | Grades |
| `ui.grades.finalgrades` | Final grades |
| `ui.messages` | Messages |
| `ui.notifications` | Notifications |
| `ui.share` | Sharing |
| `ui.submissions` | Assignment submissions |
| `ui.school` | School detail |
| `ui.section` | Section detail |
| `ui.profile.old` | User profile |
| `ui.calendar` | Calendar |
| `ui.events` | Events |
| `ui.discussion` | Discussions |
| `ui.page` | Pages |
| `ui.people` | People |
| `ui.groups` | Groups |
| `ui.requests` | Friend requests |
| `ui.parentwebview` | Parent WebView |
| `ui.elementary` | Elementary mode |
| `ui.startup` | Startup logic |
| `ui.badges` | Badges |
| `ui.attachment` | Attachments |
| `ui.fileIO` | File operations |
| `ui.widget` | Custom widgets |
| `navigation.slidingMenu` | SlidingMenu |
| `navigation.startup` | Startup |
| `navigation` | MenuActivity, etc. |
| `deeplink` | Deep link routing |
| `hybrid` | WebView hybrid |
| `account` | Login, auth |
| `sync` | Sync engine |
| `pushnotification` | Push handling |
| `dev.settings` | Developer settings |
| `settings` | App settings |
| `storage` | Storage management |

## 7. State Management

| State Component | Purpose |
|----------------|---------|
| BehaviorSubject<LoginResult> | Login state |
| Variable<...> | Reactive variables (RxJava) |
| SyncProgress | Sync progress state |
| SyncConfig | Sync configuration |
| ViewModels | Feature state retention |

## 8. Image Loading

| Library | Usage |
|---------|-------|
| Glide | Primary image loader (`GlideImageLoader`) |
| Picasso | Secondary (`PicassoProvider`) |
| SVG | Vector drawable support |

## 9. Third-Party UI/UX

| Component | Integration | Purpose |
|-----------|------------|---------|
| SlidingMenu | `com.schoology.app.navigation` | Sidebar drawer |
| PdfTron | `com.pdftron.pdf.utils` | PDF viewer |
| ZXing (via journeyapps) | `com.journeyapps.barcodescanner` | QR code scanning |
| Firebase Crashlytics | Native | Crash reports |
| Gainsight PX | Web bundle | Product analytics |

## 10. Navigation Graph Summary

```
StartupActivity
    ├── Authenticated → MenuActivity
    └── Not Authenticated → Login flows

MenuActivity
    ├── Home → HomeFragment
    ├── Courses → CourseListFragment → CoursePagerActivity
    │   ├── Assignment detail
    │   ├── Discussion
    │   ├── Materials
    │   └── LTI/SCORM → WebView
    ├── Grades → GradesActivity → FinalGradesActivity
    ├── Groups → GroupPagerActivity → GroupDetailFragment
    ├── Messages → MessageListActivity → MessageDetailActivity
    ├── Notifications → NotificationListActivity
    ├── People → PeopleListActivity
    ├── Requests → RequestListActivity
    ├── Resources → ResourceListActivity
    ├── Settings → AccountSettingsWebView / DevSettingsActivity
    ├── Calendar → CalendarActivity
    ├── Children → ElementaryCourseActivity
    ├── Storage → StorageActivity
    └── Deep Links → RouterActivity

RouterActivity → DeepLinkHost → Handler → various destinations
HybridPushActivity → WebView → hybrid screens
```

## 11. Key UI Classes

| Class | Role |
|-------|------|
| `ApplicationUtil` | Application class, context provider |
| `SchoologyBaseActivity` | Base activity for all screens |
| `MenuActivity` | Main screen with drawer |
| `RouterActivity` | Deep link routing |
| `HybridPushActivity` | WebView hybrid |
| `LoginManager` | Login state management |
| `UserManager` | User data management |
| `AuthToken` | Token data |
| `AuthStorageWriter` | Token persistence |
| `ServerConfig` | Server configuration |
| `SyncManager` | Sync orchestration |
| `SyncService` | Sync background work |
