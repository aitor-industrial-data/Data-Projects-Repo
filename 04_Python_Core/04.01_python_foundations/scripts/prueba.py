

import os
files=os.listdir('.')
update_files=['2026_03_12_sensor_A.log','2026_03_12_sensor_b.log','2026_03_12_sensor_d.log','2026_03_12_sensor_B.log','2026_03_12_sensor_B.log']
files=files+update_files
files = [f.upper() for f in files]
print(files)
sensor_report={}

for file in files:
    
        if '.LOG' in file:
            try:
                f=file.split('.')[0]
                f=file.split('_',3)
                print(f[3])
                sensor_report[f[3]]=sensor_report.get(f[3],0)+1
            except:
                 print(f'{file} [IGNORADO]')
                 
        else:
             print(f'{file} [extension no valida]')
if sensor_report != {}:
    print(sensor_report)
    print('[MOVIENDO] 2026_03_12_sensor_A.log -> /mnt/c/data/procesados/sensor_A/')