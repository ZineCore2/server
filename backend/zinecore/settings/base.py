import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "insecure-dev-key-change-me")

INSTALLED_APPS = [
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Third-party
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "drf_spectacular",
    # Local apps
    "core",
    "catalog",
    "agents",
    "repositories",
    "holdings",
]

UNFOLD = {
    "SITE_TITLE": "ZineCore2",
    "SITE_HEADER": "ZineCore2 Server",
    "DASHBOARD_CALLBACK": "core.admin.dashboard_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Catalog",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Zines",
                        "icon": "book",
                        "link": "/admin/catalog/zine/",
                    },
                    {
                        "title": "Agents",
                        "icon": "person",
                        "link": "/admin/agents/agent/",
                    },
                    {
                        "title": "Repositories",
                        "icon": "store",
                        "link": "/admin/repositories/repository/",
                    },
                    {
                        "title": "Holdings",
                        "icon": "inventory",
                        "link": "/admin/holdings/holding/",
                    },
                ],
            },
{
                "title": "Controlled Vocabularies",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Subjects",
                        "icon": "label",
                        "link": "/admin/catalog/subject/",
                    },
                    {
                        "title": "Genres",
                        "icon": "category",
                        "link": "/admin/catalog/genre/",
                    },
                    {
                        "title": "Languages",
                        "icon": "language",
                        "link": "/admin/catalog/language/",
                    },
                    {
                        "title": "Rights Statements",
                        "icon": "gavel",
                        "link": "/admin/catalog/rightsstatement/",
                    },
                                        {
                        "title": "Agent Kinds",
                        "icon": "badge",
                        "link": "/admin/agents/agentkind/",
                    },
                    {
                        "title": "Agent Roles",
                        "icon": "work",
                        "link": "/admin/agents/agentrole/",
                    },
                    {
                        "title": "Access Statuses",
                        "icon": "lock",
                        "link": "/admin/holdings/accessstatus/",
                    },
                    {
                        "title": "Distribution Statuses",
                        "icon": "local_shipping",
                        "link": "/admin/holdings/distrostatus/",
                    },
                    {
                        "title": "Repository Kinds",
                        "icon": "business",
                        "link": "/admin/repositories/repokind/",
                    },
                    {
                        "title": "Countries",
                        "icon": "public",
                        "link": "/admin/repositories/country/",
                    },

                ]
            },
            {
                "title": "User Management",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "people",
                        "link": "/admin/auth/user/",
                    },
                    {
                        "title": "Groups",
                        "icon": "groups",
                        "link": "/admin/auth/group/",
                    },
                ],
            },
        ],
    },
    "SITE_DROPDOWN": [
        {
            "icon": "diamond",
            "title": "ZineCore.org",
            "link": "https://zinecore.org",
        },
    ]
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "zinecore.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "zinecore.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME", "zinecore"),
        "USER": os.environ.get("DATABASE_USER", "zinecore"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", "zinecore_dev"),
        "HOST": os.environ.get("DATABASE_HOST", "localhost"),
        "PORT": os.environ.get("DATABASE_PORT", "5433"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "core.permissions.ReadOnlyOrAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ZineCore2 API",
    "DESCRIPTION": "REST API for the ZineCore2 metadata specification",
    "VERSION": "2.0.0",
}

# Path to canonical vocabulary JSON files
VOCAB_CANONICAL_DIR = os.environ.get(
    "VOCAB_CANONICAL_DIR",
    str(BASE_DIR.parent / "spec" / "vocabularies" / "canonical"),
)

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
