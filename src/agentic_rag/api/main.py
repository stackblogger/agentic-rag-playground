from fastapi import FastAPI

app = FastAPI(title="Agentic RAG Playground")


@app.get("/health")
def health():
    return {"status": "ok"}
