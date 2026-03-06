def calculate_intensity(v, r):
    try:
        v=float(v)
        r=float(r)

        if r<=0 or v<=0:
            return ('Error')
        else:
            i=round(v/r,2)
            return (f'Power = {i} A')
    except:
        return 'Error'
    

def calculate_power(v, i):
    try:
        v=float(v)
        i=float(i)

        if i<=0 or v<=0:
            return ('Error')
        else:
            p=round(v*i,2)
            return (f'Power = {p} W')
    except:
        return 'Error'
    
def calculate_resistance(v, i):
    try:
        v=float(v)
        i=float(i)

        if i<=0 or v<=0:
            return ('Error')
        else:
            r=round(v/i,2)
            return (f'Power = {r} Ohm')
    except:
        return 'Error'

prog = input('Elige programa: 1 - calculate_intensity, 2 - calculate_power, 3 - calculate_resistance  ')
prog=float(prog)
if prog==1:
    v = input('Intorduce voltage (V): ')
    r = input('Intorduce resistencia (Ohm): ')
    print(calculate_intensity(v, r))
elif prog==2:
    v = input('Intorduce voltage (V): ')
    i = input('Intorduce Intensidad (A): ')
    print(calculate_power(v, i))
elif prog==3:
    v = input('Intorduce voltage (V): ')
    i = input('Intorduce Intensidad (A): ')
    print(calculate_resistance(v, i))
else:
    print('Programa no valido')
