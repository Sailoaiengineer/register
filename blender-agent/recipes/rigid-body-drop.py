# Overview video: rigid body = gravity + collisions. Active cubes fall onto a passive floor; we step frames in order (the cache needs it) and assert they settled.
def build(bpy):
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=12); fl = bpy.context.object; bpy.ops.rigidbody.object_add(type="PASSIVE")
    cubes = []
    for i, (x, z) in enumerate(((0, 3), (0.2, 5), (-0.3, 7))):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0.1 * i, z), rotation=(0.4 * i, 0.3, 0.2 * i))
        bpy.ops.rigidbody.object_add(type="ACTIVE"); bpy.context.object.rigid_body.friction = 0.7; cubes.append(bpy.context.object)
    sc.frame_start = 1
    for f in range(1, 121): sc.frame_set(f)  # sequential on purpose: simulation caches rebuild only forward
    dg = bpy.context.evaluated_depsgraph_get()
    zs = [c.evaluated_get(dg).matrix_world.translation.z for c in cubes]
    assert all(0.1 < z < 1.6 for z in zs), zs  # fell from 3-7 m and rest on or near the floor, not still falling or through it
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam)
    cam.location, cam.rotation_euler = (4, -5, 3), (1.1, 0, 0.7); sc.camera = cam
