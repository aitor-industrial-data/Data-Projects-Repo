raw_data = [
    "PLANTA_A|Sensor_01|230.5",
    "planta_a|Sensor_02|210.0",
    "PLANTA_B|Sensor_01|235.2",
    "PLANTA_A|Sensor_01|231.0", # Lectura duplicada (mismo sensor)
    "PLANTA_B|Sensor_02|215.5"
]


master_report={}

clean_data=[]
for line in raw_data:
    floor, sensor, voltage =line.split('|')
    floor=floor.lower()
    

print(master_report)


#    "planta_a": {
#        "Sensor_01": 231.0, # Se queda con el mayor (231.0 > 230.5)
#        "Sensor_02": 210.0
#    },
#    "planta_b": {
#       "Sensor_01": 235.2,
#        "Sensor_02": 215.5
    
