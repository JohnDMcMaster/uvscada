'''
Manually with PyVCP
S   ~RPM
0   2.3
5   80
10  200
20  440
40  1040
60  1630
80  2220
100 2820

/usr/share/doc/linuxcnc/examples/sample-configs/common/configurable_options/pyvcp/spindle.xml
<halpin>"spindle-speed"</halpin>


axis
show pin pyvcp
can't copy...
pyvcp.spindle-speed
spindle.fb-filtered-abs-rpm
'''

import linuxcnc
import hal
if 0:
    stat = linuxcnc.stat()
    command = linuxcnc.command()
    stat.poll()
    '''
    'acceleration', 'active_queue', 'actual_position', 'adaptive_feed_enabled', 'ain', 
    'angular_units', 'aout', 'axes', 'axis', 'axis_mask', 'block_delete', 'command', 
    'current_line', 'current_vel', 'cycle_time', 'debug', 'delay_left', 'din', 
    'distance_to_go', 'dout', 'dtg', 'echo_serial_number', 'enabled', 'estop',
    'exec_state', 'feed_hold_enabled', 'feed_override_enabled', 'feedrate', 
    'file', 'flood', 'g5x_index', 'g5x_offset', 'g92_offset', 'gcodes', 'homed', 
    'id', 'inpos', 'input_timeout', 'interp_state', 'interpreter_errcode', 
    'joint_actual_position', 'joint_position', 'kinematics_type', 'limit', 
    'linear_units', 'lube', 'lube_level', 'max_acceleration', 'max_velocity', 
    'mcodes', 'mist', 'motion_line', 'motion_mode', 'motion_type', 'optional_stop',
    'paused', 'pocket_prepped', 'poll', 'position', 'probe_tripped', 'probe_val', 
    'probed_position', 'probing', 'program_units', 'queue', 'queue_full',
    'queued_mdi_commands', 'rapidrate', 'read_line', 'rotation_xy', 'settings', 
    'spindle_brake', 'spindle_direction', 'spindle_enabled', 'spindle_increasing', 
    'spindle_override_enabled', 'spindle_speed', 'spindlerate', 'state', 
    'task_mode', 'task_paused', 'task_state', 'tool_in_spindle', 'tool_offset',
    'tool_table', 'velocity']
    '''
    print 'Enabled: %s' % stat.enabled
    # print dir(stat)

    '''
    Enabled: True
    spindle_brake: 0
    spindle_direction: 1
    spindle_enabled: 1
    spindle_increasing: 0
    spindle_override_enabled: True
    commanded, not actual
    spindle_speed: 5.0
    spindlerate: 1.0
    '''

    print 'spindle_brake: %s' % stat.spindle_brake
    print 'spindle_direction: %s' % stat.spindle_direction
    print 'spindle_enabled: %s' % stat.spindle_enabled
    print 'spindle_increasing: %s' % stat.spindle_increasing
    print 'spindle_override_enabled: %s' % stat.spindle_override_enabled
    print 'spindle_speed: %s' % stat.spindle_speed
    print 'spindlerate: %s' % stat.spindlerate

    print stat.position
    print stat.velocity

if 1:
    ss = hal.component("spindle-snooper2")
    # hal.error: Invalid pin name length: max = 41 characters
    #ss.newpin("spindle-fb-filtered-abs-rps", hal.HAL_FLOAT, hal.HAL_IN)
    ss.ready()
    # AttributeError: Pin 'spindle-fb-filtered-abs-rps' does not exist
    print ss["spindle-fb-filtered-abs-rps"]


