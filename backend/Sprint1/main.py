from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from router.auth import router as auth_router
from router.jobs import router as jobs_router

app = FastAPI(title="ATS SaaS Backend", version="1.0.0")

app.include_router(auth_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail and "detail" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Unauthorized", "detail": "Invalid or missing authentication token"},
        )
    if exc.status_code == status.HTTP_403_FORBIDDEN:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "Forbidden", "detail": "You do not have access to this resource"},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Error", "detail": str(exc.detail)},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
