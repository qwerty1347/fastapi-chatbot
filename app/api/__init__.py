import logging
import pkgutil
import importlib

from types import ModuleType
from fastapi import APIRouter


api_router = APIRouter(prefix="/api")

for module in pkgutil.iter_modules(__path__):
    try:
        version_module: ModuleType = importlib.import_module(
            f"{__name__}.{module.name}"
        )
        api_router.include_router(version_module.api_router)

    except (ModuleNotFoundError, AttributeError) as e:
        logging.getLogger(__name__).error(f"{__name__}.{module.name} import 실패 {e}")
        continue