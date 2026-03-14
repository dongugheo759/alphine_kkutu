from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import socketio
import uvicorn
import os

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.io 설정 (로그 포함)
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

game_state = {
    "current_word": "알파인",
    "participants": {}, # {sid: {"nickname": str, "score": int, "dev": bool}}
}

@app.get("/")
async def get_index():
    return FileResponse('alphinekkutu.html')

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
    })

@sio.event
async def submit_word(sid, data):
    word = data.get('word')
    user = game_state["participants"].get(sid)
    if not user or not word: return

    is_dev = user.get("dev", False)
    last_char = game_state["current_word"][-1]

    # [치트 적용] 개발자면 무조건 통과, 일반인은 끝말잇기 규칙 준수
    if is_dev or (word[0] == last_char and len(word) >= 2):
        game_state["current_word"] = word
        # 개발자는 점수 10배 (글자수 * 100)
        user["score"] += len(word) * (100 if is_dev else 10)
        
        await sio.emit('word_success', {
            "word": word,
            "nickname": user["nickname"],
            "score": user["score"],
            "users": list(game_state["participants"].values()) # 전체 명단 갱신
        })

@sio.event
async def disconnect(sid):
    if sid in game_state["participants"]:
        del game_state["participants"][sid]
        await sio.emit('user_left', list(game_state["participants"].values()))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(socket_app, host="0.0.0.0", port=port)
