from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time
from picoscope import ps6000
import pylab as plt
import numpy as np

if __name__ == "__main__":
    print("Checking for devices")
    ps = ps6000.PS6000(connect=False)
    allSerialNumbers = ps.enumerateUnits()
    assert len(allSerialNumbers) == 1, "Device not found"
    serial = allSerialNumbers[0]
    print("Connecting to PS6000 %s" % serial)
    ps = ps6000.PS6000(serial)

    print("Found the following picoscope:")
    print(ps.getAllUnitInfo())
    print()

    waveform_desired_duration = 50E-6
    obs_duration = 3 * waveform_desired_duration
    sampling_interval = obs_duration / 4096

    (actualSamplingInterval, nSamples, maxSamples) = \
        ps.setSamplingInterval(sampling_interval, obs_duration)
    print("Sampling interval = %f ns" % (actualSamplingInterval * 1E9))
    print("Taking  samples = %d" % nSamples)
    print("Maximum samples = %d" % maxSamples)

    # the setChannel command will chose the next largest amplitude
    channelRange = ps.setChannel('A', 'DC', 2.0, 0.0, enabled=True,
                                 BWLimited=False)
    print("Chosen channel range = %d" % channelRange)

    ps.setSimpleTrigger('A', 1.0, 'Falling', timeout_ms=100, enabled=True)

    ps.setSigGenBuiltInSimple(offsetVoltage=0, pkToPk=1.2, waveType="Sine",
                              frequency=50E3)

    ps.runBlock()
    ps.waitReady()
    print("Waiting for awg to settle.")
    time.sleep(2.0)
    ps.runBlock()
    ps.waitReady()
    print("Done waiting for trigger")
    dataA = ps.getDataV('A', nSamples, returnOverflow=False)

    dataTimeAxis = np.arange(nSamples) * actualSamplingInterval

    ps.stop()
    ps.close()

    # Uncomment following for call to .show() to not block
    # plt.ion()

    plt.figure()
    plt.hold(True)
    plt.plot(dataTimeAxis, dataA, label="Clock")
    plt.grid(True, which='major')
    plt.title("Picoscope 2000 waveforms")
    plt.ylabel("Voltage (V)")
    plt.xlabel("Time (ms)")
    plt.legend()
    plt.show()
