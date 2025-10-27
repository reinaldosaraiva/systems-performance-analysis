"""
Minimal test server to debug middleware issue
"""

from fastapi import FastAPI
import uvicorn

# Create minimal app
app = FastAPI(title="Test Server")


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
