import os
import urllib.parse

from playhouse.postgres_ext import PostgresqlExtDatabase


def env_var(key, default=None):
    """Retrieves env vars and makes Python boolean replacements"""
    val = os.environ.get(key, default)
    if val == 'True':
        val = True
    elif val == 'False':
        val = False
    return val


DEBUG = env_var('DEBUG', False)

DATABASE_URL = env_var('DATABASE_URL', 'postgres://postgres:postgres@localhost:5433/hot_hub_vs_virus')  # noqa: E501
urllib.parse.uses_netloc.append("postgres")
db_url = urllib.parse.urlparse(DATABASE_URL)
DATABASE = PostgresqlExtDatabase(
    db_url.path[1:],
    user=db_url.username,
    password=db_url.password,
    host=db_url.hostname,
    port=db_url.port,
)

REDIS_URL = env_var('REDIS_URL')
if not REDIS_URL:
    CACHE = {'CACHE_TYPE': 'simple'}
else:
    CACHE = {
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': REDIS_URL,
        'CACHE_DEFAULT_TIMEOUT': 300,
    }
from flask_caching import Cache  # noqa: E402,I001
cache = Cache(config=CACHE)

TELEGRAM_API_KEY = env_var('TELEGRAM_API_KEY', 'telegram')
HOT_VS_VIRUS_WEBSITE = env_var('HOT_VS_VIRUS_WEBSITE', 'hot_vs_virus_website')

SOURCES = {
    'telegram': {
        'api_key': env_var('TELEGRAM_API_KEY', 'telegram'),
        'pending_help_request_callback': '',
    },
    'hot_vs_virus_website': {
        'api_key': env_var('HOT_VS_VIRUS_WEBSITE_API_KEY', 'hot_vs_virus_website'),
        'pending_help_request_callback': '',
    }
}
