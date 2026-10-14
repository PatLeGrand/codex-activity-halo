import tempfile,subprocess,os,json,socket,time,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from monitor_helper import packet
def main():
 with tempfile.TemporaryDirectory(prefix='codex-takeover-test-') as folder:
  root=Path(folder)
  env={**os.environ,'XDG_RUNTIME_DIR':folder,'QT_QPA_PLATFORM':'offscreen'}
  log=(root/'log').open('w')
  p=subprocess.Popen([sys.executable,'-c','from PySide6.QtMultimedia import QSoundEffect; QSoundEffect.play=lambda self: None; QSoundEffect.status=lambda self: QSoundEffect.Status.Ready; import overlay; overlay.main()'],env=env,stdout=log,stderr=log,cwd=str(Path(__file__).resolve().parent))
  runtime=root/'codex-activity-halo'
  def call(op):
   with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
    sock.settimeout(1);sock.connect(str(runtime/'feedback.sock'))
    sock.sendall((json.dumps({'op':op,'call':'test'})+'\n').encode())
    return json.loads(sock.makefile('rb').readline(4096))
  try:
   for _ in range(50):
    if (runtime/'status.json').exists():break
    time.sleep(.1)
   assert call('begin').get('error'), 'Missing monitor must block control'
   sender=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
   sender.sendto(json.dumps(packet(False,False,1,1)).encode(),str(runtime/'activity.sock'))
   time.sleep(.1)
   response=call('begin'); assert response.get('wait_ms') == 2000, response
   sent=time.monotonic()
   sender.sendto(json.dumps(packet(True,False,1,1)).encode(),str(runtime/'activity.sock'))
   flag=root/'computer-use-mcp-takeover'
   while not flag.exists() and time.monotonic()-sent<1:time.sleep(.005)
   assert flag.exists(), 'Human activity must reach native handoff signal'
   print('Qt signal-to-interruption latch:',round((time.monotonic()-sent)*1000,1),'ms (simulated input)')
   assert call('ready').get('error')
   sender.sendto(json.dumps(packet(False,False,1,1)).encode(),str(runtime/'activity.sock'))
   time.sleep(.1)
   assert flag.exists() and call('ready').get('error'), 'Stop must stay latched'
   print('Qt IPC and physical-takeover gating: OK')
  finally:
   try:call('quit')
   except OSError:pass
   p.wait(timeout=3)

if __name__ == "__main__":
 main()
