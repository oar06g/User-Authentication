from fastapi import FastAPI
from src.api import APIV1

def run():
    app = FastAPI()
    app.include_router(APIV1().router)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
