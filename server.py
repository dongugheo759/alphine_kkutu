from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse # 파일 전송을 위해 추가
import socketio
import uvicorn
import os

app = FastAPI()

# CORS 설정
origins = ["*"] # 테스트를 위해 모든 도메인 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.io 서버 설정
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

# --- [추가] 브라우저 접속 시 HTML 파일을 보여주는 로직 ---
@app.get("/")
async def get_index():
    # alphinekkutu.html 파일이 server.py와 같은 폴더에 있어야 합니다.
    return FileResponse('alphinekkutu.html')
# --------------------------------------------------

game_state = {
    "current_word": "알파인",
    "participants": {},
}

@sio.event
async def connect(sid, environ):
    print(f"접속: {sid}")

@sio.event
async def join(sid, data):
    nickname = data.get('nickname', '무명')
    is_dev = data.get('isDeveloper', False)
    game_state["participants"][sid] = {"nickname": nickname, "score": 0, "dev": is_dev}
    
    await sio.emit('init_state', {
        "word": game_state["current_word"],
        "users": list(game_state["participants"].values())
    }, to=sid)

@sio.event
async def submit_word(sid, data):
    word = data.get('word')
    user = game_state["participants"].get(sid)
    if not user or not word: return

    last_char = game_state["current_word"][-1]
    if word[0] == last_char and len(word) >= 2:
        game_state["current_word"] = word
        user["score"] += len(word) * 10
        await sio.emit('word_success', {
            "word": word,
            "nickname": user["nickname"],
            "score": user["score"]
        })

if __name__ == "__main__":
    # 80번 포트는 관리자 권한 필수
    uvicorn.run(socket_app, host="0.0.0.0", port=80)