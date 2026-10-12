# -*- coding: utf-8 -*-
"""Bangphra Station Windows Edge TTS agent. HTTPS outbound only; no inbound ports.
Run on the station PC, which has already passed the edge-tts voice test.
"""
from pathlib import Path
import getpass
import json
import subprocess
import sys
import time
import uuid
import urllib.request
import urllib.error
import urllib.parse
import tempfile

BASE_DIR=Path(__file__).resolve().parent
CONFIG_FILE=BASE_DIR/'station_agent_config.json'
DEFAULT_URL='https://bangphra-station.onrender.com'


def load_config():
    if CONFIG_FILE.exists():
        config=json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    else:
        print('=== ติดตั้งระบบเสียงสถานีคลองบางพระ ครั้งแรก ===')
        print('ต้องตั้งค่า STATION_AGENT_TOKEN ใน Render Environment ก่อน')
        print('ตัวอักษรที่พิมพ์ตอนกรอกรหัสจะไม่แสดงบนจอ เป็นเรื่องปกติ')
        url=input('URL เว็บสถานี [Enter เพื่อใช้ URL เดิม]: ').strip() or DEFAULT_URL
        token=getpass.getpass('วางรหัส STATION_AGENT_TOKEN จาก Render แล้วกด Enter: ').strip()
        config={'server':url,'token':token,'worker':uuid.uuid4().hex}
        if not token:
            raise RuntimeError('ยังไม่ได้ใส่รหัสจาก Render')
        CONFIG_FILE.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
        print('บันทึกการตั้งค่าแล้ว (เก็บไฟล์ station_agent_config.json ไว้ในเครื่องนี้เท่านั้น)')
    config['server']=config['server'].rstrip('/')
    if not config['server'].startswith('https://'):
        raise RuntimeError('ต้องใช้เว็บ https:// เท่านั้น')
    if not config.get('token') or len(config['token'])<24:
        raise RuntimeError('รหัส STATION_AGENT_TOKEN สั้นเกินไป หรือไม่มีค่า')
    if not config.get('worker'):
        config['worker']=uuid.uuid4().hex
    return config


def call(config,path,method='GET',data=None,content_type=None,timeout=15):
    headers={'Authorization':'Bearer '+config['token'],'User-Agent':'Bangphra-Station-WindowsAgent/1.0'}
    if data is not None and content_type:
        headers['Content-Type']=content_type
    request=urllib.request.Request(config['server']+path,data=data,headers=headers,method=method)
    with urllib.request.urlopen(request,timeout=timeout) as response:
        raw=response.read()
        return json.loads(raw.decode('utf-8'))


def submit(config,job_id,form_fields,audio=None):
    # Standard multipart body; accepts a generated MP3 or an error string.
    boundary='BANGPHRA'+uuid.uuid4().hex
    parts=[]
    for key,value in form_fields.items():
        parts.append(('--'+boundary+'\r\nContent-Disposition: form-data; name="'+key+'"\r\n\r\n'+str(value)+'\r\n').encode('utf-8'))
    if audio is not None:
        parts.append(('--'+boundary+'\r\nContent-Disposition: form-data; name="audio"; filename="speech.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n').encode('utf-8'))
        parts.append(audio)
        parts.append(b'\r\n')
    parts.append(('--'+boundary+'--\r\n').encode('utf-8'))
    body=b''.join(parts)
    return call(config,'/api/station-agent/result/'+job_id,method='POST',data=body,
                content_type='multipart/form-data; boundary='+boundary,timeout=35)


def generate(job):
    with tempfile.TemporaryDirectory(prefix='bangphra_tts_') as folder:
        target=Path(folder)/'speech.mp3'
        args=[sys.executable,'-m','edge_tts',
              '--voice='+job['voice'],'--rate='+job['rate'],
              '--volume='+job['volume'],'--pitch='+job['pitch'],
              '--text',job['speech_text'],'--write-media',str(target)]
        proc=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=65)
        if proc.returncode!=0:
            raise RuntimeError((proc.stderr or proc.stdout or 'Edge TTS error').strip()[-2400:])
        if not target.exists() or target.stat().st_size<200:
            raise RuntimeError('สร้าง MP3 ไม่สำเร็จหรือไฟล์ว่าง')
        return target.read_bytes()


def main():
    config=load_config()
    print('--- ระบบเสียงสถานีคลองบางพระ (Windows Agent) ---')
    print('เว็บ:',config['server'])
    print('เสียงเดิม: Niwat / Premwadee / Guy / Jenny')
    print('สถานะ: เริ่มเชื่อมต่อ ... ปล่อยหน้าต่างนี้เปิดไว้')
    last_idle_print=0
    while True:
        try:
            query=urllib.parse.urlencode({'worker':config['worker']})
            result=call(config,'/api/station-agent/next?'+query)
            if result.get('status')!='job':
                if time.monotonic()-last_idle_print>60:
                    print('พร้อมรับงานสร้างเสียง ·',time.strftime('%H:%M:%S'),flush=True)
                    last_idle_print=time.monotonic()
                time.sleep(3)
                continue
            job=result['job']
            print('กำลังสร้างเสียง',job['voice'], 'ข้อความ',len(job['speech_text']),'ตัวอักษร',flush=True)
            try:
                mp3=generate(job)
                response=submit(config,job['id'],{'worker':config['worker'],'status':'complete'},audio=mp3)
                print('✓ ส่งเสียงสำเร็จ',round(len(mp3)/1024),'KB',flush=True)
            except Exception as exc:
                message=str(exc)
                print('! สร้างเสียงไม่สำเร็จ (รายละเอียดตอนท้าย):',flush=True)
                # edge-tts reports the actionable exception on the last lines of its traceback.
                # The original agent printed only the first 260 characters, hiding the cause.
                print('\n'.join(message.splitlines()[-12:])[-1600:],flush=True)
                try:
                    submit(config,job['id'],{'worker':config['worker'],'status':'failed','error':message[-450:]})
                except Exception as err:
                    print('! ส่งรายละเอียดข้อผิดพลาดไม่ได้:',str(err)[:150],flush=True)
                time.sleep(3)
        except urllib.error.HTTPError as exc:
            if exc.code==401:
                print('! รหัส STATION_AGENT_TOKEN ไม่ตรงกับ Render: ตรวจไฟล์ config หรือ Render Environment',flush=True)
                return
            print('! เว็บตอบกลับ',exc.code,'ลองเชื่อมต่ออีกครั้งใน 8 วินาที',flush=True)
            time.sleep(8)
        except (OSError,ValueError) as exc:
            print('! เชื่อมต่อไม่สำเร็จ:',str(exc)[:160],'ลองใหม่ใน 8 วินาที',flush=True)
            time.sleep(8)

if __name__=='__main__':
    try: main()
    except KeyboardInterrupt:
        print('หยุดโปรแกรมแล้ว')
    except Exception as e:
        print('ข้อผิดพลาด:',e)
        input('กด Enter เพื่อปิดหน้าต่าง ...')
