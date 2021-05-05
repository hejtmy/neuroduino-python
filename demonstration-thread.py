from neuroduino.neuroduino import *
import time

## As the general recommendation is not to overwrite any instanced method, due to obfuscation, 
# the best way is to define a new threading class which overwrites the Neuroduino arduino_done function

class ThreadingNeuroduino(Neuroduino):
  def arduino_done(self, time):
    print(time)

neuroduino = ThreadingNeuroduino(timeout = 0.1, want_threading = True)

neuroduino.connect()
print(neuroduino.is_open())

while True:
  try:
    neuroduino.blink()
    time.sleep(1)
  except KeyboardInterrupt:
    sys.exit(0)

