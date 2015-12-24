#!/usr/bin/env python

from PyQt4 import Qt
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import sys
import traceback
import os
import signal

import gobject, pygst
pygst.require('0.10')
import gst

class CNCGUI(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.initUI()
        
        # Must not be initialized until after layout is set
        self.gstWindowId = None
        engine_config = 'gstreamer'
        if engine_config == 'gstreamer':
            self.source = gst.element_factory_make("v4l2src", "vsource")
            
            self.source.set_property("device", "/dev/video0")
            print 'FD', self.source.get_property("device-fd")
            #self.fd = open('/dev/video0', 'rw')
            #self.source.set_property("uri", 'fd://%s' % self.fd.fileno())
            
            self.setupGst()
        elif engine_config == 'gstreamer-testsrc':
            self.source = gst.element_factory_make("videotestsrc", "video-source")
            self.setupGst()
        else:
            raise Exception('Unknown engine %s' % (engine_config,))
        
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
        sinkx = gst.element_factory_make("ximagesink", 'sinkx_overview')
        fcs = gst.element_factory_make('ffmpegcolorspace')
        caps = gst.caps_from_string('video/x-raw-yuv')

        self.resizer =  gst.element_factory_make("videoscale")

        # Video render stream
        self.player.add(self.source, fcs, self.resizer, sinkx)
        gst.element_link_many(self.source, fcs, self.resizer, sinkx)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)
    
    def on_message(self, bus, message):
        t = message.type
        
        #print dir(self.source)
        #print self.source.props
        fd = self.source.get_property("device-fd")
        if 0 and fd != -1:
            '''
            FD 10
            <flags GST_MESSAGE_STATE_CHANGED of type GstMessageType>
            <gst.Message GstMessageState, old-state=(GstState)GST_STATE_NULL, new-state=(GstState)GST_STATE_READY, pending-state=(GstState)GST_STATE_VOID_PENDING; from sinkx_overview at 0x1e4ab80>
            
            ['__class__', '__cmp__', '__delattr__', '__dict__', '__doc__', '__format__', '__getattribute__', '__grefcount__', '__gstminiobject_init__', '__gtype__', '__hash__', 
            '__init__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', 'copy', 'flags', 'parse_async_start', 
            'parse_buffering', 'parse_buffering_stats', 'parse_clock_lost', 'parse_clock_provide', 'parse_duration', 'parse_error', 'parse_info', 'parse_new_clock', 'parse_qos',
            'parse_qos_stats', 'parse_qos_values', 'parse_request_state', 'parse_segment_done', 'parse_segment_start', 'parse_state_changed', 'parse_step_done', 'parse_step_start', 
            'parse_stream_status', 'parse_structure_change', 'parse_tag', 'parse_tag_full', 'parse_warning', 'set_buffering_stats', 'set_qos_stats', 'set_qos_values', 'set_seqnum', 
            'src', 'structure', 'timestamp', 'type']
            '''
            print 'FD', fd
            print t
            print message
            print dir(message)
            sys.exit(1)
        
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
            print "End of stream"
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.player.set_state(gst.STATE_NULL)
        #else:
        #    print t

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
        layout = QVBoxLayout()
        
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
    '''
    We are controlling a robot
    '''
    sys.excepthook = excepthook
    # Exit on ^C instead of ignoring
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    gobject.threads_init()
    
    app = QApplication(sys.argv)
    _gui = CNCGUI()
    # XXX: what about the gstreamer message bus?
    # Is it simply not running?
    # must be what pygst is doing
    sys.exit(app.exec_())
