from decouple import config
import os
from pathlib import Path

class SSLConfig:
    """
    Конфигурация SSL для API
    
    Позволяет настраивать использование SSL сертификатов через переменные окружения
    или файл .env
    """
    # Флаг включения/выключения HTTPS
    USE_SSL: bool = config("USE_SSL", default=False, cast=bool)
    
    # Пути к файлам сертификатов
    CERT_FILE: str = config("SSL_CERT_FILE", default="./certs/cert.pem")
    KEY_FILE: str = config("SSL_KEY_FILE", default="./certs/key.pem")
    
    # Дополнительные настройки SSL
    MIN_TLS_VERSION: str = config("SSL_MIN_TLS_VERSION", default="TLSv1_2")
    MAX_TLS_VERSION: str = config("SSL_MAX_TLS_VERSION", default="TLSv1_3")
    
    @classmethod
    def get_cert_dir(cls) -> Path:
        """Получить директорию для сертификатов"""
        return Path(cls.CERT_FILE).parent
    
    @classmethod
    def ensure_cert_dir_exists(cls) -> None:
        """Создать директорию для сертификатов, если она не существует"""
        cert_dir = cls.get_cert_dir()
        cert_dir.mkdir(exist_ok=True, parents=True)
    
    @classmethod
    def cert_files_exist(cls) -> bool:
        """Проверить существование файлов сертификатов"""
        return os.path.exists(cls.CERT_FILE) and os.path.exists(cls.KEY_FILE)

ssl_config = SSLConfig()