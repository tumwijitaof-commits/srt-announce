from flask import Flask, request, render_template_string, send_from_directory, jsonify
from pathlib import Path
import os
import subprocess
import json
import time
import uuid

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio_generated"
AUDIO_DIR.mkdir(exist_ok=True)

VOICE_NAME = os.environ.get("TTS_VOICE", "th-TH-NiwatNeural")
TTS_RATE = os.environ.get("TTS_RATE", "-10%")
EN_VOICE_NAME = os.environ.get("TTS_EN_VOICE", "en-US-GuyNeural")
TTS_EN_RATE = os.environ.get("TTS_EN_RATE", "-5%")
STATION_NAME = "คลองบางพระ"
CHIME_FILENAME = "chime.mp3"

# ------------------------------------------------------------
# ฐานข้อมูลตารางเดินรถ สถานีคลองบางพระ
# ------------------------------------------------------------
INBOUND_TRAINS = [
    {"label": "384 (05:30) ฉะเชิงเทรา - กรุงเทพ", "num": "384", "origin": "ชุมทางฉะเชิงเทรา", "dest": "กรุงเทพ", "time": "5 นาฬิกา 30 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    {"label": "380 (05:55) ฉะเชิงเทรา - กรุงเทพ", "num": "380", "origin": "ชุมทางฉะเชิงเทรา", "dest": "กรุงเทพ", "time": "5 นาฬิกา 55 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    {"label": "372 (06:30) ปราจีนบุรี - กรุงเทพ", "num": "372", "origin": "ปราจีนบุรี", "dest": "กรุงเทพ", "time": "6 นาฬิกา 30 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    {"label": "388 (07:12) ฉะเชิงเทรา - กรุงเทพ", "num": "388", "origin": "ชุมทางฉะเชิงเทรา", "dest": "กรุงเทพ", "time": "7 นาฬิกา 12 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    {"label": "278 (08:41) กบินทร์บุรี - กรุงเทพ", "num": "278", "origin": "กบินทร์บุรี", "dest": "กรุงเทพ", "time": "8 นาฬิกา 41 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    {"label": "280 (10:33) คลองลึก - กรุงเทพ", "num": "280", "origin": "ด่านพรมแดนบ้านคลองลึก", "dest": "กรุงเทพ", "time": "10 นาฬิกา 33 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    {"label": "368 (12:44) ฉะเชิงเทรา - กรุงเทพ", "num": "368", "origin": "ชุมทางฉะเชิงเทรา", "dest": "กรุงเทพ", "time": "12 นาฬิกา 44 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    {"label": "390 (14:12) ฉะเชิงเทรา - กรุงเทพ", "num": "390", "origin": "ชุมทางฉะเชิงเทรา", "dest": "กรุงเทพ", "time": "14 นาฬิกา 12 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    {"label": "282 (15:42) กบินทร์บุรี - กรุงเทพ", "num": "282", "origin": "กบินทร์บุรี", "dest": "กรุงเทพ", "time": "15 นาฬิกา 42 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    {"label": "284 (16:33) จุกเสม็ด - กรุงเทพ", "num": "284", "origin": "จุกเสม็ด", "dest": "กรุงเทพ", "time": "16 นาฬิกา 33 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    {"label": "276 (19:00) คลองลึก - กรุงเทพ", "num": "276", "origin": "ด่านพรมแดนบ้านคลองลึก", "dest": "กรุงเทพ", "time": "19 นาฬิกา", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
]

OUTBOUND_TRAINS = [
    {"label": "275 (07:28) กรุงเทพ - คลองลึก", "num": "275", "origin": "กรุงเทพ", "dest": "ด่านพรมแดนบ้านคลองลึก", "time": "7 นาฬิกา 28 นาที", "next": "ป้ายหยุดรถบางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    {"label": "283 (08:46) กรุงเทพ - จุกเสม็ด", "num": "283", "origin": "กรุงเทพ", "dest": "จุกเสม็ด", "time": "8 นาฬิกา 46 นาที", "next": "ป้ายหยุดรถบางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    {"label": "281 (09:23) กรุงเทพ - กบินทร์บุรี", "num": "281", "origin": "กรุงเทพ", "dest": "กบินทร์บุรี", "time": "9 นาฬิกา 23 นาที", "next": "สถานีชุมทางฉะเชิงเทรา"},
    {"label": "367 (11:35) กรุงเทพ - ฉะเชิงเทรา", "num": "367", "origin": "กรุงเทพ", "dest": "ชุมทางฉะเชิงเทรา", "time": "11 นาฬิกา 35 นาที", "next": "ป้ายหยุดรถบางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    {"label": "389 (13:23) กรุงเทพ - ฉะเชิงเทรา", "num": "389", "origin": "กรุงเทพ", "dest": "ชุมทางฉะเชิงเทรา", "time": "13 นาฬิกา 23 นาที", "next": "ป้ายหยุดรถบางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    {"label": "279 (14:08) กรุงเทพ - คลองลึก", "num": "279", "origin": "กรุงเทพ", "dest": "ด่านพรมแดนบ้านคลองลึก", "time": "14 นาฬิกา 8 นาที", "next": "สถานีชุมทางฉะเชิงเทรา"},
    {"label": "277 (16:37) กรุงเทพ - กบินทร์บุรี", "num": "277", "origin": "กรุงเทพ", "dest": "กบินทร์บุรี", "time": "16 นาฬิกา 37 นาที", "next": "ป้ายหยุดรถบางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    {"label": "379 (17:57) กรุงเทพ - ฉะเชิงเทรา", "num": "379", "origin": "กรุงเทพ", "dest": "ชุมทางฉะเชิงเทรา", "time": "17 นาฬิกา 57 นาที", "next": "ป้ายหยุดรถบางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    {"label": "391 (18:17) กรุงเทพ - ฉะเชิงเทรา", "num": "391", "origin": "กรุงเทพ", "dest": "ชุมทางฉะเชิงเทรา", "time": "18 นาฬิกา 17 นาที", "next": "ป้ายหยุดรถบางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    {"label": "371 (19:11) กรุงเทพ - ปราจีนบุรี", "num": "371", "origin": "กรุงเทพ", "dest": "ปราจีนบุรี", "time": "19 นาฬิกา 11 นาที", "next": "ป้ายหยุดรถบางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    {"label": "383 (20:25) กรุงเทพ - ฉะเชิงเทรา", "num": "383", "origin": "กรุงเทพ", "dest": "ชุมทางฉะเชิงเทรา", "time": "20 นาฬิกา 25 นาที", "next": "ป้ายหยุดรถบางเตย และ สถานีชุมทางฉะเชิงเทรา"},
]

TRAIN_DATA = {train["label"]: train for train in INBOUND_TRAINS + OUTBOUND_TRAINS}

ANNOUNCEMENT_BUTTONS = [
    {"idx": 0, "title": "ขอทาง / ขายตั๋ว", "hint": "แจ้งผู้โดยสารให้ซื้อตั๋วก่อนเดินทาง", "group": "ก่อนรถเข้า"},
    {"idx": 1, "title": "รอรับโดยสาร", "hint": "ให้ผู้โดยสารรอที่ชานชาลา", "group": "ก่อนรถเข้า"},
    {"idx": 2, "title": "รถกำลังเข้าเทียบ", "hint": "เตือนยืนหลังเส้นสีเหลือง", "group": "รถเข้า-ออก"},
    {"idx": 3, "title": "รถผ่านสถานี", "hint": "ประกาศรถผ่านขบวนปกติ", "group": "รถเข้า-ออก"},
    {"idx": 4, "title": "รถจอดรับส่ง / ออก", "hint": "ประกาศสถานีถัดไปและให้ขึ้นรถ", "group": "รถเข้า-ออก"},
    {"idx": 5, "title": "รถล่าช้า", "hint": "แจ้งเวลาคาดว่าจะถึง", "group": "เหตุการณ์พิเศษ"},
    {"idx": 6, "title": "ระวังคนลงรถ", "hint": "เตือนผู้โดยสารขณะรถเข้า", "group": "ความปลอดภัย"},
    {"idx": 7, "title": "ห้ามสูบบุหรี่", "hint": "ประกาศขอความร่วมมือ", "group": "ความปลอดภัย"},
    {"idx": 8, "title": "ประกาศเอง", "hint": "อ่านข้อความที่พิมพ์เอง", "group": "ประกาศทั่วไป"},
    {"idx": 9, "title": "สินค้า / พิเศษ ผ่าน", "hint": "เลือกประเภทรถวิ่งผ่าน", "group": "เหตุการณ์พิเศษ"},
    {"idx": 10, "title": "รถเข้าพร้อมกัน 2 ขบวน", "hint": "ใช้ข้อมูลขบวนที่ 1 และ 2", "group": "เหตุการณ์พิเศษ"},
]

HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ระบบประกาศสถานีคลองบางพระ</title>
    <style>
        :root {
            --maroon: #800000;
            --maroon-dark: #5b0000;
            --gold: #c7a12a;
            --cream: #fffaf1;
            --paper: #ffffff;
            --ink: #251d1d;
            --muted: #716464;
            --line: #e9dece;
            --green: #177744;
            --red: #b42318;
            --shadow: 0 12px 34px rgba(83, 28, 28, .10);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            min-height: 100vh;
            padding: 16px;
            color: var(--ink);
            font-family: "Sarabun", "Noto Sans Thai", "Segoe UI", sans-serif;
            background: linear-gradient(145deg, #fffaf1, #f4eadc);
        }
        button, input, select, textarea { font: inherit; }
        button { cursor: pointer; }
        .app { max-width: 1120px; margin: 0 auto; }
        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            padding: 18px 20px;
            color: white;
            border-radius: 22px;
            background: linear-gradient(135deg, var(--maroon-dark), var(--maroon));
            box-shadow: var(--shadow);
        }
        .brand { display: flex; align-items: center; gap: 13px; }
        .logo {
            width: 52px; height: 52px; flex: 0 0 auto;
            display: grid; place-items: center;
            border-radius: 16px;
            font-size: 27px;
            color: var(--maroon);
            background: linear-gradient(135deg, #fff4c4, var(--gold));
        }
        h1 { margin: 0; font-size: clamp(21px, 3vw, 30px); line-height: 1.2; }
        .subtitle { margin: 4px 0 0; opacity: .88; font-size: 13px; }
        .status {
            min-width: 180px;
            padding: 10px 14px;
            border: 1px solid rgba(255,255,255,.25);
            border-radius: 999px;
            text-align: center;
            font-weight: 800;
            background: rgba(255,255,255,.12);
        }
        .progress { display: none; height: 4px; margin-top: 10px; overflow: hidden; border-radius: 99px; background: rgba(255,255,255,.2); }
        .progress.active { display: block; }
        .progress::after {
            content: ""; display: block; width: 35%; height: 100%;
            background: linear-gradient(90deg, transparent, #fff5a5, transparent);
            animation: loading 1s linear infinite;
        }
        @keyframes loading { from { transform: translateX(-100%); } to { transform: translateX(300%); } }

        .layout {
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(320px, .74fr);
            gap: 16px;
            align-items: start;
            margin-top: 16px;
        }
        .stack { display: grid; gap: 16px; }
        .card {
            background: rgba(255,255,255,.96);
            border: 1px solid var(--line);
            border-radius: 20px;
            box-shadow: var(--shadow);
            overflow: hidden;
        }
        .card-head { padding: 15px 18px; border-bottom: 1px solid var(--line); background: #fffdf9; }
        .step-title { display: flex; align-items: center; gap: 10px; margin: 0; color: var(--maroon-dark); font-size: 18px; }
        .step {
            width: 30px; height: 30px; display: grid; place-items: center;
            border-radius: 10px; color: white; background: var(--maroon); font-size: 14px;
        }
        .card-body { padding: 17px; }
        .helper { margin: 6px 0 0; color: var(--muted); font-size: 12.5px; line-height: 1.45; }
        label { display: block; margin: 0 0 6px; font-weight: 800; }
        input, select, textarea {
            width: 100%; padding: 12px 13px;
            border: 1px solid #d9ccb9; border-radius: 13px;
            background: white; color: var(--ink); outline: none;
        }
        input:focus, select:focus, textarea:focus { border-color: var(--gold); box-shadow: 0 0 0 4px rgba(199,161,42,.14); }
        textarea { min-height: 92px; resize: vertical; }
        .field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 11px; }
        .full { grid-column: 1 / -1; }

        .language-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 9px; }
        .lang-btn {
            min-height: 62px; padding: 10px;
            border: 1px solid #dfd1bd; border-radius: 15px;
            background: #fff; color: var(--ink); font-weight: 850;
        }
        .lang-btn small { display: block; margin-top: 2px; color: var(--muted); font-weight: 600; }
        .lang-btn.active { border-color: var(--maroon); color: var(--maroon); background: #fff1f1; box-shadow: inset 0 0 0 1px var(--maroon); }

        .train-summary {
            display: grid; grid-template-columns: auto 1fr; gap: 10px 12px;
            margin-top: 12px; padding: 14px;
            border-radius: 16px; border: 1px solid #eadcc5; background: var(--cream);
        }
        .train-number {
            grid-row: 1 / span 2; align-self: stretch;
            min-width: 74px; display: grid; place-items: center;
            border-radius: 13px; background: var(--maroon); color: white;
            font-size: 22px; font-weight: 900;
        }
        .route { font-size: 17px; font-weight: 900; color: var(--maroon-dark); }
        .train-meta { color: var(--muted); font-size: 13px; line-height: 1.5; }
        .platform-row { display: grid; grid-template-columns: 1fr 140px; gap: 11px; margin-top: 12px; }

        .announce-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 9px; }
        .announce-option {
            min-height: 74px; padding: 12px;
            border: 1px solid #e5d7c4; border-radius: 15px;
            text-align: left; color: var(--ink); background: linear-gradient(145deg, #fff, #fff9ef);
        }
        .announce-option strong { display: block; color: var(--maroon-dark); font-size: 15px; }
        .announce-option span { display: block; margin-top: 3px; color: var(--muted); font-size: 12px; line-height: 1.35; }
        .announce-option.active { border-color: var(--maroon); background: #fff0f0; box-shadow: inset 0 0 0 1px var(--maroon); }
        .announce-option:disabled { opacity: .55; cursor: not-allowed; }

        .conditional {
            display: none; margin-top: 13px; padding: 14px;
            border-radius: 16px; border: 1px dashed rgba(128,0,0,.35); background: #fffaf3;
        }
        .conditional.show { display: block; }
        .conditional-title { margin: 0 0 10px; color: var(--maroon); font-weight: 900; }
        .advanced { margin-top: 12px; }
        .advanced summary { cursor: pointer; color: var(--maroon); font-weight: 850; }
        .advanced-content { margin-top: 12px; }

        .sticky { position: sticky; top: 16px; }
        .selected-type {
            padding: 12px 14px; margin-bottom: 12px;
            border-radius: 14px; background: #f7f1e8; color: var(--muted);
        }
        .selected-type b { color: var(--maroon-dark); }
        .preview {
            min-height: 150px; max-height: 390px; overflow: auto;
            padding: 15px; border: 1px solid #eadcc5; border-radius: 16px;
            background: #fffaf0; line-height: 1.7; font-size: 14px;
        }
        .action-stack { display: grid; gap: 9px; margin-top: 13px; }
        .primary, .secondary, .danger {
            width: 100%; border: 0; border-radius: 14px; padding: 14px;
            color: white; font-weight: 900;
        }
        .primary { background: linear-gradient(135deg, var(--maroon-dark), var(--maroon)); font-size: 17px; }
        .secondary { background: #665b55; }
        .danger { background: var(--red); }
        .primary:disabled { opacity: .45; cursor: not-allowed; }
        .two-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; }
        .mini-note { margin-top: 12px; color: var(--muted); font-size: 12px; line-height: 1.5; }
        .hidden { display: none !important; }

        @media (max-width: 860px) {
            body { padding: 9px; }
            .topbar { border-radius: 18px; padding: 15px; }
            .status { min-width: auto; }
            .layout { grid-template-columns: 1fr; }
            .sticky { position: static; }
        }
        @media (max-width: 560px) {
            .topbar { align-items: flex-start; }
            .logo { width: 44px; height: 44px; font-size: 23px; }
            .status { font-size: 12px; padding: 8px 10px; }
            .language-grid { grid-template-columns: 1fr; }
            .lang-btn { min-height: 52px; text-align: left; }
            .announce-grid, .field-grid, .platform-row { grid-template-columns: 1fr; }
            .train-summary { grid-template-columns: 64px 1fr; }
            .train-number { min-width: 64px; font-size: 19px; }
        }
    </style>
</head>
<body>
<main class="app">
    <header class="topbar">
        <div class="brand">
            <div class="logo">🚆</div>
            <div>
                <h1>ระบบประกาศสถานีคลองบางพระ</h1>
                <p class="subtitle">เลือกข้อมูลไม่กี่ขั้นตอน แล้วกดประกาศได้ทันที</p>
            </div>
        </div>
        <div class="status" id="statusText">พร้อมใช้งาน</div>
        <div class="progress" id="loadingBar"></div>
    </header>

    <section class="layout">
        <div class="stack">
            <section class="card">
                <div class="card-head"><h2 class="step-title"><span class="step">1</span> เลือกภาษาประกาศ</h2></div>
                <div class="card-body">
                    <input type="hidden" id="announce_mode" value="thai_only">
                    <div class="language-grid">
                        <button type="button" class="lang-btn active" data-mode="thai_only" onclick="setLanguage('thai_only', this)">🇹🇭 ภาษาไทย<small>ประกาศภาษาเดียว</small></button>
                        <button type="button" class="lang-btn" data-mode="english_only" onclick="setLanguage('english_only', this)">🇬🇧 English<small>English only</small></button>
                        <button type="button" class="lang-btn" data-mode="bilingual" onclick="setLanguage('bilingual', this)">🇹🇭 + 🇬🇧 สองภาษา<small>ไทย แล้วอังกฤษ</small></button>
                    </div>
                </div>
            </section>

            <section class="card">
                <div class="card-head"><h2 class="step-title"><span class="step">2</span> เลือกขบวนและชานชาลา</h2></div>
                <div class="card-body">
                    <label for="train_select">ขบวนรถ</label>
                    <select id="train_select" onchange="autoFill(1)">
                        <option value="">-- เลือกขบวนรถ --</option>
                        <optgroup label="ขาเข้า กรุงเทพ (หัวลำโพง)">
                        {% for train in inbound %}<option value="{{ train.label }}">{{ train.label }}</option>{% endfor %}
                        </optgroup>
                        <optgroup label="ขาออก ไปทางตะวันออก">
                        {% for train in outbound %}<option value="{{ train.label }}">{{ train.label }}</option>{% endfor %}
                        </optgroup>
                    </select>

                    <div class="train-summary" id="trainSummary">
                        <div class="train-number" id="summaryNum">–</div>
                        <div class="route" id="summaryRoute">ยังไม่ได้เลือกขบวนรถ</div>
                        <div class="train-meta" id="summaryMeta">เมื่อเลือกขบวน ระบบจะเติมต้นทาง ปลายทาง เวลา และสถานีต่อไปให้อัตโนมัติ</div>
                    </div>

                    <div class="platform-row">
                        <div>
                            <label for="platform">ชานชาลาที่</label>
                            <select id="platform" onchange="syncPlatformDefaults()">
                                <option value="1" selected>ชานชาลาที่ 1</option>
                                <option value="2">ชานชาลาที่ 2</option>
                                <option value="3">ชานชาลาที่ 3</option>
                            </select>
                        </div>
                        <div>
                            <label for="current">สถานีปัจจุบัน</label>
                            <input type="text" id="current" value="คลองบางพระ">
                        </div>
                    </div>

                    <details class="advanced">
                        <summary>แก้ไขรายละเอียดขบวนเพิ่มเติม</summary>
                        <div class="advanced-content field-grid">
                            <div><label>ขบวนที่</label><input type="text" id="num" oninput="refreshSummary()"></div>
                            <div><label>เวลา</label><input type="text" id="time" oninput="refreshSummary()"></div>
                            <div><label>ต้นทาง</label><input type="text" id="origin" oninput="refreshSummary()"></div>
                            <div><label>ปลายทาง</label><input type="text" id="dest" oninput="refreshSummary()"></div>
                            <div class="full"><label>สถานีต่อไป</label><input type="text" id="next_station" oninput="refreshSummary()"></div>
                        </div>
                    </details>
                </div>
            </section>

            <section class="card">
                <div class="card-head"><h2 class="step-title"><span class="step">3</span> เลือกประเภทประกาศ</h2></div>
                <div class="card-body">
                    <div class="announce-grid">
                        {% for group, buttons in grouped_buttons.items() %}
                            {% for button in buttons %}
                            <button type="button" class="announce-option" data-index="{{ button.idx }}" data-title="{{ button.title }}" onclick="selectAnnouncement({{ button.idx }}, this)">
                                <strong>{{ button.title }}</strong><span>{{ button.hint }}</span>
                            </button>
                            {% endfor %}
                        {% endfor %}
                    </div>

                    <div class="conditional" id="delayFields">
                        <p class="conditional-title">ข้อมูลรถล่าช้า</p>
                        <label for="delay_time">คาดว่าจะถึงเวลา</label>
                        <input type="text" id="delay_time" placeholder="เช่น 19 นาฬิกา 30 นาที">
                    </div>

                    <div class="conditional" id="passFields">
                        <p class="conditional-title">ข้อมูลรถวิ่งผ่าน</p>
                        <div class="field-grid">
                            <div id="trainTypeWrap">
                                <label for="train_type">ประเภทรถ</label>
                                <select id="train_type">
                                    <option value="สินค้า">สินค้า</option>
                                    <option value="ด่วนพิเศษ">ด่วนพิเศษ</option>
                                    <option value="พิเศษ">พิเศษ</option>
                                    <option value="รถจักรเปล่า">รถจักรเปล่า</option>
                                </select>
                            </div>
                            <div>
                                <label for="pass_platform">ชานชาลาที่รถผ่าน</label>
                                <select id="pass_platform">
                                    <option value="1" selected>ชานชาลาที่ 1</option>
                                    <option value="2">ชานชาลาที่ 2</option>
                                    <option value="3">ชานชาลาที่ 3</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="conditional" id="customFields">
                        <p class="conditional-title">ข้อความประกาศเอง</p>
                        <div id="thaiCustomWrap">
                            <label for="custom_text">ข้อความภาษาไทย</label>
                            <textarea id="custom_text" placeholder="พิมพ์ข้อความภาษาไทยที่ต้องการประกาศ"></textarea>
                        </div>
                        <div id="englishCustomWrap" class="hidden" style="margin-top:10px;">
                            <label for="custom_text_en">English announcement</label>
                            <textarea id="custom_text_en" placeholder="Type the English announcement"></textarea>
                        </div>
                    </div>

                    <div class="conditional" id="secondTrainFields">
                        <p class="conditional-title">ข้อมูลขบวนที่ 2</p>
                        <label for="train_select_2">เลือกขบวนที่ 2</label>
                        <select id="train_select_2" onchange="autoFill(2)">
                            <option value="">-- เลือกขบวนรถ --</option>
                            <optgroup label="ขาเข้า กรุงเทพ (หัวลำโพง)">
                            {% for train in inbound %}<option value="{{ train.label }}">{{ train.label }}</option>{% endfor %}
                            </optgroup>
                            <optgroup label="ขาออก ไปทางตะวันออก">
                            {% for train in outbound %}<option value="{{ train.label }}">{{ train.label }}</option>{% endfor %}
                            </optgroup>
                        </select>
                        <div class="field-grid" style="margin-top:11px;">
                            <div><label>ขบวนที่ 2</label><input type="text" id="num_2"></div>
                            <div><label>ชานชาลาที่ 2</label><select id="platform_2"><option value="1">1</option><option value="2" selected>2</option><option value="3">3</option></select></div>
                            <div><label>ต้นทาง 2</label><input type="text" id="origin_2"></div>
                            <div><label>ปลายทาง 2</label><input type="text" id="dest_2"></div>
                            <div><label>เวลา 2</label><input type="text" id="time_2"></div>
                            <div><label>สถานีต่อไป 2</label><input type="text" id="next_station_2"></div>
                        </div>
                    </div>
                </div>
            </section>
        </div>

        <aside class="card sticky">
            <div class="card-head"><h2 class="step-title"><span class="step">4</span> ตรวจสอบและประกาศ</h2></div>
            <div class="card-body">
                <div class="selected-type" id="selectedType"><b>ยังไม่ได้เลือกประเภทประกาศ</b><br>เลือกปุ่มในขั้นตอนที่ 3 ก่อน</div>
                <div class="preview" id="previewBox"><b>ตัวอย่างข้อความประกาศ</b><br><br>เมื่อกดเริ่มประกาศ ระบบจะสร้างข้อความและไฟล์เสียงตามภาษาที่เลือก</div>
                <div class="action-stack">
                    <button type="button" class="primary" id="playButton" onclick="playSelectedAnnouncement()" disabled>🔊 เริ่มประกาศเสียง</button>
                    <div class="two-actions">
                        <button type="button" class="danger" onclick="stopAudio()">■ หยุดเสียง</button>
                        <button type="button" class="secondary" onclick="clearData()">ล้างข้อมูล</button>
                    </div>
                </div>
                <p class="mini-note">เสียงเตือนจะเล่นก่อนเสียงประกาศ ระบบใช้เสียงไทย <b>{{ voice_name }}</b> และเสียงอังกฤษ <b>{{ en_voice_name }}</b></p>
            </div>
        </aside>
    </section>
</main>

<script>
    const trainData = {{ trains_json | safe }};
    let selectedAnnouncement = null;
    let mainPlayer = null;
    let isBusy = false;
    let sharedAudioContext = null;
    let mobileAudioUnlocked = false;

    function byId(id) { return document.getElementById(id); }
    function value(id) { return (byId(id)?.value || "").trim(); }

    function setLanguage(mode, button) {
        byId("announce_mode").value = mode;
        document.querySelectorAll(".lang-btn").forEach(btn => btn.classList.remove("active"));
        if (button) button.classList.add("active");
        updateCustomLanguageFields();
    }

    function updateCustomLanguageFields() {
        const mode = value("announce_mode") || "thai_only";
        byId("thaiCustomWrap").classList.toggle("hidden", mode === "english_only");
        byId("englishCustomWrap").classList.toggle("hidden", mode === "thai_only");
    }

    function autoFill(type) {
        const isFirst = type === 1;
        const selectId = isFirst ? "train_select" : "train_select_2";
        const suffix = isFirst ? "" : "_2";
        const data = trainData[value(selectId)];
        if (!data) return;
        byId("num" + suffix).value = data.num || "";
        byId("origin" + suffix).value = data.origin || "";
        byId("dest" + suffix).value = data.dest || "";
        byId("time" + suffix).value = data.time || "";
        byId("next_station" + suffix).value = data.next || "";
        if (isFirst) refreshSummary();
    }

    function refreshSummary() {
        const num = value("num") || "–";
        const origin = value("origin");
        const dest = value("dest");
        const time = value("time");
        const next = value("next_station");
        byId("summaryNum").textContent = num;
        byId("summaryRoute").textContent = origin && dest ? `${origin} → ${dest}` : "ยังไม่ได้เลือกขบวนรถ";
        const details = [];
        if (time) details.push(`เวลา ${time}`);
        if (next) details.push(`สถานีต่อไป: ${next}`);
        byId("summaryMeta").textContent = details.length ? details.join(" • ") : "เมื่อเลือกขบวน ระบบจะเติมข้อมูลให้อัตโนมัติ";
    }

    function syncPlatformDefaults() {
        const platform = value("platform") || "1";
        if (byId("pass_platform")) byId("pass_platform").value = platform;
        if (byId("platform_2") && byId("platform_2").value === platform) {
            byId("platform_2").value = platform === "1" ? "2" : "1";
        }
    }

    function selectAnnouncement(index, button) {
        selectedAnnouncement = index;
        document.querySelectorAll(".announce-option").forEach(btn => btn.classList.remove("active"));
        button.classList.add("active");
        byId("playButton").disabled = false;
        byId("selectedType").innerHTML = `<b>${escapeHtml(button.dataset.title || "ประเภทประกาศ")}</b><br>พร้อมสร้างเสียงตามข้อมูลที่เลือก`;

        ["delayFields", "passFields", "customFields", "secondTrainFields"].forEach(id => byId(id).classList.remove("show"));
        byId("trainTypeWrap").classList.remove("hidden");
        if (index === 5) byId("delayFields").classList.add("show");
        if (index === 3 || index === 9) {
            byId("passFields").classList.add("show");
            if (index === 3) byId("trainTypeWrap").classList.add("hidden");
        }
        if (index === 8) {
            byId("customFields").classList.add("show");
            updateCustomLanguageFields();
        }
        if (index === 10) byId("secondTrainFields").classList.add("show");
        byId("previewBox").innerHTML = "<b>พร้อมประกาศ</b><br><br>ตรวจสอบขบวนรถ ชานชาลา และภาษาที่เลือก แล้วกดปุ่มเริ่มประกาศเสียง";
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text == null ? "" : String(text);
        return div.innerHTML;
    }

    function renderServerPreview(html) {
        const safe = escapeHtml(html).replace(/&lt;br\s*\/?&gt;/gi, "<br>");
        byId("previewBox").innerHTML = safe;
    }

    function collectPayload(tabIndex) {
        return {
            tab_index: tabIndex,
            announce_mode: value("announce_mode") || "thai_only",
            num: value("num"), origin: value("origin"), dest: value("dest"), time: value("time"),
            platform: value("platform") || "1", current: value("current") || "คลองบางพระ",
            next: value("next_station"), delay: value("delay_time"),
            custom_text: value("custom_text"), custom_text_en: value("custom_text_en"),
            train_type: value("train_type") || "สินค้า",
            pass_platform: value("pass_platform") || value("platform") || "1",
            num_2: value("num_2"), origin_2: value("origin_2"), dest_2: value("dest_2"),
            time_2: value("time_2"), platform_2: value("platform_2"), next_2: value("next_station_2")
        };
    }

    function validateSelection() {
        if (selectedAnnouncement === null) return "กรุณาเลือกประเภทประกาศ";
        if (![7, 8].includes(selectedAnnouncement) && !value("num") && ![3, 9].includes(selectedAnnouncement)) return "กรุณาเลือกขบวนรถ";
        if (selectedAnnouncement === 5 && !value("delay_time")) return "กรุณาระบุเวลาที่คาดว่าจะถึง";
        if (selectedAnnouncement === 8) {
            const mode = value("announce_mode");
            if (mode !== "english_only" && !value("custom_text")) return "กรุณาพิมพ์ข้อความภาษาไทย";
            if (mode !== "thai_only" && !value("custom_text_en")) return "กรุณาพิมพ์ข้อความภาษาอังกฤษ";
        }
        if (selectedAnnouncement === 10 && !value("num_2")) return "กรุณาเลือกขบวนที่ 2";
        return "";
    }

    function setStatus(text, type = "normal") {
        const el = byId("statusText");
        el.textContent = text;
        if (type === "ok") el.style.background = "rgba(23,119,68,.92)";
        else if (type === "error") el.style.background = "rgba(180,35,24,.92)";
        else if (type === "work") el.style.background = "rgba(199,161,42,.96)";
        else el.style.background = "rgba(255,255,255,.12)";
    }

    function setLoading(active) {
        byId("loadingBar").classList.toggle("active", active);
        document.querySelectorAll(".announce-option, .lang-btn").forEach(btn => btn.disabled = active);
        byId("playButton").disabled = active || selectedAnnouncement === null;
    }

    function getMainPlayer() {
        if (!mainPlayer) {
            mainPlayer = new Audio();
            mainPlayer.preload = "auto";
            mainPlayer.setAttribute("playsinline", "");
            mainPlayer.setAttribute("webkit-playsinline", "");
        }
        return mainPlayer;
    }

    function stopAudio() {
        const player = getMainPlayer();
        try { player.pause(); player.currentTime = 0; } catch (e) {}
        setStatus("หยุดเสียงแล้ว");
    }

    function getAudioContext() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!sharedAudioContext) sharedAudioContext = new AudioContext();
            if (sharedAudioContext.state === "suspended") sharedAudioContext.resume().catch(() => {});
            return sharedAudioContext;
        } catch (e) { return null; }
    }

    async function unlockMobileAudio() {
        getAudioContext();
        if (mobileAudioUnlocked) return;
        const player = getMainPlayer();
        try {
            player.muted = true; player.volume = 0;
            player.src = "/audio/chime.mp3?unlock=" + Date.now();
            player.currentTime = 0;
            await player.play();
            player.pause();
            try { player.currentTime = 0; } catch (e) {}
            mobileAudioUnlocked = true;
        } catch (e) { console.warn("Mobile audio unlock failed:", e); }
        finally { player.muted = false; player.volume = 1; }
    }

    function playWarningTone() {
        return new Promise(resolve => {
            try {
                const ctx = getAudioContext();
                if (!ctx) return resolve();
                const startAt = ctx.currentTime + .02;
                const gain = ctx.createGain();
                gain.gain.setValueAtTime(.0001, startAt);
                gain.gain.exponentialRampToValueAtTime(.12, startAt + .02);
                gain.gain.exponentialRampToValueAtTime(.0001, startAt + .42);
                gain.connect(ctx.destination);
                const osc1 = ctx.createOscillator(); osc1.type = "sine"; osc1.frequency.setValueAtTime(880, startAt); osc1.connect(gain); osc1.start(startAt); osc1.stop(startAt + .18);
                const osc2 = ctx.createOscillator(); osc2.type = "sine"; osc2.frequency.setValueAtTime(660, startAt + .19); osc2.connect(gain); osc2.start(startAt + .19); osc2.stop(startAt + .42);
                setTimeout(resolve, 455);
            } catch (e) { resolve(); }
        });
    }

    function playUrl(url, options = {}) {
        return new Promise((resolve, reject) => {
            const player = getMainPlayer();
            const maxWaitMs = options.maxWaitMs || null;
            const errorText = options.errorText || "เล่นไฟล์เสียงไม่สำเร็จ";
            let finished = false, started = false, safetyTimer = null, startTimer = null;
            function cleanup() {
                player.removeEventListener("ended", onEnded); player.removeEventListener("error", onError); player.removeEventListener("canplay", startPlay);
                if (safetyTimer) clearTimeout(safetyTimer); if (startTimer) clearTimeout(startTimer);
            }
            function finish() { if (finished) return; finished = true; cleanup(); if (maxWaitMs) { try { player.pause(); player.currentTime = 0; } catch (e) {} } resolve(); }
            function fail(e) { if (finished) return; finished = true; cleanup(); reject(e instanceof Error ? e : new Error(errorText)); }
            function onEnded() { finish(); }
            function onError() { fail(new Error(errorText)); }
            async function startPlay() {
                if (started || finished) return; started = true;
                try { player.muted = false; player.volume = 1; await player.play(); } catch (e) { fail(e); }
            }
            try {
                player.pause(); player.src = url; player.preload = "auto"; player.muted = false; player.volume = 1; player.currentTime = 0;
                player.addEventListener("ended", onEnded, { once: true });
                player.addEventListener("error", onError, { once: true });
                player.addEventListener("canplay", startPlay, { once: true });
                player.load(); startTimer = setTimeout(startPlay, 450);
                if (maxWaitMs) safetyTimer = setTimeout(finish, maxWaitMs);
            } catch (e) { fail(e); }
        });
    }

    async function playOriginalChime() {
        try { await playUrl("/audio/chime.mp3?v=" + Date.now(), { maxWaitMs: 5200, errorText: "เล่นเสียงเตือนไม่สำเร็จ" }); }
        catch (e) { await playWarningTone(); }
    }

    async function playSelectedAnnouncement() {
        const error = validateSelection();
        if (error) {
            setStatus("ข้อมูลไม่ครบ", "error");
            byId("previewBox").innerHTML = `<b>กรุณาตรวจสอบข้อมูล</b><br><br>${escapeHtml(error)}`;
            return;
        }
        await playAnnouncement(selectedAnnouncement);
    }

    async function playAnnouncement(tabIndex) {
        if (isBusy) return;
        isBusy = true;
        await unlockMobileAudio();
        setLoading(true); stopAudio();
        setStatus("กำลังสร้างเสียง...", "work");
        byId("previewBox").innerHTML = "<b>กำลังสร้างไฟล์เสียง</b><br><br>ระบบกำลังเตรียมเสียงประกาศ กรุณารอสักครู่";
        try {
            const response = await fetch("/announce", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify(collectPayload(tabIndex))
            });
            const data = await response.json();
            if (!response.ok || data.status !== "success") throw new Error(data.message || "สร้างเสียงไม่สำเร็จ");
            renderServerPreview(data.text_preview || "-");
            const audioUrls = (data.audio_urls && data.audio_urls.length) ? data.audio_urls : [data.audio_url].filter(Boolean);
            const audioLabels = data.audio_labels || [];
            if (!audioUrls.length) throw new Error("ไม่พบไฟล์เสียงสำหรับประกาศ");
            audioUrls.forEach(url => { try { fetch(url, { cache: "no-store" }).catch(() => {}); } catch (e) {} });
            setStatus("เสียงเตือน...", "work");
            await playOriginalChime();
            for (let i = 0; i < audioUrls.length; i++) {
                setStatus(`กำลังประกาศ ${audioLabels[i] || ""}`.trim(), "ok");
                await playUrl(audioUrls[i], { errorText: "มือถือบล็อกเสียงประกาศ กรุณากดปุ่มอีกครั้ง" });
            }
            setStatus("ประกาศเสร็จแล้ว", "ok");
        } catch (err) {
            console.error(err);
            setStatus("เกิดข้อผิดพลาด", "error");
            let message = err.message || String(err);
            if (message.includes("not allowed") || message.includes("permission") || message.includes("บล็อก")) {
                message = "มือถือบล็อกการเล่นเสียงชั่วคราว กรุณากดปุ่มประกาศอีกครั้ง หรือเปิดหน้านี้ผ่าน Chrome/Safari โดยตรง";
            }
            byId("previewBox").innerHTML = `<b>เกิดข้อผิดพลาด</b><br><br>${escapeHtml(message)}`;
        } finally {
            setLoading(false); isBusy = false;
        }
    }

    function clearData() {
        stopAudio();
        ["train_select", "num", "time", "origin", "dest", "next_station", "delay_time", "custom_text", "custom_text_en",
         "train_select_2", "num_2", "time_2", "origin_2", "dest_2", "next_station_2"].forEach(id => { if (byId(id)) byId(id).value = ""; });
        byId("platform").value = "1"; byId("pass_platform").value = "1"; byId("platform_2").value = "2";
        byId("current").value = "คลองบางพระ"; byId("train_type").value = "สินค้า";
        setLanguage("thai_only", document.querySelector('[data-mode="thai_only"]'));
        selectedAnnouncement = null;
        document.querySelectorAll(".announce-option").forEach(btn => btn.classList.remove("active"));
        ["delayFields", "passFields", "customFields", "secondTrainFields"].forEach(id => byId(id).classList.remove("show"));
        byId("playButton").disabled = true;
        byId("selectedType").innerHTML = "<b>ยังไม่ได้เลือกประเภทประกาศ</b><br>เลือกปุ่มในขั้นตอนที่ 3 ก่อน";
        byId("previewBox").innerHTML = "<b>ตัวอย่างข้อความประกาศ</b><br><br>เมื่อกดเริ่มประกาศ ระบบจะสร้างข้อความและไฟล์เสียงตามภาษาที่เลือก";
        refreshSummary(); setStatus("พร้อมใช้งาน");
    }

    updateCustomLanguageFields();
    refreshSummary();
</script>
</body>
</html>
"""



def group_buttons(buttons):
    grouped = {}
    for item in buttons:
        grouped.setdefault(item["group"], []).append(item)
    return grouped


def cleanup_old_audio(max_age_seconds=3600):
    """ลบไฟล์เสียงเก่าที่เกิน 1 ชั่วโมง เพื่อไม่ให้โฟลเดอร์โตเกินไป"""
    now = time.time()
    for file in AUDIO_DIR.glob("announce_*.mp3"):
        try:
            if now - file.stat().st_mtime > max_age_seconds:
                file.unlink(missing_ok=True)
        except OSError:
            pass


def spaced_train_number(number_text):
    digits = "".join(ch for ch in str(number_text) if ch.isdigit())
    return " ".join(digits) if digits else str(number_text or "")


def tidy_time(text):
    return (text or "").replace(" 0 นาที", "").strip()


def station(name):
    name = (name or "").strip()
    if not name:
        return ""
    if name.startswith("สถานี") or name.startswith("ป้ายหยุดรถ") or name.startswith("ที่หยุดรถ"):
        return name
    return f"สถานี{name}"


def clean_space(text):
    return " ".join((text or "").split())


# คำอ่านสำหรับส่งให้ระบบ TTS เท่านั้น
# ข้อความที่แสดงบนหน้าเว็บยังคงเป็นคำทางการเหมือนเดิม
PRONUNCIATION_FIXES = {
    "คลองบางพระ": "คลอง บางพระ",
    "คลองแขวงกลั่น": "คลอง แขวง กลั่น",
    "คลองเปรง": "คลอง เปรง",
    "ชุมทางฉะเชิงเทรา": "ชุมทาง ฉะเชิงเทรา",
    "ด่านพรมแดนบ้านคลองลึก": "ด่านพรมแดน บ้านคลองลึก",
    "กบินทร์บุรี": "กะบินบุรี",
    "จุกเสม็ด": "จุก สะเม็ด",
    "รับส่ง": "รับ ส่ง",
    "ไปมา": "ไป มา",
}


def prepare_tts_text(text):
    tts_text = text or ""
    for official_word, spoken_word in PRONUNCIATION_FIXES.items():
        tts_text = tts_text.replace(official_word, spoken_word)
    return clean_space(tts_text)



EN_STATION_NAMES = {
    "คลองบางพระ": "Khlong Bang Phra",
    "กรุงเทพ": "Bangkok",
    "หัวลำโพง": "Hua Lamphong",
    "ชุมทางฉะเชิงเทรา": "Chachoengsao Junction",
    "ฉะเชิงเทรา": "Chachoengsao",
    "ปราจีนบุรี": "Prachin Buri",
    "กบินทร์บุรี": "Kabin Buri",
    "จุกเสม็ด": "Chuk Samet",
    "ด่านพรมแดนบ้านคลองลึก": "Ban Klong Luk Border",
    "คลองแขวงกลั่น": "Khlong Khwaeng Klan",
    "คลองเปรง": "Khlong Preng",
    "บางเตย": "Bang Toei",
    "สถานีคลองเปรง": "Khlong Preng Station",
    "สถานีชุมทางฉะเชิงเทรา": "Chachoengsao Junction Station",
    "ป้ายหยุดรถคลองแขวงกลั่น": "Khlong Khwaeng Klan Halt",
    "ป้ายหยุดรถบางเตย": "Bang Toei Halt",
}

EN_TRAIN_TYPES = {
    "สินค้า": "freight train",
    "ด่วนพิเศษ": "special express train",
    "พิเศษ": "special train",
    "รถจักรเปล่า": "light engine",
}

DIGIT_WORDS_EN = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
}


def train_number_en(number_text):
    digits = "".join(ch for ch in str(number_text) if ch.isdigit())
    return " ".join(DIGIT_WORDS_EN.get(ch, ch) for ch in digits) if digits else str(number_text or "")


def station_en(name):
    name = (name or "").strip()
    if not name:
        return ""
    cleaned = name
    for prefix in ("สถานี", "ป้ายหยุดรถ", "ที่หยุดรถ"):
        if cleaned.startswith(prefix):
            cleaned = cleaned.replace(prefix, "", 1).strip()
    return EN_STATION_NAMES.get(name) or EN_STATION_NAMES.get(cleaned) or cleaned


def next_stations_en(text):
    result = text or ""
    # แทนคำที่ยาวก่อน เพื่อไม่ให้ชนกับชื่อสถานีย่อย
    for th_name in sorted(EN_STATION_NAMES, key=len, reverse=True):
        result = result.replace(th_name, EN_STATION_NAMES[th_name])
    result = result.replace(" และ ", " and ").replace("และ", " and ")
    return clean_space(result)


def time_en(text):
    raw = text or ""
    nums = [int(part) for part in __import__("re").findall(r"\d+", raw)]
    if not nums:
        return raw
    hour = nums[0]
    minute = nums[1] if len(nums) > 1 else 0
    suffix = "A.M." if hour < 12 else "P.M."
    hour12 = hour % 12
    if hour12 == 0:
        hour12 = 12
    return f"{hour12}:{minute:02d} {suffix}"


def build_english_announcement(data):
    idx = int(data.get("tab_index", -1))

    t_num = train_number_en(data.get("num", ""))
    origin = station_en(data.get("origin", ""))
    dest = station_en(data.get("dest", ""))
    t_time = time_en(tidy_time(data.get("time", "")))
    platform = data.get("platform", "")
    pass_platform = data.get("pass_platform") or platform
    current = station_en(data.get("current", STATION_NAME) or STATION_NAME)
    next_st = next_stations_en(data.get("next", ""))
    delay = time_en(data.get("delay", ""))
    custom_text_en = data.get("custom_text_en", "")
    train_type = EN_TRAIN_TYPES.get(data.get("train_type", "สินค้า") or "สินค้า", "train")

    t_num_2 = train_number_en(data.get("num_2", ""))
    origin_2 = station_en(data.get("origin_2", ""))
    dest_2 = station_en(data.get("dest_2", ""))
    platform_2 = data.get("platform_2", "")
    next_st_2 = next_stations_en(data.get("next_2", ""))

    if idx == 0:
        text = f"Attention please. Passengers traveling on train number {t_num}, from {origin} to {dest}, scheduled at {t_time}, please purchase your ticket at the ticket office before boarding."
    elif idx == 1:
        text = f"Attention please. Passengers holding tickets for train number {t_num}, from {origin} to {dest}, scheduled at {t_time}, please wait with your belongings on platform {platform}."
    elif idx == 2:
        text = f"Attention please. Train number {t_num}, from {origin} to {dest}, scheduled at {t_time}, will shortly arrive at platform {platform}. For your safety, please stand behind the yellow line and do not cross the tracks."
    elif idx == 3:
        text = f"Attention please. A train will shortly pass through platform {pass_platform}. For your safety, please stand behind the yellow line and do not cross the tracks."
    elif idx == 4:
        text = f"Attention please. This is {current} Station. Before leaving the train, please check all your belongings. The train at platform {platform} is train number {t_num}, from {origin} to {dest}, scheduled at {t_time}. After departing {current} Station, the next stops will be {next_st}."
    elif idx == 5:
        text = f"Attention please. Train number {t_num}, from {origin} to {dest}, scheduled at {t_time}, is delayed. The train is expected to arrive at {current} Station at approximately {delay}. The State Railway of Thailand apologizes for the inconvenience."
    elif idx == 6:
        text = f"Attention please. Train number {t_num} will shortly arrive at platform {platform}. Passengers leaving the train, please be careful."
    elif idx == 7:
        text = "Attention please. For safety and good hygiene, the State Railway of Thailand would like to inform all passengers that all station areas, trains, and railway station premises are smoke-free and alcohol-free areas. Smoking and drinking alcoholic beverages are strictly prohibited. Violators are subject to legal action."
    elif idx == 8:
        text = custom_text_en.strip() if custom_text_en.strip() else "Attention please. Please listen carefully to the station announcement."
    elif idx == 9:
        text = f"Attention please. A {train_type} will shortly pass through platform {pass_platform}. For your safety, please stand behind the yellow line and do not cross the tracks."
    elif idx == 10:
        text = (
            f"Attention please. This is {current} Station. Before leaving the train, please check all your belongings. "
            f"The train at platform {platform} is train number {t_num}, from {origin} to {dest}. "
            f"The train at platform {platform_2} is train number {t_num_2}, from {origin_2} to {dest_2}. "
            f"After departing {current} Station, the train at platform {platform} will next stop at {next_st}. "
            f"The train at platform {platform_2} will next stop at {next_st_2}."
        )
    else:
        raise ValueError("ไม่พบประเภทประกาศที่เลือก")

    text = clean_space(text)
    if not text.lower().endswith("thank you."):
        text = f"{text} Thank you."
    return text

def build_announcement(data):
    idx = int(data.get("tab_index", -1))

    t_num = spaced_train_number(data.get("num", ""))
    origin = data.get("origin", "")
    dest = data.get("dest", "")
    t_time = tidy_time(data.get("time", ""))
    platform = data.get("platform", "")
    pass_platform = data.get("pass_platform") or platform
    current = data.get("current", STATION_NAME) or STATION_NAME
    next_st = data.get("next", "")
    delay = data.get("delay", "")
    custom_text = data.get("custom_text", "")
    train_type = data.get("train_type", "สินค้า") or "สินค้า"

    t_num_2 = spaced_train_number(data.get("num_2", ""))
    origin_2 = data.get("origin_2", "")
    dest_2 = data.get("dest_2", "")
    platform_2 = data.get("platform_2", "")
    next_st_2 = data.get("next_2", "")

    if idx == 0:
        text = f"โปรดทราบ ผู้โดยสารที่มีความประสงค์จะเดินทางกับขบวนรถ ขบวนที่ {t_num} รับส่งผู้โดยสารต้นทาง {station(origin)} ปลายทาง {station(dest)} เที่ยวกำหนดเวลา {t_time} ผู้โดยสารท่านใดยังไม่มีตั๋วใช้ในการโดยสาร สามารถติดต่อซื้อตั๋วโดยสารได้ที่ช่องจำหน่ายตั๋ว ขอบคุณครับ"
    elif idx == 1:
        text = f"โปรดทราบ ผู้โดยสารที่มีตั๋วใช้ในการโดยสารกับขบวนรถ ขบวนที่ {t_num} รับส่งผู้โดยสารต้นทาง {station(origin)} ปลายทาง {station(dest)} เที่ยวกำหนดเวลา {t_time} ขอให้ผู้โดยสารนำสิ่งของและสัมภาระของท่าน ไปรอรับการโดยสารในชานชาลาที่ {platform} ขอบคุณครับ"
    elif idx == 2:
        text = f"โปรดทราบ อีกสักครู่ ขบวนรถ ขบวนที่ {t_num} รับส่งผู้โดยสารต้นทาง {station(origin)} ปลายทาง {station(dest)} เที่ยวกำหนดเวลา {t_time} กำลังจะเข้าเทียบสถานีในชานชาลาที่ {platform} เพื่อความปลอดภัย กรุณายืนหลังเส้นสีเหลืองขอบชานชาลา และไม่เดินข้ามไปมา ระหว่างชานชาลาที่ {platform} ขอบคุณครับ"
    elif idx == 3:
        text = f"โปรดทราบ อีกสักครู่จะมีขบวนรถวิ่งผ่านสถานี บริเวณชานชาลาที่ {pass_platform} เพื่อความปลอดภัย กรุณายืนหลังเส้นสีเหลืองขอบชานชาลา และไม่เดินข้ามไปมา ระหว่างชานชาลาที่ {pass_platform} ขอบคุณครับ"
    elif idx == 4:
        text = f"โปรดทราบ ที่นี่{station(current)} ที่นี่{station(current)} ผู้โดยสารก่อนลงจากขบวนรถ โปรดตรวจสอบสิ่งของและสัมภาระของท่าน นำลงจากขบวนรถให้ครบถ้วน ขบวนรถที่จอดเทียบในชานชาลาที่ {platform} เป็นขบวนรถ ขบวนที่ {t_num} รับส่งผู้โดยสารต้นทาง {station(origin)} ปลายทาง {station(dest)} เที่ยวกำหนดเวลา {t_time}  ขบวนรถเที่ยวนี้เมื่อออกจาก{station(current)} แล้ว จะหยุดรับส่งผู้โดยสารที่ {next_st} เป็นสถานีต่อไปตามลำดับ ขอบคุณครับ"
    elif idx == 5:
        text = f"โปรดทราบ วันนี้ขบวนรถ ขบวนที่ {t_num} รับส่งผู้โดยสารต้นทาง {station(origin)} ปลายทาง {station(dest)} เที่ยวกำหนดเวลา {t_time} ล่าช้ากว่ากำหนดเวลาเดิม คาดว่าจะถึง{station(current)} ได้ในเวลาโดยประมาณ {delay} ในนามของการรถไฟแห่งประเทศไทย ต้องขออภัยในความไม่สะดวกในครั้งนี้ ขอบคุณครับ"
    elif idx == 6:
        text = f"โปรดทราบ อีกสักครู่จะมีขบวนรถ ขบวนที่ {t_num} เข้าเทียบในชานชาลาที่ {platform} ผู้โดยสารที่ลงจากขบวนรถ โปรดระมัดระวังด้วยครับ ขอบคุณครับ"
    elif idx == 7:
        text = "ท่านผู้โดยสารโปรดทราบ เพื่อความปลอดภัยและสุขอนามัยที่ดี การรถไฟฯ ขอแจ้งให้ทราบว่า บริเวณสถานี บนขบวนรถ และภายในเขตพื้นที่สถานีทุกแห่ง เป็นเขตปลอดบุหรี่และเครื่องดื่มแอลกอฮอล์ ห้ามสูบบุหรี่และห้ามดื่มสุราโดยเด็ดขาด ผู้ฝ่าฝืนมีความผิดตามกฎหมาย ขอขอบคุณในความร่วมมือครับ"
    elif idx == 8:
        text = custom_text if custom_text.strip() else "กรุณาพิมพ์ข้อความที่ต้องการประกาศในช่องข้อความประกาศเองก่อนกดปุ่มครับ"
    elif idx == 9:
        text = f"โปรดทราบ อีกสักครู่จะมีขบวนรถ{train_type}วิ่งผ่านสถานี บริเวณชานชาลาที่ {pass_platform} เพื่อความปลอดภัย กรุณายืนหลังเส้นสีเหลืองขอบชานชาลา และไม่เดินข้ามไปมา ระหว่างชานชาลาที่ {pass_platform} ขอบคุณครับ"
    elif idx == 10:
        text = (
            f"ผู้โดยสารโปรดทราบ ที่นี่{station(current)} ที่นี่{station(current)} ก่อนผู้โดยสารจะลงจากขบวนรถ โปรดตรวจสอบสิ่งของและสัมภาระของท่าน นำลงให้ถูกต้องครบถ้วน "
            f"ขบวนรถที่จอดในชานชาลาที่ {platform} เป็นขบวนรถ ขบวนที่ {t_num} รับส่งผู้โดยสารต้นทาง {station(origin)} ปลายทาง {station(dest)} "
            f"และขบวนรถที่จอดในชานชาลาที่ {platform_2} เป็นขบวนรถ ขบวนที่ {t_num_2} รับส่งผู้โดยสารต้นทาง {station(origin_2)} ปลายทาง {station(dest_2)} "
            f"ขบวนรถในชานชาลาที่ {platform} เมื่อออกจาก{station(current)}แล้ว จะหยุดรับส่งผู้โดยสารที่ {next_st} เป็นสถานีต่อไปตามลำดับ "
            f"และขบวนรถในชานชาลาที่ {platform_2} เมื่อออกจาก{station(current)}แล้ว จะหยุดรับส่งผู้โดยสารที่ {next_st_2} เป็นสถานีต่อไปตามลำดับ ขอบคุณครับ"
        )
    else:
        raise ValueError("ไม่พบประเภทประกาศที่เลือก")

    return clean_space(text)


@app.route("/")
def index():
    return render_template_string(
        HTML_PAGE,
        inbound=INBOUND_TRAINS,
        outbound=OUTBOUND_TRAINS,
        trains_json=json.dumps(TRAIN_DATA, ensure_ascii=False),
        grouped_buttons=group_buttons(ANNOUNCEMENT_BUTTONS),
        voice_name=VOICE_NAME,
        en_voice_name=EN_VOICE_NAME,
    )


@app.route("/audio/<path:filename>")
def serve_audio(filename):
    # ไฟล์เสียงเตือนเดิม ให้วาง chime.mp3 ไว้โฟลเดอร์เดียวกับไฟล์ Python
    if filename == CHIME_FILENAME:
        return send_from_directory(BASE_DIR, CHIME_FILENAME, mimetype="audio/mpeg", as_attachment=False)

    # ไฟล์เสียงประกาศที่ระบบสร้างใหม่ จะอยู่ในโฟลเดอร์ audio_generated
    return send_from_directory(AUDIO_DIR, filename, mimetype="audio/mpeg", as_attachment=False)


@app.route("/announce", methods=["POST"])
def announce():
    cleanup_old_audio()
    data = request.get_json(silent=True) or {}

    mode = (data.get("announce_mode") or "thai_only").strip()
    allowed_modes = {"thai_only", "english_only", "bilingual"}
    if mode not in allowed_modes:
        return jsonify({"status": "error", "message": "รูปแบบภาษาที่เลือกไม่ถูกต้อง"}), 400

    thai_text = ""
    english_text = ""
    segments = []

    if mode in {"thai_only", "bilingual"}:
        try:
            thai_text = build_announcement(data)
        except Exception as exc:
            return jsonify({"status": "error", "message": f"สร้างข้อความไทยไม่สำเร็จ: {exc}"}), 400

        if not thai_text:
            return jsonify({"status": "error", "message": "ไม่มีข้อความภาษาไทยสำหรับประกาศ"}), 400

        segments.append({
            "code": "th",
            "display_label": "ภาษาไทย",
            "text": thai_text,
            "voice": VOICE_NAME,
            "rate": TTS_RATE,
            "prepare": prepare_tts_text,
        })

    if mode in {"english_only", "bilingual"}:
        try:
            english_text = build_english_announcement(data)
        except Exception as exc:
            return jsonify({"status": "error", "message": f"สร้างข้อความอังกฤษไม่สำเร็จ: {exc}"}), 400

        if not english_text:
            return jsonify({"status": "error", "message": "ไม่มีข้อความภาษาอังกฤษสำหรับประกาศ"}), 400

        segments.append({
            "code": "en",
            "display_label": "ภาษาอังกฤษ",
            "text": english_text,
            "voice": EN_VOICE_NAME,
            "rate": TTS_EN_RATE,
            "prepare": clean_space,
        })

    audio_urls = []
    audio_labels = []
    created_files = []

    try:
        for segment in segments:
            label = segment["code"]
            segment_text = segment["text"]
            filename = f"announce_{label}_{int(time.time())}_{uuid.uuid4().hex[:8]}.mp3"
            output_path = AUDIO_DIR / filename
            tts_text = segment["prepare"](segment_text)

            subprocess.run(
                [
                    "edge-tts",
                    "--voice", segment["voice"],
                    "--rate", segment["rate"],
                    "--text", tts_text,
                    "--write-media", str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            if not output_path.exists() or output_path.stat().st_size == 0:
                raise RuntimeError(f"ระบบสร้างไฟล์เสียงช่วง {label} ไม่สำเร็จ หรือไฟล์เสียงว่าง")

            created_files.append(output_path)
            audio_urls.append(f"/audio/{filename}?v={int(time.time())}")
            audio_labels.append(segment["display_label"])

    except FileNotFoundError:
        return jsonify({
            "status": "error",
            "message": "ยังไม่ได้ติดตั้ง edge-tts ให้รันคำสั่ง: pip install edge-tts",
            "text_preview": thai_text or english_text,
        }), 500
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        return jsonify({
            "status": "error",
            "message": f"สร้างเสียงไม่สำเร็จ: {detail}",
            "text_preview": thai_text or english_text,
        }), 500
    except Exception as exc:
        return jsonify({
            "status": "error",
            "message": str(exc),
            "text_preview": thai_text or english_text,
        }), 500

    if not audio_urls:
        return jsonify({
            "status": "error",
            "message": "ไม่มีไฟล์เสียงสำหรับประกาศ",
            "text_preview": thai_text or english_text,
        }), 500

    if mode == "bilingual":
        preview = f"🇹🇭 {thai_text}<br><br>🇬🇧 {english_text}"
    elif mode == "english_only":
        preview = f"🇬🇧 {english_text}"
    else:
        preview = f"🇹🇭 {thai_text}"

    return jsonify({
        "status": "success",
        "audio_url": audio_urls[0],
        "audio_urls": audio_urls,
        "audio_labels": audio_labels,
        "announce_mode": mode,
        "text_preview": preview,
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
