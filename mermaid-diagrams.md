# Mermaid Diagrams - Schoology APK Reverse Engineering

> Based on decompiled sources from `com.schoology.app` v2026.06.0

## 1. System Architecture

```mermaid
flowchart TB
    subgraph UI["UI Layer"]
        MenuAct["MenuActivity<br/>(SlidingMenu drawer)"]
        Hybrid["HybridPushActivity<br/>(WebView hybrid screens)"]
        Startup["StartupActivity<br/>(ParallelStartup)"]
        Router["RouterActivity<br/>(Deep link entry)"]
        Storage["StorageActivity"]
        Settings["AccountSettingsWebView"]
        Dev["DevSettingsActivity"]
        Login["Login flows<br/>(Native/External/QR/SSO)"]
    end

    subgraph VM["ViewModel / Domain Model"]
        NavVM["SectionNavViewModel"]
        DM["DomainModels<br/>Assignment/User/Section/Discussion/Page"]
    end

    subgraph Data["Data Layer"]
        Repo["Repositories<br/>(ApiStrategy + CacheStrategy)"]
        DM2["Datamodels<br/>(AssignmentData/UserData/...)"]
    end

    subgraph Store["Persistence"]
        GD["GreenDAO<br/>DaoMaster/DaoSession"]
        Cache["OkHttp Cache<br/>CacheFactory/CacheResponsePolicy"]
        File["DownloadStorageManager<br/>FileReferenceUsage"]
    end

    subgraph Net["Network"]
        OkHttp["OkHttpFactory<br/>JWT Signer Interceptor"]
        Retro["Retrofit / SchoologyApiClient"]
        UrlInt["UrlInterceptor<br/>SGYDeepLinkInterceptor"]
        FCM["Firebase<br/>FCM/Analytics/Crashlytics"]
    end

    subgraph DI["DI"]
        Dagger["DaggerAppComponent<br/>NetworkModule/JwtModule"]
    end

    subgraph Ext["External Services"]
        API["api.schoology.com<br/>OAuth 1.0a + JWT"]
        Firebase["Firebase project<br/>api-key hardcoded"]
        PdfTron["PdfTron"]
        Gainsight["Gainsight PX"]
    end

    UI --> VM
    VM --> Data
    Data --> Store
    Data --> Net
    Net --> Ext
    DI --> UI
    DI --> Data
    DI --> Net
    Store --> Net
```

## 2. Authentication & Network Flow

> **Wire-verified 2026-09-22** from a debuggable v2026.06.0 runtime login through Burp.
> Corrects the earlier decompilation-derived assumptions: token requests are GET (not
> POST), credentials are bound via an unsigned web-host endpoint, and the runtime signs
> every API request with OAuth 1.0a. The JWT layer (JwtModule) remains in the app but was
> not exercised in this flow — retained here for later use.

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant LM as LoginManager
    participant LF as AbstractLoginFlow<br/>(Native/ExternalBrowser/AppSso/QR)
    participant WEB as app.schoology.com<br/>(web host)
    participant API as api.schoology.com<br/>(API host)
    participant Ok as OkHttp<br/>(OAuth 1.0a signer)
    participant Retro as Retrofit API
    participant Store as AuthToken Storage
    participant FCM as Firebase FCM

    U->>LM: initiate login
    LM->>LF: select flow
    LF->>WEB: GET /oauth/timestamp (unsigned)
    WEB-->>LF: server epoch (clock-skew offset)
    LF->>API: GET /v1/oauth/request_token<br/>(signed, oauth_token="")
    API-->>LF: oauth_token + secret + ttl=3600
    LF->>U: credentials prompt / QR / browser
    U-->>LF: credentials / scan
    LF->>WEB: POST /oauth/authorize_auto<br/>(UNSIGNED: user, password, oauth_token)
    WEB-->>LF: 204 No Content
    LF->>API: GET /v1/oauth/access_token<br/>(signed with request token, no verifier)
    API-->>LF: access_token + secret (AuthToken)
    LF->>Store: persist AuthToken + clock offset (+ UserInfo)
    LF->>API: GET /v1/users/me (signed)
    API-->>LF: 303 → /v1/users/{uid}
    LF->>API: GET /v1/users/{uid} (RE-SIGNED)
    API-->>LF: user object (uid, name_display, position, child_uids…)
    LF->>Store: persist AuthToken + UserInfo
    LM-->>U: login success

    Ok->>Retro: OAuth-signed /v1/* requests<br/>(per-request HMAC-SHA1 signature)
    Retro->>API: /v1/* endpoints
    API-->>Retro: JSON (singular envelope keys:<br/>section / update / messages / enabled_features)

    Note over Ok,API: JWT layer (JwtModule) is present but not<br/>observed in v2026.06.0: POST /v1/jwt/token<br/>→ Bearer cache → 401 refresh-retry-once.<br/>Retained for later use.

    Note over LM,FCM: Post-login
    LM->>FCM: register FCM token<br/>(FirebaseNotificationRegistrar)
    FCM-->>LM: registration id
```

## 3. UI / Navigation Flow

```mermaid
flowchart LR
    Start["App Start"] --> Startup["StartupActivity<br/>(ParallelStartup)"]
    Startup --> Auth{"Authenticated?"}
    Auth -- No --> Login["Login Flow<br/>(account.* package)"]
    Login --> Menu
    Auth -- Yes --> Menu

    subgraph Menu["MenuActivity — SlidingMenu Drawer"]
        Home["Home"]
        Courses["Courses"]
        Grades["Grades"]
        Groups["Groups"]
        Messages["Messages"]
        Notifications["Notifications"]
        People["People"]
        Requests["Requests"]
        Resources["Resources"]
        Settings["Settings"]
        Calendar["Calendar"]
        Children["Children"]
        Logout["Logout"]
    end

    Menu --> Native["Native Fragments<br/>(SlidingMenuSectionFragment)"]
    Menu --> Hybrid["HybridPushActivity<br/>(WebView + JS Bridge)"]
    Menu --> Deep["DeepLink Router<br/>(deeplink.*)"]
    Menu --> Storage["StorageActivity"]
    Menu --> Dev["DevSettingsActivity"]

    Deep --> Handler{"DeepLinkHost"}
    Handler --> ELH["ExternalLoginHandler<br/>→ Login flow"]
    Handler --> CMR["CourseMaterialRouter<br/>→ Assignment/Section nav"]
    Handler --> PR["ParentRouter<br/>→ ParentMaterial/Submission"]
    Handler --> SCR["ScormHandler / LTI / ExternalTool"]
    Handler --> EDH["ExternalDocumentHandler<br/>→ WebView"]
    Handler --> Gainsight["GainsightDeepLinkHandler"]
```

## 4. Data Persistence & Sync Flow

```mermaid
flowchart TD
    UI2["UI (Fragments/Activities)"] --> Repo["Repository<br/>(ApiStrategy + CacheStrategy)"]
    Repo --> Strategy{"Fetch Strategy"}
    Strategy -- Network --> API2["API (Retrofit)"]
    Strategy -- Cache --> Cache2["OkHttp Cache<br/>CacheFactory / CacheResponsePolicy"]
    Strategy -- DB --> DB2["GreenDAO DB<br/>DaoMaster/DaoSession"]

    subgraph Entities["GreenDAO Entities"]
        E1["AssignmentEntity"]
        E2["UserEntity"]
        E3["SectionEntity"]
        E4["DiscussionEntity"]
        E5["PageEntity"]
        E6["FolderEntity"]
        E7["DocumentEntity"]
        E8["FileEntity"]
        E9["AlbumEntity"]
        E10["InAppNotifsEntity"]
        E11["OfflineInfoEntity"]
        E12["VideoEntity / LinkEntity / EmbedEntity"]
    end

    DB2 --> Entities
    Entities --> DM3["Datamodels<br/>(AssignmentData/UserData/...)"]
    DM3 --> DM4["DomainModels<br/>(AssignmentDomainModel/...)"]
    DM4 --> UI2

    subgraph Sync["Sync Layer"]
        SM["SyncManager"]
        SS["SyncService<br/>(ForegroundService)"]
        SB["SyncBroadcastManager"]
        OCP["OfflineContentPurger<br/>OfflineContentDisposer"]
        CRS["CompletionRulesSyncingHandler"]
        DLM["DownloadStorageManager<br/>DownloadQueue"]
    end

    SM --> Repo
    SM --> SS
    SS --> SB
    SB --> OCP
    OCP --> DLM
    OCP --> CRS
    CRS --> DB2
    SM --> Entities
```

## 5. Key Class / Package Relationships

```mermaid
flowchart TB
    subgraph App["com.schoology.app"]
        subgraph Account["account"]
            LM["LoginManager"]
            LF["AbstractLoginFlow<br/>Native/External/AppSso/QR"]
            Auth["AuthToken / AuthStorageWriter"]
            UM["UserManager"]
        end

        subgraph Api["api"]
            Env["SGYEnvironment<br/>LIVE/STAGING/DEV/SANDBOX/CANADIAN"]
            Ok["OkHttpFactory<br/>JWT Signer Interceptor"]
            Cache["CacheFactory<br/>CacheResponsePolicy/InvalidateCache"]
        end

        subgraph Data["dataaccess"]
            subgraph Repo["repository"]
                R1["AssignmentRepository<br/>DiscussionRepository"]
                R2["UserRepository / SchoolRepository"]
                R3["Messages / Notifications / Grades"]
                R4["File / Folder / Page / Document"]
            end
            subgraph DM["datamodels"]
                M1["AssignmentData / UserData"]
                M2["SectionData / SchoolData"]
                M3["FolderItemData / PageData"]
            end
        end

        subgraph DB["dbgen"]
            G["GreenDAO Entities + Daos<br/>DaoMaster / DaoSession"]
        end

        subgraph DI["di"]
            D1["DaggerAppComponent"]
            D2["NetworkModule / JwtModule"]
            D3["RepositoryModule / LoginModule"]
        end

        subgraph Hybrid["hybrid"]
            H1["HybridPushActivity"]
            H2["HybridPresenter / HybridViewModel"]
            H3["HybridInteractor / JSBridge"]
            H4["HybridWebSession / Renderers"]
        end

        subgraph Nav["navigation"]
            N1["MenuActivity / SlidingMenu"]
            N2["SlidingMenuFragment<br/>SlidingMenuSectionFragment"]
            N3["StartupActivity / ParallelStartup"]
        end

        subgraph DL["deeplink"]
            DL1["RouterActivity / DeepLinkHost"]
            DL2["Handlers (ExternalLogin/CourseMaterial/Parent)"]
            DL3["RouterModule (Dagger)"]
        end

        subgraph Other["..."]
            O1["pushnotification (FCM)"]
            O2["logging (Analytics/Gainsight)"]
            O3["imageloader (Glide/SVG)"]
            O4["sync (SyncManager/SyncService)"]
            O5["persistence (CacheManager/DbHelper)"]
        end
    end

    Account --> Api
    Account --> DI
    Api --> Data
    Data --> DB
    Data --> Hybrid
    DI --> Account
    DI --> Data
    DI --> Api
    DI --> Hybrid
    Nav --> Hybrid
    Nav --> DL
    DL --> Account
    DL --> Data
    Other --> Data
    Other --> DB
```

## 6. Deep Link Routing Flow

```mermaid
flowchart TD
    Ext["External Intent / schoology:// URL"] --> RA["RouterActivity"]
    RA --> V{"DeeplinkUrlValidator"}
    V -- Invalid --> Err["RoutingResult.NotRouted"]
    V -- Valid --> HR["DeepLinkHost.parse()"]

    HR --> Kind{"Host Type"}
    Kind -- EXTERNAL_LOGIN --> ELH["ExternalLoginHandler<br/>→ Login flow"]
    Kind -- EXTERNAL_DOCUMENT --> EDH["ExternalDocumentHandler<br/>→ WebView"]
    Kind -- EXTERNAL_LINK_MATERIAL --> ELIH["ExternalLinkHandler<br/>→ CourseMaterialRouter"]
    Kind -- EXTERNAL_TOOL_MATERIAL --> ETH["ExternalToolHandler<br/>→ LTI/SCORM"]
    Kind -- LTI_ASSIGNMENT --> LTIH["LTIAssignmentHandler"]
    Kind -- SCORM_MATERIAL --> SCH["ScormHandler"]
    Kind -- GAINSIGHT_LINK --> GDH["GainsightDeepLinkHandler"]
    Kind -- COURSE_MATERIAL --> CMR["CourseMaterialRouter<br/>→ Assignment/Section nav"]
    Kind -- PARENT_* --> PR["ParentRouter<br/>→ ParentMaterial/Submission"]
    Kind -- SECTION/OPEN_SUBMISSION --> SR["StartupRouter / ComposableRouter"]

    ELH --> LM2["LoginManager"]
    CMR --> Navig["Native screen navigation<br/>(SectionNavViewModel)"]
    PR --> Navig
    SR --> Navig
    EDH --> HW["HybridPushActivity"]
    ETH --> HW
    SCH --> HW
    LTIH --> HW

    Navig --> R{"RoutingResult"}
    R -- NeedsLogin --> LM2
    R -- Routed --> Done["Screen displayed"]
    R -- NotRouted --> Err
```
