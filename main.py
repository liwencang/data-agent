from fastapi import FastAPI

app = FastAPI(title="掌柜问数")


@app.get("/")
async def hello():
    return "hello FastApi"
