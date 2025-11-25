from fastapi import APIRouter

class APIV1:
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1")
    
        @self.router.get("/login")
        def login():
            return {"message": "Login endpoint"}

        @self.router.get("/register")
        def register():
            return {"message": "Register endpoint"}