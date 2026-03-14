@sio.event
async def submit_word(sid, data):
    word = data.get('word')
    user = game_state["participants"].get(sid)
    if not user or not word: return

    # 개발자 여부 확인
    is_dev = user.get("dev", False)

    last_char = game_state["current_word"][-1]
    
    # [치트 로직] 개발자거나, 규칙에 맞으면 통과!
    if is_dev or (word[0] == last_char and len(word) >= 2):
        game_state["current_word"] = word
        
        # 개발자는 점수를 100배로 받음 (치트)
        score_gain = len(word) * 100 if is_dev else len(word) * 10
        user["score"] += score_gain
        
        await sio.emit('word_success', {
            "word": word,
            "nickname": user["nickname"],
            "score": user["score"],
            "isDev": is_dev # 개발자가 성공했음을 알림
        })
