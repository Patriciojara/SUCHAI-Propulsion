#!/usr/bin/env python3
import argparse, csv, math, re, signal, time
from datetime import datetime
import can
CAN_TX_ID=0x100; CAN_ACK_ID=0x101; CAN_STREAM_ID=0x200
CMD_ICM_WHOAMI=0x41; CMD_ICM_STREAM_SET=0x42
ACCEL_LSB_PER_G=2048.0; GYRO_LSB_PER_DPS=16.4; GRAVITY=9.80665
running=True
def stop_handler(signum,frame):
    global running; running=False
def clean_ascii(data:bytes)->str:
    return data.rstrip(b"\x00").decode('ascii',errors='ignore').strip()
def send_fd(bus,data):
    bus.send(can.Message(arbitration_id=CAN_TX_ID,data=bytearray(data),is_extended_id=False,is_fd=True,bitrate_switch=True))
def request_whoami(bus): send_fd(bus,[CMD_ICM_WHOAMI])
def set_stream(bus,en): send_fd(bus,[CMD_ICM_STREAM_SET,0x01 if en else 0x00])
def parse_icm(text):
    m=re.search(r"ICM\s+A=(-?\d+),(-?\d+),(-?\d+)\s+G=(-?\d+),(-?\d+),(-?\d+)\s+T=(-?\d+(?:\.\d+)?)C",text)
    if not m: return None
    axr,ayr,azr,gxr,gyr,gzr=map(int,m.groups()[:6]); temp=float(m.group(7))
    ax=axr/ACCEL_LSB_PER_G; ay=ayr/ACCEL_LSB_PER_G; az=azr/ACCEL_LSB_PER_G
    gx=gxr/GYRO_LSB_PER_DPS; gy=gyr/GYRO_LSB_PER_DPS; gz=gzr/GYRO_LSB_PER_DPS
    return dict(ax_raw=axr,ay_raw=ayr,az_raw=azr,gx_raw=gxr,gy_raw=gyr,gz_raw=gzr,ax_g=ax,ay_g=ay,az_g=az,ax_ms2=ax*GRAVITY,ay_ms2=ay*GRAVITY,az_ms2=az*GRAVITY,accel_norm_g=math.sqrt(ax*ax+ay*ay+az*az),gx_dps=gx,gy_dps=gy,gz_dps=gz,gyro_norm_dps=math.sqrt(gx*gx+gy*gy+gz*gz),temp_c=temp)
def main():
    p=argparse.ArgumentParser(description='Logger CSV continuo para ICM-42688-V por CAN-FD')
    p.add_argument('--channel',default='can0'); p.add_argument('--output',default=None); p.add_argument('--no-whoami',action='store_true'); p.add_argument('--no-stream-off',action='store_true'); p.add_argument('--print',action='store_true'); p.add_argument('--show-raw',action='store_true')
    a=p.parse_args(); signal.signal(signal.SIGINT,stop_handler); signal.signal(signal.SIGTERM,stop_handler)
    out=a.output or f"icm42688_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    bus=can.interface.Bus(channel=a.channel,interface='socketcan',fd=True)
    fields=['timestamp_iso','epoch_s','elapsed_s','can_id','raw_text','ax_raw','ay_raw','az_raw','gx_raw','gy_raw','gz_raw','ax_g','ay_g','az_g','ax_ms2','ay_ms2','az_ms2','accel_norm_g','gx_dps','gy_dps','gz_dps','gyro_norm_dps','temp_c']
    print('ICM-42688-V logger'); print('CSV:',out); print('Ctrl+C para terminar')
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
            set_stream(bus,True); print('Stream ICM ON')
            while running:
                msg=bus.recv(timeout=1.0)
                if msg is None or msg.arbitration_id!=CAN_STREAM_ID: continue
                txt=clean_ascii(bytes(msg.data)); d=parse_icm(txt)
                if d is None:
                    if a.show_raw and txt: print('No parseado:',txt)
                    continue
                row={k:'' for k in fields}; row.update(d); row['timestamp_iso']=datetime.now().astimezone().isoformat(timespec='milliseconds'); row['epoch_s']=f'{time.time():.6f}'; row['elapsed_s']=f'{time.monotonic()-start:.6f}'; row['can_id']=f'0x{msg.arbitration_id:X}'; row['raw_text']=txt
                w.writerow(row); f.flush(); samples+=1
                if a.print: print(f"{row['timestamp_iso']} ACC[g] x={d['ax_g']:+.3f} y={d['ay_g']:+.3f} z={d['az_g']:+.3f} GYRO[dps] x={d['gx_dps']:+.2f} y={d['gy_dps']:+.2f} z={d['gz_dps']:+.2f} T={d['temp_c']:.1f}C")
                elif samples%20==0: print('Muestras guardadas:',samples)
    finally:
        if not a.no_stream_off:
            try: set_stream(bus,False); print('Stream ICM OFF')
            except Exception: pass
        bus.shutdown(); print('Archivo guardado:',out)
if __name__=='__main__': main()
