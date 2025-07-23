import bpy

def add_vgroup(obj, name="", ids=[], weight=1, debug=False):
    vgroup = obj.vertex_groups.new(name=name)

    if debug:
        print("INFO: Created new vertex group: %s" % (name))

    if ids:
        vgroup.add(ids, weight, "ADD")

    else:
        obj.vertex_groups.active_index = vgroup.index
        bpy.ops.object.vertex_group_assign()

    return vgroup

def get_vgroup_index(obj, vgname):
    if vgname in obj.vertex_groups:
        return [vg.name for vg in obj.vertex_groups].index(vgname)
