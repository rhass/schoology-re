#!/usr/bin/env python3
import json
import logging
import re
from collections import Counter, defaultdict
from pathlib import Path

from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = Path("/Users/ryan/schoology-re/apk/schoology.apk")
DEX_DIR = Path("/Users/ryan/schoology-re/dex")
OUT_JSON = Path("/Users/ryan/schoology-re/analysis_data.json")
APP_PREFIX = "Lcom/schoology/app/"
APP_DOT_PREFIX = "com.schoology.app."
MAJOR_PACKAGES = [
    "com.schoology.app.ui",
    "com.schoology.app.network",
    "com.schoology.app.data",
    "com.schoology.app.model",
    "com.schoology.app.service",
    "com.schoology.app.util",
    "com.schoology.app.adapter",
    "com.schoology.app.fragment",
    "com.schoology.app.holder",
    "com.schoology.app.task",
]

logging.getLogger("androguard").setLevel(logging.ERROR)


def to_java(internal):
    if not internal:
        return ""
    return internal.lstrip("L").rstrip(";").replace("/", ".")


def package_of(name):
    return name.rsplit(".", 1)[0] if "." in name else ""


def simple_name(name):
    return name.rsplit(".", 1)[-1]


def is_in_app(name):
    return name == "com.schoology.app" or name.startswith(APP_DOT_PREFIX)


def is_subclass(supername, candidate):
    return supername == candidate


def is_framework_component(supername):
    return supername in {
        "android.app.Application",
        "android.app.Activity",
        "androidx.fragment.app.Fragment",
        "android.app.Fragment",
        "android.app.Service",
        "android.content.BroadcastReceiver",
        "android.content.ContentProvider",
    }


def is_obfuscated_simple_name(name):
    return len(name) <= 3 and name.isalpha() and name.islower()


def class_kind(supername, interfaces):
    if supername == "android.app.Application":
        return "Application"
    if supername == "android.app.Activity" or supername.endswith("Activity"):
        return "Activity"
    if supername in {"androidx.fragment.app.Fragment", "android.app.Fragment"} or supername.endswith("Fragment"):
        return "Fragment"
    if supername == "android.app.Service" or supername.endswith("Service"):
        return "Service"
    if supername == "android.content.BroadcastReceiver" or supername.endswith("Receiver"):
        return "BroadcastReceiver"
    if supername == "android.content.ContentProvider" or supername.endswith("Provider"):
        return "ContentProvider"
    return ""


def class_access_flags(cls):
    try:
        return cls.get_access_flags_string()
    except Exception:
        return ""


def method_names(cls):
    names = []
    try:
        for m in cls.get_methods():
            try:
                names.append(m.get_name())
            except Exception:
                pass
    except Exception:
        pass
    return names


def field_names(cls):
    names = []
    try:
        for f in cls.get_fields():
            try:
                names.append(f.get_name())
            except Exception:
                pass
    except Exception:
        pass
    return names


def source_file(cls):
    try:
        return cls.get_source_file()
    except Exception:
        return ""


def apk_string_values(apk):
    vals = []
    try:
        for s in apk.get_strings():
            vals.append(s)
    except Exception:
        pass
    return vals


def dex_string_values(dex):
    vals = []
    try:
        for s in dex.get_strings():
            vals.append(s)
    except Exception:
        pass
    return vals


def main_activity(apk):
    try:
        return apk.get_main_activity()
    except Exception:
        return None


def main_activities(apk):
    try:
        return list(apk.get_main_activities())
    except Exception:
        return []


def manifest_components(apk):
    result = {}
    for key, func in [
        ("activities", "get_activities"),
        ("services", "get_services"),
        ("receivers", "get_receivers"),
        ("providers", "get_providers"),
    ]:
        try:
            result[key] = list(getattr(apk, func)())
        except Exception:
            result[key] = []
    return result


def apk_files(apk):
    try:
        return list(apk.get_files())
    except Exception:
        return []


def analyze():
    apk = APK(str(APK_PATH))
    dex_objects = []
    dex_meta = []
    for i, raw in enumerate(apk.get_all_dex(), start=1):
        d = DEX(raw)
        dex_objects.append(d)
        dex_meta.append({"index": i, "classes": len(d.get_classes()), "strings": len(d.get_strings())})

    all_classes = []
    seen = set()
    for d in dex_objects:
        for cls in d.get_classes():
            name = to_java(cls.get_name())
            if name not in seen:
                seen.add(name)
                all_classes.append(cls)

    app_classes = []
    app_names = set()
    for cls in all_classes:
        name = to_java(cls.get_name())
        if is_in_app(name):
            app_names.add(name)
            app_classes.append(cls)

    app_data = []
    for cls in app_classes:
        name = to_java(cls.get_name())
        supername = to_java(cls.get_superclassname()) if cls.get_superclassname() else ""
        interfaces = [to_java(i) for i in cls.get_interfaces()]
        app_data.append({
            "name": name,
            "package": package_of(name),
            "simple": simple_name(name),
            "superclass": supername,
            "interfaces": interfaces,
            "access": class_access_flags(cls),
            "source": source_file(cls),
            "methods": method_names(cls),
            "fields": field_names(cls),
            "kind": class_kind(supername, interfaces),
            "obfuscated": is_obfuscated_simple_name(simple_name(name)),
        })

    all_strings = []
    for d in dex_objects:
        all_strings.extend(dex_string_values(d))
    apk_strings = apk_string_values(apk)
    unique_strings = sorted(set(all_strings + apk_strings))

    url_re = re.compile(r"https?://[^\s]+", re.I)
    endpoint_re = re.compile(r"(/api/|/v[0-9]+/|\.schoology\.com|schoology\.com|api\.schoology\.com|graphql|oauth|token|client[_-]?secret|secret|key|base[_-]?url)", re.I)
    secret_re = re.compile(r"(api[_-]?key|client[_-]?secret|secret|password|token|authorization|bearer|private[_-]?key|access[_-]?key|session[_-]?key)", re.I)
    urls = []
    endpoints = []
    secrets = []
    config = []
    for s in unique_strings:
        if not isinstance(s, str) or not s:
            continue
        if url_re.search(s):
            urls.append(s)
        if endpoint_re.search(s):
            endpoints.append(s)
        if secret_re.search(s):
            secrets.append(s)
        if re.search(r"(com\.schoology|schoology|prod|staging|dev|debug|release|config|environment|feature|flag|timeout|retry|cache|database|room|firebase|google|facebook|branch|intercom|pdf|oauth|analytics|crashlytics)", s, re.I):
            config.append(s)

    # Keep the most useful/least noisy subsets for report generation.
    urls = sorted(set(urls))
    endpoints = sorted(set(endpoints))
    secrets = sorted(set(secrets))
    config = sorted(set(config))

    # Networking and persistence detection.
    networking_hits = []
    persistence_hits = []
    for name in sorted(seen):
        low = name.lower()
        if any(k in low for k in ["retrofit", "okhttp", "volley", "moshi", "gson", "rxjava", "rxandroid", "coroutines", "interceptor", "httpurlconnection", "apache/http", "networksecurityconfig"]):
            networking_hits.append(name)
        if any(k in low for k in ["room", "sqlite", "dao", "database", "dbhelper", "contentprovider", "sharedpreferences"]):
            persistence_hits.append(name)

    # Manifest components, de-duplicated.
    manifest = manifest_components(apk)
    for key in manifest:
        manifest[key] = sorted(set(manifest[key]))

    # Navigation resources.
    nav_files = [f for f in apk_files(apk) if "navigation" in f.lower() or f.lower().startswith("res/navigation/")]
    xml_files = [f for f in apk_files(apk) if f.lower().endswith(".xml")]

    # Class package counts.
    package_counts = Counter(package_of(n) for n in app_names)
    major = {}
    for pkg in MAJOR_PACKAGES:
        members = sorted(n for n in app_names if package_of(n) == pkg)
        major[pkg] = members

    # Superclass counts and obfuscation summary.
    super_counts = Counter(c["superclass"] for c in app_data)
    obfuscated = sorted(c["name"] for c in app_data if c["obfuscated"])

    result = {
        "apk": str(APK_PATH),
        "dex_meta": dex_meta,
        "dex_dir": str(DEX_DIR),
        "total_unique_classes": len(seen),
        "app_class_count": len(app_names),
        "app_classes": sorted(app_names),
        "app_data": sorted(app_data, key=lambda x: x["name"]),
        "package_counts": dict(sorted(package_counts.items())),
        "major_packages": major,
        "manifest": manifest,
        "main_activity": main_activity(apk),
        "main_activities": main_activities(apk),
        "nav_files": nav_files,
        "xml_files": xml_files,
        "urls": urls,
        "endpoints": endpoints,
        "secrets": secrets,
        "config_strings": config,
        "networking_hits": sorted(networking_hits),
        "persistence_hits": sorted(persistence_hits),
        "superclass_counts": dict(super_counts.most_common()),
        "obfuscated_classes": obfuscated,
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps({
        "dex_meta": dex_meta,
        "total_unique_classes": len(seen),
        "app_class_count": len(app_names),
        "main_activity": main_activity(apk),
        "main_activities": main_activities(apk),
        "nav_files": nav_files,
        "manifest_counts": {k: len(v) for k, v in manifest.items()},
        "urls_count": len(urls),
        "endpoints_count": len(endpoints),
        "secrets_count": len(secrets),
        "config_count": len(config),
    }, indent=2))


if __name__ == "__main__":
    analyze()
