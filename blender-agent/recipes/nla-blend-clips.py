def build(bpy):
    # two clips pushed to NLA tracks with a blend-in, the non-destructive layering from the tutorial
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
    ob = bpy.context.object
    ad = ob.animation_data_create()
    def clip(name, a, b, start):
        ob.location = a; ob.keyframe_insert("location", frame=1)
        ob.location = b; ob.keyframe_insert("location", frame=20)
        act = ad.action; act.name = name
        tr = ad.nla_tracks.new(); st = tr.strips.new(name, start, act)
        ad.action = None
        return st
    run = clip("run", (-3, 0, 0.5), (0, 0, 0.5), 1)
    jump = clip("jump", (0, 0, 0.5), (3, 0, 2.5), 15)  # overlaps run by 5 frames
    jump.blend_in = 5
    assert len(ad.nla_tracks) == 2 and jump.blend_in == 5
    bpy.context.scene.frame_set(18)
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
