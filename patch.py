import re

def patch_file():
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. ADD YT PLAYER DIV AND GSI SCRIPT
    if 'id="yt-player"' not in html:
        html = html.replace('</div><!-- /shell -->', 
        '<div id="yt-player-wrap" style="position:fixed;top:-200px;left:-200px;width:1px;height:1px;overflow:hidden;pointer-events:none"><div id="yt-player"></div></div>\n</div><!-- /shell -->')
        
    if 'accounts.google.com/gsi/client' not in html:
        html = html.replace('</head>', '<script src="https://accounts.google.com/gsi/client" async defer></script>\n  </head>')

    if 'www.youtube.com/iframe_api' not in html:
        html = html.replace('</head>', '<script src="https://www.youtube.com/iframe_api" async></script>\n  </head>')

    # 2. REPLACE AUDIO ENGINE WITH YT ENGINE + SILENT AUDIO CONTEXT FOR IOS
    old_engine = r'// ── Native Audio Engine .*?// ── Welcome ──'
    
    yt_engine = """// ── YouTube IFrame Engine ──
      let __ytPlayer = null;
      let __ctx = null;
      
      window.onYouTubeIframeAPIReady = function() {
        __ytPlayer = new YT.Player('yt-player', {
          height: '10',
          width: '10',
          videoId: '',
          playerVars: { autoplay: 0, controls: 0, disablekb: 1, fs: 0, rel: 0, playsinline: 1 },
          events: {
            onReady: (e) => { S.ytReady = true; },
            onStateChange: onYTStateChange,
            onError: onYTError
          }
        });
      };
      
      function ensureAudioContext() {
        if (!__ctx) {
          __ctx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (__ctx.state === 'suspended') {
          __ctx.resume();
        }
        // Play silent buffer for iOS keep-alive
        const buf = __ctx.createBuffer(1, 1, 22050);
        const src = __ctx.createBufferSource();
        src.buffer = buf;
        src.connect(__ctx.destination);
        src.start(0);
      }

      function onYTStateChange(e) {
        if (e.data === YT.PlayerState.PLAYING) {
          S.playing = true;
          updPlayUI();
          startTick();
          loadBar(false);
          ensureAudioContext();
        } else if (e.data === YT.PlayerState.PAUSED) {
          S.playing = false;
          updPlayUI();
          stopTick();
        } else if (e.data === YT.PlayerState.ENDED) {
          S.playing = false;
          updPlayUI();
          stopTick();
          if (S.rep) {
            __ytPlayer.seekTo(0);
            __ytPlayer.playVideo();
          } else {
            nextT();
          }
        }
      }

      function onYTError(e) {
        S.playing = false;
        updPlayUI();
        stopTick();
        loadBar(false);
        toast("Stream error — skipping...");
        setTimeout(() => nextT(), 1500);
      }

      function playOnNative(videoId) {
        if (!S.ytReady || !__ytPlayer) {
          toast("Player not ready, wait a sec...");
          return;
        }
        ensureAudioContext();
        __ytPlayer.loadVideoById(videoId);
      }

      // ── Welcome ──"""
    html = re.sub(old_engine, yt_engine, html, flags=re.DOTALL)

    # 3. REPLACE togPlay, getAudio refs, etc.
    html = html.replace('function togPlay() {\n        if (!S.track) return;\n        const audio = getAudio();\n        if (S.playing) audio.pause();\n        else audio.play().catch(() => {});\n      }', 
    'function togPlay() {\n        if (!S.track || !__ytPlayer) return;\n        if (S.playing) __ytPlayer.pauseVideo();\n        else __ytPlayer.playVideo();\n      }')

    html = html.replace('const audio = getAudio();\n        if (audio.currentTime > 3) {\n          audio.currentTime = 0;\n          return;\n        }',
    'if (__ytPlayer && __ytPlayer.getCurrentTime() > 3) {\n          __ytPlayer.seekTo(0);\n          return;\n        }')

    html = html.replace('function seekTo(v) {\n        const audio = getAudio();\n        if (audio.duration > 0) audio.currentTime = (v / 100) * audio.duration;\n      }',
    'function seekTo(v) {\n        if (__ytPlayer && __ytPlayer.getDuration() > 0) __ytPlayer.seekTo((v / 100) * __ytPlayer.getDuration(), true);\n      }')

    html = html.replace('function setVol(v) {\n        getAudio().volume = v / 100;\n      }',
    'function setVol(v) {\n        if (__ytPlayer) __ytPlayer.setVolume(v);\n      }')

    html = html.replace('if (!S.playing || !_audio) return;\n          const dur = _audio.duration;\n          const cur = _audio.currentTime;',
    'if (!S.playing || !__ytPlayer) return;\n          const dur = __ytPlayer.getDuration();\n          const cur = __ytPlayer.getCurrentTime();')

    # Add Google Identity decoding
    if 'function handleCredentialResponse' not in html:
        # Inject handleCredentialResponse near launch()
        gsi_code = """function handleCredentialResponse(response) {
        // Decode JWT payload
        const base64Url = response.credential.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        const p = JSON.parse(jsonPayload);
        S.user = p.name;
        localStorage.setItem("sonora_user", S.user);
        document.getElementById("welcome").classList.add("out");
        setTimeout(() => document.getElementById("welcome").style.display = "none", 580);
        document.getElementById("shell").classList.add("ready");
        updHomeUI();
      }
      
      // """
        html = html.replace('// ── Welcome ──', gsi_code + '── Welcome ──')
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Patched index.html")

if __name__ == "__main__":
    patch_file()
