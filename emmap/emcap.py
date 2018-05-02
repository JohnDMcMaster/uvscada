#!/usr/bin/env python

from config import get_config
from uvscada.v4l2_util import ctrl_set
from uvscada.minipro import Minipro

from PyQt4 import Qt
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import QWidget, QLabel

import Queue
import threading
import sys
import traceback
import os
import signal

import gobject, pygst
pygst.require('0.10')
import gst

import StringIO
from PIL import Image

uconfig = {
        "Red Balance":  90,
        "Gain":         100,
        "Blue Balance": 207,
        "Exposure":     800
    }

'''
Do not encode images in gstreamer context or it brings system to halt
instead, request images and have them encoded in requester's context
'''
class CaptureSink(gst.Element):
    __gstdetails__ = ('CaptureSink','Sink', \
                      'Captures images for the CNC', 'John McMaster')

    _sinkpadtemplate = gst.PadTemplate ("sinkpadtemplate",
                                        gst.PAD_SINK,
                                        gst.PAD_ALWAYS,
                                        gst.caps_new_any())

    def __init__(self):
        gst.Element.__init__(self)
        self.sinkpad = gst.Pad(self._sinkpadtemplate, "sink")
        self.add_pad(self.sinkpad)

        self.sinkpad.set_chain_function(self.chainfunc)
        self.sinkpad.set_event_function(self.eventfunc)

        self.img_cb = lambda buffer: None

    '''
    gstreamer plugin core methods
    '''

    def chainfunc(self, pad, buffer):
        #print 'Capture sink buffer in'
        try:
            self.img_cb(buffer)
        except:
            traceback.print_exc()
            os._exit(1)

        return gst.FLOW_OK

    def eventfunc(self, pad, event):
        return True

gobject.type_register(CaptureSink)
# Register the element into this process' registry.
gst.element_register (CaptureSink, 'capturesink', gst.RANK_MARGINAL)

class ImageProcessor(QThread):
    n_frames = pyqtSignal(int) # Number of images

    def __init__(self):
        QThread.__init__(self)

        self.running = threading.Event()

        self.image_requested = threading.Event()
        self.q = Queue.Queue()
        self.ncap = 0
        self.imgbuff = []
        self.out_dir = 'out'

    def run(self):
        self.running.set()
        self.image_requested.set()
        while self.running.is_set():
            try:
                img = self.q.get(True, 0.05)
            except Queue.Empty:
                continue
            self.imgbuff.append(img)
            print 'Loop: got image w/ cnt %d' % len(self.imgbuff)

            # Got two dark frames?
            if len(self.imgbuff) == 2:
                # Start light frames
                _fw = prog.read()
            elif len(self.imgbuff) == 4:
                # Verify we haven't overrun buffer
                while True:
                    try:
                        img_none = self.q.get(False)
                    except Queue.Empty:
                        break
                    self.imgbuff.append(img_none)

                if len(self.imgbuff) > 4:
                    #raise Exception("Image buffer overrun")
                    print "Image buffer overrun w/ %d images" % len(self.imgbuff)
                else:
                    # First two frames are dark, second two are light
                    # 0.3 sec / frame => 1.2 sec per cycle
                    # say 5 MB / image => 
                    # overnight easily 10k+ frames => 250 GB of data?
                    # FIXME: get png not jpg
                    for i, img in enumerate(self.imgbuff):
                        open('%s/cap_%05u-%u.jpg' % (self.out_dir, self.ncap, i), 'w').write(img)
                self.imgbuff = []
                self.ncap += 1
            elif len(self.imgbuff) > 4:
                raise Exception("bad state")

    def stop(self):
        self.running.clear()

    def img_cb(self, buffer):
        print 'got image'
        self.q.put(buffer.data)

class GUI(QMainWindow):
    def __init__(self, prog):
        QMainWindow.__init__(self)
        self.showMaximized()

        self.prog = prog
        self.initUI()

        self.vid_fd = None

        # Must not be initialized until after layout is set
        self.gstWindowId = None
        engine_config = 'gstreamer'
        #engine_config = 'gstreamer-testsrc'
        if engine_config == 'gstreamer':
            self.source = gst.element_factory_make("v4l2src", "vsource")
            self.source.set_property("device", "/dev/video0")
            self.vid_fd = -1
            self.setupGst()
        elif engine_config == 'gstreamer-testsrc':
            print 'WARNING: using test source'
            self.source = gst.element_factory_make("videotestsrc", "video-source")
            self.setupGst()
        else:
            raise Exception('Unknown engine %s' % (engine_config,))

        self.processor = ImageProcessor()
        self.capture_sink.img_cb = self.processor.img_cb

        self.processor.start()

        if self.gstWindowId:
            print "Starting gstreamer pipeline"
            self.player.set_state(gst.STATE_PLAYING)

    def get_video_layout(self):
        # Overview
        def low_res_layout():
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Overview"))

            # Raw X-windows canvas
            self.video_container = QWidget()
            # Allows for convenient keyboard control by clicking on the video
            self.video_container.setFocusPolicy(Qt.ClickFocus)
            w, h = 3264/4, 2448/4
            self.video_container.setMinimumSize(w, h)
            self.video_container.resize(w, h)
            policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.video_container.setSizePolicy(policy)

            layout.addWidget(self.video_container)

            return layout

        layout = QHBoxLayout()
        layout.addLayout(low_res_layout())
        return layout

    def setupGst(self):
        print "Setting up gstreamer pipeline"
        self.gstWindowId = self.video_container.winId()

        self.player = gst.Pipeline("player")
        self.tee = gst.element_factory_make("tee")
        sinkx = gst.element_factory_make("ximagesink", 'sinkx_overview')
        fcs = gst.element_factory_make('ffmpegcolorspace')
        caps = gst.caps_from_string('video/x-raw-yuv')
        self.capture_enc = gst.element_factory_make("jpegenc")
        self.capture_sink = gst.element_factory_make("capturesink")
        self.capture_sink_queue = gst.element_factory_make("queue")
        self.resizer =  gst.element_factory_make("videoscale")

        # Video render stream
        self.player.add(      self.source, self.tee)
        gst.element_link_many(self.source, self.tee)

        self.player.add(fcs,                 self.resizer, sinkx)
        gst.element_link_many(self.tee, fcs, self.resizer, sinkx)

        self.player.add(                self.capture_sink_queue, self.capture_enc, self.capture_sink)
        gst.element_link_many(self.tee, self.capture_sink_queue, self.capture_enc, self.capture_sink)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)

    def on_message(self, bus, message):
        t = message.type

        if self.vid_fd is not None and self.vid_fd < 0:
            self.vid_fd = self.source.get_property("device-fd")
            if self.vid_fd >= 0:
                print 'Initializing V4L controls'
                self.v4l_load()

        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
            print "End of stream"
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.player.set_state(gst.STATE_NULL)
            ''

    def v4l_load(self):
        for k, v in uconfig.iteritems():
            print '%s => %s' % (k, v)
            ctrl_set(self.vid_fd, k, v)

    def on_sync_message(self, bus, message):
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            if message.src.get_name() == 'sinkx_overview':
                print 'sinkx_overview win_id'
                win_id = self.gstWindowId
            else:
                raise Exception('oh noes')

            assert win_id
            imagesink = message.src
            imagesink.set_xwindow_id(win_id)

    def initUI(self):
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('pyv4l test')

        # top layout
        layout = QHBoxLayout()
        layout.addLayout(self.get_video_layout())

        w = QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)
        self.show()

def excepthook(excType, excValue, tracebackobj):
    print '%s: %s' % (excType, excValue)
    traceback.print_tb(tracebackobj)
    os._exit(1)

if __name__ == '__main__':
    from uvscada.util import IOTimestamp
    _ts = IOTimestamp()

    prog = Minipro(device='PIC16C57')

    '''
    We are controlling a robot
    '''
    sys.excepthook = excepthook
    # Exit on ^C instead of ignoring
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    gobject.threads_init()

    app = QApplication(sys.argv)
    _gui = GUI(prog)
    sys.exit(app.exec_())
