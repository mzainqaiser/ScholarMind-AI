"""ScholarMind AI backend entry point.  Run: uvicorn backend.app.main:app --reload"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import agent, analytics, conversations, documents, health, rag, study
from .services.container import Services

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app() -> FastAPI:
    app = FastAPI(title="ScholarMind AI", version="0.1.0",
                  description="Agentic academic research & learning assistant (RAG backend)")
    app.state.services = Services()
    app.add_middleware(CORSMiddleware, allow_origins=app.state.services.settings.cors_origins,
                       allow_methods=["*"], allow_headers=["*"])
    for r in (health.router, documents.router, rag.router, agent.router, conversations.router, study.router, analytics.router):
        app.include_router(r)
    return app


app = create_app()
