"""FastAPI boundary for legal matter intake."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .infrai_gateway import InfraiError, InfraiGateway
from .matter_workflow import MatterIntake, MatterWorkflow


app = FastAPI(title="Legal matter call cost")


@app.exception_handler(InfraiError)
async def infrai_error_response(_request: Request, error: InfraiError) -> JSONResponse:
    status = error.status if 400 <= error.status < 500 else 502
    return JSONResponse(status_code=status, content={"error": error.code, "detail": error.detail})


@app.post("/matters/process")
def process_matter(matter: MatterIntake) -> dict[str, object]:
    result = MatterWorkflow(InfraiGateway.from_environment()).process(matter)
    return result.model_dump(mode="json")
