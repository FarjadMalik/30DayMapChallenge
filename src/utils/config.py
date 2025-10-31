from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG_MODE = config('DEBUG_MODE', default=False, cast=bool)