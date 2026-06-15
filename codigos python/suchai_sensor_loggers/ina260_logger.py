#!/usr/bin/env python3
import argparse, csv, re, signal, time
from datetime import datetime
import can
CAN_TX_ID=0x100; CAN_ACK_ID=0x101; CAN_INA3V3_ID=0x202; CAN_INABAT_ID=0x203
CMD_INA_WHOAMI=0x60; CMD_INA_STREAM_SET=0x63
running=True
def stop_handler(signum,frame):
    global running; running=False
def clean_ascii(data:bytes)->str: return data.rstrip(b"\x00").decode('ascii',errors='ignore').strip()
def send_fd(bus,data): bus.send(can.Message(arbitration_id=CAN_TX_ID,data=bytearray(data),is_extended_id=False,is_fd=True,bitrate_switch=True))
def request_whoami(bus): send_fd(bus,[CMD_INA_WHOAMI])
def set_stream(bus,en): send_fd(bus,[CMD_INA_STREAM_SET,0x01 if en else 0x00])
def parse_ina(text):
    m=re.search(r"(INA3V3|INABAT)\s+I=(-?\d+(?:\.\d+)?)mA\s+V=(-?\d+(?:\.\d+)?)mV\s+P=(-?\d+)mW",text)
    if not m: return None
    return dict(sensor=m.group(1),current_mA=float(m.group(2)),voltage_mV=float(m.group(3)),voltage_V=float(m.group(3))/1000.0,power_mW=float(m.group(4)))
def main():
    p=argparse.ArgumentParser(description='Logger CSV continuo para INA260 3V3/BAT por CAN-FD')
    p.add_argument('--channel',default='can0'); p.add_argument('--output',default=None); p.add_argument('--sensor',choices=['both','3v3','bat'],default='both'); p.add_argument('--no-whoami',action='store_true'); p.add_argument('--no-stream-off',action='store_true'); p.add_argument('--print',action='store_true'); p.add_argument('--show-raw',action='store_true')
    a=p.parse_args(); signal.signal(signal.SIGINT,stop_handler); signal.signal(signal.SIGTERM,stop_handler)
    out=a.output or f"ina260_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"; bus=can.interface.Bus(channel=a.channel,interface='socketcan',fd=True)
    wanted=set();
    if a.sensor in ('both','3v3'): wanted.add(CAN_INA3V3_ID)
    if a.sensor in ('both','bat'): wanted.add(CAN_INABAT_ID)
    fields=['timestamp_iso','epoch_s','elapsed_s','can_id','raw_text','sensor','current_mA','voltage_mV','voltage_V','power_mW']
    print('INA260 logger'); print('CSV:',out); print('Sensor:',a.sensor); print('Ctrl+C para terminar')
    start=time.monotonic(); samples=0
    try:
        with open(out,'w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); f.flush()
            if not a.no_whoami:
                request_whoami(bus); t0=time.time()
                while time.time()-t0<1.5:
                    msg=bus.recv(timeout=0.2)
                    if msg and msg.arbitration_id==CAN_ACK_ID:
                        txt=clean_ascii(bytes(msg.data));
                        if txt: print('ACK:',txt)
            set_stream(bus,True); print('Stream INA ON')
            while running:
                msg=bus.recv(timeout=1.0)
                if msg is None or msg.arbitration_id not in wanted: continue
                txt=clean_ascii(bytes(msg.data)); d=parse_ina(txt)
                if d is None:
                    if a.show_raw and txt: print('No parseado:',txt)
                    continue
                row={k:'' for k in fields}; row.update(d); row['timestamp_iso']=datetime.now().astimezone().isoformat(timespec='milliseconds'); row['epoch_s']=f'{time.time():.6f}'; row['elapsed_s']=f'{time.monotonic()-start:.6f}'; row['can_id']=f'0x{msg.arbitration_id:X}'; row['raw_text']=txt
                w.writerow(row); f.flush(); samples+=1
                if a.print: print(f"{row['timestamp_iso']} {d['sensor']} I={d['current_mA']:+.2f}mA V={d['voltage_V']:.3f}V P={d['power_mW']:.0f}mW")
                elif samples%20==0: print('Muestras guardadas:',samples)
    finally:
        if not a.no_stream_off:
            try: set_stream(bus,False); print('Stream INA OFF')
            except Exception: pass
        bus.shutdown(); print('Archivo guardado:',out)
if __name__=='__main__': main()
