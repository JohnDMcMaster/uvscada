import matplotlib.pyplot as plt
import json

f = open('2016-10-20_01_cs-137.csv', 'r')
data = []
print 'Loading'
for l in f:
    try:
        j = json.loads(l)
    except:
        break
    data.append(j['v'])

print 'Plotting (%d samples)' % (len(data),)
plt.hist(data, bins=range(0, 32768, 32))
plt.show()



