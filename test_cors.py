from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from threading import Thread
import time
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/test")
def test():
    return {"ok": True}

def run():
    uvicorn.run(app, host="127.0.0.1", port=8005)

t = Thread(target=run)
t.daemon = True
t.start()
time.sleep(2)

response = httpx.options("http://127.0.0.1:8005/test", headers={
    "Origin": "https://vercel.app",
    "Access-Control-Request-Method": "GET"
})
print("STATUS:", response.status_code)
print("HEADERS:", response.headers)
