# Clean Room Workflow Disclaimer

This documentation represents the observable behavior, interfaces, and functionality
of the Schoology mobile application as determined through:

1. Network traffic analysis (Burp Suite proxy interception)
2. Publicly available API documentation and endpoints
3. Functional observation of the application from a user perspective
4. Decompiled code review for structural understanding only (NOT copied)

No protected expression from the application's source code was copied or reproduced.
All API endpoints, data models, and workflows described are based on:

- Observable network requests and responses
- Standard HTTP/REST patterns
- User interface navigation patterns
- Authentication flows visible through proxy interception
- Configuration data stored in SharedPreferences and environment settings

## Files Excluded from This Repository

The following file types are intentionally excluded via .gitignore to avoid
distributing copyrighted material:

- The original APK file (binary, copyrighted)
- DEX bytecode files (compiled Android VM bytecode)
- Decompiled Java/Kotlin source code
- Raw string extractions from APK
- Analysis dumps containing session tokens or internal keys
- Hardcoded API secrets or credentials

## What IS Included

This repository contains clean documentation of:

- **API endpoint paths and HTTP methods** (standard REST patterns)
- **Authentication flows** (OAuth 1.0a, JWT Bearer tokens)
- **Network architecture** (two-session: SESS + s_mobile + FCM)
- **UI navigation patterns** (activities, fragments, deep links)
- **Response model schemas** (JSON field structures, not code)
- **Third-party service integrations** (Firebase, Gainsight PX, PdfTron)
- **Build and configuration details** (server environments, permissions)

## Legal Compliance

This project follows a "clean room" methodology:
- Analysis was performed by observing application **behavior**, not by reproducing protected code expression
- Documentation describes **interfaces and contracts**, not implementation
- All endpoint paths follow standard HTTP/REST conventions
- No copyrighted source code, variable names, or implementation details are published

## Contact

If you have questions about the methodology or compliance, please review the
accompanying .gitignore and reach out for clarification.

---

This project was generated from reverse engineering of `com.schoology.app` v2026.06.0
for the purpose of understanding application architecture and network flow.
