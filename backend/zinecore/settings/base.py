import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env from server/ root (parent of backend/) if it exists.
# Real env vars take precedence — this only fills in gaps.
_env_file = BASE_DIR.parent / ".env"
if _env_file.is_file():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _key, _, _val = _line.partition("=")
        os.environ.setdefault(_key.strip(), _val.strip())

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
    "django_extensions",
    # Local apps
    "core",
    "catalog",
    "agents",
    "repositories",
    "geography",
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
                        "title": "External ID Systems",
                        "icon": "fingerprint",
                        "link": "/admin/core/externalidsystem/",
                    },
                    {
                        "title": "External URI Types",
                        "icon": "link",
                        "link": "/admin/core/externaluritype/",
                    },
                    {
                        "title": "Geographic Places",
                        "icon": "public",
                        "link": "/admin/geography/geoplace/",
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
            {
                "title": "Data Management",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Import JSON",
                        "icon": "upload",
                        "link": "/admin/import-json/",
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
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "core.renderers.JSONLDRenderer",
        "core.renderers.CSVRenderer",
        "core.renderers.DublinCoreXMLRenderer",
        "core.renderers.TurtleRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_CONTENT_NEGOTIATION_CLASS": "core.negotiation.FormatOverrideNegotiation",
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
    "DESCRIPTION": (
        "REST API implementing the four ZineCore2 metadata profiles: "
        "**ZineCore2** (zines), **AgentCore2** (people & organizations), "
        "**RepoCore2** (repositories), and **HoldingCore2** (holdings).\n\n"
        "## Authentication\n"
        "Read endpoints are public. Write endpoints require token or session authentication.\n\n"
        "## Output Formats\n"
        "Use the `?format=` query parameter or `Accept` header to request alternate formats:\n\n"
        "| Format | `?format=` | `Accept` header |\n"
        "|--------|-----------|----------------|\n"
        "| JSON | `json` | `application/json` |\n"
        "| JSON-LD | `jsonld` | `application/ld+json` |\n"
        "| CSV | `csv` | `text/csv` |\n"
        "| Dublin Core XML | `dc-xml` | `application/xml` |\n"
        "| RDF/Turtle | `turtle` | `text/turtle` |\n"
        "| BibTeX | `bibtex` | `application/x-bibtex` |\n"
        "| MARCXML | `marcxml` | `application/marcxml+xml` |\n\n"
        "BibTeX is available on `/api/zines/` only. "
        "MARCXML is available on `/api/zines/` and `/api/holdings/`."
    ),
    "VERSION": "2.0.0",
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
    "TAGS": [
        {"name": "Zines", "description": "ZineCore2 profile — bibliographic zine records."},
        {"name": "Agents", "description": "AgentCore2 profile — people and organizations."},
        {"name": "Repositories", "description": "RepoCore2 profile — physical and digital collections."},
        {"name": "Holdings", "description": "HoldingCore2 profile — links between zines and repositories."},
        {"name": "Vocabularies", "description": "Read-only controlled vocabulary endpoints."},
        {"name": "Geography", "description": "GeoNames-based geographic place lookups."},
    ],
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
