import mathutils
def build(bpy):
    # weapon follows the hand bone via Child Of; the other hand is pinned to the weapon with IK to an empty
    arm = bpy.data.objects.new("Rig", bpy.data.armatures.new("Rig")); bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    up = eb.new("upper"); up.head, up.tail = (0, 0, 1), (0, 0, 2)
    fo = eb.new("fore"); fo.head, fo.tail = (0, 0, 2), (0.6, 0, 2.6); fo.parent = up; fo.use_connect = True
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0)); gun = bpy.context.object; gun.scale = (0.1, 0.1, 0.6)
    c = gun.constraints.new("CHILD_OF"); c.target, c.subtarget = arm, "fore"
    bpy.ops.object.empty_add(location=(0.9, 0, 2.2)); tgt = bpy.context.object  # stands in for the weapon grip
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    ik = arm.pose.bones["fore"].constraints.new("IK"); ik.target = tgt; ik.chain_count = 2
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.update()
    bpy.ops.mesh.primitive_plane_add(size=10)
    tip = (arm.matrix_world @ arm.pose.bones["fore"].tail)
    assert (tip - tgt.location).length < 0.1, f"IK tip {tip} missed target"
