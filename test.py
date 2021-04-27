from neuroduino.neuroduino import *

neuroduino = Neuroduino(timeout=0.1)
neuroduino.connect()
print(neuroduino.is_open())
