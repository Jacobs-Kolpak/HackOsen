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
    
    os.makedirs(os.path.dirname(settings.SSL_CERT_FILE), exist_ok=True)
    if settings.USE_HTTPS and not (os.path.exists(settings.SSL_CERT_FILE) and os.path.exists(settings.SSL_KEY_FILE)):
        from pathlib import Path
        cert_dir = Path(settings.SSL_CERT_FILE).parent
        cert_dir.mkdir(exist_ok=True, parents=True)
        
        print("Генерация самоподписанных SSL сертификатов...")
        import subprocess
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:4096", "-keyout", 
            settings.SSL_KEY_FILE, "-out", settings.SSL_CERT_FILE, 
            "-days", "365", "-nodes", "-subj", f"/CN=localhost"
        ])
        print(f"SSL сертификаты созданы: {settings.SSL_CERT_FILE}, {settings.SSL_KEY_FILE}")
    
    ssl_config = {
        "ssl_keyfile": settings.SSL_KEY_FILE,
        "ssl_certfile": settings.SSL_CERT_FILE,
        "ssl_version": 2, 
    } if settings.USE_HTTPS else {}
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        **ssl_config
    )