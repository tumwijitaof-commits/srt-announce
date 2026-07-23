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
    {"label": "389 (13:23) กรุงเทพ - ฉะเชิงเทรา", "num": "389", "origin": "กรุงเทพ", "dest": "ชุมทางฉะเชิงเทรา", "time": "13 นาฬิกา 23 นาที", "next": "สถานีชุมทางฉะเชิงเทรา"},
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
            --srt-maroon: #800000;
            --srt-maroon-dark: #5d0000;
            --srt-gold: #c9a227;
            --paper: #fffaf0;
            --ink: #221b1b;
            --muted: #6f6262;
            --line: #e8ddca;
            --success: #1b7f45;
            --danger: #b3261e;
            --blue: #0b57d0;
            --shadow: 0 14px 36px rgba(65, 0, 0, 0.12);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            color: var(--ink);
            font-family: "Sarabun", "Noto Sans Thai", "Segoe UI", Tahoma, sans-serif;
            background:
                radial-gradient(circle at top left, rgba(201,162,39,0.20), transparent 30%),
                linear-gradient(135deg, #fff8ea 0%, #f5efe3 48%, #efe2ce 100%);
            min-height: 100vh;
            padding: 18px;
        }
        .app-shell { max-width: 1180px; margin: 0 auto; }
        .official-header {
            color: white;
            background: linear-gradient(135deg, var(--srt-maroon-dark), var(--srt-maroon));
            border: 1px solid rgba(201,162,39,0.65);
            border-radius: 24px;
            padding: 22px;
            box-shadow: var(--shadow);
            position: sticky;
            top: 12px;
            z-index: 10;
        }
        .header-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            flex-wrap: wrap;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .seal {
            width: 58px;
            height: 58px;
            border-radius: 18px;
            background: linear-gradient(135deg, #fff4c2, var(--srt-gold));
            color: var(--srt-maroon);
            display: grid;
            place-items: center;
            font-size: 30px;
            box-shadow: inset 0 0 0 3px rgba(255,255,255,0.35);
            flex: 0 0 auto;
        }
        h1 { margin: 0; font-size: clamp(22px, 3vw, 32px); line-height: 1.2; }
        .sub { margin: 5px 0 0; opacity: 0.92; font-size: 14px; }
        .status-pill {
            background: rgba(255,255,255,0.13);
            border: 1px solid rgba(255,255,255,0.27);
            border-radius: 999px;
            padding: 10px 14px;
            font-weight: 700;
            min-width: 220px;
            text-align: center;
        }
        .main-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.04fr) minmax(360px, 0.96fr);
            gap: 18px;
            margin-top: 18px;
            align-items: start;
        }
        .card {
            background: rgba(255,255,255,0.92);
            border: 1px solid var(--line);
            border-radius: 22px;
            box-shadow: var(--shadow);
            overflow: hidden;
        }
        .card-title {
            margin: 0;
            padding: 15px 18px;
            color: var(--srt-maroon-dark);
            border-bottom: 1px solid var(--line);
            background: linear-gradient(180deg, #fffdf8, #fff7e8);
            font-size: 18px;
        }
        .card-body { padding: 18px; }
        label {
            display: block;
            font-weight: 800;
            margin: 12px 0 6px;
            color: #352828;
        }
        select, input, textarea {
            width: 100%;
            border: 1px solid #d6c7b0;
            border-radius: 14px;
            padding: 12px 13px;
            background: white;
            color: var(--ink);
            font-size: 15px;
            outline: none;
            transition: border 0.15s, box-shadow 0.15s;
            font-family: inherit;
        }
        select:focus, input:focus, textarea:focus {
            border-color: var(--srt-gold);
            box-shadow: 0 0 0 4px rgba(201,162,39,0.18);
        }
        textarea { min-height: 84px; resize: vertical; }
        .field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 12px; }
        .helper { color: var(--muted); font-size: 13px; margin-top: 7px; line-height: 1.45; }
        .train-card-2 {
            border: 1px dashed rgba(128,0,0,0.35);
            border-radius: 18px;
            padding: 15px;
            background: #fffaf0;
            margin-top: 14px;
        }
        .action-groups { display: grid; gap: 14px; }
        .group-title {
            margin: 4px 0 8px;
            color: var(--srt-maroon);
            font-size: 15px;
            border-left: 5px solid var(--srt-gold);
            padding-left: 10px;
        }
        .button-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        button {
            border: 0;
            font-family: inherit;
            cursor: pointer;
            transition: transform 0.12s ease, opacity 0.12s ease, box-shadow 0.12s ease;
        }
        button:active { transform: translateY(1px) scale(0.99); }
        button:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }
        .announce-btn {
            text-align: left;
            border-radius: 16px;
            padding: 14px;
            background: linear-gradient(135deg, #ffffff, #fff7e7);
            border: 1px solid #eadcc4;
            color: var(--ink);
            min-height: 82px;
            box-shadow: 0 6px 16px rgba(68,0,0,0.06);
        }
        .announce-btn:hover { box-shadow: 0 10px 22px rgba(68,0,0,0.12); }
        .announce-btn strong { display: block; color: var(--srt-maroon-dark); font-size: 16px; }
        .announce-btn span { display: block; color: var(--muted); font-size: 12.5px; margin-top: 3px; line-height: 1.35; }
        .toolbar { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 14px; }
        .secondary, .stop {
            border-radius: 14px;
            padding: 13px;
            font-weight: 900;
            color: white;
        }
        .secondary { background: var(--srt-maroon); }
        .stop { background: var(--danger); }
        .preview-box {
            margin-top: 14px;
            border-radius: 18px;
            padding: 14px;
            background: #fff8e8;
            border: 1px solid #eadcc4;
            color: #473535;
            font-size: 14px;
            line-height: 1.65;
            min-height: 88px;
        }
        .preview-box b { color: var(--srt-maroon); }
        .notice {
            margin-top: 12px;
            background: #f4efe4;
            border: 1px solid #e2d7c4;
            border-radius: 16px;
            padding: 12px;
            color: #5d5149;
            font-size: 13px;
            line-height: 1.55;
        }
        .loading-bar {
            height: 5px;
            width: 100%;
            border-radius: 999px;
            background: rgba(255,255,255,0.20);
            overflow: hidden;
            margin-top: 13px;
            display: none;
        }
        .loading-bar.active { display: block; }
        .loading-bar::after {
            content: "";
            display: block;
            height: 100%;
            width: 38%;
            border-radius: inherit;
            background: linear-gradient(90deg, transparent, #fff4b2, transparent);
            animation: move 1s linear infinite;
        }
        @keyframes move { from { transform: translateX(-100%); } to { transform: translateX(280%); } }
        @media (max-width: 900px) {
            body { padding: 10px; }
            .official-header { position: static; border-radius: 20px; }
            .main-grid { grid-template-columns: 1fr; }
            .button-grid { grid-template-columns: 1fr; }
        }
        @media (max-width: 560px) {
            .field-grid, .toolbar { grid-template-columns: 1fr; }
            .seal { width: 48px; height: 48px; font-size: 25px; }
        }
    </style>
</head>
<body>
    <main class="app-shell">
        <section class="official-header">
            <div class="header-top">
                <div class="brand">
                    <div class="seal">🚆</div>
                    <div>
                        <h1>ระบบประกาศสถานีคลองบางพระ</h1>
                        <p class="sub">แบบฟอร์มประกาศเสียงอัตโนมัติ | สถานีคลองบางพระ</p>
                    </div>
                </div>
                <div class="status-pill" id="statusText">พร้อมใช้งาน</div>
            </div>
            <div class="loading-bar" id="loadingBar"></div>
        </section>

        <section class="main-grid">
            <div class="card">
                <h2 class="card-title">1) เลือกข้อมูลขบวนรถ</h2>
                <div class="card-body">
                    <label>เลือกขบวนที่ 1</label>
                    <select id="train_select" onchange="autoFill(1)">
                        <option value="">-- เลือกขบวนรถ --</option>
                        <optgroup label="ขาเข้า กรุงเทพ (หัวลำโพง)">
                        {% for train in inbound %}
                            <option value="{{ train.label }}">{{ train.label }}</option>
                        {% endfor %}
                        </optgroup>
                        <optgroup label="ขาออก ไปทางตะวันออก">
                        {% for train in outbound %}
                            <option value="{{ train.label }}">{{ train.label }}</option>
                        {% endfor %}
                        </optgroup>
                    </select>

                    <div class="field-grid">
                        <div><label>ขบวนที่</label><input type="text" id="num" placeholder="เช่น 383"></div>
                        <div><label>เวลา</label><input type="text" id="time" placeholder="เช่น 20 นาฬิกา 25 นาที"></div>
                        <div><label>ต้นทาง</label><input type="text" id="origin"></div>
                        <div><label>ปลายทาง</label><input type="text" id="dest"></div>
                        <div><label>ชานชาลาที่</label><input type="text" id="platform" placeholder="เช่น 1"></div>
                        <div><label>สถานีปัจจุบัน</label><input type="text" id="current" value="คลองบางพระ"></div>
                    </div>

                    <label>สถานีต่อไป</label>
                    <input type="text" id="next_station" placeholder="ใช้กับประกาศรถออก / รถเข้าพร้อมกัน">

                    <label>คาดว่าจะถึงเวลา</label>
                    <input type="text" id="delay_time" placeholder="ใช้กับรถล่าช้า เช่น 19 นาฬิกา 30 นาที">

                    <div class="train-card-2">
                        <b style="color:var(--srt-maroon);">ข้อมูลขบวนที่ 2</b>
                        <div class="helper">ใช้เฉพาะปุ่ม “รถเข้าพร้อมกัน 2 ขบวน”</div>
                        <label>เลือกขบวนที่ 2</label>
                        <select id="train_select_2" onchange="autoFill(2)">
                            <option value="">-- เลือกขบวนรถ --</option>
                            <optgroup label="ขาเข้า กรุงเทพ (หัวลำโพง)">
                            {% for train in inbound %}
                                <option value="{{ train.label }}">{{ train.label }}</option>
                            {% endfor %}
                            </optgroup>
                            <optgroup label="ขาออก ไปทางตะวันออก">
                            {% for train in outbound %}
                                <option value="{{ train.label }}">{{ train.label }}</option>
                            {% endfor %}
                            </optgroup>
                        </select>

                        <div class="field-grid">
                            <div><label>ขบวนที่ 2</label><input type="text" id="num_2"></div>
                            <div><label>เวลา 2</label><input type="text" id="time_2"></div>
                            <div><label>ต้นทาง 2</label><input type="text" id="origin_2"></div>
                            <div><label>ปลายทาง 2</label><input type="text" id="dest_2"></div>
                            <div><label>ชานชาลาที่ 2</label><input type="text" id="platform_2"></div>
                            <div><label>สถานีต่อไป 2</label><input type="text" id="next_station_2"></div>
                        </div>
                    </div>

                    <label>ประเภทรถวิ่งผ่าน</label>
                    <select id="train_type">
                        <option value="สินค้า">สินค้า</option>
                        <option value="ด่วนพิเศษ">ด่วนพิเศษ</option>
                        <option value="พิเศษ">พิเศษ</option>
                        <option value="รถจักรเปล่า">รถจักรเปล่า</option>
                    </select>

                    <label>ชานชาลาสำหรับประกาศรถผ่าน</label>
                    <select id="pass_platform">
                        <option value="1" selected>ชานชาลาที่ 1</option>
                        <option value="2">ชานชาลาที่ 2</option>
                        <option value="3">ชานชาลาที่ 3</option>
                    </select>
                    <div class="helper">ใช้กับปุ่ม “รถผ่านสถานี” และ “สินค้า / พิเศษ ผ่าน” เพื่อไม่ต้องพิมพ์ชานชาลาเอง</div>

                    <label>รูปแบบเสียงประกาศ</label>
                    <select id="announce_mode">
                        <option value="bilingual" selected>ไทย + อังกฤษ</option>
                        <option value="thai_only">ภาษาไทยเท่านั้น</option>
                    </select>
                    <div class="helper">โหมดสองภาษา: เล่นเสียงเตือน → ภาษาไทย → ภาษาอังกฤษ</div>

                    <label>พิมพ์ข้อความประกาศเอง ภาษาไทย</label>
                    <textarea id="custom_text" placeholder="พิมพ์ข้อความที่ต้องการประกาศเองตรงนี้"></textarea>

                    <label>ข้อความอังกฤษสำหรับประกาศเอง</label>
                    <textarea id="custom_text_en" placeholder="ใช้เฉพาะปุ่มประกาศเอง ถ้าเว้นว่าง ระบบจะพูดอังกฤษแบบทั่วไป"></textarea>

                    <div class="toolbar">
                        <button class="secondary" onclick="clearData()">ล้างข้อมูล</button>
                        <button class="stop" onclick="stopAudio()">หยุดเสียง</button>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2 class="card-title">2) เลือกประเภทประกาศ</h2>
                <div class="card-body">
                    <div class="action-groups">
                        {% for group, buttons in grouped_buttons.items() %}
                        <div>
                            <h3 class="group-title">{{ group }}</h3>
                            <div class="button-grid">
                                {% for button in buttons %}
                                <button class="announce-btn" onclick="playAnnouncement({{ button.idx }})">
                                    <strong>{{ button.title }}</strong>
                                    <span>{{ button.hint }}</span>
                                </button>
                                {% endfor %}
                            </div>
                        </div>
                        {% endfor %}
                    </div>

                    <div class="preview-box" id="previewBox">
                        <b>ตัวอย่างข้อความประกาศ:</b><br>
                        กดปุ่มประกาศเพื่อสร้างเสียง ระบบจะสร้างไฟล์เสียงให้เสร็จก่อน แล้วเล่นเสียงเตือนสั้น ๆ ต่อด้วยเสียงประกาศทันที
                    </div>

                    <div class="notice">
                        หมายเหตุ: ระบบนี้ใช้เสียงไทย <b>{{ voice_name }}</b> และเสียงอังกฤษ <b>{{ en_voice_name }}</b> ผ่าน edge-tts โดยสร้างไฟล์เสียงแยกทุกครั้ง เพื่อลดปัญหาไฟล์เก่าค้างหรือกดพร้อมกันแล้วเสียงชนกัน
                    </div>
                </div>
            </div>
        </section>
    </main>

    <script>
        const trainData = {{ trains_json | safe }};
        let mainPlayer = null;
        let isBusy = false;
        let sharedAudioContext = null;
        let mobileAudioUnlocked = false;

        function byId(id) { return document.getElementById(id); }
        function value(id) { return (byId(id)?.value || "").trim(); }

        function getMainPlayer() {
            if (!mainPlayer) {
                mainPlayer = new Audio();
                mainPlayer.preload = "auto";
                mainPlayer.setAttribute("playsinline", "");
                mainPlayer.setAttribute("webkit-playsinline", "");
            }
            return mainPlayer;
        }

        function setStatus(text, type = "normal") {
            const el = byId("statusText");
            el.innerText = text;
            if (type === "ok") el.style.background = "rgba(27,127,69,0.92)";
            else if (type === "error") el.style.background = "rgba(179,38,30,0.92)";
            else if (type === "work") el.style.background = "rgba(201,162,39,0.96)";
            else el.style.background = "rgba(255,255,255,0.13)";
        }

        function setLoading(active) {
            byId("loadingBar").classList.toggle("active", active);
            document.querySelectorAll(".announce-btn").forEach(btn => btn.disabled = active);
        }

        function autoFill(type) {
            const suffix = type === 1 ? "" : "_2";
            const selectId = type === 1 ? "train_select" : "train_select_2";
            const selected = value(selectId);
            const data = trainData[selected];
            if (!data) return;
            byId("num" + suffix).value = data.num || "";
            byId("origin" + suffix).value = data.origin || "";
            byId("dest" + suffix).value = data.dest || "";
            byId("time" + suffix).value = data.time || "";
            byId("next_station" + suffix).value = data.next || "";
        }

        function clearData() {
            const fields = [
                "train_select", "num", "time", "origin", "dest", "platform", "next_station", "delay_time", "custom_text", "custom_text_en",
                "train_select_2", "num_2", "time_2", "origin_2", "dest_2", "platform_2", "next_station_2"
            ];
            fields.forEach(id => { if (byId(id)) byId(id).value = ""; });
            byId("current").value = "คลองบางพระ";
            byId("announce_mode").value = "bilingual";
            if (byId("pass_platform")) byId("pass_platform").value = "1";
            byId("previewBox").innerHTML = "<b>ตัวอย่างข้อความประกาศ:</b><br>ล้างข้อมูลเรียบร้อยแล้ว";
            setStatus("พร้อมใช้งาน");
        }

        function stopAudio() {
            const player = getMainPlayer();
            try {
                player.pause();
                player.currentTime = 0;
            } catch (e) {}
            setStatus("หยุดเสียงแล้ว");
        }

        function collectPayload(tabIndex) {
            return {
                tab_index: tabIndex,
                announce_mode: value("announce_mode") || "bilingual",
                num: value("num"),
                origin: value("origin"),
                dest: value("dest"),
                time: value("time"),
                platform: value("platform"),
                current: value("current") || "คลองบางพระ",
                next: value("next_station"),
                delay: value("delay_time"),
                custom_text: value("custom_text"),
                custom_text_en: value("custom_text_en"),
                train_type: value("train_type") || "สินค้า",
                pass_platform: value("pass_platform") || value("platform") || "1",
                num_2: value("num_2"),
                origin_2: value("origin_2"),
                dest_2: value("dest_2"),
                time_2: value("time_2"),
                platform_2: value("platform_2"),
                next_2: value("next_station_2")
            };
        }

        function getAudioContext() {
            try {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                if (!sharedAudioContext) sharedAudioContext = new AudioContext();
                if (sharedAudioContext.state === "suspended") sharedAudioContext.resume().catch(() => {});
                return sharedAudioContext;
            } catch (e) {
                return null;
            }
        }

        async function unlockMobileAudio() {
            // มือถือบางรุ่นจะบล็อกเสียง ถ้า play() เกิดหลังจากรอสร้างไฟล์เสียงนานไป
            // วิธีแก้คือปลดล็อก media element หลักทันทีตอนผู้ใช้แตะปุ่ม แล้วใช้ element เดิมเล่นทุกไฟล์ต่อกัน
            getAudioContext();
            if (mobileAudioUnlocked) return;
            const player = getMainPlayer();
            try {
                player.muted = true;
                player.volume = 0;
                player.src = "/audio/chime.mp3?unlock=" + Date.now();
                player.currentTime = 0;
                await player.play();
                player.pause();
                try { player.currentTime = 0; } catch (e) {}
                mobileAudioUnlocked = true;
            } catch (e) {
                console.warn("Mobile audio unlock failed:", e);
            } finally {
                player.muted = false;
                player.volume = 1;
            }
        }

        function playWarningTone() {
            return new Promise((resolve) => {
                try {
                    const ctx = getAudioContext();
                    if (!ctx) return resolve();

                    const startAt = ctx.currentTime + 0.02;
                    const gain = ctx.createGain();
                    gain.gain.setValueAtTime(0.0001, startAt);
                    gain.gain.exponentialRampToValueAtTime(0.12, startAt + 0.02);
                    gain.gain.exponentialRampToValueAtTime(0.0001, startAt + 0.42);
                    gain.connect(ctx.destination);

                    const osc1 = ctx.createOscillator();
                    osc1.type = "sine";
                    osc1.frequency.setValueAtTime(880, startAt);
                    osc1.connect(gain);
                    osc1.start(startAt);
                    osc1.stop(startAt + 0.18);

                    const osc2 = ctx.createOscillator();
                    osc2.type = "sine";
                    osc2.frequency.setValueAtTime(660, startAt + 0.19);
                    osc2.connect(gain);
                    osc2.start(startAt + 0.19);
                    osc2.stop(startAt + 0.42);

                    setTimeout(resolve, 455);
                } catch (e) {
                    resolve();
                }
            });
        }

        function playUrl(url, options = {}) {
            return new Promise((resolve, reject) => {
                const player = getMainPlayer();
                const maxWaitMs = options.maxWaitMs || null;
                const errorText = options.errorText || "เล่นไฟล์เสียงไม่สำเร็จ";
                let finished = false;
                let started = false;
                let safetyTimer = null;
                let startTimer = null;

                function cleanup() {
                    player.removeEventListener("ended", onEnded);
                    player.removeEventListener("error", onError);
                    player.removeEventListener("canplay", startPlay);
                    if (safetyTimer) clearTimeout(safetyTimer);
                    if (startTimer) clearTimeout(startTimer);
                }

                function finish() {
                    if (finished) return;
                    finished = true;
                    cleanup();
                    if (maxWaitMs) {
                        try { player.pause(); player.currentTime = 0; } catch (e) {}
                    }
                    resolve();
                }

                function fail(e) {
                    if (finished) return;
                    finished = true;
                    cleanup();
                    reject(e instanceof Error ? e : new Error(errorText));
                }

                function onEnded() { finish(); }
                function onError() { fail(new Error(errorText)); }

                async function startPlay() {
                    if (started || finished) return;
                    started = true;
                    try {
                        player.muted = false;
                        player.volume = 1;
                        await player.play();
                    } catch (e) {
                        fail(e);
                    }
                }

                try {
                    player.pause();
                    player.src = url;
                    player.preload = "auto";
                    player.muted = false;
                    player.volume = 1;
                    player.currentTime = 0;
                    player.addEventListener("ended", onEnded, { once: true });
                    player.addEventListener("error", onError, { once: true });
                    player.addEventListener("canplay", startPlay, { once: true });
                    player.load();
                    startTimer = setTimeout(startPlay, 450);
                    if (maxWaitMs) safetyTimer = setTimeout(finish, maxWaitMs);
                } catch (e) {
                    fail(e);
                }
            });
        }

        async function playOriginalChime() {
            try {
                await playUrl("/audio/chime.mp3?v=" + Date.now(), {
                    maxWaitMs: 5200,
                    errorText: "เล่นเสียงเตือนไม่สำเร็จ"
                });
            } catch (e) {
                await playWarningTone();
            }
        }

        async function playAnnouncement(tabIndex) {
            if (isBusy) return;
            isBusy = true;
            await unlockMobileAudio();
            setLoading(true);
            stopAudio();
            setStatus("กำลังสร้างเสียงประกาศ...", "work");
            byId("previewBox").innerHTML = "<b>สถานะ:</b><br>กำลังสร้างไฟล์เสียง กรุณารอสักครู่";

            try {
                const response = await fetch("/announce", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(collectPayload(tabIndex))
                });
                const data = await response.json();

                if (!response.ok || data.status !== "success") {
                    throw new Error(data.message || "สร้างเสียงไม่สำเร็จ");
                }

                byId("previewBox").innerHTML = "<b>ข้อความประกาศ:</b><br>" + (data.text_preview || "-");
                const audioUrls = (data.audio_urls && data.audio_urls.length) ? data.audio_urls : [data.audio_url].filter(Boolean);
                if (!audioUrls.length) throw new Error("ไม่พบไฟล์เสียงสำหรับประกาศ");

                // โหลดไฟล์เข้าหน่วยความจำล่วงหน้าเล็กน้อย ลดการหน่วงระหว่างไทย-อังกฤษ
                audioUrls.forEach(url => { try { fetch(url, { cache: "no-store" }).catch(() => {}); } catch (e) {} });

                setStatus("เสียงเตือน...", "work");
                await playOriginalChime();

                const labels = ["ภาษาไทย", "ภาษาอังกฤษ"];
                for (let i = 0; i < audioUrls.length; i++) {
                    setStatus(audioUrls.length > 1 ? "กำลังประกาศ " + (labels[i] || (i + 1)) : "กำลังประกาศ", "ok");
                    await playUrl(audioUrls[i], { errorText: "มือถือบล็อกเสียงประกาศ กรุณาแตะปุ่มประกาศอีกครั้ง" });
                }
                setStatus("ประกาศเสร็จแล้ว", "ok");
            } catch (err) {
                console.error(err);
                setStatus("เกิดข้อผิดพลาด", "error");
                let message = err.message || String(err);
                if (message.includes("not allowed") || message.includes("permission") || message.includes("บล็อก")) {
                    message = "มือถือบล็อกการเล่นเสียงชั่วคราว ให้กดปุ่มประกาศเดิมอีกครั้ง หรือเปิดหน้านี้ผ่าน Chrome/Safari โดยตรง และตรวจว่าไม่ได้ปิดเสียงมือถือ";
                }
                byId("previewBox").innerHTML = "<b>เกิดข้อผิดพลาด:</b><br>" + message;
            } finally {
                setLoading(false);
                isBusy = false;
            }
        }
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

    try:
        thai_text = build_announcement(data)
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    if not thai_text:
        return jsonify({"status": "error", "message": "ไม่มีข้อความสำหรับประกาศ"}), 400

    mode = (data.get("announce_mode") or "bilingual").strip()
    segments = [("th", thai_text, VOICE_NAME, TTS_RATE, prepare_tts_text)]

    english_text = ""
    if mode == "bilingual":
        try:
            english_text = build_english_announcement(data)
        except Exception as exc:
            return jsonify({"status": "error", "message": f"สร้างข้อความอังกฤษไม่สำเร็จ: {exc}"}), 400
        segments.append(("en", english_text, EN_VOICE_NAME, TTS_EN_RATE, clean_space))

    audio_urls = []
    created_files = []

    try:
        for label, segment_text, voice, rate, prepare_func in segments:
            if not segment_text:
                continue
            filename = f"announce_{label}_{int(time.time())}_{uuid.uuid4().hex[:8]}.mp3"
            output_path = AUDIO_DIR / filename
            tts_text = prepare_func(segment_text)
            subprocess.run(
                [
                    "edge-tts",
                    "--voice", voice,
                    "--rate", rate,
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
    except FileNotFoundError:
        return jsonify({
            "status": "error",
            "message": "ยังไม่ได้ติดตั้ง edge-tts ให้รันคำสั่ง: pip install edge-tts",
            "text_preview": thai_text,
        }), 500
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        return jsonify({
            "status": "error",
            "message": f"สร้างเสียงไม่สำเร็จ: {detail}",
            "text_preview": thai_text,
        }), 500
    except Exception as exc:
        return jsonify({
            "status": "error",
            "message": str(exc),
            "text_preview": thai_text,
        }), 500

    if not audio_urls:
        return jsonify({
            "status": "error",
            "message": "ไม่มีไฟล์เสียงสำหรับประกาศ",
            "text_preview": thai_text,
        }), 500

    preview = thai_text
    if mode == "bilingual":
        preview = f"🇹🇭 {thai_text}<br><br>🇬🇧 {english_text}"

    return jsonify({
        "status": "success",
        "audio_url": audio_urls[0],
        "audio_urls": audio_urls,
        "text_preview": preview,
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
