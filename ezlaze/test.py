from uvscada.ezlaze import EzLaze
import time

# frickin laser
el = EzLaze()

#el.off()
#el.on()
if not el.is_on():
    el.on()

for i in xrange(3):
    el.pulse()
    time.sleep(0.1)
