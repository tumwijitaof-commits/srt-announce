from flask import Flask, request, render_template_string, send_file
import os
import subprocess
import json
import time

app = Flask(__name__)

# --- ฐานข้อมูลตารางเดินรถ ---
TRAINS = {
    "--- ขบวนขาเข้า กรุงเทพ (หัวลำโพง) ---": None,
    "384 (05:30) ฉะเชิงเทรา - กรุงเทพ": {"num": "384", "origin": "ชุมทางฉะเชิงเทรา", "dest": "กรุงเทพ", "time": "5 นาฬิกา 30 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    "380 (05:55) ฉะเชิงเทรา - กรุงเทพ": {"num": "380", "origin": "ชุมทางฉะเชิงเทรา", "dest": "กรุงเทพ", "time": "5 นาฬิกา 55 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    "372 (06:30) ปราจีนบุรี - กรุงเทพ": {"num": "372", "origin": "ปราจีนบุรี", "dest": "กรุงเทพ", "time": "6 นาฬิกา 30 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    "388 (07:12) ฉะเชิงเทรา - กรุงเทพ": {"num": "388", "origin": "ชุมทางฉะเชิงเทรา", "dest": "กรุงเทพ", "time": "7 นาฬิกา 12 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    "278 (08:41) กบินทร์บุรี - กรุงเทพ": {"num": "278", "origin": "กบินทร์บุรี", "dest": "กรุงเทพ", "time": "8 นาฬิกา 41 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    "280 (10:33) คลองลึก - กรุงเทพ": {"num": "280", "origin": "ด่านพรมแดนบ้านคลองลึก", "dest": "กรุงเทพ", "time": "10 นาฬิกา 33 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    "368 (12:44) ฉะเชิงเทรา - กรุงเทพ": {"num": "368", "origin": "ชุมทางฉะเชิงเทรา", "dest": "กรุงเทพ", "time": "12 นาฬิกา 44 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    "390 (14:12) ฉะเชิงเทรา - กรุงเทพ": {"num": "390", "origin": "ชุมทางฉะเชิงเทรา", "dest": "กรุงเทพ", "time": "14 นาฬิกา 12 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    "282 (15:42) กบินทร์บุรี - กรุงเทพ": {"num": "282", "origin": "กบินทร์บุรี", "dest": "กรุงเทพ", "time": "15 นาฬิกา 42 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    "284 (16:33) ดอนสีมนท์ - กรุงเทพ": {"num": "284", "origin": "จุกเสม็ด", "dest": "กรุงเทพ", "time": "16 นาฬิกา 33 นาที", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    "276 (19:00) คลองลึก - กรุงเทพ": {"num": "276", "origin": "ด่านพรมแดนบ้านคลองลึก", "dest": "กรุงเทพ", "time": "19 นาฬิกา", "next": "ป้ายหยุดรถคลองแขวงกลั่น และ สถานีคลองเปรง"},
    
    "--- ขบวนขาออก ไปทางตะวันออก ---": None,
    "275 (07:28) กรุงเทพ - คลองลึก": {"num": "275", "origin": "กรุงเทพ", "dest": "ด่านพรมแดนบ้านคลองลึก", "time": "7 นาฬิกา 28 นาที", "next": "บางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    "283 (08:46) กรุงเทพ - จุกเสม็ด": {"num": "283", "origin": "กรุงเทพ", "dest": "จุกเสม็ด", "time": "8 นาฬิกา 46 นาที", "next": "บางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    "281 (09:23) กรุงเทพ - กบินทร์บุรี": {"num": "281", "origin": "กรุงเทพ", "dest": "กบินทร์บุรี", "time": "9 นาฬิกา 23 นาที", "next": "สถานีชุมทางฉะเชิงเทรา"},
    "367 (11:35) กรุงเทพ - ฉะเชิงเทรา": {"num": "367", "origin": "กรุงเทพ", "dest": "ชุมทางฉะเชิงเทรา", "time": "11 นาฬิกา 35 นาที", "next": "บางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    "389 (13:23) กรุงเทพ - ฉะเชิงเทรา": {"num": "389", "origin": "กรุงเทพ", "dest": "ชุมทางฉะเชิงเทรา", "time": "13 นาฬิกา 23 นาที", "next": "บางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    "279 (14:08) กรุงเทพ - คลองลึก": {"num": "279", "origin": "กรุงเทพ", "dest": "ด่านพรมแดนบ้านคลองลึก", "time": "14 นาฬิกา 8 นาที", "next": "สถานีชุมทางฉะเชิงเทรา"},
    "277 (16:37) กรุงเทพ - กบินทร์บุรี": {"num": "277", "origin": "กรุงเทพ", "dest": "กบินทร์บุรี", "time": "16 นาฬิกา 37 นาที", "next": "บางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    "379 (17:57) กรุงเทพ - ฉะเชิงเทรา": {"num": "379", "origin": "กรุงเทพ", "dest": "ชุมทางฉะเชิงเทรา", "time": "17 นาฬิกา 57 นาที", "next": "บางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    "391 (18:17) กรุงเทพ - ฉะเชิงเทรา": {"num": "391", "origin": "กรุงเทพ", "dest": "ชุมทางฉะเชิงเทรา", "time": "18 นาฬิกา 17 นาที", "next": "บางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    "371 (19:11) กรุงเทพ - ปราจีนบุรี": {"num": "371", "origin": "กรุงเทพ", "dest": "ปราจีนบุรี", "time": "19 นาฬิกา 11 นาที", "next": "บางเตย และ สถานีชุมทางฉะเชิงเทรา"},
    "383 (20:25) กรุงเทพ - ฉะเชิงเทรา": {"num": "383", "origin": "กรุงเทพ", "dest": "ชุมทางฉะเชิงเทรา", "time": "20 นาฬิกา 25 นาที", "next": "บางเตย และ สถานีชุมทางฉะเชิงเทรา"},
}

HTML_PAGE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ระบบประกาศสถานีคลองบางพระ</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; padding: 15px; margin: 0; }
        .container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }
        h2 { text-align: center; color: #1a73e8; font-size: 22px; }
        label { font-weight: bold; margin-top: 10px; display: block; font-size: 14px; }
        select, input, textarea { width: 100%; padding: 12px; margin-top: 5px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; font-size: 16px; }
        .btn { width: 100%; padding: 15px; margin-top: 10px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; color: white; transition: 0.2s; }
        .btn-play { background-color: #4CAF50; }
        .btn-play:active { background-color: #45a049; transform: scale(0.98); }
        .btn-clear { background-color: #f44336; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .status { text-align: center; margin-top: 15px; color: #1a73e8; font-weight: bold; display: none; padding: 10px; border-radius: 5px; background: #e8f0fe;}
    </style>
</head>
<body>
    <div class="container">
        <h2>📢 ประกาศสถานีคลองบางพระ (ออนไลน์)</h2>
        
        <label>เลือกรถขบวนที่:</label>
        <select id="train_select" onchange="autoFill()">
            <option value="">-- เลือกขบวน --</option>
            {% for key in trains.keys() %}
                <option value="{{ key }}">{{ key }}</option>
            {% endfor %}
        </select>

        <div class="grid">
            <div><label>ขบวนที่:</label><input type="text" id="num"></div>
            <div><label>เวลา:</label><input type="text" id="time"></div>
            <div><label>ต้นทาง:</label><input type="text" id="origin"></div>
            <div><label>ปลายทาง:</label><input type="text" id="dest"></div>
            <div><label>ชานชะลาที่:</label><input type="text" id="platform"></div>
            <div><label>สถานีปัจจุบัน:</label><input type="text" id="current" value="คลองบางพระ"></div>
        </div>
        
        <label>สถานีต่อไป (สำหรับหมวด 5):</label>
        <input type="text" id="next_station">
        
        <label>คาดว่าจะถึงเวลา (สำหรับหมวด 6):</label>
        <input type="text" id="delay_time" placeholder="เช่น 19 นาฬิกา 30 นาที">

        <label style="color:#d32f2f;">📝 พิมพ์ข้อความประกาศเอง (สำหรับปุ่ม 9):</label>
        <textarea id="custom_text" rows="3" placeholder="พิมพ์ข้อความที่ต้องการให้พี่นิวัฒน์พูดตรงนี้เลยครับ..."></textarea>

        <button class="btn btn-clear" onclick="clearData()">🧹 ล้างข้อมูลหน้าจอ</button>
        <hr>

        <button class="btn btn-play" onclick="playAudio(0)">1. ขอทาง/ขายตั๋ว</button>
        <button class="btn btn-play" onclick="playAudio(1)">2. รอรับโดยสาร</button>
        <button class="btn btn-play" onclick="playAudio(2)">3. รถเข้าจอด</button>
        <button class="btn btn-play" onclick="playAudio(3)">4. รถผ่าน</button>
        <button class="btn btn-play" onclick="playAudio(4)">5. รถจอดรับส่ง/ออก</button>
        <button class="btn btn-play" style="background-color:#ff9800;" onclick="playAudio(5)">6. รถล่าช้า</button>
        <button class="btn btn-play" style="background-color:#2196F3;" onclick="playAudio(6)">7. ระวังคนลงรถ</button>
        <button class="btn btn-play" style="background-color:#E91E63;" onclick="playAudio(7)">🚭 8. ห้ามสูบบุหรี่</button>
        <button class="btn btn-play" style="background-color:#9C27B0;" onclick="playAudio(8)">🎙️ 9. ประกาศตามข้อความที่พิมพ์เอง</button>

        <div class="status" id="statusBox">🔊 กำลังประมวลผลเสียง...</div>
    </div>

    <script>
        const trainData = {{ trains_json | safe }};
        let mobilePlayer = new Audio(); 
        
        function autoFill() {
            let sel = document.getElementById('train_select').value;
            let data = trainData[sel];
            if(data) {
                document.getElementById('num').value = data.num;
                document.getElementById('origin').value = data.origin;
                document.getElementById('dest').value = data.dest;
                document.getElementById('time').value = data.time;
                document.getElementById('next_station').value = data.next;
            }
        }

        function clearData() {
            document.getElementById('train_select').value = "";
            document.getElementById('num').value = "";
            document.getElementById('time').value = "";
            document.getElementById('origin').value = "";
            document.getElementById('dest').value = "";
            document.getElementById('platform').value = "";
            document.getElementById('next_station').value = "";
            document.getElementById('delay_time').value = "";
            document.getElementById('custom_text').value = "";
        }

        function playAudio(tabIndex) {
            // หยุดเสียงเก่าทันที ไม่ให้ไปรบกวนของใหม่
            mobilePlayer.pause();
            mobilePlayer.currentTime = 0; 

            let statusBox = document.getElementById('statusBox');
            statusBox.style.display = "block";
            statusBox.innerText = "⏳ กำลังดึงเสียงพี่นิวัฒน์...";
            statusBox.style.color = "#ff9800";
            
            // เล่นกระดิ่งทันทีที่กดปุ่ม!
            mobilePlayer.src = '/audio/chime.mp3';
            mobilePlayer.play().catch(()=>{});

            let payload = {
                tab_index: tabIndex,
                num: document.getElementById('num').value,
                origin: document.getElementById('origin').value,
                dest: document.getElementById('dest').value,
                time: document.getElementById('time').value,
                platform: document.getElementById('platform').value,
                current: document.getElementById('current').value,
                next: document.getElementById('next_station').value,
                delay: document.getElementById('delay_time').value,
                custom_text: document.getElementById('custom_text').value
            };

            fetch('/announce', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            }).then(response => response.json())
            .then(data => {
                if(data.status === "success") {
                    statusBox.innerText = "🔊 กำลังกระจายเสียงประกาศ!";
                    statusBox.style.color = "#4CAF50";

                    let announceUrl = '/audio/temp_announce.mp3?t=' + new Date().getTime(); 
                    
                    // ระบบเนียนๆ: เช็คว่ากระดิ่งเล่นจบหรือยัง
                    if (!mobilePlayer.paused && mobilePlayer.src.includes('chime.mp3')) {
                        // ถ้ากระดิ่งยังดังอยู่ ให้รอจนจบหลอดแล้วค่อยพูดต่อ
                        mobilePlayer.onended = () => {
                            mobilePlayer.src = announceUrl;
                            mobilePlayer.play();
                            mobilePlayer.onended = null;
                        };
                    } else {
                        // ถ้ากระดิ่งจบไปแล้ว ก็เล่นเสียงพูดได้เลย
                        mobilePlayer.src = announceUrl;
                        mobilePlayer.play();
                    }

                    setTimeout(() => { statusBox.style.display = "none"; }, 7000);
                }
            });
        }
    </script>
</body>
</html>
"""

@app.route('/audio/<filename>')
def serve_audio(filename):
    if os.path.exists(filename):
        return send_file(filename, mimetype="audio/mpeg")
    return "File not found", 404

@app.route("/")
def index():
    return render_template_string(HTML_PAGE, trains=TRAINS, trains_json=json.dumps(TRAINS))

@app.route("/announce", methods=["POST"])
def announce():
    data = request.json
    idx = data.get('tab_index')
    t_num = " ".join(list(data.get('num', '')))
    origin = data.get('origin', '')
    dest = data.get('dest', '')
    t_time = data.get('time', '').replace(" 0 นาที", "")
    platform = data.get('platform', '')
    current = data.get('current', '')
    next_st = data.get('next', '')
    delay = data.get('delay', '')
    custom_text = data.get('custom_text', '')

    text = ""
    if idx == 0:
        text = f"โปรดทราบ ผู้โดยสารที่มีความประสงค์จะเดินทางกับขบวนรถ ขบวนที่ {t_num} รับส่งผู้โดยสารต้นทาง สถานี{origin} ปลายทาง สถานี{dest} เที่ยวกำหนดเวลา {t_time} ผู้โดยสารท่านใดยังไม่มีตั๋วใช้ในการโดยสารสามารถติดต่อซื้อตั๋วโดยสารได้ที่ช่องจำหน่ายตั๋ว ขอบคุณครับ"
    elif idx == 1:
        text = f"โปรดทราบ ผู้โดยสารที่มีตั๋วใช้ในการโดยสารกับขบวนรถ ขบวนที่ {t_num} รับส่งผู้โดยสารต้นทาง สถานี{origin} ปลายทาง สถานี{dest} เที่ยวกำหนดเวลา {t_time} ผู้โดยสารท่านใดมีตั๋วที่ใช้ในการโดยสารแล้วนำสิ่งของและสัมภาระของท่าน รอรับการโดยสารได้ในชานชะลาที่ {platform} ขอบคุณครับ"
    elif idx == 2:
        text = f"โปรดทราบอีกสักครู่ ขบวนรถ ขบวนที่ {t_num} รับส่งผู้โดยสารต้นทาง สถานี{origin} ปลายทาง สถานี{dest} เที่ยวกำหนดเวลา {t_time} กำลังจะเข้าเทียบสถานีในชานชะลาที่ {platform} เพื่อความปลอดภัยของผู้โดยสาร กรุณายืนหลังเส้นสีเหลืองขอบชานชะลา และไม่เดินข้ามผ่านไป-มา ระหว่างชานชะลาที่ {platform} ขอบคุณครับ"
    elif idx == 3:
        text = f"โปรดทราบอีกสักครู่ ขบวนรถ วิ่งผ่านสถานี ในบริเวณชานชะลาที่ {platform} เพื่อความปลอดภัยของผู้โดยสาร กรุณายืนหลังเส้นสีเหลืองขอบชานชะลา และไม่เดินข้ามผ่านไป-มา ระหว่างชานชะลาที่ {platform} ขอบคุณครับ"
    elif idx == 4:
        text = f"โปรดทราบที่นี่สถานี{current} ที่นี่สถานี{current} ผู้โดยสารก่อนลงจากขบวนรถโปรดตรวจสอบสิ่งของและสัมภาระของท่านที่นำติดตัวมา นำลงจากขบวนรถให้ครบถ้วน ถูกต้องด้วยครับ ขบวนรถที่จอดเทียบในชานชะลาที่ {platform} เป็นขบวนรถ ขบวนที่ {t_num} รับส่งผู้โดยสารต้นทาง สถานี{origin} ปลายทาง สถานี{dest} เที่ยวกำหนดเวลา {t_time} ผู้โดยสารที่มีตั๋วใช้ในการโดยสารกับขบวนรถเที่ยวนี้แล้ว กรุณานำสิ่งของและสัมภาระของท่านขึ้นบนขบวนรถ และจัดหาที่นั่งให้เป็นที่เรียบร้อย ขบวนรถเที่ยวนี้เมื่อออกจากสถานีคลองบางพระ แล้วจะหยุดรับ ส่งผู้โดยสารที่สถานี{next_st} เป็นสถานีต่อไปตามลำดับ ขอบคุณครับ"
    elif idx == 5:
        text = f"โปรดทราบ วันนี้ขบวนรถ ขบวนที่ {t_num} รับส่งผู้โดยสารต้นทาง สถานี{origin} ปลายทาง สถานี{dest} เที่ยวกำหนดเวลา {t_time} ล่าช้ากว่ากำหนดเวลาเดิม คาดว่าจะถึงสถานี{current} ได้ในเวลาโดยประมาณ {delay} ในนามของการรถไฟแห่งประเทศไทย ต้องขออภัยในความไม่สะดวกในครั้งนี้ ขอบคุณครับ"
    elif idx == 6:
        text = f"โปรดทราบ อีกสักครู่จะมีขบวนรถ ขบวนที่ {t_num} เข้าเทียบในชานชะลาที่ {platform} ผู้โดยสารที่ลงจากขบวนรถ โปรดระมัดระวังด้วยครับ ขอบคุณครับ"
    elif idx == 7:
        text = "โปรดทราบ ขอความร่วมมือผู้โดยสารทุกท่าน ห้ามสูบบุหรี่บนชานชะลา บริเวณสถานี และบนขบวนรถ เพื่อสุขภาพอนามัยที่ดีของส่วนรวม ขอบคุณครับ"
    elif idx == 8:
        text = custom_text if custom_text.strip() != "" else "โปรดพิมพ์ข้อความที่ต้องการประกาศในช่องด้านบนด้วยครับ"

    filename = "temp_announce.mp3"
    
    if os.path.exists(filename):
        try: os.remove(filename)
        except: pass
        
    try:
        subprocess.run(
            ["edge-tts", "--voice", "th-TH-NiwatNeural", "--rate=-10%", "--text", text, "--write-media", filename], 
            check=True
        )
    except Exception as e:
        print(f"TTS Error: {e}")

    return {"status": "success"}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
