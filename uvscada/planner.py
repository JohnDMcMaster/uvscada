#!/usr/bin/python
'''
pr0ncnc: IC die image scan
Copyright 2010 John McMaster <JohnDMcMaster@gmail.com>
Licensed under a 2 clause BSD license, see COPYING for details
'''

import time
import math
import numpy
import numpy.linalg
import os
import copy
import shutil
import json
import threading
import abc
from collections import OrderedDict

def format_t(dt):
    s = dt % 60
    m = int(dt / 60 % 60)
    hr = int(dt / 60 / 60)
    return '%02d:%02d:%02d' % (hr, m, s)

def drange(start, stop, step, inclusive = False):
    r = start
    if inclusive:
        while r <= stop:
            yield r
            r += step
    else:
        while r < stop:
            yield r
            r += step

def drange_at_least(start, stop, step):
    '''Garauntee max is in the output'''
    r = start
    while True:
        yield r
        if r > stop:
            break
        r += step

# tolerance drange
# in output if within a delta
def drange_tol(start, stop, step, delta = None):
    '''Garauntee max is in the output'''
    if delta is None:
        delta = step * 0.05
    r = start
    while True:
        yield r
        if r > stop:
            break
        r += step

class PlannerAxis:
    def __init__(self, name,
                # Desired image overlap
                # Actual may be greater if there is more area
                # than minimum number of pictures would support
                req_overlap_percent, 
                # How much the imager can see (in um)
                view,
                # Actual sensor dimension may be oversampled, scale down as needed
                imager_scalar,
                # start and end absolute positions (in um)
                # Inclusive such that 0:0 means image at position 0 only
                start, end,
                log=None):
        if log is None:
            def log(s):
                print s
        self.log = log
        # How many the pixels the imager sees after scaling
        # XXX: is this global scalar playing correctly with the objective scalar?
        self.view_pixels = view * imager_scalar
        #self.pos = 0.0
        self.name = name
        '''
        The naming is somewhat bad on this as it has an anti-intuitive meaning
        
        Proportion of each image that is unique from previous
        Overlap of 1.0 means that images are all unique sections
        Overlap of 0.0 means never move and keep taking the same spot
        '''
        self.req_overlap_percent = req_overlap_percent
        
        self.start = start
        # Requested end, not necessarily true end
        self.req_end = end
        self.end = end
        if self.delta() < view:
            self.log('Axis %s: delta %0.3f < view %0.3f, expanding end' % (self.name, self.delta(), view))
            self.end = start + view
        self.view = view

        # Its actually less than this but it seems it takes some stepping
        # to get it out of the system
        self.backlash = 50
        '''
        Backlash compensation
        0: no compensation
        -1: compensated for decreasing
        1: compensated for increasing
        '''
        self.comp = 0

        self.last = None
        
        self._meta = {}

    def meta(self):
        self._meta['backlash'] = self.backlash
        self._meta['overlap']  = self.step_percent()
        return self._meta

    def delta(self):
        '''Total distance that will actually be imaged'''
        return self.end - self.start + 1
                
    def req_delta(self):
        '''Total distance that needs to be imaged (ie requested)'''
        return self.req_end - self.start + 1
                
    def delta_pixels(self):
        return self.images_ideal() * self.view_pixels
        
    def images_ideal(self):
        '''
        Always 1 non-overlapped image + the overlapped images
        (can actually go negative though)
        Remaining distance from the first image divided by
        how many pixels of each image are unique to the previously taken image when linear
        '''
        if self.req_delta() <= self.view:
            return 1.0 * self.req_delta() / self.view
        ret = 1.0 + (self.req_delta() - self.view) / (self.req_overlap_percent * self.view)
        if ret < 0:
            raise Exception('bad number of idea images %s' % ret)
        return ret
    
    def images(self):
        '''How many images should actually take after considering margins and rounding'''
        ret = int(math.ceil(self.images_ideal()))
        if ret < 1:
            raise Exception('Bad number of images %d' % ret)
        return ret
    
    def step(self):
        '''How much to move each time we take the next image'''
        '''
        Note that one picture has wider coverage than the others
        Thus its treated specially and subtracted from the remainder
        
        It is okay for the second part to be negative since we could
        try to image less than our sensor size
        However, the entire quantity should not be negative
        '''
        # Note that we don't need to adjust the initial view since its fixed, only the steps
        images_to_take = self.images()
        if images_to_take == 1:
            return self.delta()
        else:
            return (self.delta() - self.view) / (images_to_take - 1.0)
        
    def step_percent(self):
        '''Actual percentage we move to take the next picture'''
        # Contrast with requested value self.req_overlap_percent
        return self.step() / self.view
        
    def points(self):
        step = self.step()
        for i in xrange(self.images()):
            yield self.start + i * step
    
class Planner:
    def __init__(self, scan_config, progress_cb, hal,
                img_sz, img_scalar,
                out_dir, overwrite=False, dry=False,
                log=None, verbosity=2):
        if log is None:
            def log(msg):
                print msg
        self.log = log
        self.v = verbosity
        self.hal = hal
        self.dry = dry
        # os.path.join(config['cnc']['out_dir'], self.rconfig.job_name)
        self.out_dir = out_dir
        # config['cnc']['overwrite']:
        self.overwrite = overwrite
        
        self.normal_running = threading.Event()
        self.normal_running.set()
        # FIXME: this is better than before but CTypes pickle error from deepcopy
        self.config = scan_config
        self.progress_cb = progress_cb
        
        self._meta = {
            'x':{},
            'y':{},
            }
        
        ideal_overlap = 2.0 / 3.0
        if 'overlap' in scan_config:
            ideal_overlap = float(scan_config['overlap'])
        # Maximum allowable overlap proportion error when trying to fit number of snapshots
        #overlap_max_error = 0.05
        
        '''
        Planar test run
        plane calibration corner ended at 0.0000, 0.2674, -0.0129
        '''
    
        start = (float(scan_config['start']['x']), float(scan_config['start']['y']))
        end = (float(scan_config['end']['x']), float(scan_config['end']['y']))
        self.axes = OrderedDict([
                ('x', PlannerAxis('X', ideal_overlap,
                    img_sz[0], img_scalar,
                    start[0], end[0], log=self.log)),
                ('y', PlannerAxis('Y', ideal_overlap,
                    img_sz[1], img_scalar,
                    start[1], end[1], log=self.log)),
                ])
        self.x = self.axes['x']
        self.y = self.axes['y']
        
        self.parse_points()
        self.parse_focus_stack()
        
        for axisc, axis in self.axes.iteritems():
            self.log('Axis %s' % axisc)
            self.log('  %f to %f' % (axis.start, axis.end), 2)
            self.log('  Ideal overlap: %f, actual %g' % (ideal_overlap, axis.step_percent()), 2)
            self.log('  full delta: %f' % (self.x.delta()), 2)
            self.log('  view: %f' % (axis.view,), 2)
            
        # A true useful metric of efficieny loss is how many extra pictures we had to take
        # Maybe overhead is a better way of reporting it
        ideal_n_pictures = self.x.images_ideal() * self.y.images_ideal()
        expected_n_pictures = self.x.images() * self.y.images()
        self.log('Ideally taking %g pictures (%g X %g) but actually taking %d (%d X %d), %g efficient' % (
                ideal_n_pictures, self.x.images_ideal(), self.y.images_ideal(), 
                expected_n_pictures, self.y.images(), self.y.images(),
                ideal_n_pictures / expected_n_pictures * 100.0), 2)
        
        # Try actually generating the points and see if it matches how many we thought we were going to get
        self.pictures_to_take = self.n_xy()
        self._meta['pictures_to_take'] = self.pictures_to_take
        if self.scan_config.get('exclude', []):
            self.log('Suppressing picture take check on exclusions')
        elif self.pictures_to_take != expected_n_pictures:
            self.log('Going to take %d pictures but thought was going to take %d pictures (x %d X y %d)' % (self.pictures_to_take, expected_n_pictures, self.x.images(), self.y.images()))
            self.log('Points:')
            for p in self.gen_xys():
                self.log('    ' + str(p))
            raise Exception('See above')
        self.notify_progress(None, True)
        self.img_ext = '.jpg'

        # Total number of images taken
        self.all_imgs = 0
        # Number of images taken at unique x, y coordinates
        # May be different than all_imags if image stacking
        self.xy_imgs = 0

    def _log(self, msg='', verbosity=2):
        if verbosity <= self.v:
            self.log(msg)

    def parse_focus_stack(self):
        if 'stack' in self.scan_config:
            stack = self.scan_config['stack']
            self.num_stack = int(stack['num'])
            self.stack_step_size = int(stack['step_size'])
        else:
            self.num_stack = None
            self.stack_step_size = None
        
    def notify_progress(self, image_file_name, first = False):
        if self.progress_cb:
            self.progress_cb(self.pictures_to_take, self.xy_imgs, image_file_name, first)

    def comment(self, s = '', verbosity=2):
        if len(s) == 0:
            self.log(verbosity=verbosity)
        else:
            self.log('# %s' % s, verbosity=verbosity)

    def end_program(self):
        pass
    
    def pause(self, seconds):
        pass

    def write_metadata(self):
        # Copy config for reference
        self.rconfig.write_to_dir(self.out_dir)
        # TODO: write out coordinate map
        
    def prepare_image_output(self):
        if self.dry:
            self.log('DRY: mkdir(%s)' % self.out_dir)
            return
        
        if os.path.exists(self.out_dir):
            if not self.overwrite:
                raise Exception("Output dir %s already exists" % self.out_dir)
            self.log('WARNING: overwriting old output')
            shutil.rmtree(self.out_dir)
        self.log('Creating output directory %s' % self.out_dir)
        os.mkdir(self.out_dir)
            
    def img_fn(self, stack_suffix=''):
        return os.path.join(self.out_dir,
                'c%03d_r%03d%s%s' % (self.cur_col, self.cur_row, stack_suffix, self.img_ext))
        
    def take_picture(self, fn):
        self.hal.img_get().save(fn)
        self.all_imgs += 1
    
    def take_pictures(self):
        if self.num_stack:
            n = self.num_stack
            if n % 2 != 1:
                raise Exception('Center stacking requires odd n')
            # how much to step on each side
            n2 = (self.num_stack - 1) / 2
            self.mv_abs(None, None, -n2 * self.stack_step_size)
            
            '''
            Say 3 image stack
            Move down 1 step to start and will have to do 2 more
            '''
            for i in range(n):
                img_fn = self.img_fn('_z%02d' % i)
                self.take_picture(img_fn)
                # Avoid moving at end
                if i != n:
                    self.mv_rel(None, None, self.stack_step_size)
                    # we now sleep before the actual picture is taken
                    #time.sleep(3)
                self.notify_progress(img_fn)
        else:
            img_fn = self.img_fn()
            self.take_picture(img_fn)        
            self.notify_progress(img_fn)

        self.xy_imgs += 1
    
    def validate_point(self, p):
        (cur_x, cur_y, cur_row, cur_col) = p
        #self.log('xh: %g vs cur %g, yh: %g vs cur %g' % (xh, cur_x, yh, cur_y))
        #do = False
        #do = cur_x > 3048 and cur_y > 3143
        x_tol = 3.0
        y_tol = 3.0
        xmax = cur_x + self.focus.x_view
        ymax = cur_y + self.focus.y_view
        
        fail = False
        
        if cur_col < 0 or cur_col >= self.x.images():
            self.log('Col out of range 0 <= %d <= %d' % (cur_col, self.x.images()))
            fail = True
        if cur_x < self.x.start - x_tol or xmax > self.x.end + x_tol:
            self.log('X out of range')
            fail = True
            
        if cur_row < 0 or cur_row >= self.y.images():
            self.log('Row out of range 0 <= %d <= %d' % (cur_row, self.y.images()))
            fail = True
        if cur_y < self.y.start - y_tol or ymax > self.y.end + y_tol:
            self.log('Y out of range')
            fail = True        
        
        if fail:
            self.log('Bad point:')
            self.log('  X: %g' % cur_x)
            self.log('  Y: %g' % cur_y)
            self.log('  Row: %g' % cur_row)
            self.log('  Col: %g' % cur_col)
            raise Exception('Bad point (%g + %g = %g, %g + %g = %g) for range (%g, %g) to (%g, %g)' % (
                    cur_x, self.focus.x_view, xmax,
                    cur_y, self.focus.y_view, ymax,
                    self.x.start, self.y.start,
                    self.x.end, self.y.end))
    
    def exclude(self, p):
        (_xy, (cur_row, cur_col)) = p
        for exclusion in self.scan_config.get('exclude', []):
            '''
            If neither limit is specified don't exclude
            maybe later: if one limit is specified but not the other take it as the single bound
            '''
            r0 = exclusion.get('r0', float('inf'))
            r1 = exclusion.get('r1', float('-inf'))
            c0 = exclusion.get('c0', float('inf'))
            c1 = exclusion.get('c1', float('-inf'))
            if cur_row >= r0 and cur_row <= r1 and cur_col >= c0 and cur_col <= c1:
                self.log('Excluding r%d, c%d on r%s:%s, c%s:%s' % (cur_row, cur_col, r0, r1, c0, c1))
                return True
        return False

    def n_xy(self):
        '''Number of unique x, y coordinates'''
        pictures_to_take = 0
        for _p in self.gen_xys():
            pictures_to_take += 1
        return pictures_to_take
    
    def gen_xys(self):
        for (x, y), _cr in self.gen_xycr():
            yield (x, y)
    
    def gen_xycr(self):
        for p in self.gen_xycr_serp():
            self.validate_point(p)
            if self.exclude(p):
                continue
            yield p
    
    def gen_xycr_serp(self):
        '''Generate serpentine pattern'''
        x_list = [x for x in self.x.points()]
        x_list_rev = list(x_list)
        x_list_rev.reverse()
        row = 0
        
        active = (x_list, 0, 1)
        nexts = (x_list_rev, len(x_list_rev) - 1, -1)
        
        for cur_y in self.y.points():
            x_list, col, cold = active
            
            for cur_x in x_list:
                yield ((cur_x, cur_y), (row, col))
                col += cold
            # swap direction
            active, nexts = nexts, active
            row += 1
    
    def set_run(self, running):
        '''Used to pause movement'''
        if running:
            self.normal_running.set()
        else:
            self.normal_running.clear()
        
    def run(self, start_hook=None):
        self.start_time = time.time()
        self.log()
        self.log()
        self.log()
        self.comment('Generated by pr0ncnc on %s' % (time.strftime("%d/%m/%Y %H:%M:%S"),))
        focus = self.focus
        net_mag = focus.objective_mag * focus.eyepiece_mag * focus.camera_mag
        self.comment('objective: %f, eyepiece: %f, camera: %f, net: %f' % (focus.objective_mag, focus.eyepiece_mag, focus.camera_mag, net_mag))
        self.comment('x size: %f um / %d pix, y size: %f um / %d pix' % (self.x.delta(), self.x.delta_pixels(), self.y.delta(), self.y.delta_pixels()))
        mp = self.x.delta_pixels() * self.y.delta_pixels() / (10**6)
        if mp >= 1000:
            self.comment('Image size: %0.1f GP' % (mp/1000,))
        else:
            self.comment('Image size: %0.1f MP' % (mp,))
        self.comment('x fov: %f, y fov: %f' % (focus.x_view, focus.y_view))
        self.comment('x_step: %f, y_step: %f' % (self.x.step(), self.y.step()))
        
        self.comment('pictures: %d' % self.pictures_to_take)
        self.comment()

        self.prepare_image_output()
        if start_hook:
            start_hook(self.out_dir())
        
        # Do initial backlash compensation
        self.backlash_init()
        
        self.cur_col = -1
        # columns
        for ((cur_x, cur_y), (self.cur_col, self.cur_row)) in self.gen_xycr():
            if not self.normal_running.is_set():
                self.log('Planner paused')
                self.normal_running.wait()
                self.log('Planner unpaused')
            if True:
                self.log('', 3)
                self.comment('comp (%d, %d, %d), pos (%f, %f, %s)' % (self.x_comp, self.y_comp, cur_x, cur_y), 3)

                self.mv_abs_backlash({'x':cur_x, 'y':cur_y})
                self.take_pictures()

        self.ret0()
        self.end_program()
        self.end_time = time.time()

        self.log()
        self.log()
        self.log()
        #self.comment('Statistics:')
        #self.comment('Pictures: %d' % pictures_taken)
        if not self.xy_imgs == self.pictures_to_take:
            if self.scan_config.get('exclude', []):
                self.log('Suppressing for exclusion: pictures taken mismatch (taken: %d, to take: %d)' % (self.pictures_to_take, self.xy_imgs))
            else:
                raise Exception('pictures taken mismatch (taken: %d, to take: %d)' % (self.pictures_to_take, self.xy_imgs))
           
        self.write_metadata()
        
    def meta(self):
        '''Can only be called after run'''
        for axisc, axis in self.axes.iteritems():
            self._meta[axisc] = axis.meta()
    
        # In seconds
        self._meta['time'] = self.end_time - self.start_time
        self._meta['pictures_taken'] = self.xy_imgs
        
        return self._meta
        
    def backlash_init(self):
        self.hal.mv_abs({'x': -self.x.backlash, 'y': -self.y.backlash})
        self.x.comp = -1
        self.y.comp = -1
        
    def mv_abs_backlash(self, move_to):
        '''Do an absolute move with backlash compensation'''
        
        for axisc in move_to.keys():
            axis = self.axes[axisc]
            
            # Going right but was not compensating right?
            if (move_to[axisc] - axis.last > 0) and (axis.comp <= 0):
                self.log('Axis %c: compensate for changing to increasing' % axisc, 3)
                self.mv_abs({axisc:move_to[axisc] - axis.backlash})
                axis.comp = 1
            # Going left but was not compensating left?
            elif (move_to[axisc] - axis.last < 0) and (axis.comp >= 0):
                self.log('Axis %c: compensate for changing to decreasing' % axisc, 3)
                self.mv_abs({axisc:move_to[axisc] + axis.backlash})
                axis.comp = -1
            
        self.hal.mv_abs(move_to)

'''
Planner hardware abstraction layer (HAL)
At this time there is no need for unit conversions
Operate in whatever the native system is
'''
class Hal:
    def __init__(self, dry, log):
        self.dry = dry
        self.log = log

    def ret0(self):
        '''Return to origin'''
        self.mv_abs(0, 0, 0)

    @abc.abstractmethod
    def mv_abs(self, pos):
        '''Relative move to positions specified by pos dict'''
        pass

    @abc.abstractmethod
    def mv_rel(self, delta):
        '''Absolute move to positions specified by delta dict'''
        pass
    
    '''
    In modern systems the first is almost always used
    The second is supported for now while porting legacy code
    '''
    @abc.abstractmethod
    def img_get(self):
        '''Take a picture and return a PIL image'''
        pass
    def img_take(self):
        '''Take a picture and save it to internal.  File name is generated automatically'''
        raise Exception("Unsupported")

    @abc.abstractmethod
    def pos(self, axes):
        '''Return current position for given axes'''
        pass

    @abc.abstractmethod
    def begin(self):
        '''Call at start of active use'''
        pass
    
    @abc.abstractmethod
    def end(self):
        '''Called after machine is no longer in use.  Motors must maintain position'''
        pass

    def stop(self):
        '''Stop motion as soon as convenient.  Motors must maintain position'''
        pass

    def estop(self):
        '''Stop motion ASAP.  Motors are not required to maintain position'''
        pass

    def unestop(self):
        '''Allow system to move again after estop'''
        pass

    def meta(self):
        '''Supplementary info to add to run log'''
        return {}

    def forever_pos(self):
        raise Exception("Not supported")

    def forever_neg(self):
        raise Exception("Not supported")

'''
Has no actual hardware associated with it
'''
class MockHAL(Hal):
    def __init__(self, dry, log, axes):
        Hal.__init__(self, dry, log)

        self.axes = list(axes)
        self._pos = {}
        # Assume starting at 0.0 until causes problems
        for axis in self.axes:
            self._pos[axis] = 0.0

    def _log(self, msg):
        if self.dry:
            self.log('Mock-dry: ' + msg)
        else:
            self.log('Mock: ' + msg)

    def take_picture(self, file_name):
        self._log('taking picture to %s' % file_name)

    def mv_abs(self, pos):
        for axis, apos in pos.itervalues():
            self._pos[axis] = apos
        self._log('absolute move to ' + ' '.join(['%c%0.3f' % (k.upper(), v) for k, v in pos.itervalues()]))

    def mv_rel(self, delta):
        for axis, adelta in delta.itervalues():
            self._pos[axis] += adelta
        self._log('relative move to ' + ' '.join(['%c%0.3f' % (k.upper(), v) for k, v in delta.itervalues()]))

    def img_get(self):
        self._log('img_get()')
        # XXX: return image?
        return None
    
    def img_take(self):
        self._log('img_take()')

'''
Legacy uvscada.mc adapter
'''
class MCHal(Hal):
    def __init__(self, dry, log, mc, imager):
        Planner.__init__(self, dry, log)
        self.mc = mc
        self.imager = imager
        # seconds to wait before snapping picture
        self.t_settle = 4.0

    def settle(self):
        '''Check last move time and wait if its not safe to take picture'''
        if self.dry:
            self.sleep(self.t_settle, 'settle')
        else:
            sleept = self.t_settle + self.mv_lastt - time.time()
            if sleept > 0.0:
                self.sleep(sleept, 'settle')

    def sleep(self, sec, why):
        self.log('Sleep %s' % (format_t(sec), why), 3)
        self.rt_sleep += sec

    def img_get(self):
        self.settle()
        return self.imager.get()

    def reset_camera(self):
        # original needed focus button released
        #self.line('M9')
        # suspect I don't need anything here
        pass

    def mv_abs(self, pos):
        # Only one axis can be moved at a time
        for axis, apos in pos.itervalues():
            if self.dry:
                self._pos[axis] = apos
            else:
                self.mc.axes[axis].mv_abs(apos)
                self.mv_lastt = time.time()
        
    def mv_rel(self, delta):
        # Only one axis can be moved at a time
        for axis, adelta in delta.itervalues():
            if self.dry:
                self._pos[axis] += adelta
            else:
                self.mc.axes[axis].mv_rel(adelta)
                self.mv_lastt = time.time()

    '''
    def meta(self):
        ret = {}
        
        # FIXME: time estimator
        # It didn't really work so I didn't bother porting it over during cleanup
        self.rt_move = 0.0
        self.rt_settle = 0.0
        self.rt_sleep = 0.0

        rt_tot = self.rt_move + self.rt_settle + self.rt_sleep
        if self.rconfig.dry:
            rt_k = 'rt_est'
        else:
            rt_k = 'rt'
        ret[rt_k] = {
                    'total':    rt_tot,
                    'move':     self.rt_move,
                    'settle':   self.rt_settle,
                    'sleep':    self.rt_sleep,
                    }
        
        return ret
        '''

'''
Static gcode generator using coolant hack
Not to be confused LCncHal which uses MDI g-code in real time

M7 (coolant on): tied to focus / half press pin
M8 (coolant flood): tied to snap picture
    M7 must be depressed first
M9 (coolant off): release focus / picture
'''
class GCodeHal(Hal):
    def __init__(self, dry, log, axes):
        Hal.__init__(self, dry, log)
        self.axes = list(axes)
        
        self._pos = {}
        # Assume starting at 0.0 until causes problems
        for axis in self.axes:
            self._pos[axis] = 0.0
        self._buff = bytearray()

    def img_take(self):
        # Focus (coolant mist)
        self._line('M7')
        self._dwell(2)
        
        # Snap picture (coolant flood)
        self._line('M8')
        self._dwell(3)
        
        # Release shutter (coolant off)
        self._line('M9')

    def mv_abs(self, pos):
        for axis, apos in pos.itervalues():
            self._pos[axis] = apos
        self._line('G90 G0' + ' '.join(['%c%0.3f' % (k.upper(), v) for k, v in pos.itervalues()]))

    def mv_rel(self, pos):
        for axis, delta in pos.itervalues():
            self._pos[axis] += delta
        self._line('G91 G0' + ' '.join(['%c%0.3f' % (k.upper(), v) for k, v in pos.itervalues()]))

    def comment(self, s=''):
        if len(s) == 0:
            self._line()
        else:
            self._line('(%s)' % s)

    def _line(self, s=''):
        #self.log(s)
        self._buff += s + '\n'

    def begin(self):
        pass
    
    def end(self):
        self.line()
        self.line('(Done!)')
        self.line('M2')

    def _dwell(self, seconds):
        raise Exception("FIXME")

    def get(self):
        return str(self._buff)

# Camera always local
class LcncHal(Hal):
    def __init__(self, dry, log, rsh, imager):
        Hal.__init__(self, dry, log)
        self.imager = imager

    def settle(self):
        '''Check last move time and wait if its not safe to take picture'''
        if self.dry:
            self.sleep(self.t_settle, 'settle')
        else:
            sleept = self.t_settle + self.mv_lastt - time.time()
            if sleept > 0.0:
                self.sleep(sleept, 'settle')

    def sleep(self, sec, why):
        self.log('Sleep %s' % (format_t(sec), why), 3)
        self.rt_sleep += sec

    def img_get(self):
        self.settle()
        return self.imager.get()

    @abc.abstractmethod
    def cmd(self, cmd):
        pass
   
    def do_cmd(self, cmd):
        if self.dry:
            self.log(cmd)
        else:
            self.cmd(cmd)
            
    def mv_abs(self, pos):
        # Unlike DIY controllers, all axes can be moved concurrently
        # Don't waste time moving them individually
        self.cmd_('G90 G0' + ' '.join(['%c%0.3f' % (k.upper(), v) for k, v in pos.itervalues()]))
        
    def mv_rel(self, delta):
        # Unlike DIY controllers, all axes can be moved concurrently
        # Don't waste time moving them individually
        self.cmd('G91 G0' + ' '.join(['%c%0.3f' % (k.upper(), v) for k, v in delta.itervalues()]))

# LinuxCNC python connection
# Currently the rpc version emulates stat and command channels
# making these identical for the time being
class LcncPyHal(LcncHal):
    def __init__(self, dry, log, imager, linuxcnc):
        LcncHal.__init__(self, dry, log, imager)
        self.linuxcnc = linuxcnc
        self.stat = self.linuxcnc.stat()
        self.command = self.linuxcnc.command()
    
    def ok_for_mdi(self):
        self.stat.poll()
        return not self.stat.estop and self.stat.enabled and self.stat.homed and self.stat.interp_state == self.linuxcnc.INTERP_IDLE
        
    def wait_mdi_idle(self):
        while not self.ok_for_mdi():
            time.sleep(0.1)
        
    def do_cmd(self, cmd):
        self.wait_mdi_idle()
        self.command.mdi(cmd)            
        self.wait_mdi_idle()
    
# LinuxCNC remote connection
class LcncRshHal(LcncHal):
    def __init__(self, dry, log, imager, rsh):
        LcncHal.__init__(self, dry, log, imager)
        self.rsh = rsh
        self.t_settle = 4.0
        
    def do_cmd(self, cmd):
        # Waits for completion before returning
        self.rsh.mdi(cmd, timeout=0)            
