from __future__ import annotations

import base64
import html
import mimetypes
import random
from pathlib import Path

import streamlit as st


APP_DIR = Path(__file__).parent
GAME_TITLE = "닥쳐씹련아 강화하기"
DIFFICULTY = "easy"
STARTING_MONEY = 2_000_000
PROTECTION_SCROLL_PRICE = 50_000
AUTO_USE_PROTECTION_SCROLL = False

# 강화 단계별 아이템 설정입니다.
# 원하는 이미지를 assets/ 폴더에 넣고 image 값을 그 파일명으로 바꾸면 됩니다.
# 예: 7강 이미지를 바꾸려면 "assets/level07.png" 파일을 넣고 그대로 사용.
DEFAULT_ITEM_IMAGE = "assets/item.svg"
ITEMS_BY_LEVEL = {
    0: {"name": "빈첸 희운", "image": "assets/정희운.png"},
    1: {"name": "피콜로 김강민", "image": "assets/김강민2.png"},
    2: {"name": "애새끼 윤수환", "image": "assets/윤수환.jpg"},
    3: {"name": "악마의 임석환", "image": "assets/임석환.jpg"},
    4: {"name": "욕망의 이찬빈", "image": "assets/이찬빈.jpg"},
    5: {"name": "가오가이 차도현", "image": "assets/차도현.jpg"},
    6: {"name": "예쁜이 유지승", "image": "assets/유지승.jpg"},
    7: {"name": "개쫄보 김준석", "image": "assets/김준석.jpg"},
    8: {"name": "눈사람 박이람", "image": "assets/박이람.jpg"},
    9: {"name": "다이아 강태민", "image": "assets/강태민.jpg"},
    10: {"name": "M자 임서하", "image": "assets/임서하.jpg"},
    11: {"name": "포식의 임지욱", "image": "assets/임지욱.jpg"},
    12: {"name": "불꽃 카리스마 김우진", "image": "assets/김우진.jpg"},
    13: {"name": "뚱땡이 김근영", "image": "assets/김근영.jpg"},
    14: {"name": "해바라기 김강민", "image": "assets/김강민3.jpg"},
    15: {"name": "대두레이븐 김홍민", "image": "assets/김홍민.jpg"},
    16: {"name": "버억 김근영", "image": "assets/김근영2.jpg"},
    17: {"name": "스파이더 한하랑", "image": "assets/한하랑.jpg"},
    18: {"name": "스윗가이 조태홍", "image": "assets/조태홍.jpg"},
    19: {"name": "화염의 김태호", "image": "assets/김태호.jpg"},
    20: {"name": "신의 가호를 받은 차도현", "image": "assets/승천 차도현.png"},
}
MAX_LEVEL = max(ITEMS_BY_LEVEL)

MATERIAL_REQUIREMENTS = {
    13: {12: 1},
    14: {13: 1, 12: 1},
    15: {14: 1},
    16: {15: 1, 14: 2, 13: 2},
    17: {16: 2},
    18: {17: 1, 16: 1},
    19: {18: 2},
    20: {19: 3},
}


def success_rate(level: int) -> int:
    rates = [
        100,
        99,
        98,
        95,
        90,
        88,
        85,
        80,
        75,
        70,
        65,
        45,
        32,
        20,
        18,
        15,
        12,
        10,
        8,
        5,
    ]
    if level < len(rates):
        return rates[level]
    return 2


def enhancement_cost(level: int) -> int:
    return 300 + (level * 250) + (level * level * 120)


def sale_price(level: int) -> int:
    if level <= 0:
        return 0

    custom_prices = {
        15: 2_000_000,
        16: 3_500_000,
        17: 4_500_000,
        18: 6_000_000,
        19: 10_000_000,
    }
    if level in custom_prices:
        return custom_prices[level]

    base_price = (level * level * 800) + (level * 1_000)
    if level < 13:
        return base_price

    high_level = level - 12
    high_level_bonus = (high_level * high_level * 80_000) + (high_level**3 * 120_000)
    return base_price + high_level_bonus


def failure_penalty(level: int) -> str:
    if level < 5:
        return "keep"
    if level < 10:
        return "down"
    return "break"


def format_won(value: int) -> str:
    return f"{value}원"


def image_to_data_uri(path: str) -> str:
    image_path = Path(path)
    if not image_path.is_absolute():
        image_path = APP_DIR / image_path
    if not image_path.exists():
        return ""

    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def item_for_level(level: int) -> dict[str, str]:
    if level in ITEMS_BY_LEVEL:
        return ITEMS_BY_LEVEL[level]

    fallback_level = max(item_level for item_level in ITEMS_BY_LEVEL if item_level <= level)
    return ITEMS_BY_LEVEL[fallback_level]


def material_count(level: int) -> int:
    return int(st.session_state.materials.get(level, 0))


def material_name(level: int) -> str:
    return item_for_level(level)["name"]


def material_requirement_text(requirements: dict[int, int]) -> str:
    return ", ".join(
        f"+{level} {material_name(level)} x{quantity}"
        for level, quantity in sorted(requirements.items(), reverse=True)
    )


def missing_materials(target_level: int, current_level: int) -> dict[int, int]:
    missing = {}
    for material_level, required_quantity in MATERIAL_REQUIREMENTS.get(target_level, {}).items():
        available_quantity = material_count(material_level)
        if current_level == material_level:
            available_quantity += 1

        if available_quantity < required_quantity:
            missing[material_level] = required_quantity - available_quantity

    return missing


def consume_extra_materials(target_level: int, current_level: int) -> None:
    materials = st.session_state.materials
    for material_level, required_quantity in MATERIAL_REQUIREMENTS.get(target_level, {}).items():
        extra_quantity = required_quantity - (1 if current_level == material_level else 0)
        if extra_quantity <= 0:
            continue

        materials[material_level] = max(0, material_count(material_level) - extra_quantity)


def stored_material_summary(min_level: int = 12) -> str:
    rows = []
    for level in range(min_level, MAX_LEVEL + 1):
        count = material_count(level)
        if count > 0:
            rows.append(f"+{level} {html.escape(material_name(level))}: {count}개")

    return "<br>".join(rows) if rows else "보관 중인 재료 검이 없습니다."


def init_state() -> None:
    defaults = {
        "level": 0,
        "money": STARTING_MONEY,
        "protection_scrolls": 0,
        "last_message": "강화를 시작하세요.",
        "history": [],
        "panel": "",
        "auto_protect": AUTO_USE_PROTECTION_SCROLL,
        "materials": {},
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def push_history(message: str) -> None:
    st.session_state.history.insert(0, message)
    st.session_state.history = st.session_state.history[:8]


def enhance_item() -> None:
    level = st.session_state.level
    target_level = level + 1

    if level >= MAX_LEVEL:
        message = f"이미 최대 강화 단계 +{MAX_LEVEL}입니다."
        st.session_state.last_message = message
        push_history(message)
        return

    missing = missing_materials(target_level, level)
    if missing:
        message = f"+{target_level} 강화 재료 부족: {material_requirement_text(missing)}"
        st.session_state.last_message = message
        push_history(message)
        return

    cost = enhancement_cost(level)
    if st.session_state.money < cost:
        message = "돈이 부족합니다."
        st.session_state.last_message = message
        push_history(message)
        return

    st.session_state.money -= cost
    consume_extra_materials(target_level, level)
    rate = success_rate(level)
    roll = random.randint(1, 100)

    if roll <= rate:
        st.session_state.level = target_level
        message = f"강화 성공! +{level}에서 +{target_level}이 되었습니다."
    else:
        penalty = failure_penalty(level)
        use_protection = (
            st.session_state.auto_protect
            and st.session_state.protection_scrolls > 0
            and penalty in {"down", "break"}
        )

        if use_protection:
            st.session_state.protection_scrolls -= 1
            if penalty == "down":
                message = "강화 실패! 방지권을 사용해서 하락을 막았습니다."
            else:
                message = "강화 실패! 방지권을 사용해서 파괴를 막았습니다."
        elif penalty == "keep":
            message = "강화 실패! 단계는 유지됩니다."
        elif penalty == "down":
            st.session_state.level = max(0, level - 1)
            message = f"강화 실패! +{level}에서 +{st.session_state.level}로 내려갔습니다."
        else:
            st.session_state.level = 0
            message = "강화 실패! 아이템이 파괴되어 +0으로 돌아갔습니다."

    st.session_state.last_message = message
    push_history(message)


def sell_item(item_name: str) -> None:
    price = sale_price(st.session_state.level)
    st.session_state.money += price
    message = f"+{st.session_state.level} {item_name}을 {format_won(price)}에 판매했습니다."
    st.session_state.level = 0
    st.session_state.last_message = message
    push_history(message)


def store_current_item(item_name: str) -> None:
    level = st.session_state.level
    if level <= 0:
        message = "+1 이상 아이템부터 재료로 보관할 수 있습니다."
    else:
        st.session_state.materials[level] = material_count(level) + 1
        st.session_state.level = 0
        message = f"+{level} {item_name}을 재료로 보관했습니다."

    st.session_state.last_message = message
    push_history(message)


def buy_protection_scroll(quantity: int) -> None:
    quantity = max(1, quantity)
    total_price = PROTECTION_SCROLL_PRICE * quantity

    if st.session_state.money < total_price:
        max_quantity = st.session_state.money // PROTECTION_SCROLL_PRICE
        message = f"돈이 부족합니다. 현재는 방지권을 최대 {max_quantity}장 살 수 있습니다."
    else:
        st.session_state.money -= total_price
        st.session_state.protection_scrolls += quantity
        message = (
            f"방지권을 {quantity}장 샀습니다. "
            f"현재 {st.session_state.protection_scrolls}장"
        )

    st.session_state.last_message = message
    push_history(message)


def reset_game() -> None:
    st.session_state.level = 0
    st.session_state.money = STARTING_MONEY
    st.session_state.protection_scrolls = 0
    st.session_state.materials = {}
    st.session_state.last_message = "새 게임을 시작했습니다."
    st.session_state.history = []
    st.session_state.panel = ""


def render_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: #202124;
        }

        .block-container {
            max-width: 980px;
            padding-top: 16px;
            padding-bottom: 40px;
            position: relative;
        }

        .game-board {
            background: #ffffff;
            border: 3px solid #1d1d1d;
            color: #050505;
            font-family: Arial, "Malgun Gothic", sans-serif;
            padding: 10px 34px 24px;
        }

        .game-board-top {
            border-bottom: 0;
            padding-bottom: 6px;
        }

        .game-board-bottom {
            border-top: 0;
            min-height: 500px;
            padding-top: 6px;
        }

        .top-row {
            align-items: start;
            display: flex;
            min-height: 118px;
            justify-content: center;
        }

        .title-wrap {
            max-width: 100%;
            position: relative;
            text-align: center;
        }

        .game-title {
            color: #d40000;
            font-size: 72px;
            font-weight: 900;
            letter-spacing: 0;
            line-height: 2.4;
            margin: 10px 0 0;
            max-width: 100%;
            overflow-wrap: normal;
            text-shadow: 4px 5px 0 #050505;
            white-space: nowrap;
        }

        .difficulty {
            color: #9b9b9b;
            font-size: 30px;
            font-weight: 900;
            opacity: 0.75;
            position: absolute;
            right: -8px;
            top: 104px;
        }

        .stats-row {
            display: none;
            margin-top: 52px;
            text-align: center;
        }

        .main-row {
            display: grid;
            gap: 20px;
            grid-template-columns: 0.9fr 2fr 0.35fr;
            margin-top: 18px;
        }

        .left-stats {
            font-size: 32px;
            font-weight: 900;
            line-height: 1.28;
            padding-top: 18px;
            white-space: nowrap;
        }

        div[data-testid="stElementContainer"]:has(.game-board-top),
        div[data-testid="stElementContainer"]:has(.game-board-bottom),
        div[data-testid="stElementContainer"]:has(div[data-testid="stCheckbox"]) {
            margin-bottom: 0 !important;
        }

        div[data-testid="stVerticalBlock"]:has(.game-board-top) {
            gap: 0 !important;
        }

        div[data-testid="stElementContainer"]:has(div[data-testid="stCheckbox"]) {
            background: #ffffff;
            border-radius: 4px;
            left: 70px !important;
            margin-top: 0 !important;
            padding: 2px 6px;
            position: absolute !important;
            top: 385px !important;
            width: max-content !important;
            z-index: 30;
        }

        div[data-testid="stCheckbox"] {
            background: #ffffff;
            border-radius: 4px;
            padding: 2px 6px;
        }

        div[data-testid="stCheckbox"] label {
            align-items: center;
            color: #050505;
            display: flex;
            font-family: Arial, "Malgun Gothic", sans-serif;
            font-size: 20px;
            font-weight: 900;
            gap: 8px;
            justify-content: center;
            white-space: nowrap;
        }

        div[data-testid="stCheckbox"] p {
            color: #050505;
            font-size: 20px;
            font-weight: 900;
            line-height: 1.1;
        }

        .item-area {
            align-items: center;
            display: flex;
            flex-direction: column;
            min-width: 0;
            padding-top: 18px;
            text-align: center;
        }

        .item-image {
            height: 320px;
            object-fit: contain;
            width: min(420px, 100%);
        }

        .missing-image {
            align-items: center;
            border: 4px solid #111111;
            display: flex;
            font-size: 22px;
            font-weight: 900;
            height: 300px;
            justify-content: center;
            width: min(380px, 100%);
        }

        .item-name {
            color: #050505;
            font-size: 46px;
            font-weight: 900;
            letter-spacing: 0;
            line-height: 1.16;
            margin-top: 16px;
            max-width: 520px;
            overflow-wrap: anywhere;
            text-align: center;
        }

        .right-space {
            min-height: 260px;
        }

        .bottom-row {
            align-items: end;
            display: grid;
            gap: 16px;
            grid-template-columns: 1fr 1fr 1fr;
            margin-top: 36px;
        }

        .bottom-left,
        .bottom-center,
        .bottom-right {
            font-size: 32px;
            font-weight: 900;
            line-height: 1.3;
        }

        .bottom-center {
            text-align: center;
        }

        .bottom-right {
            text-align: right;
        }

        .made-by {
            font-size: 18px;
            font-weight: 800;
            margin-bottom: 2px;
        }

        .money {
            font-size: 36px;
            font-weight: 400;
        }

        .money strong {
            font-size: 44px;
            font-weight: 900;
        }

        .message-bar {
            background: #111111;
            border: 3px solid #111111;
            color: #ffffff;
            font-size: 22px;
            font-weight: 800;
            margin-top: 20px;
            min-height: 46px;
            padding: 8px 12px;
            text-align: center;
        }

        .stButton > button {
            border: 3px solid #111111;
            border-radius: 4px;
            font-size: 20px;
            font-weight: 900;
            min-height: 48px;
        }

        .stButton > button[kind="primary"] {
            background: #d40000;
            color: #ffffff;
        }

        .info-panel {
            background: #ffffff;
            border: 3px solid #111111;
            color: #050505;
            font-family: Arial, "Malgun Gothic", sans-serif;
            font-size: 20px;
            font-weight: 800;
            margin-top: 14px;
            padding: 16px;
        }

        div[data-testid="stNumberInput"] label,
        div[data-testid="stNumberInput"] label p,
        div[data-testid="stCaptionContainer"],
        div[data-testid="stCaptionContainer"] p {
            color: #ffffff;
        }

        @media (max-width: 760px) {
            .game-board {
                padding: 10px 16px 20px;
            }

            .game-board-top {
                padding-bottom: 4px;
            }

            .game-board-bottom {
                min-height: 470px;
                padding-top: 4px;
            }

            .top-row {
                align-items: flex-start;
                display: flex;
                min-height: 118px;
                padding-top: 28px;
                text-align: center;
            }

            .game-title {
                font-size: 48px;
                line-height: 1.25;
                margin: 0;
                text-shadow: 3px 4px 0 #050505;
            }

            .difficulty {
                display: none;
            }

            .stats-row {
                display: block;
                margin-top: 14px;
            }

            .main-row {
                grid-template-columns: 1fr;
                margin-top: 18px;
            }

            .left-stats {
                font-size: 24px;
                text-align: center;
            }

            .desktop-stats {
                display: none;
            }

            div[data-testid="stElementContainer"]:has(div[data-testid="stCheckbox"]) {
                border-left: 3px solid #1d1d1d;
                border-radius: 0;
                border-right: 3px solid #1d1d1d;
                left: auto !important;
                padding: 0 16px 8px;
                position: static !important;
                top: auto !important;
                width: 100% !important;
            }

            div[data-testid="stCheckbox"] p {
                font-size: 18px;
            }

            .item-area {
                padding-top: 8px;
            }

            .item-image {
                height: 250px;
                width: min(330px, 100%);
            }

            .item-name {
                font-size: 32px;
            }

            .right-space {
                display: none;
            }

            .bottom-row {
                grid-template-columns: 1fr;
                margin-top: 18px;
                text-align: center;
            }

            .bottom-left,
            .bottom-center,
            .bottom-right {
                font-size: 24px;
                text-align: center;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_board_top() -> None:
    level = st.session_state.level
    escaped_title = html.escape(GAME_TITLE)
    escaped_difficulty = html.escape(DIFFICULTY)

    st.html(
        f"""
<div class="game-board game-board-top">
  <div class="top-row">
    <div class="title-wrap">
      <div class="game-title">{escaped_title}</div>
      <div class="difficulty">{escaped_difficulty}</div>
    </div>
  </div>
  <div class="stats-row">
    <div class="left-stats">
      강화비용:{format_won(enhancement_cost(level))}<br>
      판매가격:{format_won(sale_price(level))}
    </div>
  </div>
</div>
        """
    )


def render_board_bottom(item_name: str, image_data_uri: str) -> None:
    level = st.session_state.level
    escaped_name = html.escape(item_name)
    escaped_message = html.escape(st.session_state.last_message)

    image_html = (
        f'<img class="item-image" src="{image_data_uri}" alt="{escaped_name}">'
        if image_data_uri
        else '<div class="missing-image">이미지 없음</div>'
    )

    st.html(
        f"""
<div class="game-board game-board-bottom">
  <div class="main-row">
    <div class="left-stats desktop-stats">
      강화비용:{format_won(enhancement_cost(level))}<br>
      판매가격:{format_won(sale_price(level))}
    </div>
    <div class="item-area">
      {image_html}
      <div class="item-name">+{level} {escaped_name}</div>
    </div>
    <div class="right-space"></div>
  </div>
  <div class="bottom-row">
    <div class="bottom-left">
      방지권: {st.session_state.protection_scrolls}<br>
      돈:
    </div>
    <div class="bottom-center">
      성공률 {success_rate(level)} %
    </div>
    <div class="bottom-right">
      <div class="made-by">by NBS style</div>
      <div class="money">{st.session_state.money}<strong>원</strong></div>
    </div>
  </div>
  <div class="message-bar">{escaped_message}</div>
</div>
        """
    )


def render_panel(item_name: str) -> None:
    if st.session_state.panel == "inventory":
        st.html(
            f"""
<div class="info-panel">
  보유 아이템: +{st.session_state.level} {html.escape(item_name)}<br>
  판매가격: {format_won(sale_price(st.session_state.level))}<br>
  방지권: {st.session_state.protection_scrolls}장<br><br>
  재료 보관함<br>
  {stored_material_summary()}
</div>
            """
        )

        left, center, right = st.columns(3)
        with left:
            if st.button("판매하기", use_container_width=True):
                sell_item(item_name)
                st.rerun()
        with center:
            if st.button("재료로 보관", use_container_width=True):
                store_current_item(item_name)
                st.rerun()
        with right:
            if st.button("새로 시작", use_container_width=True):
                reset_game()
                st.rerun()

    elif st.session_state.panel == "shop":
        max_buyable = max(1, st.session_state.money // PROTECTION_SCROLL_PRICE)
        st.html(
            f"""
<div class="info-panel">
  방지권 가격: {format_won(PROTECTION_SCROLL_PRICE)}<br>
  실패 시 하락 또는 파괴를 1회 막습니다.
</div>
            """
        )

        quantity = st.number_input(
            "구매할 방지권 수량",
            min_value=1,
            max_value=max_buyable,
            value=1,
            step=1,
        )
        st.caption(f"총 가격: {format_won(PROTECTION_SCROLL_PRICE * quantity)}")

        left, right = st.columns(2)
        with left:
            if st.button("방지권 구매", use_container_width=True):
                buy_protection_scroll(quantity)
                st.rerun()
        with right:
            if st.button("강화창으로", use_container_width=True):
                st.session_state.panel = ""
                st.rerun()


def main() -> None:
    st.set_page_config(page_title=GAME_TITLE, page_icon="⚔️", layout="centered")
    init_state()
    render_css()

    current_item = item_for_level(st.session_state.level)
    image_data_uri = image_to_data_uri(current_item["image"])
    if not image_data_uri:
        image_data_uri = image_to_data_uri(DEFAULT_ITEM_IMAGE)

    render_board_top()

    st.checkbox(
        f"방지권 사용 ({st.session_state.protection_scrolls}장)",
        key="auto_protect",
        help="실패 시 하락 또는 파괴가 발생할 때 방지권을 1장 사용합니다.",
    )

    render_board_bottom(current_item["name"], image_data_uri)

    nav_left, nav_center, nav_right = st.columns([1, 1.25, 1])
    with nav_left:
        if st.button("아이템창가기", use_container_width=True):
            st.session_state.panel = "inventory"
    with nav_center:
        if st.button("강화하기", type="primary", use_container_width=True):
            st.session_state.panel = ""
            enhance_item()
            st.rerun()
    with nav_right:
        if st.button("상점가기", use_container_width=True):
            st.session_state.panel = "shop"

    render_panel(current_item["name"])

    if st.session_state.history:
        with st.expander("강화 기록"):
            for message in st.session_state.history:
                st.write(message)


if __name__ == "__main__":
    main()
