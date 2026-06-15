#!/usr/bin/env python3
import argparse, csv, math, re, signal, time
from datetime import datetime
import can
CAN_TX_ID=0x100; CAN_ACK_ID=0x101; CAN_STREAM_ID=0x201
CMD_GPIO_SET=0x30; CMD_AK_WHOAMI=0x51; CMD_AK_STREAM_SET=0x52
running=True
def stop_handler(signum,frame):
    global running; running=False
def clean_ascii(data:bytes)->str: return data.rstrip(b"\x00").decode('ascii',errors='ignore').strip()
def send_fd(bus,data): bus.send(can.Message(arbitration_id=CAN_TX_ID,data=bytearray(data),is_extended_id=False,is_fd=True,bitrate_switch=True))
def set_g1_1v8(bus,en): send_fd(bus,[CMD_GPIO_SET,0x01,0x01 if en else 0x00])
def request_whoami(bus): send_fd(bus,[CMD_AK_WHOAMI])
def set_stream(bus,en): send_fd(bus,[CMD_AK_STREAM_SET,0x01 if en else 0x00])
def parse_ak(text):
    m=re.search(r"AK\s+M=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)uT\s+T=(\d+)",text)
    if not m: return None
    mx,my,mz=map(float,m.groups()[:3]); tr=int(m.group(4))
    return dict(mx_uT=mx,my_uT=my,mz_uT=mz,mag_norm_uT=math.sqrt(mx*mx+my*my+mz*mz),temp_raw=tr)
def main():
    p=argparse.ArgumentParser(description='Logger CSV continuo para AK09940A por CAN-FD')
    p.add_argument('--channel',default='can0'); p.add_argument('--output',default=None); p.add_argument('--no-power-on',action='store_true'); p.add_argument('--power-off-exit',action='store_true'); p.add_argument('--no-whoami',action='store_true'); p.add_argument('--no-stream-off',action='store_true'); p.add_argument('--print',action='store_true'); p.add_argument('--show-raw',action='store_true')
    a=p.parse_args(); signal.signal(signal.SIGINT,stop_handler); signal.signal(signal.SIGTERM,stop_handler)
    out=a.output or f"ak09940a_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"; bus=can.interface.Bus(channel=a.channel,interface='socketcan',fd=True)
    fields=['timestamp_iso','epoch_s','elapsed_s','can_id','raw_text','mx_uT','my_uT','mz_uT','mag_norm_uT','temp_raw']
    print('AK09940A logger'); print('CSV:',out); print('Ctrl+C para terminar')
    start=time.monotonic(); samples=0
    try:
        with open(out,'w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); f.flush()
            if not a.no_power_on:
                print('Activando 1V8: G1/PE5 ON'); set_g1_1v8(bus,True); time.sleep(0.3)
            if not a.no_whoami:
                request_whoami(bus); t0=time.time()
                while time.time()-t0<1.5:
                    msg=bus.recv(timeout=0.2)
                    if msg and msg.arbitration_id==CAN_ACK_ID:
                        txt=clean_ascii(bytes(msg.data));
                        if txt: print('ACK:',txt)
            set_stream(bus,True); print('Stream AK ON')
            while running:
                msg=bus.recv(timeout=1.0)
                if msg is None or msg.arbitration_id!=CAN_STREAM_ID: continue
                txt=clean_ascii(bytes(msg.data)); d=parse_ak(txt)
                if d is None:
                    if a.show_raw and txt: print('No parseado:',txt)
                    continue
                row={k:'' for k in fields}; row.update(d); row['timestamp_iso']=datetime.now().astimezone().isoformat(timespec='milliseconds'); row['epoch_s']=f'{time.time():.6f}'; row['elapsed_s']=f'{time.monotonic()-start:.6f}'; row['can_id']=f'0x{msg.arbitration_id:X}'; row['raw_text']=txt
                w.writerow(row); f.flush(); samples+=1
                if a.print: print(f"{row['timestamp_iso']} M[uT] x={d['mx_uT']:+.2f} y={d['my_uT']:+.2f} z={d['mz_uT']:+.2f} |M|={d['mag_norm_uT']:.2f} Traw={d['temp_raw']}")
                elif samples%20==0: print('Muestras guardadas:',samples)
    finally:
        if not a.no_stream_off:
            try: set_stream(bus,False); print('Stream AK OFF')
            except Exception: pass
        if a.power_off_exit:
            try: set_g1_1v8(bus,False); print('1V8 OFF')
            except Exception: pass
        bus.shutdown(); print('Archivo guardado:',out)
if __name__=='__main__': main()
