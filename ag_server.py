import json, time, os, urllib.request, urllib.error, datetime, mimetypes, http.server

BASE_URL = "https://apihub.agnes-ai.com"
DEFAULT_API_KEY = "sk-D7ZTOQoga44G24luT7Z2ueEaXtijOgsGo3TXzGo2jORV4To8"
DEFAULT_DOWNLOAD_DIR = "D:\\Downloads"
DEFAULT_BG = "D:/Jiong-ci-yuan/初音未来.mp4"
PORT = 8080


def _frames_ok(n):
    return n <= 441 and (n - 1) % 8 == 0
def _nearest_frames(n):
    return max(9, min(((n - 1) // 8) * 8 + 1, 441))
def _create_task(payload, api_key):
    for attempt in range(5):
        req = urllib.request.Request(BASE_URL + "/v1/videos", data=json.dumps(payload).encode(), method="POST")
        req.add_header("Authorization", "Bearer " + api_key)
        req.add_header("Content-Type", "application/json")
        try:
            return json.loads(urllib.request.urlopen(req, timeout=120).read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if "rate_limit" in body and attempt < 4:
                time.sleep(70)
                continue
            return {"error": "API error %d: %s" % (e.code, body[:200])}
    return {"error": "Rate-limit retries exhausted"}
def _poll(video_id, api_key):
    for _ in range(120):
        time.sleep(5)
        req = urllib.request.Request(BASE_URL + "/agnesapi?video_id=" + video_id)
        req.add_header("Authorization", "Bearer " + api_key)
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=30).read())
        except Exception as e:
            continue
        st = r.get("status", "")
        if st == "completed":
            return r
        if st in ("failed", "error"):
            return {"error": "Failed: " + str(r.get("error", "?"))}
    return {"error": "Timeout"}


CSS = "*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0d0d1a;color:#eee;min-height:100vh}#bg-wrap{position:fixed;inset:0;z-index:-1;overflow:hidden}#bg-wrap video{width:100%;height:100%;object-fit:cover;opacity:.5}.container{max-width:1300px;margin:0 auto;padding:20px;position:relative;z-index:1;display:flex;flex-direction:column;gap:10px}.glass{background:rgba(255,255,255,0.06)!important;backdrop-filter:blur(8px)!important;-webkit-backdrop-filter:blur(8px)!important;border:1px solid rgba(255,255,255,0.12)!important;border-radius:12px!important;transform:translateZ(0);will-change:transform}.card{padding:16px;margin-bottom:0}.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}.row>*{flex:1;min-width:0}input,select,textarea{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.15);border-radius:6px;padding:8px 10px;color:#eee;font-size:14px;width:100%;outline:none}input:focus,select:focus,textarea:focus{border-color:rgba(100,140,255,.6)}textarea{resize:vertical;font-family:inherit}label{font-size:13px;color:rgba(255,255,255,.7);margin-bottom:3px;display:block}button{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.15);border-radius:6px;padding:8px 18px;color:#eee;font-size:14px;cursor:pointer;transition:background .2s}button:hover{background:rgba(100,140,255,.2)}button.primary{background:rgba(100,140,255,.2)}button.primary:hover{background:rgba(100,140,255,.35)}h1{font-size:20px;font-weight:600;margin-bottom:12px;color:rgba(255,255,255,.9);text-align:center}#pv{min-height:65vh;max-height:78vh;overflow:hidden;padding:0;display:flex;align-items:center;justify-content:center;margin-bottom:0}#pv{position:relative}#pv{position:relative}#pv video{width:100%;height:100%;min-height:65vh;max-height:78vh;object-fit:contain;border-radius:12px}#rp{display:none;position:absolute;bottom:10px;right:10px;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);border-radius:8px;padding:6px 14px;color:#fff;font-size:13px;cursor:pointer;z-index:10}#rp{display:none;position:absolute;bottom:10px;right:10px;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);border-radius:8px;padding:6px 14px;color:#fff;font-size:13px;cursor:pointer;z-index:10}#st{font-size:13px;color:rgba(255,255,255,.6);padding:6px 0;text-align:center}.hidden{display:none!important}.mt-8{margin-top:8px}.il{white-space:nowrap!important;margin:0!important;flex:0 0 auto!important;line-height:32px}.mode-select{display:flex;gap:4px}.mode-btn{flex:1;padding:7px 8px;text-align:center;cursor:pointer;font-size:13px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:6px;color:rgba(255,255,255,.6);transition:all .2s}.mode-btn.active{background:rgba(100,180,255,.25);border-color:rgba(100,180,255,.4);color:#fff}.mode-btn:hover{background:rgba(100,140,255,.15)}input:-webkit-autofill,input:-webkit-autofill:hover,input:-webkit-autofill:focus,input:-webkit-autofill:active{-webkit-box-shadow:0 0 0 30px rgba(20,20,40,0.95) inset!important;-webkit-text-fill-color:#eee!important;caret-color:#eee!important}@media(max-width:768px){#pv{min-height:40vh;max-height:55vh}#pv video{min-height:40vh;max-height:55vh}.row{flex-direction:column}.row>*{width:100%!important}}"

H = "<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Agnes Video</title><style>" + CSS + "</style></head><body><div id=\"bg-wrap\"><video id=\"bgv\" autoplay loop muted playsinline><source src=\"/bg\" type=\"video/mp4\"></video></div><div class=\"container\"><h1>Agnes Video V2.0</h1><div class=\"card glass\"><div class=\"row\" style=\"gap:6px;flex-wrap:nowrap;align-items:center\"><label class=\"il\" style=\"flex:0 0 auto\">API Key</label><input type=\"password\" id=\"ak\" value=\"" + DEFAULT_API_KEY + "\" style=\"flex:1;min-width:100px\"><button onclick=\"var e=document.getElementById('ak');e.type=e.type==='password'?'text':'password'\" style=\"flex:0 0 auto\">&#x1F441;</button></div></div><div id=\"pv\" class=\"glass\"><video id=\"prv\" autoplay playsinline onclick=\"this.currentTime=0;this.play()\"></video><button id=\"rp\" onclick=\"var v=document.getElementById('prv');if(v.src){v.currentTime=0;v.play()}\" style=\"display:none\">重播</button></div><div id=\"st\">就绪</div><div class=\"card glass row\" style=\"gap:6px;padding:10px 14px\"><button class=\"primary\" onclick=\"gen()\" id=\"gb\" style=\"flex:1;min-width:80px\">生成视频</button><button onclick=\"dl()\" id=\"db\" style=\"flex:1;min-width:80px\">下载</button><div style=\"display:flex;align-items:center;gap:6px;flex:1;min-width:120px\"><label class=\"il\" style=\"flex:0 0 auto;white-space:nowrap\">保存目录</label><input type=\"text\" id=\"savedir\" value=\"" + DEFAULT_DOWNLOAD_DIR + "\" style=\"flex:1;min-width:60px\"></div></div><div class=\"card glass\"><label>提示词</label><textarea id=\"pt\" rows=\"2\" placeholder=\"描述视频内容...\"></textarea></div><div class=\"row\" style=\"gap:6px\"><div class=\"card glass\" style=\"flex:2\"><label>模式</label><input type=\"hidden\" id=\"md\" value=\"text2video\"><div class=\"mode-select\"><div class=\"mode-btn active\" data-mode=\"text2video\" onclick=\"setMode(this.dataset.mode)\">文生视频</div><div class=\"mode-btn\" data-mode=\"image2video\" onclick=\"setMode(this.dataset.mode)\">图生视频</div><div class=\"mode-btn\" data-mode=\"keyframes\" onclick=\"setMode(this.dataset.mode)\">关键帧动画</div></div></div><div class=\"card glass\"><label>宽</label><input type=\"number\" id=\"wd\" value=\"1152\" step=\"8\"></div><div class=\"card glass\"><label>高</label><input type=\"number\" id=\"ht\" value=\"768\" step=\"8\"></div><div class=\"card glass\"><label>帧数</label><input type=\"number\" id=\"nf\" value=\"121\" step=\"8\"></div><div class=\"card glass\"><label>帧率</label><input type=\"number\" id=\"fr\" value=\"24\" step=\"1\"></div></div><div id=\"ii\" class=\"hidden card glass\"><label>图片 URL</label><input type=\"text\" id=\"iu\" placeholder=\"https://...\"></div><div id=\"ki\" class=\"hidden card glass\"><label>关键帧 URL (每行一个)</label><textarea id=\"ku\" rows=\"2\"></textarea></div><details class=\"card glass\"><summary style=\"cursor:pointer;color:rgba(255,255,255,.6);font-size:13px\">高级参数</summary><div class=\"row\" style=\"gap:6px;margin-top:8px\"><div style=\"flex:1\"><label>种子 (0=随机)</label><input type=\"number\" id=\"sd\" value=\"0\"></div><div style=\"flex:1\"><label>推理步数 (0=默认)</label><input type=\"number\" id=\"ns\" value=\"0\"></div></div><div class=\"mt-8\"><label>反向提示词</label><textarea id=\"np\" rows=\"2\"></textarea></div></details></div><script>function tm(){var m=document.getElementById('md').value;document.getElementById('ii').className=m==='image2video'?'card glass':'hidden card glass';document.getElementById('ki').className=m==='keyframes'?'card glass':'hidden card glass'}function setMode(m){document.getElementById('md').value=m;var bs=document.querySelectorAll('.mode-btn');for(var i=0;i<bs.length;i++){bs[i].className='mode-btn'+(bs[i].getAttribute('data-mode')===m?' active':'')}tm()}function st(t){document.getElementById('st').textContent=t}var _bu='/bg';function gen(){var b=document.getElementById('gb');b.disabled=true;b.textContent='生成中..';var bgv=document.getElementById('bgv');if(bgv)bgv.src=_bu;var p={ak:document.getElementById('ak').value,pt:document.getElementById('pt').value,md:document.getElementById('md').value,wd:parseInt(document.getElementById('wd').value)||1152,ht:parseInt(document.getElementById('ht').value)||768,nf:parseInt(document.getElementById('nf').value)||121,fr:parseInt(document.getElementById('fr').value)||24,sd:parseInt(document.getElementById('sd').value)||0,np:document.getElementById('np').value,ns:parseInt(document.getElementById('ns').value)||0,iu:document.getElementById('iu').value,ku:document.getElementById('ku').value.split('\\n').filter(function(s){return s.trim()})};st('创建任务...');fetch('/api/create',{method:'POST',body:JSON.stringify(p),headers:{'Content-Type':'application/json'}}).then(function(r){return r.json()}).then(function(d){if(d.error){st('错误: '+d.error);b.disabled=false;b.textContent='生成视频';return}st('任务已创建，等待生成...');po(d.video_id)}).catch(function(e){st('请求失败: '+e);b.disabled=false;b.textContent='生成视频'})}function po(id){var k=document.getElementById('ak').value;function t(){fetch('/api/poll?video_id='+encodeURIComponent(id)+'&api_key='+encodeURIComponent(k)).then(function(r){return r.json()}).then(function(d){if(d.error){st('错误: '+d.error);dn();return}if(d.status==='completed'){st('完成!');var u=d.url;document.getElementById('prv').src=u;var v=document.getElementById('bgv');if(v)v.src=u;document.getElementById('gb').disabled=false;document.getElementById('gb').textContent='生成视频';document.getElementById('rp').style.display='block';window._lu=u}else if(d.status==='failed'||d.status==='error'){st('失败: '+(d.error||'?'));dn()}else{var p=d.progress||0;st(d.status+' '+p+'%');setTimeout(t,3000)}}).catch(function(e){st('轮询失败: '+e);setTimeout(t,5000)})}t()}function dn(){document.getElementById('gb').disabled=false;document.getElementById('gb').textContent='生成视频'}function dl(){var u=window._lu;if(!u){st('请先生成视频');return}var d=document.getElementById('savedir').value||'DIR';st('下载中..');fetch('/api/download?video_url='+encodeURIComponent(u)+'&save_dir='+encodeURIComponent(d)).then(function(r){return r.json()}).then(function(d){if(d.path){st('已保存 '+d.file);var v=document.getElementById('bgv');if(v)v.src=_bu}else{st('下载失败')}}).catch(function(e){st('下载错误: '+e)})}</script></body></html>"


def _poll_once(video_id, api_key):
    req = urllib.request.Request(BASE_URL + "/agnesapi?video_id=" + video_id)
    req.add_header("Authorization", "Bearer " + api_key)
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=30).read())
        st = r.get("status", "")
        if st == "completed":
            return {"status": "completed", "url": r.get("url", "")}
        if st in ("failed", "error"):
            return {"error": "Failed: " + str(r.get("error", "?"))}
        return {"status": st, "progress": r.get("progress", 0)}
    except Exception as e:
        return {"error": str(e)}

import urllib.parse

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(H.encode("utf-8"))
        elif self.path == "/bg":
            if os.path.exists(DEFAULT_BG):
                ct, _ = mimetypes.guess_type(DEFAULT_BG)
                self.send_response(200)
                self.send_header("Content-Type", ct or "video/mp4")
                self.send_header("Content-Length", str(os.path.getsize(DEFAULT_BG)))
                self.end_headers()
                with open(DEFAULT_BG, "rb") as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk: break
                        self.wfile.write(chunk)
            else:
                self.send_error(404)
        elif self.path.startswith("/api/poll?"):
            q = urllib.parse.parse_qs(self.path.split("?", 1)[1])
            r = _poll_once(q.get("video_id", [""])[0], q.get("api_key", [DEFAULT_API_KEY])[0])
            self._json(r)
        elif self.path.startswith("/api/download?"):
            q = urllib.parse.parse_qs(self.path.split("?", 1)[1])
            url = q.get("video_url", [""])[0]
            if url:
                dl_dir = q.get("save_dir", [DEFAULT_DOWNLOAD_DIR])[0]
                os.makedirs(dl_dir, exist_ok=True)
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                fname = "agnes_video_%s.mp4" % ts
                path = os.path.join(dl_dir, fname)
                urllib.request.urlretrieve(url, path)
                self._json({"path": path, "file": fname})
            else:
                self._json({"error": "no url"})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/create":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            key = body.get("ak", DEFAULT_API_KEY)
            prompt = body.get("pt", "")
            mode = body.get("md", "text2video")
            if not prompt:
                self._json({"error": "no prompt"})
                return
            nf = body.get("nf", 121)
            if not _frames_ok(nf):
                nf = _nearest_frames(nf)
            payload = {"model": "agnes-video-v2.0", "prompt": prompt,
                       "width": body.get("wd", 1152), "height": body.get("ht", 768),
                       "num_frames": nf, "frame_rate": body.get("fr", 24)}
            if body.get("sd", 0) > 0: payload["seed"] = body["sd"]
            if body.get("np", ""): payload["negative_prompt"] = body["np"]
            if body.get("ns", 0) > 0: payload["num_inference_steps"] = body["ns"]
            if mode == "image2video" and body.get("iu"):
                payload["image"] = body["iu"]
            elif mode == "keyframes":
                urls = body.get("ku", [])
                if urls: payload["extra_body"] = {"image": urls, "mode": "keyframes"}
            resp = _create_task(payload, key)
            if "error" in resp:
                self._json(resp)
            else:
                self._json({"video_id": resp.get("video_id") or resp.get("id", "")})
        else:
            self.send_error(404)

    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        body = json.dumps(data).encode("utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    http.server.HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
