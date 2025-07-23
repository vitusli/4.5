import bpy
from bpy.props import EnumProperty, StringProperty, BoolProperty, IntProperty

from .. import HyperCursorManager as HC

from .. utils.modifier import get_mod_input, get_next_mod, get_previous_mod, hyper_array_poll, is_radial_array, remove_mod, boolean_poll, local_boolean_poll, array_poll, mirror_poll, remote_hook_poll, is_mod_obj, remote_boolean_poll, get_mod_obj, edgebevel_poll, apply_mod, solidify_poll, other_poll
from .. utils.object import is_removable, parent, remove_obj, get_object_tree, is_wire_object
from .. utils.system import printd
from .. utils.view import ensure_visibility

from .. items import axis_index_mappings, backup_vanish_active_items

class ChangeRemoteBoolean(bpy.types.Operator):
    bl_idname = "machin3.change_remote_boolean"
    bl_label = "MACHIN3: Change Remote Boolean"
    bl_options = {'REGISTER', 'UNDO'}

    objname: StringProperty(name="Object Name")
    modname: StringProperty(name="Modifier Name")

    mode: StringProperty(name="Change Boolean Mode", default='SOLVER')
    stash_cutters: BoolProperty(name="Stash the Cutters", default=True)
    @classmethod
    def description(cls, context, properties):
        if properties:
            objname = f"{properties.objname}"
            modname = f"{properties.modname}"
            mode = f"{properties.mode}"

            if mode == 'HIDE':
                desc = "Toggle Operand Object's Visibility"

            elif mode == 'WIRE':
                desc = "Toggle Operand Object's Display Type"

            elif mode == 'ACTIVATE':
                desc = f"On {objname}, Toggle {modname}'s VIewport Visibility"

            elif mode == 'SOLVER':
                desc = f"On {objname}, Toggle {modname}'s Solver"

            elif mode in ['APPLY', 'REMOVE']:
                desc = f"On {objname}, {mode.title()} {modname}"

            return desc
        return "Invalid Context"

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            if active:
                return [obj for obj in context.scene.objects if any([mod.object == active for mod in obj.modifiers if mod.type == 'BOOLEAN'])]

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        if HC.get_addon('MESHmachine'):
            column.prop(self, 'stash_cutters', toggle=True)

    def execute(self, context):
        active = context.active_object

        obj = bpy.data.objects.get(self.objname)

        if obj:
            mod = obj.modifiers.get(self.modname)

            if mod:

                mod.is_active = True

                if self.mode == 'HIDE':
                    active.hide_set(True)

                    obj.select_set(True)
                    context.view_layer.objects.active = obj

                    bpy.types.MACHIN3_OT_hyper_cursor_object.last = active.name

                elif self.mode == 'WIRE':
                    active.display_type = 'BOUNDS' if active.display_type == 'WIRE' else 'WIRE'

                elif self.mode == 'ACTIVATE':
                    mod.show_viewport = not mod.show_viewport

                elif self.mode == 'SOLVER':
                    mod.solver = 'FAST' if mod.solver == 'EXACT' else 'EXACT'

                elif self.mode in ['APPLY', 'REMOVE']:

                    if HC.get_addon('MESHmachine') and self.mode == 'APPLY' and self.stash_cutters:
                        MM = HC.addons['meshmachine']['module']

                        if mod.object.data:
                            MM.utils.stash.create_stash(obj, mod.object)

                    weld = prev_mod if (prev_mod := get_previous_mod(mod)) and prev_mod.type == 'WELD' else None

                    if 'Hyper Bevel' in self.modname and weld:
                        apply_mod(weld) if self.mode == 'APPLY' else remove_mod(weld)

                    apply_mod(mod) if self.mode == 'APPLY' else remove_mod(mod)

                    remote_booleans = remote_boolean_poll(context, active)

                    if not remote_booleans:
                        active.display_type = 'TEXTURED'

                    if active.children_recursive:

                        boolean_operand_objs = [mod.object for mod in local_boolean_poll(context, active)]

                        for ob in active.children:
                            if ob not in boolean_operand_objs:
                                parent(ob, obj)

        return {'FINISHED'}

class ChangeLocalBoolean(bpy.types.Operator):
    bl_idname = "machin3.change_local_boolean"
    bl_label = "MACHIN3: Change Local Boolean"
    bl_options = {'REGISTER', 'UNDO'}

    modname: StringProperty(name="Modifier Name")

    mode: StringProperty(name="Change Boolean Mode", default='HIDE')
    boolean_type: StringProperty(name="Boolean Type", default='Other')
    stash_cutters: BoolProperty(name="Stash the Cutters", default=True)
    alt: BoolProperty(name="Alt key is pressed")
    shift: BoolProperty(name="Shift key is pressed")

    @classmethod
    def description(cls, context, properties):
        if properties:
            modname = f"{properties.modname}"
            mode = f"{properties.mode}"

            if mode == 'HIDE':
                desc = f"Toggle {modname}'s Operand Object's Visibility"

            elif mode == 'WIRE':
                desc = f"Toggle {modname}'s Operand Object's Display Type"

            elif mode == 'ACTIVATE':
                desc = f"Toggle {modname}'s VIewport Visibility"

            elif mode == 'SOLVER':
                desc = f"Toggle {modname}'s Solver"

            elif mode in ['APPLY', 'REMOVE']:
                desc = f"{mode.title()} {modname}"

            else:
                desc = "Nothing" # just to silence pyright

            desc += "\nSHIFT: Affect all Modifiers"

            if mode == 'HIDE':
                desc += "\nALT: Suppress Object Selection when Unhiding single mod object"

            elif mode in ['APPLY']:
                desc += "\nALT: Affect Active Modifiers"

            elif mode in ['REMOVE']:
                desc += "\nALT: Affect Inactive Modifiers"

            return desc
        return "Invalid Context"

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            if active:
                return boolean_poll(context, active)

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        if HC.get_addon('MESHmachine'):
            column.prop(self, 'stash_cutters', toggle=True)

    def invoke(self, context, event):
        self.alt = event.alt

        self.shift = event.shift
        return self.execute(context)

    def execute(self, context):
        active = context.active_object

        if self.mode == 'REMOVE' and self.alt:
            if self.boolean_type == 'Hyper Bevel':
                mods = [mod for mod in local_boolean_poll(context, active, hyperbevel=True, hypercut=False, other=False) if not mod.show_viewport]

            elif self.boolean_type == 'Hyper Cut':
                mods = [mod for mod in local_boolean_poll(context, active, hyperbevel=False, hypercut=True, other=False) if not mod.show_viewport]

            else:
                mods = [mod for mod in local_boolean_poll(context, active, hyperbevel=False, hypercut=False, other=True) if not mod.show_viewport]

        elif self.mode == 'APPLY' and self.alt:
            if self.boolean_type == 'Hyper Bevel':
                mods = [mod for mod in local_boolean_poll(context, active, hyperbevel=True, hypercut=False, other=False) if mod.show_viewport]

            elif self.boolean_type == 'Hyper Cut':
                mods = [mod for mod in local_boolean_poll(context, active, hyperbevel=False, hypercut=True, other=False) if mod.show_viewport]

            else:
                mods = [mod for mod in local_boolean_poll(context, active, hyperbevel=False, hypercut=False, other=True) if mod.show_viewport]

        elif self.shift:
            if self.boolean_type == 'Hyper Bevel':
                mods = local_boolean_poll(context, active, hyperbevel=True, hypercut=False, other=False)

            elif self.boolean_type == 'Hyper Cut':
                mods = local_boolean_poll(context, active, hyperbevel=False, hypercut=True, other=False)

            else:
                mods = local_boolean_poll(context, active, hyperbevel=False, hypercut=False, other=True)

        else:
            mod = active.modifiers.get(self.modname)
            mod.is_active = True

            mods = [mod]

        statemod = active.modifiers.get(self.modname)

        if self.mode == 'HIDE':
            state = statemod.object.visible_get()

            if not state:
                ensure_visibility(context, [mod.object for mod in mods])

        elif self.mode == 'WIRE':
            state = 'WIRE' if statemod.object.display_type == 'BOUNDS' else 'BOUNDS'

        elif self.mode == 'ACTIVATE':
            state = not statemod.show_viewport

        elif self.mode == 'SOLVER':
            state = 'FAST' if statemod.solver == 'EXACT' else 'EXACT'

        for mod in mods:

            if self.mode == 'HIDE':
                mobj = mod.object
                mobj.hide_set(state)

                if not state and not any([self.alt, self.shift]):
                    bpy.ops.object.select_all(action='DESELECT')

                    mobj.select_set(True)
                    context.view_layer.objects.active = mobj

                    bpy.types.MACHIN3_OT_hyper_cursor_object.last = active.name

            elif self.mode == 'WIRE':
                mod.object.display_type = state

            elif self.mode == 'ACTIVATE':
                mod.show_viewport = state

            elif self.mode == 'SOLVER':
                mod.solver = state

            elif self.mode in ['APPLY', 'REMOVE']:
                obj = mod.object

                if HC.get_addon('MESHmachine') and self.mode == 'APPLY' and self.stash_cutters:
                    MM = HC.addons['meshmachine']['module']

                    if obj.data:
                        MM.utils.stash.create_stash(active, obj)

                weld = prev_mod if (prev_mod := get_previous_mod(mod)) and prev_mod.type == 'WELD' else None

                if self.boolean_type == 'Hyper Bevel' and weld:
                    apply_mod(weld) if self.mode == 'APPLY' else remove_mod(weld)

                apply_mod(mod) if self.mode == 'APPLY' else remove_mod(mod)

                other_booleans = [mod for ob in bpy.data.objects for mod in ob.modifiers if mod.type == 'BOOLEAN' and mod.object == obj]

                if not other_booleans:

                    if self.mode == 'APPLY':
                        removable = self.get_removable_children_APPLY(context, active, obj, debug=False)

                    else:
                        removable = self.get_removable_children_REMOVE(context, active, obj, debug=False)

                    for ob in [obj] + removable:
                        remove_obj(ob)

        return {'FINISHED'}

    def get_removable_children_APPLY(self, context, active, obj, debug=False):
        removable = []

        children = obj.children_recursive

        if debug:
            print(" children")

        for ob in children:
            if debug:
                print("\n ", ob.name)

            is_removable = False

            remote_hooks = remote_hook_poll(context, ob)

            if debug:
                printd(remote_hooks, name="remote hooks", indent=3)

            if remote_hooks:
                if len(remote_hooks) == 1 and obj in remote_hooks:
                    if debug:
                        print("   > has a single remote hook, which is the to-be removed object")
                        is_removable = True
                else:
                    if debug:
                        print("   > has remote hooks, and should not be removed")

            if is_removable:
                removable.append(ob)

        orphans = [obj for obj in children if obj not in removable]

        if debug:
            print()
            print("children:", [o.name for o in children])
            print("removable:", [o.name for o in removable])
            print("orphans:", [o.name for o in orphans])
            print()

        if orphans:
            if debug:
                print("reparenting")

            hook_orphans = [o for o in orphans if remote_hook_poll(context, o)]
            other_orphans = [o for o in orphans if o not in hook_orphans]

            if debug:
                print("hook orphans:", [o.name for o in hook_orphans])
                print("other orphans:", [o.name for o in other_orphans])

            if hook_orphans and other_orphans:
                other = other_orphans[0]

                for ob in hook_orphans:
                    if debug:
                        print("", ob.name, "to", other.name)
                    parent(ob, other)

            for ob in other_orphans:
                if debug:
                    print("", ob.name, "to", active.name)
                parent(ob, active)

        return removable

    def get_removable_children_REMOVE(self, context, active, obj, debug=False):
        removable = []

        children = obj.children_recursive

        if debug:
            print(" children")

        for ob in children:
            if debug:
                print("\n ", ob.name)

            is_removable = True

            remote_booleans = remote_boolean_poll(context, ob)

            if debug:
                printd(remote_booleans, name="remote booleans", indent=3)

            if remote_booleans:
                if all(o in children for o in remote_booleans):
                    if debug:
                        print("   > has remote booleans, but can be safely removed anyway as its on other children!")
                else:
                    if debug:
                        print("   > has remote booleans, and should not be removed")
                    is_removable = False
            else:
                if debug:
                    print("   > no remote booleans, can be safely removed")

            remote_hooks = remote_hook_poll(context, ob)

            if debug:
                printd(remote_hooks, name="remote hooks", indent=3)

            if remote_hooks:
                if len(remote_hooks) == 1 and obj in remote_hooks:
                    if debug:
                        print("   > has a single remote hook, which is the to-be removed object")
                else:
                    if debug:
                        print("   > has remote hooks, and should not be removed")
                    is_removable = False
            else:
                if debug:
                    print("   > no remote hooks, can be safely removed")

            if is_removable:
                removable.append(ob)

        orphans = [obj for obj in children if obj not in removable]

        if debug:
            print()
            print("children:", [o.name for o in children])
            print("removable:", [o.name for o in removable])
            print("orphans:", [o.name for o in orphans])
            print()

        if orphans:
            if debug:
                print("reparenting")

            hook_orphans = [o for o in orphans if remote_hook_poll(context, o)]
            other_orphans = [o for o in orphans if o not in hook_orphans]

            if debug:
                print("hook orphans:", [o.name for o in hook_orphans])
                print("other orphans:", [o.name for o in other_orphans])

            if hook_orphans and other_orphans:
                other = other_orphans[0]

                for ob in hook_orphans:
                    if debug:
                        print("", ob.name, "to", other.name)
                    parent(ob, other)

            for ob in other_orphans:
                if debug:
                    print("", ob.name, "to", active.name)
                parent(ob, active)

        return removable

class ChangeEdgeBevel(bpy.types.Operator):
    bl_idname = "machin3.change_edge_bevel"
    bl_label = "MACHIN3: Change Edge Bevel"
    bl_options = {'REGISTER', 'UNDO'}

    modname: StringProperty(name="Modifier Name")

    mode: StringProperty(name="Change Bevel Mode", default='ACTIVATE')
    alt: BoolProperty(name="Alt key is pressed")
    shift: BoolProperty(name="Shift key is pressed")

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            if active:
                return edgebevel_poll(context, active)

    @classmethod
    def description(cls, context, properties):
        if properties:
            modname = f"{properties.modname}"
            mode = f"{properties.mode}"

            if mode == 'ACTIVATE':
                desc = f"Toggle {modname}'s VIewport Visibility"

            elif mode in ['APPLY', 'REMOVE']:
                desc = f"{mode.title()} {modname}"

            desc += "\nSHIFT: Affect all Modifiers"

            if mode in ['APPLY']:
                desc += "\nALT: Affect Active Modifiers"

            elif mode in ['REMOVE']:
                desc += "\nALT: Affect Inactive Modifiers"

            return desc
        return "Invalid Context"

    def invoke(self, context, event):
        self.alt = event.alt
        self.shift = event.shift
        return self.execute(context)

    def execute(self, context):
        active = context.active_object

        if self.mode == 'REMOVE' and self.alt:
            mods = [mod for mod in edgebevel_poll(context) if not mod.show_viewport]

        elif self.mode == 'APPLY' and self.alt:
            mods = [mod for mod in edgebevel_poll(context) if mod.show_viewport]

        elif self.shift:
            mods = edgebevel_poll(context)

        else:
            mod = active.modifiers.get(self.modname)
            mod.is_active = True

            mods = [mod]

        statemod = active.modifiers.get(self.modname)

        if self.mode == 'ACTIVATE':
            state = not statemod.show_viewport

        for mod in mods:

            if self.mode == 'ACTIVATE':
                mod.show_viewport = state

            elif self.mode in ['APPLY', 'REMOVE']:
                vgroupname = mod.vertex_group

                if self.mode == 'APPLY':

                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.object.mode_set(mode='OBJECT')

                    apply_mod(mod)

                elif self.mode == 'REMOVE':
                    remove_mod(mod)

                if vgroupname:
                    vgroup = active.vertex_groups.get(vgroupname)

                    active.vertex_groups.remove(vgroup)

        return {'FINISHED'}

class ChangeSolidify(bpy.types.Operator):
    bl_idname = "machin3.change_solidify"
    bl_label = "MACHIN3: Change Solidify"
    bl_options = {'REGISTER', 'UNDO'}

    modname: StringProperty(name="Modifier Name")

    mode: StringProperty(name="Change Solidify Mode", default='HIDE')
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            if active:
                return solidify_poll(context, active)

    @classmethod
    def description(cls, context, properties):
        if properties:
            return f"{properties.mode.title()} Solidify modifier"
        return "Invalid Context"

    def invoke(self, context, event):
        active = context.active_object

        mod = active.modifiers.get(self.modname)
        mod.is_active = True

        if self.mode == 'ACTIVATE':
            mod.show_viewport = not mod.show_viewport

        elif self.mode in ['APPLY', 'REMOVE']:
            if self.mode == 'APPLY':
                apply_mod(mod)

            elif self.mode == 'REMOVE':
                remove_mod(mod)

        return {'FINISHED'}

class ChangeMirror(bpy.types.Operator):
    bl_idname = "machin3.change_mirror"
    bl_label = "MACHIN3: Change Mirror"
    bl_options = {'REGISTER', 'UNDO'}

    modname: StringProperty(name="Modifier Name")

    mode: StringProperty(name="Change Mirror Mode", default='ACTIVATE')
    alt: BoolProperty(name="Alt key is pressed")
    shift: BoolProperty(name="Shift key is pressed")

    @classmethod
    def description(cls, context, properties):
        if properties:
            modname = f"{properties.modname}"
            mode = f"{properties.mode}"

            if mode == 'ACTIVATE':
                return f"Toggle {modname}'s' Viewport Visibility"
            elif mode in ['X', 'Y', 'Z']:
                return f"Toggle {modname}'s' {mode} Axis\nALT: Toggle Bisect Flip"
            elif mode in ['APPLY', 'REMOVE']:
                return f"{mode.title()} {modname}"
        return "Invalid Context"

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            if active:
                return mirror_poll(context, active)

    def invoke(self, context, event):
        self.alt = event.alt
        self.shift = event.shift

        return self.execute(context)

    def execute(self, context):
        active = context.active_object

        if self.shift:
            mods = mirror_poll(context, active)

        else:
            mod = active.modifiers.get(self.modname)
            mod.is_active = True

            mods = [mod]

        statemod = active.modifiers.get(self.modname)

        if self.mode == 'ACTIVATE':
            state = not statemod.show_viewport

        elif self.mode in ['X', 'Y', 'Z']:

            if self.alt:
                state = not statemod.use_bisect_flip_axis[axis_index_mappings[self.mode]]

            else:
                state = not statemod.use_axis[axis_index_mappings[self.mode]]

        for mod in mods:

            if self.mode == 'ACTIVATE':
                mod.show_viewport = state

            elif self.mode in ['X', 'Y', 'Z']:

                if self.alt:
                    mod.use_bisect_flip_axis[axis_index_mappings[self.mode]] = state

                    if mod.use_bisect_flip_axis[axis_index_mappings[self.mode]] and not mod.use_bisect_axis[axis_index_mappings[self.mode]]:
                        mod.use_bisect_axis[axis_index_mappings[self.mode]] = mod.use_bisect_flip_axis[axis_index_mappings[self.mode]]

                else:
                    mod.use_axis[axis_index_mappings[self.mode]] = state

            elif self.mode in ['APPLY', 'REMOVE']:

                modobj = get_mod_obj(mod)

                apply_mod(mod) if self.mode == 'APPLY' else remove_mod(mod)

                if modobj and modobj.type == 'EMPTY' and not is_mod_obj(modobj):
                    remove_obj(modobj)

        return {'FINISHED'}

class ChangeArray(bpy.types.Operator):
    bl_idname = "machin3.change_array"
    bl_label = "MACHIN3: Change Array"
    bl_options = {'REGISTER', 'UNDO'}

    modname: StringProperty(name="Modifier Name")

    mode: StringProperty(name="Change Array Mode", default='ACTIVATE')
    @classmethod
    def description(cls, context, properties):
        if properties:
            modname = f"{properties.modname}"
            mode = f"{properties.mode}"

            if mode == 'HIDE' and 'Radial' in modname:
                return f"Toggle {modname}'s Offset Object's Visibility"
            elif mode == 'ACTIVATE':
                return f"Toggle {modname}'s' Viewport Visibility"
            elif mode in ['APPLY', 'REMOVE']:
                return f"{mode.title()} {modname}"
        return "Invalid Context"

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            if active:
                return array_poll(context, active)

    def execute(self, context):
        active = context.active_object

        mod = active.modifiers.get(self.modname)
        mod.is_active = True

        if mod:

            if self.mode == 'HIDE' and 'Radial' in mod.name:
                oobj = mod.offset_object
                oobj.hide_set(oobj.visible_get())

            elif self.mode == 'ACTIVATE':
                mod.show_viewport = not mod.show_viewport

            elif self.mode in ['APPLY', 'REMOVE']:
                obj = mod.offset_object
                weld = next_mod if (next_mod := get_next_mod(mod)) and next_mod.type == 'WELD' else None

                apply_mod(mod) if self.mode == 'APPLY' else remove_mod(mod)

                if weld:
                    apply_mod(weld) if self.mode == 'APPLY' else remove_mod(weld)

                if obj and is_removable(obj):
                    remove_obj(obj)

        return {'FINISHED'}

class ChangeHyperArray(bpy.types.Operator):
    bl_idname = "machin3.change_hyper_array"
    bl_label = "MACHIN3: Change Hyper Array"
    bl_options = {'REGISTER', 'UNDO'}

    modname: StringProperty(name="Modifier Name")
    mode: StringProperty(name="Change Hyper Array Mode", default='ACTIVATE')
    @classmethod
    def description(cls, context, properties):
        if properties:
            modname = f"{properties.modname}"
            mode = f"{properties.mode}"

            if mode == 'HIDE' and 'Radial' in modname:
                return f"Toggle {modname}'s Origin Object's Visibility"
            elif mode == 'ACTIVATE':
                return f"Toggle {modname}'s' Viewport Visibility"
            elif mode in ['APPLY', 'REMOVE']:
                return f"{mode.title()} {modname}"
        return "Invalid Context"

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            if active:
                return hyper_array_poll(context, active)

    def execute(self, context):
        active = context.active_object

        mod = active.modifiers.get(self.modname)
        mod.is_active = True

        if mod:

            modobj = get_mod_input(mod, 'Origin') if is_radial_array(mod) else None

            if self.mode == 'HIDE' and modobj:
                state = not modobj.visible_get()

                if state:
                    ensure_visibility(context, modobj, select=True)

                else:
                    modobj.hide_set(True)

            elif self.mode == 'ACTIVATE':
                mod.show_viewport = not mod.show_viewport

            elif self.mode in ['APPLY', 'REMOVE']:
                weld = next_mod if (next_mod := get_next_mod(mod)) and next_mod.type == 'WELD' else None

                apply_mod(mod) if self.mode == 'APPLY' else remove_mod(mod)

                if weld:
                    apply_mod(weld) if self.mode == 'APPLY' else remove_mod(weld)

                if modobj and is_removable(modobj):
                    remove_obj(modobj)

        return {'FINISHED'}

class ChangeOther(bpy.types.Operator):
    bl_idname = "machin3.change_other"
    bl_label = "MACHIN3: Change Other"
    bl_options = {'REGISTER', 'UNDO'}

    modname: StringProperty(name="Modifier Name")
    mode: StringProperty(name="Change Modifier Mode", default='HIDE')
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            if active:
                return other_poll(context, active)

    @classmethod
    def description(cls, context, properties):
        if properties:
            modname = f"{properties.modname}"
            mode = f"{properties.mode}"

            if mode == 'ACTIVATE':
                desc = f"Toggle {modname}'s VIewport Visibility"

            elif mode in ['APPLY', 'REMOVE']:
                desc = f"{mode.title()} {modname}"

            desc += "\nSHIFT: Affect all Modifiers"

            if mode in ['APPLY']:
                desc += "\nALT: Affect Active Modifiers"

            elif mode in ['REMOVE']:
                desc += "\nALT: Affect Inactive Modifiers"

            return desc
        return "Invalid Context"

    def invoke(self, context, event):
        self.alt = event.alt
        self.shift = event.shift
        return self.execute(context)

    def execute(self, context):
        active = context.active_object

        if self.mode == 'REMOVE' and self.alt:
            mods = [mod for mod in other_poll(context) if not mod.show_viewport]

        elif self.mode == 'APPLY' and self.alt:
            mods = [mod for mod in other_poll(context) if mod.show_viewport]

        elif self.shift:
            mods = other_poll(context)

        else:
            mod = active.modifiers.get(self.modname)
            mod.is_active = True

            mods = [mod]

        statemod = active.modifiers.get(self.modname)

        if self.mode == 'ACTIVATE':
            state = not statemod.show_viewport

        for mod in mods:

            if self.mode == 'ACTIVATE':
                mod.show_viewport = state

            elif self.mode in ['APPLY', 'REMOVE']:
                if self.mode == 'APPLY':
                    apply_mod(mod)

                elif self.mode == 'REMOVE':
                    remove_mod(mod)

        return {'FINISHED'}

class ChangeBackup(bpy.types.Operator):
    bl_idname = "machin3.change_backup"
    bl_label = "MACHIN3: Change Backup"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty()
    index: IntProperty()
    mode: StringProperty(name="Mode", default='REMOVE')
    remove_all: BoolProperty(name="Remove All Backups", default=False)
    vanish_active: EnumProperty(name="Vanish the Active Object", description="Delete or Hide the Active when recovering Backup", items=backup_vanish_active_items, default='REMOVE')
    avoid_update: BoolProperty()

    @classmethod
    def poll(cls, context):
        return False

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        if self.mode == 'RECOVER':
            row = column.row(align=True)
            row.prop(self, 'hide_active', toggle=True)
            row.prop(self, 'delete_active', toggle=True)

    @classmethod
    def description(cls, context, properties):
        if properties:
            desc = f"{properties.mode.title()} Backup '{properties.name}'"

            if properties.mode == 'REMOVE':
                desc += "\nALT: Remove all Backups at once"

            elif properties.mode == 'RECOVER':
                desc += "\nALT: Hide Active instead of Removing it"

            return desc
        return "Invalid Context"

    def invoke(self, context, event):
        if self.mode == 'REMOVE':
            self.remove_all = event.alt

        elif self.mode == 'RECOVER':
            self.vanish_active = 'HIDE' if event.alt else 'REMOVE'

        return self.execute(context)

    def execute(self, context):
        active = context.active_object
        backupCOL = active.HC.backupCOL

        if self.mode == 'REMOVE':
            if self.remove_all:
                backupCOL.clear()
            else:
                backupCOL.remove(self.index)

            bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

        elif self.mode in ['RECOVER']:
            bc = backupCOL[self.index]
            collection = bc.collection

            if collection:
                if self.mode == 'RECOVER':

                    bpy.ops.object.select_all(action='DESELECT')

                    context.scene.collection.children.link(collection)

                    backupobj = bc.active

                    context.view_layer.objects.active = backupobj

                    for obj in collection.objects:
                        obj.select_set(True)

                    bpy.ops.object.duplicate()

                    recoveredobj = context.active_object

                    for obj in context.selected_objects:
                        for col in active.users_collection:
                            col.objects.link(obj)

                        collection.objects.unlink(obj)

                    context.scene.collection.children.unlink(collection)

                    selected = [obj for obj in context.selected_objects if obj != recoveredobj]

                    for obj in selected:
                        if obj.parent:
                            if is_wire_object(obj):
                                obj.hide_set(True)
                            else:
                                obj.select_set(False)

                    tree = []
                    remove = []

                    get_object_tree(active, obj_tree=tree, include_hidden=('COLLECTION'))

                    for obj in tree + [active]:
                        if self.vanish_active == 'HIDE':
                            if obj.visible_get():
                                obj.hide_set(True)

                        elif self.vanish_active == 'REMOVE':
                            remove.append(obj)

                    if remove:
                        bpy.data.batch_remove(remove)
                        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

        return {'FINISHED'}
