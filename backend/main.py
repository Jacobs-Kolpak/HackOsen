from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.auth import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Защищенная система аутентификации с JWT токенами",
    version="1.0.0",
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix="/api/jacobs/auth")


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    import os
    import ssl
    
    os.makedirs(os.path.dirname(settings.SSL_CERT_FILE), exist_ok=True)
    if settings.USE_HTTPS and not (os.path.exists(settings.SSL_CERT_FILE) and os.path.exists(settings.SSL_KEY_FILE)):
        from pathlib import Path
        cert_dir = Path(settings.SSL_CERT_FILE).parent
        cert_dir.mkdir(exist_ok=True, parents=True)
    
        print("Генерация самоподписанных SSL сертификатов с SAN...")
        import subprocess
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:4096", "-keyout",
            settings.SSL_KEY_FILE, "-out", settings.SSL_CERT_FILE,
            "-days", "365", "-nodes",
            "-subj", "/CN=localhost",
            "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1"
        ], check=True)
        print(f"SSL сертификаты созданы: {settings.SSL_CERT_FILE}, {settings.SSL_KEY_FILE}")
    
    # Явно задаем TLS 1.2–1.3 через SSLContext
    ssl_ctx = None
    if settings.USE_HTTPS:
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_ctx.maximum_version = ssl.TLSVersion.TLSv1_3
        ssl_ctx.load_cert_chain(certfile=settings.SSL_CERT_FILE, keyfile=settings.SSL_KEY_FILE)
    
    # Запуск Uvicorn с SSLContext через Config/Server
    if ssl_ctx:
        config = uvicorn.Config(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.DEBUG,
            ssl_certfile=settings.SSL_CERT_FILE,
            ssl_keyfile=settings.SSL_KEY_FILE
        )

        server = uvicorn.Server(config)
        server.run()
    else:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.DEBUG
        )