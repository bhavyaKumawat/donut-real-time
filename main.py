import uvicorn
import base64
import cv2
import numpy as np
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocket

from detect import run

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        resp = predict(data)
        await websocket.send_json(resp)


def from_b64(uri):
    """
        Convert from b64 uri to OpenCV image
        Sample input: 'data:image/jpg;base64,/9j/4AAQSkZJR......'
    """
    encoded_data = uri.split(',')[1]
    data = base64.b64decode(encoded_data)
    np_arr = np.fromstring(data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img


def to_b64(img):
    """
        Convert from OpenCV image to b64 uri
        Sample output: 'data:image/jpg;base64,/9j/4AAQSkZJR......'
    """
    _, buffer = cv2.imencode('.jpg', img)
    uri = base64.b64encode(buffer).decode('utf-8')
    return f'data:image/jpg;base64,{uri}'


def predict(data):
    try:
        img = from_b64(data)
        frame, count = run(img)
        resp = {'frame': to_b64(frame), 'count': count}
        return resp

    except:
        resp = {'frame': data, 'count': ''}
        return resp

