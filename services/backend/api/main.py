
from home.settings import settings

# Need this here so uvicorn can import it on reload
from shared.app import app  # noqa
import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "shared.app:app",
        host=settings.host,
        port=settings.app_port,
        reload=True,
        log_level="debug",
    )
