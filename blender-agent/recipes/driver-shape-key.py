# Overview video: drivers control one parameter from another, shape keys give expressive deformation. A cube's "Stretch" shape key is driven by an empty's height.
def build(bpy):
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5)); ob = bpy.context.object; ob.shape_key_add(name="Basis")
    sk = ob.shape_key_add(name="Stretch")
    for i, v in enumerate(sk.data): v.co.z *= 3 if ob.data.vertices[i].co.z > 0 else 1  # taller top
    sk.slider_min, sk.slider_max = 0, 1
    bpy.ops.object.empty_add(location=(2, 0, 0)); ctl = bpy.context.object; ctl.name = "controller"
    fc = sk.driver_add("value"); d = fc.driver; d.type = "SCRIPTED"; d.expression = "clamp(h / 2, 0, 1)"
    var = d.variables.new(); var.name = "h"; var.type = "TRANSFORMS"
    var.targets[0].id = ctl; var.targets[0].transform_type = "LOC_Z"; var.targets[0].transform_space = "WORLD_SPACE"
    ctl.location.z = 1.5; bpy.context.view_layer.update(); sc.frame_set(2)
    assert abs(sk.value - 0.75) < 1e-3, sk.value  # driver evaluates: 1.5 / 2
    tc = ob.constraints  # constraints article: a predefined rule, easier than a driver
    bpy.ops.mesh.primitive_plane_add(size=8)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam)
    cam.location, cam.rotation_euler = (4, -5, 3), (1.1, 0, 0.7); sc.camera = cam
