"""FastAPI app entrypoint. """


from __future__ import annotations

from fastapi import FastAPI

from cmo_platform.api.routers import datasets, expression
from cmo_platform.config import settings

app = FastAPI(title='Cardiometabolic Crosstalk Omics Platfrom API')

app.include_router(datasets.router, prefix= settings.api_v1_prefix)
app.include_router(expression.router, prefix=settings.api_v1_prefix)

