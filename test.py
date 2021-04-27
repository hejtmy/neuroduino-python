from neuroduino.neuroduino import *
import time
import random

neuroduino = Neuroduino(timeout=0.1, want_threading=False)
neuroduino.connect()
print(neuroduino.is_open())

if not neuroduino.is_open():
    sys.exit(0)

filename = "neuroduino-no-thread.txt"
f = open(filename, "w")
f.write("sleep_time;python_start_time;python_end_time;arduino_done_time\n")
f.close()

def current_milli_time():
    return round(time.time() * 1000)

def neuroduino_done(neuroduino, msg):
    global sleep_time, start_time, is_sending, filename
    end_time = current_milli_time()
    print(end_time - start_time)
    with open(filename, "a") as f:
      # the -1 removes newline symbol at the end
      f.write(f'{sleep_time};{start_time};{end_time};{msg[4:len(msg)-1]}')
    is_sending = False

def neuroduino_send(neuroduino):
    global is_sending, start_time
    start_time = current_milli_time()
    neuroduino.blink()
    is_sending = True

is_sending = False
message = ""

while True:
  try:
    if neuroduino.arduinoConnection.in_waiting > 0:
        message += neuroduino.arduinoConnection.read_all().decode("utf-8")
        print(message)
        if "DONE" in message:
            neuroduino_done(neuroduino, message)
            message = ""
    if not is_sending:
        sleep_time = random.uniform(0.15, 1)
        time.sleep(sleep_time)
        neuroduino_send(neuroduino)
  except KeyboardInterrupt:
    sys.exit(0)
