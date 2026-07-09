"""
main.py
--------
FastAPI application entrypoint for the RetailIQ backend.

Run (from project root):
    uvicorn api.main:app --reload --port 8000

Then open:
    http://localhost:8000/docs   (interactive Swagger UI)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(
    title="RetailIQ API",
    description="Sales Analytics & Demand Insights REST API for the RetailIQ project.",
    version="1.0.0",
)

# Allow the local dashboard (or any frontend during development) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "Welcome to the RetailIQ API",
        "docs": "/docs",
        "endpoints": [
            "/dashboard", "/sales", "/sales/monthly", "/products", "/products/top",
            "/customers", "/customers/top", "/stores", "/inventory",
            "/inventory/reorder", "/forecast",
        ],
    }
