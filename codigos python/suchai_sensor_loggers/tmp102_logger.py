#!/usr/bin/env python3
import argparse, csv, re, signal, time
from datetime import datetime
import can
CAN_TX_ID=0x100; CAN_STREAM_ID=0x204; CMD_TMP102_STREAM_SET=0x71
running=True
def stop_handler(signum,frame):
    global running; running=False
def clean_ascii(data:bytes)->str: return data.rstrip(b"\x00").decode('ascii',errors='ignore').strip()
def send_fd(bus,data): bus.send(can.Message(arbitration_id=CAN_TX_ID,data=bytearray(data),is_extended_id=False,is_fd=True,bitrate_switch=True))
def set_stream(bus,en): send_fd(bus,[CMD_TMP102_STREAM_SET,0x01 if en else 0x00])
def parse_tmp102(text):
    m=re.search(r"TMP102\s+T=(-?\d+(?:\.\d+)?)C",text)
    if not m: return None
    return dict(temp_c=float(m.group(1)))
def main():
    p=argparse.ArgumentParser(description='Logger CSV continuo para TMP102 por CAN-FD')
    p.add_argument('--channel',default='can0'); p.add_argument('--output',default=None); p.add_argument('--no-stream-off',action='store_true'); p.add_argument('--print',action='store_true'); p.add_argument('--show-raw',action='store_true')
    a=p.parse_args(); signal.signal(signal.SIGINT,stop_handler); signal.signal(signal.SIGTERM,stop_handler)
    out=a.output or f"tmp102_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"; bus=can.interface.Bus(channel=a.channel,interface='socketcan',fd=True)
    fields=['timestamp_iso','epoch_s','elapsed_s','can_id','raw_text','temp_c']
    print('TMP102 logger'); print('CSV:',out); print('Ctrl+C para terminar')
    start=time.monotonic(); samples=0
    try:
        with open(out,'w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); f.flush()
            set_stream(bus,True); print('Stream TMP102 ON')
            while running:
                msg=bus.recv(timeout=1.0)
                if msg is None or msg.arbitration_id!=CAN_STREAM_ID: continue
                txt=clean_ascii(bytes(msg.data)); d=parse_tmp102(txt)
                if d is None:
                    if a.show_raw and txt: print('No parseado:',txt)
                    continue
                row={k:'' for k in fields}; row.update(d); row['timestamp_iso']=datetime.now().astimezone().isoformat(timespec='milliseconds'); row['epoch_s']=f'{time.time():.6f}'; row['elapsed_s']=f'{time.monotonic()-start:.6f}'; row['can_id']=f'0x{msg.arbitration_id:X}'; row['raw_text']=txt
                w.writerow(row); f.flush(); samples+=1
                if a.print: print(f"{row['timestamp_iso']} TMP102 T={d['temp_c']:.2f}C")
                elif samples%10==0: print('Muestras guardadas:',samples)
    finally:
        if not a.no_stream_off:
            try: set_stream(bus,False); print('Stream TMP102 OFF')
            except Exception: pass
        bus.shutdown(); print('Archivo guardado:',out)
if __name__=='__main__': main()
