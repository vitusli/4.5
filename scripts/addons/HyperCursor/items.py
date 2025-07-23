import bpy
from mathutils import Vector
from . colors import axis_red, axis_green, axis_blue, red, blue, normal, green, orange, white, yellow

axis_items = [('X', 'X', ''),
              ('Y', 'Y', ''),
              ('Z', 'Z', '')]

axis_index_mappings = {'X': 0,
                       'Y': 1,
                       'Z': 2}

index_axis_mappings = {0: 'X',
                       1: 'Y',
                       2: 'Z'}

axis_vector_mappings = {'X': Vector((1, 0, 0)),
                        'Y': Vector((0, 1, 0)),
                        'Z': Vector((0, 0, 1))}

axis_constraint_mappings = {'X': (True, False, False),
                            'Y': (False, True, False),
                            'Z': (False, False, True)}

axis_color_mappings = {'X': axis_red,
                       'Y': axis_green,
                       'Z': axis_blue}

axis_direction_items = [('XMIN', 'XMin', ''),
                        ('XMAX', 'XMax', ''),
                        ('YMIN', 'YMin', ''),
                        ('YMAX', 'YMax', ''),
                        ('ZMIN', 'ZMin', ''),
                        ('ZMAX', 'ZMax', '')]

ctrl = ['LEFT_CTRL', 'RIGHT_CTRL']
alt = ['LEFT_ALT', 'RIGHT_ALT']
shift = ['LEFT_SHIFT', 'RIGHT_SHIFT']

numbers = ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'ZERO',
           'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4', 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9', 'NUMPAD_0']

number_mappings = {'ZERO':0,
                   'ONE': 1,
                   'TWO': 2,
                   'THREE': 3,
                   'FOUR': 4,
                   'FIVE': 5,
                   'SIX': 6,
                   'SEVEN': 7,
                   'EIGHT': 8,
                   'NINE': 9}

input_mappings = {'ONE': "1",
                  'TWO': "2",
                  'THREE': "3",
                  'FOUR': "4",
                  'FIVE': "5",
                  'SIX': "6",
                  'SEVEN': "7",
                  'EIGHT': "8",
                  'NINE': "9",
                  'ZERO': "0",

                  'NUMPAD_1': "1",
                  'NUMPAD_2': "2",
                  'NUMPAD_3': "3",
                  'NUMPAD_4': "4",
                  'NUMPAD_5': "5",
                  'NUMPAD_6': "6",
                  'NUMPAD_7': "7",
                  'NUMPAD_8': "8",
                  'NUMPAD_9': "9",
                  'NUMPAD_0': "0",

                  'BACK_SPACE': "",
                  'DELETE': "",
                  'PERIOD': ".",
                  'COMMA': ".",
                  'MINUS': "-",

                  'NUMPAD_PERIOD': ".",
                  'NUMPAD_COMMA': ".",
                  'NUMPAD_MINUS': "-"}

def numeric_input_event_items(comma=True, minus=True):
    events = [*numbers, 'BACK_SPACE', 'DELETE']

    if comma:
        events.extend(['PERIOD', 'COMMA', 'NUMPAD_PERIOD', 'NUMPAD_COMMA'])

    if minus:
        events.extend(['MINUS', 'NUMPAD_MINUS'])

    return events

keymap_folds = {'OBJECT': {1: 'Box Select',
                           4: 'Toggle Gizmos',
                           9: 'Cursor History',
                           11: 'Cursor Focus',
                           13: 'Cursor Transformation',
                           17: 'Add Hyper Object',
                           18: 'Boolean, Hyper Cut, Bevel and Bend',
                           22: 'Object and Modifier Management',
                           28: 'Boolean Translate and Duplicate',
                           30: 'Misc'},
                'EDIT_MESH': {1: 'Box Select',
                              4: 'Toggle Gizmos',
                              6: 'Cursor History',
                              8: 'Cursor Focus' ,
                              10: 'Cursor Transformation',
                              14: 'Hyper Bevel'}}

prefs_tab_items = [("SETTINGS", "Settings", ""),
                   ("KEYMAPS", "Keymaps", "")]

transform_mode_items = [('TRANSLATE', 'Translate', ''),
                        ('ROTATE', 'Rotate', ''),
                        ('DRAG', 'Drag', '')]

transform_snap_face_center_items = [('PROJECTED_BOUNDS', 'Projected Bounds', ''),
                                    ('MEDIAN', 'Median', ''),
                                    ('MEDIAN_WEIGHTED', 'Median Weighted', '')]

array_mode_items = [('ADD', 'Add', ''),
                    ('FIT', 'Fit', '')]

change_history_mode_items = [('ADD', 'Add', ''),
                             ('REMOVE', 'Remove', ''),
                             ('MOVEUP', 'Move Up', ''),
                             ('MOVEDOWN', 'Move Down', '')]

focus_mode_items = [('SOFT', 'Soft Focus', ''),
                    ('HARD', 'Hard Focus', '')]

add_object_items = [('CUBE', 'Cube', ''),
                    ('CYLINDER', 'Cylinder', ''),
                    ('ASSET', 'Asset', '')]

add_cylinder_side_items = [('3', '3', ''),
                           ('5', '5', ''),
                           ('6', '6', ''),
                           ('8', '8', ''),
                           ('9', '9', ''),
                           ('12', '12', ''),
                           ('16', '16', ''),
                           ('18', '18', ''),
                           ('24', '24', ''),
                           ('32', '32', ''),
                           ('64', '64', ''),
                           ('72', '72', ''),
                           ('96', '96', ''),
                           ('128', '128', ''),
                           ('256', '256', '')]

boolean_method_items = [("NONE", "None", ""),
                        ("DIFFERENCE", "Difference", ""),
                        ("UNION", "Union", ""),
                        ("INTERSECT", "Intersect", ""),
                        ("SPLIT", "Split", ""),
                        ("GAP", "Gap", ""),
                        ("MESHCUT", "Meshcut", "")]

add_boolean_method_items = [("UNION", "Union", ""),
                            ("DIFFERENCE", "Difference", ""),
                            ("INTERSECT", "Intersect", ""),
                            ("SPLIT", "Split", ""),
                            ("MESHCUT", "Meshcut", "")]

if bpy.app.version >= (4, 5, 0):
    add_boolean_solver_items = [("FAST", "Fast", ""),
                                ("EXACT", "Exact", ""),
                                ("MANIFOLD", "Manifold", "")]

    extended_boolean_solver_items = [("FAST", "Fast", ""),
                                     ("EXACT", "Exact", ""),
                                     ("EXACT_SELF", "Exact, Self Intersection", ""),
                                     ("EXACT_HOLES", "Exact, Hole Tolerant", ""),
                                     ("EXACT_SELF_HOLES", "Exact, Self Intersection + Hole Tolerant", ""),
                                     ("MANIFOLD", "Manifold", "")]

else:
    add_boolean_solver_items = [("FAST", "Fast", ""),
                                ("EXACT", "Exact", "")]

    extended_boolean_solver_items = [("FAST", "Fast", ""),
                                     ("EXACT", "Exact", ""),
                                     ("EXACT_SELF", "Exact, Self Intersection", ""),
                                     ("EXACT_HOLES", "Exact, Hole Tolerant", ""),
                                     ("EXACT_SELF_HOLES", "Exact, Self Intersection + Hole Tolerant", "")]

boolean_display_type_items = [("WIRE", "Wire", ""),
                              ("BOUNDS", "Bounds", "")]

boolean_color_mappings = {'NONE': white,
                          'DIFFERENCE': red,
                          'UNION': blue,
                          'INTERSECT': normal,
                          'SPLIT': green,
                          'GAP': orange,
                          'MESHCUT': yellow}

display_type_items = [("WIRE", "Wire", ""),
                      ("TEXTURED", "Textured", ""),
                      ("SOLID", "Solid", ""),
                      ("BOUNDS", "Bounds", "")]

pipe_mode_items = [('ROUND', 'Round', ''),
                   ('DIAMOND', 'Diamond', ''),
                   ('SQUARE', 'Square', ''),
                   ('OBJECT', 'Object', '')]

pipe_round_mode_items = [('RADIUS', 'Radius', ''),
                         ('OFFSET', 'Offset', '')]

pipe_origin_items = [('AVERAGE_ENDS', 'Average Ends', ''),
                     ('CURSOR_ORIENTATION', 'Cursor Orientation', ''),
                     ('CURSOR', 'Cursor', '')]

cast_direction_items = [('UP', 'Up', ''),
                        ('DOWN', 'Down', '')]

push_mode_items = [('MOVE', 'Move', ''),
                   ('SLIDE', 'Slide', '')]

extrude_mode_items = [('SELECTED', 'Selected', ''),
                      ('AVERAGED', 'Averaged', ''),
                      ('VERT', 'Vert', '')]

backup_vanish_active_items = [('REMOVE', 'Remove', ''),
                              ('HIDE', 'Hide', '')]

obj_type_items = [('NONE', 'None', ''),
                  ('CUBE', 'Cube', ''),
                  ('CYLINDER', 'Cylinder', '')]

obj_type_items_without_none = [('CUBE', 'Cube', ''),
                               ('CYLINDER', 'Cylinder', '')]

edit_mode_items = [('EDIT', 'Edit Gizmos', ''),
                   ('SCALE', 'Scale Gizmos', '')]

hyperbevel_mode_items = [('SELECTION', 'Selection', ''),
                         ('CUTTER', 'Cutter', ''),
                         ('RAYCAST', 'Raycast', '')]

hyperbevel_segment_preset_items = [('3', '3', 'Tiny Fillet'),
                                   ('6', '6', 'Small Fillet'),
                                   ('12', '12', 'Big Fillet'),
                                   ('24', '24', 'Huge Fillet'),
                                   ('CUSTOM', 'Custom', 'Custom')]

merge_object_preset_items = [('11', '1/1', ''),
                             ('12', '1/2', ''),
                             ('1020', '10/20', '')]

shell_offset_mappings = {-1: 'Inwards',
                         0: 'Centered',
                         1: 'Outwards'}

gizmo_angle_presets = [('0', '0', ''),
                       ('5', '5', ''),
                       ('10', '10', ''),
                       ('20', '20', ''),
                       ('30', '30', ''),
                       ('45', '45', ''),
                       ('CUSTOM', 'Custom', '')]

bend_angle_presets = [('10', '10', ''),
                      ('15', '15', ''),
                      ('30', '30', ''),
                      ('45', '45', ''),
                      ('60', '60', ''),
                      ('90', '90', ''),
                      ('120', '120', ''),
                      ('135', '135', ''),
                      ('180', '180', ''),
                      ('360', '360', ''),
                      ('CUSTOM', 'C', 'Custom')]
