import discord
from discord import app_commands
from discord.ext import commands
import json, os, asyncio, random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_PATH = "./data"
FILES = ["config","game","points","shop","voice"]

# ---------------------------
# 파일 자동 생성
# ---------------------------
if not os.path.exists(DATA_PATH):
    os.mkdir(DATA_PATH)

for f in FILES:
    path = f"{DATA_PATH}/{f}.json"
    if not os.path.exists(path):
        with open(path,"w",encoding="utf-8") as file:
            json.dump({},file)

def load(name):
    with open(f"{DATA_PATH}/{name}.json","r",encoding="utf-8") as f:
        return json.load(f)

def save(name,data):
    with open(f"{DATA_PATH}/{name}.json","w",encoding="utf-8") as f:
        json.dump(data,f,indent=4,ensure_ascii=False)

async def auto_delete(interaction):
    await asyncio.sleep(3)
    try:
        await interaction.delete_original_response()
    except:
        pass

def get_nick(user):
    return user.display_name.split("/")[0]

def check_channel(interaction,key):
    config = load("config")
    gid = str(interaction.guild.id)
    return config.get(gid,{}).get(key)==interaction.channel.id

# ---------------------------
# 채널 설정
# ---------------------------
@tree.command(name="게임닉네임")
@app_commands.checks.has_permissions(administrator=True)
async def set_game(interaction: discord.Interaction):
    config = load("config")
    gid=str(interaction.guild.id)
    config.setdefault(gid,{})
    config[gid]["game"]=interaction.channel.id
    save("config",config)

    await interaction.response.send_message("게임채널 설정 완료",ephemeral=True)
    await auto_delete(interaction)

@tree.command(name="음성채널")
@app_commands.checks.has_permissions(administrator=True)
async def set_voice(interaction: discord.Interaction):
    config = load("config")
    gid=str(interaction.guild.id)
    config.setdefault(gid,{})
    config[gid]["voice"]=interaction.channel.id
    save("config",config)

    category = interaction.channel.category
    vc = await interaction.guild.create_voice_channel("➕ 음성채널 생성하기",category=category)

    voice = load("voice")
    voice[str(vc.id)] = "generator"
    save("voice",voice)

    await interaction.response.send_message("생성 채널 만들어짐",ephemeral=True)
    await auto_delete(interaction)

@tree.command(name="오늘뭐하지")
@app_commands.checks.has_permissions(administrator=True)
async def set_food(interaction: discord.Interaction):
    config=load("config")
    gid=str(interaction.guild.id)
    config.setdefault(gid,{})
    config[gid]["food"]=interaction.channel.id
    save("config",config)

    await interaction.response.send_message("추천채널 설정 완료",ephemeral=True)
    await auto_delete(interaction)

@tree.command(name="출석체크")
@app_commands.checks.has_permissions(administrator=True)
async def set_attendance(interaction: discord.Interaction):
    config=load("config")
    gid=str(interaction.guild.id)
    config.setdefault(gid,{})
    config[gid]["attendance"]=interaction.channel.id
    save("config",config)

    await interaction.response.send_message("출석채널 설정 완료",ephemeral=True)
    await auto_delete(interaction)

# ---------------------------
# 음성채널 생성 시스템
# ---------------------------
@bot.event
async def on_voice_state_update(member,before,after):
    voice = load("voice")

    # 생성채널 들어감
    if after.channel and str(after.channel.id) in voice:
        if voice[str(after.channel.id)] != "generator":
         return
        category = after.channel.category
        new_vc = await member.guild.create_voice_channel("방이름을 변경해주세요.",category=category)

        voice[str(new_vc.id)] = member.id
        save("voice",voice)

        await member.move_to(new_vc)

    # 방 비었을 때 삭제
    if before.channel and str(before.channel.id) in voice:
        # 🔥 생성채널은 삭제 금지
     if voice[str(before.channel.id)] == "generator":
        return

     if len(before.channel.members)==0:
        try:
            del voice[str(before.channel.id)]
            save("voice",voice)
            await before.channel.delete()
        except:
            pass

# 방 이름 변경 제한
@bot.event
async def on_guild_channel_update(before,after):
    voice = load("voice")
    cid = str(after.id)

    if cid in voice and voice[cid]!="generator":
        owner = voice[cid]

        # 방장 없으면 제한 해제
        if not any(m.id==owner for m in after.members):
            return

        # 변경 시도자 체크
        # discord는 누가 바꿨는지 직접 제공 안해서 완벽차단은 어려움
        # 대신 이름 되돌리는 방식
        if before.name != after.name:
            try:
                await after.edit(name=before.name)
            except:
                pass

# ---------------------------
# 게임 프로필
# ---------------------------
profile_messages={}

@tree.command(name="등록")
async def register(interaction: discord.Interaction):
    if not check_channel(interaction,"game"):
        return

    data=load("game")
    gid,cid,uid=str(interaction.guild.id),str(interaction.channel.id),str(interaction.user.id)

    data.setdefault(gid,{}).setdefault(cid,{})
    data[gid][cid][uid]={"nickname":get_nick(interaction.user),"games":{}}
    save("game",data)

    await interaction.response.send_message("등록 완료",ephemeral=True)
    await auto_delete(interaction)

@tree.command(name="게임")
async def add_game(interaction: discord.Interaction,게임:str,닉네임:str):
    if not check_channel(interaction,"game"):
        return

    data=load("game")
    gid,cid,uid=str(interaction.guild.id),str(interaction.channel.id),str(interaction.user.id)

    data[gid][cid][uid]["games"][게임]=닉네임
    save("game",data)

    await interaction.response.send_message("추가 완료",ephemeral=True)
    await auto_delete(interaction)

@tree.command(name="게임수정")
async def edit_game(interaction: discord.Interaction,게임:str,닉네임:str):
    await add_game(interaction,게임,닉네임)

@tree.command(name="게임삭제")
async def delete_game(interaction: discord.Interaction,게임:str):
    if not check_channel(interaction,"game"):
        return

    data=load("game")
    gid,cid,uid=str(interaction.guild.id),str(interaction.channel.id),str(interaction.user.id)

    data[gid][cid][uid]["games"].pop(게임,None)
    save("game",data)

    await interaction.response.send_message("삭제 완료",ephemeral=True)
    await auto_delete(interaction)

@tree.command(name="프로필")
async def profile(interaction: discord.Interaction,닉네임:str):
    data=load("game")
    gid,cid=str(interaction.guild.id),str(interaction.channel.id)

    for uid,info in data.get(gid,{}).get(cid,{}).items():
        if info["nickname"]==닉네임:
            embed=discord.Embed(title=f"🌸{닉네임}님의 프로필🌸",color=0x6EC6FF)

            if info["games"]:
                for g, n in info["games"].items():
                    embed.add_field(
                        name=f"🎮 {g}",
                        value=f"닉네임: {n}",
                        inline=False
                   )
            else:
                embed.description="비어있음"

            if 닉네임 in profile_messages:
                try:
                    old=await interaction.channel.fetch_message(profile_messages[닉네임])
                    await old.delete()
                except:
                    pass

            await interaction.response.send_message(embed=embed)
            msg=await interaction.original_response()
            profile_messages[닉네임]=msg.id
            return

    await interaction.response.send_message("등록되어있지 않음",ephemeral=True)
    await auto_delete(interaction)

@tree.command(name="등록취소")
async def unregister(interaction: discord.Interaction):
    if not check_channel(interaction,"game"):
        return

    data=load("game")
    gid,cid,uid=str(interaction.guild.id),str(interaction.channel.id),str(interaction.user.id)

    data.get(gid,{}).get(cid,{}).pop(uid,None)
    save("game",data)

    await interaction.response.send_message("삭제 완료",ephemeral=True)
    await auto_delete(interaction)

# ---------------------------
# 추천
# ---------------------------
foods = [
# 기존 (절대 유지)
"불고기","된장찌개","제육볶음","김치찌개","라면",
"삼겹살","치킨","피자","햄버거","돈까스","떡볶이","순대","오뎅","김밥","쌀국수",
"파스타","스테이크","초밥","회","짜장면","짬뽕","탕수육","마라탕","마라샹궈",
"곱창","막창","닭갈비","보쌈","족발","감자탕","설렁탕","갈비탕","육개장","칼국수",
"비빔밥","냉면","쫄면","우동","샌드위치","토스트","핫도그","타코","부리또","나초",
"리조또","오므라이스","카레","덮밥","계란말이","계란찜","샐러드","요거트",
"아이스크림","빙수","케이크","도넛","쿠키","초콜릿","와플","팬케이크",
"닭강정","간장게장","양념게장","조개구이","해물탕","해물파전","파전",
"닭발","닭꼬치","소세지","베이컨","프라이드치킨","양념치킨","간장치킨",
"치즈볼","치즈스틱","감자튀김","어니언링","크림파스타","로제파스타",

# 추가 확장
"간장불고기","고추장불고기","LA갈비","돼지갈비","소갈비",
"순두부찌개","청국장","부대찌개","콩나물국","미역국","북엇국",
"닭곰탕","삼계탕","추어탕","오리탕",
"코다리조림","갈치조림","고등어조림","꽁치조림",
"잡채","주먹밥","유부초밥",
"비빔국수","잔치국수","열무국수",
"쭈꾸미볶음","낙지볶음","오징어볶음",
"두루치기","닭도리탕","찜닭","돼지김치찜",

"유린기","깐풍기","마파두부","멘보샤",
"딤섬","샤오롱바오","탄탄면",
"나시고랭","팟타이","똠얌꿍",
"반미","분짜","월남쌈",
"오코노미야끼","타코야끼","규동","가츠동","텐동","라멘",

"치즈버거","베이글","크로와상","바게트","치아바타",
"그라탕","라자냐","피쉬앤칩스","폭립","핫윙","치킨너겟",

"컵라면","즉석떡볶이","치즈떡볶이","로제떡볶이",
"순대볶음","어묵탕","핫바","계란빵","붕어빵","호떡",

"마카롱","티라미수","치즈케이크","수플레","푸딩","젤리","아포가토",
"버블티","밀크티","아메리카노","카페라떼","프라페","스무디","에이드",

"샤브샤브","훠궈","양꼬치","케밥",
"포케","샐러드볼","도시락","컵밥"
]
games = [
# 기본
"롤","롤토체스","마인크래프트",

# FPS / 슈팅
"오버워치","배틀그라운드","발로란트","에이펙스레전드","포트나이트",
"레인보우식스시즈","콜오브듀티","팀포트리스2","페이데이2","인서전시샌드스톰",

# 오픈월드 / 대작
"GTA5","레드데드리뎀션2","사이버펑크2077","엘든링","호그와트레거시",
"위쳐3","어쌔신크리드","스카이림","폴아웃4","스타필드",

# 공포게임
"파스모포비아","데드바이데이라이트","아웃라스트","아웃라스트2",
"더포레스트","선즈오브더포레스트","페이탈프레임","비지지","데브아워",
"프레디의피자가게","SCP시크릿랩","PACIFY","그린헬","이블위딘",

# 방탈출 / 퍼즐
"위워히어","위워히어투게더","위워히어포에버",
"더룸","더룸2","더룸3","포탈","포탈2",
"휴먼폴플랫","브리지컨스트럭터","슈퍼리미널",
"이스케이프시뮬레이터","큐브이스케이프","러스트레이크",

# 멀티 / 협동
"잇테이크투","오버쿡드","오버쿡드2","무빙아웃",
"발헤임","돈스타브투게더","프로젝트좀보이드",
"러스트","아크서바이벌","데이즈",
"리썰컴퍼니","콘트라밴드폴리스",
"레포","GTFO","드립드립","콘텐츠워닝",

# 생존 / 샌드박스
"마인크래프트","테라리아","스타듀밸리",
"림월드","팩토리오","서브노티카","서브노티카빌로우제로",
"그린헬","더롱다크",

# 인디 / 명작
"하데스","데드셀","슬레이더스파이어","언더테일",
"할로우나이트","컵헤드","오리와눈먼숲","오리와도깨비불",
"카타나제로","핫라인마이애미","인사이드","림보",

# 시뮬 / 운영
"심즈4","풋볼매니저","시티즈스카이라인",
"플래닛주","플래닛코스터","투포인트호스피탈",
"유로트럭시뮬레이터2","하우스플리퍼","파워워시시뮬레이터",

# 전략
"문명6","에이지오브엠파이어","토탈워",
"컴퍼니오브히어로즈","스타크래프트",

# 기타 인기
"로블록스","브롤스타즈","쿠키런",
"몬스터헌터월드","몬스터헌터라이즈",
"니어오토마타","페르소나5",
"드래곤볼파이터즈","철권","스트리트파이터"
]

@tree.command(name="아메추")
async def a(interaction: discord.Interaction):
    if not check_channel(interaction,"food"):
        return
    await interaction.response.send_message(random.choice(foods))

@tree.command(name="점메추")
async def b(interaction: discord.Interaction):
    if not check_channel(interaction,"food"):
        return
    await interaction.response.send_message(random.choice(foods))

@tree.command(name="저메추")
async def c(interaction: discord.Interaction):
    if not check_channel(interaction,"food"):
        return
    await interaction.response.send_message(random.choice(foods))

@tree.command(name="게임추천")
async def d(interaction: discord.Interaction):
    if not check_channel(interaction,"food"):
        return
    await interaction.response.send_message(f"{random.choice(games)}을 추천합니다.")

# ---------------------------
# 출석 + 포인트
# ---------------------------
@tree.command(name="출석")
async def attendance(interaction: discord.Interaction):
    if not check_channel(interaction,"attendance"):
        return

    data=load("points")
    gid,uid=str(interaction.guild.id),str(interaction.user.id)

    data.setdefault(gid,{}).setdefault(uid,{"points":0,"last":""})
    today=str(datetime.now().date())

    if data[gid][uid]["last"]==today:
        return await interaction.response.send_message("이미 출석함",ephemeral=True)

    data[gid][uid]["points"]+=10
    data[gid][uid]["last"]=today
    save("points",data)

    await interaction.response.send_message("출석 +10",ephemeral=True)
    await auto_delete(interaction)

@tree.command(name="포인트확인")
async def check_point(interaction: discord.Interaction):
    data=load("points")
    gid,uid=str(interaction.guild.id),str(interaction.user.id)
    p=data.get(gid,{}).get(uid,{}).get("points",0)

    await interaction.response.send_message(f"{p}포인트",ephemeral=True)
    await auto_delete(interaction)

@tree.command(name="포인트지급")
@app_commands.checks.has_permissions(administrator=True)
async def give_point(interaction: discord.Interaction,유저:discord.Member,포인트:int):
    data=load("points")
    gid,uid=str(interaction.guild.id),str(유저.id)

    data.setdefault(gid,{}).setdefault(uid,{"points":0,"last":""})
    data[gid][uid]["points"]+=포인트
    save("points",data)

    await interaction.response.send_message("지급 완료",ephemeral=True)
    await auto_delete(interaction)

@tree.command(name="포인트차감")
@app_commands.checks.has_permissions(administrator=True)
async def remove_point(interaction: discord.Interaction,유저:discord.Member,포인트:int):
    data=load("points")
    gid,uid=str(interaction.guild.id),str(유저.id)

    data.setdefault(gid,{}).setdefault(uid,{"points":0,"last":""})
    data[gid][uid]["points"]-=포인트
    if data[gid][uid]["points"]<0:
        data[gid][uid]["points"]=0

    save("points",data)

    await interaction.response.send_message("차감 완료",ephemeral=True)
    await auto_delete(interaction)

# ---------------------------
# 역할상점
# ---------------------------
@tree.command(name="역할상점")
@app_commands.checks.has_permissions(administrator=True)
async def shop(interaction: discord.Interaction, 역할:discord.Role, 포인트:int):
    data = load("shop")
    gid = str(interaction.guild.id)

    data.setdefault(gid, {"roles":{}, "msg":None})
    data[gid]["roles"][str(역할.id)] = 포인트

    embed = discord.Embed(title="🛒 역할 상점", color=0x00BFFF)

    lines = []
    temp = []

    for i, (rid, pt) in enumerate(data[gid]["roles"].items(), 1):
        role = interaction.guild.get_role(int(rid))
        temp.append(f"🎭 {role.name} ({pt})")

        if i % 2 == 0:
            lines.append("   ".join(temp))
            temp = []

    if temp:
        lines.append("   ".join(temp))

    embed.description = "\n".join(lines)

    if data[gid]["msg"]:
        try:
            msg = await interaction.channel.fetch_message(data[gid]["msg"])
            await msg.edit(embed=embed)
            await interaction.response.send_message("수정 완료", ephemeral=True)
            await auto_delete(interaction)
        except:
            await interaction.response.send_message(embed=embed)
            msg = await interaction.original_response()
            data[gid]["msg"] = msg.id
    else:
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        data[gid]["msg"] = msg.id

    save("shop", data)
@tree.command(name="역할제거")
@app_commands.checks.has_permissions(administrator=True)
async def remove_role(interaction: discord.Interaction, 역할:discord.Role):
    data = load("shop")
    gid = str(interaction.guild.id)

    data.setdefault(gid, {"roles":{}, "msg":None})

    # 역할 삭제
    data[gid]["roles"].pop(str(역할.id), None)

    # embed 다시 생성
    embed = discord.Embed(title="🛒 역할 상점", color=0x00BFFF)

    lines = []
    temp = []

    for i, (rid, pt) in enumerate(data[gid]["roles"].items(), 1):
        role_obj = interaction.guild.get_role(int(rid))
        if role_obj:
            temp.append(f"🎭 {role_obj.name} ({pt})")

        if i % 2 == 0:
            lines.append("   ".join(temp))
            temp = []

    if temp:
        lines.append("   ".join(temp))

    embed.description = "\n".join(lines) if lines else "비어있음"

    # 기존 메시지 수정
    if data[gid]["msg"]:
        try:
            msg = await interaction.channel.fetch_message(data[gid]["msg"])
            await msg.edit(embed=embed)
        except:
            await interaction.response.send_message(embed=embed)
            msg = await interaction.original_response()
            data[gid]["msg"] = msg.id
    else:
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        data[gid]["msg"] = msg.id

    save("shop", data)

    await interaction.response.send_message("삭제 완료", ephemeral=True)
    await auto_delete(interaction)

@tree.command(name="역할초기화")
@app_commands.checks.has_permissions(administrator=True)
async def reset_shop(interaction: discord.Interaction):
    data=load("shop")
    gid=str(interaction.guild.id)

    data.setdefault(gid, {"roles":{}, "msg":None})

    # 역할만 초기화
    data[gid]["roles"] = {}

    embed = discord.Embed(
        title="🛒 역할 상점",
        color=0x00BFFF
    )

    if data[gid]["msg"]:
        try:
            msg = await interaction.channel.fetch_message(data[gid]["msg"])
            await msg.edit(embed=embed)
        except:
            await interaction.response.send_message(embed=embed)
            msg = await interaction.original_response()
            data[gid]["msg"] = msg.id
    else:
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        data[gid]["msg"] = msg.id

    save("shop",data)

    # 🔥 여기 핵심 (followup 제거)
    try:
        await interaction.response.send_message("초기화 완료", ephemeral=True)
    except:
        await interaction.followup.send("초기화 완료", ephemeral=True)

    await auto_delete(interaction)

@tree.command(name="포인트사용")
async def use_point(interaction: discord.Interaction,역할:discord.Role):
    shop=load("shop")
    points=load("points")
    
    # 이미 역할 있는지 체크
    if 역할 in interaction.user.roles:
        await interaction.response.send_message("이미 보유한 역할입니다",ephemeral=True)
        await auto_delete(interaction)
        return

    gid,uid=str(interaction.guild.id),str(interaction.user.id)

    cost=shop.get(gid,{}).get("roles",{}).get(str(역할.id))
    if not cost:
        return await interaction.response.send_message("구매불가",ephemeral=True)

    if points[gid][uid]["points"]<cost:
        return await interaction.response.send_message("포인트 부족",ephemeral=True)

    points[gid][uid]["points"]-=cost
    save("points",points)

    await interaction.user.add_roles(역할)
    await interaction.response.send_message("구매 완료",ephemeral=True)
    await auto_delete(interaction)

# ---------------------------
@bot.event
async def on_ready():
    await tree.sync()
    print("봇 실행됨")

bot.run(TOKEN)