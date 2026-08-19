from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from fastapi.responses import StreamingResponse

from app.api.schemas.query_schemas import QuerySchema
from app.services.query_service import QueryService
from app.api.dependencies import get_query_service

query_router = APIRouter(tags=['用户提问'])

@query_router.post("/api/query")
async def query(request: QuerySchema,service:Annotated[QueryService,Depends(get_query_service)]):
    return StreamingResponse(service.query_answer(request.query),media_type="text/event-stream")