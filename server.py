from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import socketio
import uvicorn
import os

app = FastAPI()

# 모든 도메인에서의 접속을 허용합니다 (CORS 설정)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.io 서버 설정
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

# 기본 경로로 접속 시 alphinekkutu.html 파일을 보여줍니다
@app.get("/")
async def get_index():
    return FileResponse('alphinekkutu.html')

# 게임 데이터 저장소
game_state = {
    "current_word": "알파인",
    "participants": {}, # sid별 닉네임, 점수, 개발자 여부 저장
}

@sio.event
async def connect(sid, environ):
    print(f"접속: {sid}")

@sio.event
async def join(sid, data):
    nickname = data.get('nickname', '무명')
    # 클라이언트에서 보낸 개발자 인증 여부를 저장합니다
    is_dev = data.get('isDeveloper', False) 
    game_state["participants"][sid] = {"nickname": nickname, "score": 0, "dev": is_dev}
    
    # 현재 게임 단어와 참가자 명단을 모든 유저에게 보냅니다
    await sio.emit('init_state', {
        "word": game_state["current_word"],
        "users": list(game_state["participants"].values())
    })

@sio.event
async def submit_word(sid, data):
    word = data.get('word')
    user = game_state["participants"].get(sid)
    if not user or not word: return

    is_dev = user.get("dev", False) # 해당 유저가 개발자인지 확인
    last_char = game_state["current_word"][-1]

    # [치트 로직] 개발자라면 규칙을 무시하고, 일반인은 끝말잇기 규칙을 지켜야 합니다
    if is_dev or (word[0] == last_char and len(word) >= 2):
        game_state["current_word"] = word
        # 개발자는 점수를 일반 유저보다 10배 더 많이 획득합니다 (치트)
        user["score"] += len(word) * (100 if is_dev else 10)
        
        # 성공 결과를 모든 유저에게 실시간으로 알립니다
        await sio.emit('word_success', {
            "word": word,
            "nickname": user["nickname"],
            "score": user["score"],
            "users": list(game_state["participants"].values())
        })

@sio.event
async def disconnect(sid):
    if sid in game_state["participants"]:
        del game_state["participants"][sid]
        # 유저가 나가면 명단을 다시 갱신합니다
        await sio.emit('init_state', {
            "word": game_state["current_word"],
            "users": list(game_state["participants"].values())
        })

if __name__ == "__main__":
    # Render 등의 환경에서 제공하는 포트 번호를 사용합니다
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(socket_app, host="0.0.0.0", port=port)
