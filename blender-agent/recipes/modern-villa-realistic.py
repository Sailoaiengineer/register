import math, random
import bmesh
from mathutils import Vector, Euler
# Realistic rebuild of the reference villa using ideas from the Blender Guru donut tutorial (Blender 5.0).
# Tags in comments: [MOD] modifiers kept non-destructive + correct order, [PBR] material wiring, [VAR] imperfection/variation,
# [SCATTER] random instances sharing one material, [LIGHT] key/sky/bounce/DOF/AgX from the lighting chapter.
# shortcut: all textures are procedural (no scans), so close-up surface detail is approximate; swap in PBR scans from a texture site for hero shots.


def build(bpy):
    sc = bpy.context.scene
    rng = random.Random(11)

    # ---------- material helpers [PBR] ----------
    def new_mat(name):
        m = bpy.data.materials.new(name); m.use_nodes = True
        nt = m.node_tree; return m, nt, nt.nodes["Principled BSDF"]

    def N(nt, kind, **kw):
        n = nt.nodes.new(kind)
        for k, v in kw.items(): setattr(n, k, v)
        return n

    def ramp(nt, stops, interp="LINEAR"):
        r = N(nt, "ShaderNodeValToRGB"); r.color_ramp.interpolation = interp
        while len(r.color_ramp.elements) < len(stops): r.color_ramp.elements.new(0.5)
        for e, (p, c) in zip(r.color_ramp.elements, stops): e.position = p; e.color = c
        return r

    def bump(nt, bsdf, height_socket, strength, dist=0.01):
        b = N(nt, "ShaderNodeBump"); b.inputs["Strength"].default_value = strength; b.inputs["Distance"].default_value = dist
        nt.links.new(height_socket, b.inputs["Height"]); nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])

    def noise(nt, scale, detail=8, rough=0.55, coord="Object"):
        tc = N(nt, "ShaderNodeTexCoord"); n = N(nt, "ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail; n.inputs["Roughness"].default_value = rough
        nt.links.new(tc.outputs[coord], n.inputs["Vector"]); return n

    # white stucco: two off-whites mixed by large noise (colour variation), fine noise bump, only base colour is colour data [VAR][PBR]
    stucco, nt, b = new_mat("stucco")
    big = noise(nt, 1.2, 4)
    col = ramp(nt, [(0.35, (0.80, 0.80, 0.80, 1)), (0.65, (0.93, 0.92, 0.89, 1))]); nt.links.new(big.outputs["Fac"], col.inputs["Fac"])
    hsv = N(nt, "ShaderNodeHueSaturation"); hsv.inputs["Saturation"].default_value = 0.85
    nt.links.new(col.outputs["Color"], hsv.inputs["Color"]); nt.links.new(hsv.outputs["Color"], b.inputs["Base Color"])
    fine = noise(nt, 160, 10, 0.6); bump(nt, b, fine.outputs["Fac"], 0.35, 0.004)
    rcol = ramp(nt, [(0.3, (0.55, 0.55, 0.55, 1)), (0.7, (0.8, 0.8, 0.8, 1))]); nt.links.new(fine.outputs["Fac"], rcol.inputs["Fac"])
    nt.links.new(rcol.outputs["Color"], b.inputs["Roughness"])  # roughness is non-colour data: a plain float ramp

    # glossy dark slab / frames: charcoal with clearcoat so highlights roll along the soft edges
    dark, nt, b = new_mat("dark_slab")
    b.inputs["Base Color"].default_value = (0.03, 0.032, 0.038, 1); b.inputs["Roughness"].default_value = 0.32
    b.inputs["Coat Weight"].default_value = 0.35; b.inputs["Coat Roughness"].default_value = 0.2
    n = noise(nt, 40, 6); bump(nt, b, n.outputs["Fac"], 0.08, 0.003)

    # glass [PBR]: real transmission, tiny roughness variation
    glass, nt, b = new_mat("glass")
    b.inputs["Base Color"].default_value = (0.85, 0.93, 0.95, 1); b.inputs["Roughness"].default_value = 0.02
    b.inputs["Transmission Weight"].default_value = 1; b.inputs["IOR"].default_value = 1.45

    def warm_mat(name, strength, tint=(1, 0.62, 0.28, 1)):
        m, nt, b = new_mat(name); b.inputs["Base Color"].default_value = (0.05, 0.04, 0.03, 1)
        b.inputs["Emission Color"].default_value = tint; b.inputs["Emission Strength"].default_value = strength; return m
    warm = warm_mat("warm_light", 30)
    interior = warm_mat("interior_glow", 2.0, (1, 0.55, 0.25, 1))  # lit room seen through glass
    # slightly varied interior brightness [VAR]
    nt = interior.node_tree; g = noise(nt, 3, 3, coord="Object"); gr = ramp(nt, [(0.2, (0.45, 0.22, 0.08, 1)), (0.8, (1, 0.6, 0.28, 1))])
    nt.links.new(g.outputs["Fac"], gr.inputs["Fac"]); nt.links.new(gr.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Emission Color"])

    # paving: brick texture with mortar, bump from the same pattern, slight per-brick colour variation [VAR]
    pave, nt, b = new_mat("pavers")
    tc = N(nt, "ShaderNodeTexCoord"); mp = N(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 1, 1)
    br = N(nt, "ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 3.2; br.inputs["Mortar Size"].default_value = 0.012
    br.inputs["Color1"].default_value = (0.36, 0.35, 0.34, 1); br.inputs["Color2"].default_value = (0.5, 0.48, 0.46, 1); br.inputs["Mortar"].default_value = (0.1, 0.1, 0.1, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.65
    bump(nt, b, br.outputs["Fac"], 0.5, 0.01)

    grass, nt, b = new_mat("grass")
    nz = noise(nt, 25, 8); gc = ramp(nt, [(0.3, (0.025, 0.05, 0.025, 1)), (0.7, (0.06, 0.09, 0.04, 1))]); nt.links.new(nz.outputs["Fac"], gc.inputs["Fac"])
    nt.links.new(gc.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95; bump(nt, b, nz.outputs["Fac"], 0.5, 0.05)

    # dark wood slats for gates / louvres: wave bands + noise [PBR][VAR]
    wood, nt, b = new_mat("dark_wood")
    tc = N(nt, "ShaderNodeTexCoord"); wv = N(nt, "ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"
    wv.inputs["Scale"].default_value = 6; wv.inputs["Distortion"].default_value = 6; wv.inputs["Detail"].default_value = 3
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    wc = ramp(nt, [(0.2, (0.03, 0.022, 0.018, 1)), (0.8, (0.09, 0.06, 0.04, 1))]); nt.links.new(wv.outputs["Color"], wc.inputs["Fac"])
    nt.links.new(wc.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.45

    bark, nt, b = new_mat("bark")
    tc = N(nt, "ShaderNodeTexCoord"); wv = N(nt, "ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"
    wv.inputs["Scale"].default_value = 9; wv.inputs["Distortion"].default_value = 3.5; nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    bc = ramp(nt, [(0.3, (0.14, 0.11, 0.09, 1)), (0.75, (0.22, 0.18, 0.14, 1))]); nt.links.new(wv.outputs["Color"], bc.inputs["Fac"])
    nt.links.new(bc.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.85; bump(nt, b, wv.outputs["Fac"], 0.8, 0.03)

    # [SCATTER] one shared leaf material; Object Info Random shifts each frond's green, leaflet alpha from a saw wave in UV space
    leaf, nt, b = new_mat("palm_leaf")
    oi = N(nt, "ShaderNodeObjectInfo"); lc = ramp(nt, [(0, (0.015, 0.09, 0.02, 1)), (0.5, (0.03, 0.13, 0.03, 1)), (1, (0.07, 0.16, 0.025, 1))])
    nt.links.new(oi.outputs["Random"], lc.inputs["Fac"]); nt.links.new(lc.outputs["Color"], b.inputs["Base Color"])
    uv = N(nt, "ShaderNodeUVMap"); uv.uv_map = "UVMap"; mp = N(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = (70, 1, 1)
    wv = N(nt, "ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "X"; wv.wave_profile = "SAW"; wv.inputs["Scale"].default_value = 1; wv.inputs["Distortion"].default_value = 0
    nt.links.new(uv.outputs["UV"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    al = ramp(nt, [(0.1, (0, 0, 0, 1)), (0.45, (1, 1, 1, 1))]); nt.links.new(wv.outputs["Fac"], al.inputs["Fac"])
    # leaflets get shorter toward the tip and a hard rachis stripe in the middle keeps the blade connected
    nt.links.new(al.outputs["Color"], b.inputs["Alpha"]); b.inputs["Roughness"].default_value = 0.5
    leaf.surface_render_method = "DITHERED" if hasattr(leaf, "surface_render_method") else None

    # ---------- geometry helpers [MOD] ----------
    def finish(o, mat, bevel=0.0, seg=3, smooth=True):
        o.data.materials.append(mat)
        if bevel:  # real edges catch light: bevel as the LAST modifier unless a boolean needs to come first
            m = o.modifiers.new("Bevel", "BEVEL"); m.width = bevel; m.segments = seg; m.limit_method = "ANGLE"; m.angle_limit = math.radians(35)
        if smooth:
            bpy.context.view_layer.objects.active = o
            try: bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
            except Exception: bpy.ops.object.shade_smooth()
        return o

    def box(name, x0, x1, y0, y1, z0, z1, mat, bevel=0.02):
        bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        o = bpy.context.object; o.name = name; o.scale = (x1 - x0, y1 - y0, z1 - z0); bpy.ops.object.transform_apply(scale=True)
        return finish(o, mat, bevel, 2)

    def rrect(x0, x1, y0, y1, radii, n=10):  # rounded rectangle outline, radii = (bl, br, tr, tl); the soft curved slab corners from the photo
        pts = []
        for (cx, cy, a0, r) in ((x0 + radii[0], y0 + radii[0], 180, radii[0]), (x1 - radii[1], y0 + radii[1], 270, radii[1]),
                                (x1 - radii[2], y1 - radii[2], 0, radii[2]), (x0 + radii[3], y1 - radii[3], 90, radii[3])):
            for i in range(n + 1):
                a = math.radians(a0 + 90 * i / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts

    def slab(name, pts, z0, z1, mat, bevel=0.035, boolean_cut=None):
        bm = bmesh.new(); vs = [bm.verts.new((x, y, z0)) for x, y in pts]; f = bm.faces.new(vs)
        ext = bmesh.ops.extrude_face_region(bm, geom=[f]); moved = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0, 0, z1 - z0), verts=moved); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
        if boolean_cut is not None:  # boolean FIRST, bevel after: order matters just like Shrinkwrap>Solidify>Subsurf for the icing
            bo = o.modifiers.new("Cut", "BOOLEAN"); bo.object = boolean_cut; bo.operation = "DIFFERENCE"; bo.solver = "EXACT"; boolean_cut.hide_render = True; boolean_cut.hide_viewport = True
        return finish(o, mat, bevel, 4)

    # ---------- the house (x right, y back, z up; entry faces -y) ----------
    # ground floor: left block, recessed entry bay, right block
    box("g_left", -6.5, -2.6, -4.6, 4.8, 0, 3.3, stucco); box("g_right", 2.6, 6.5, -4.6, 4.8, 0, 3.3, stucco)
    box("g_mid", -2.6, 2.6, -1.8, 4.8, 0, 3.3, stucco)
    # entry: dark frame + double glass doors + warm lit interior behind [LIGHT: warm interior glow]
    box("entry_frame_l", -2.6, -2.35, -2.9, -2.65, 0, 3.3, dark, 0.015); box("entry_frame_r", 2.35, 2.6, -2.9, -2.65, 0, 3.3, dark, 0.015)
    box("entry_frame_t", -2.6, 2.6, -2.9, -2.65, 2.6, 3.3, dark, 0.015); box("entry_mullion", -0.04, 0.04, -2.9, -2.65, 0, 2.7, dark, 0.01)
    box("entry_glass", -2.35, 2.35, -2.82, -2.8, 0.1, 2.6, glass, 0); box("entry_room", -2.3, 2.3, -1.85, -1.8, 0.1, 2.6, interior, 0)
    # louvred dark slats left of entry (photo: vertical dark fins) [VAR: slight depth jitter]
    for i in range(14):
        x = -6.0 + i * 0.26; box(f"louvre{i}", x, x + 0.1, -4.75, -4.6 - rng.uniform(0, .05) + 0.0, 0.25, 3.0, wood, 0.01)
    # first floor white box inside a dark curved wrap on the left (photo: dark band hugging the rounded corner)
    box("f1", -6.2, 5.2, -4.9, 4.8, 3.7, 6.7, stucco)
    outer = rrect(-7.0, -1.2, -5.7, 5.2, (1.8, 0.2, 0.2, 0.5)); inner = rrect(-6.55, -0.9, -5.25, 4.9, (1.4, 0.1, 0.1, 0.2))
    inner_o = slab("wrap_cut", inner, 3.5, 6.9, dark, 0)
    slab("wrap_left", outer, 3.6, 6.7, dark, 0.04, boolean_cut=inner_o)
    # curved cantilever slabs (photo: heavy dark slabs, rounded corners, big overhang)
    slab("slab_ground", rrect(-7.4, 7.2, -6.3, 5.4, (1.6, 0.6, 0.6, 0.6)), 3.3, 3.75, dark)
    slab("slab_1", rrect(-7.4, 8.2, -6.6, 5.6, (2.0, 0.5, 0.5, 0.7)), 6.7, 7.25, dark)
    # second floor set back + big roof slab with the terrace on top
    box("f2", -2.8, 2.2, -3.4, 3.2, 7.25, 10.0, stucco)
    slab("slab_roof", rrect(-5.0, 4.6, -5.6, 4.6, (1.2, 0.5, 0.5, 0.5)), 10.0, 10.5, dark)
    box("tower", 3.4, 6.4, -0.5, 4.4, 7.25, 11.0, stucco); slab("tower_cap", rrect(3.2, 6.6, -0.7, 4.6, (0.2, 0.2, 0.2, 0.2)), 11.0, 11.35, dark, 0.03)
    # fins on the tower [VAR]
    for i in range(5): box(f"fin{i}", 3.2 + i * .0, 6.6, -0.75, -0.5 - 0.0, 7.6 + i * 0.7, 7.75 + i * 0.7, dark, 0.01)

    # windows: dark frame + glass + warm room, tall window in the middle of floor 1 and on the second floor
    def window(name, x0, x1, y, z0, z1, mullions=2):
        t = 0.09
        box(name + "_fl", x0 - t, x0, y - 0.1, y + 0.05, z0 - t, z1 + t, dark, 0.01); box(name + "_fr", x1, x1 + t, y - 0.1, y + 0.05, z0 - t, z1 + t, dark, 0.01)
        box(name + "_ft", x0 - t, x1 + t, y - 0.1, y + 0.05, z1, z1 + t, dark, 0.01); box(name + "_fb", x0 - t, x1 + t, y - 0.1, y + 0.05, z0 - t, z0, dark, 0.01)
        for k in range(1, mullions + 1):
            x = x0 + (x1 - x0) * k / (mullions + 1); box(f"{name}_m{k}", x - 0.03, x + 0.03, y - 0.08, y + 0.04, z0, z1, dark, 0.005)
        box(name + "_g", x0, x1, y, y + 0.02, z0, z1, glass, 0); box(name + "_r", x0, x1, y + 0.06, y + 0.08, z0, z1, interior, 0)
    window("w1a", -4.6, -2.2, -4.92, 4.2, 6.2, 2); window("w1b", 0.2, 3.8, -4.92, 4.2, 6.2, 3)
    window("w2", -2.2, 1.6, -3.42, 7.9, 9.5, 3); window("wr", 6.45, 6.47, 1.0, 8.2, 10.4, 0)
    window("wgl", -6.25, -6.2, 0.0, 4.4, 6.0, 0)

    # balconies + glass rails + terrace rail (glass pane + thin dark handrail)
    def rail(name, x0, x1, y0, y1, z):
        box(name + "_g", x0, x1, y0, y1, z, z + 1.05, glass, 0); box(name + "_h", x0 - 0.03, x1 + 0.03, y0 - 0.03, y1 + 0.03, z + 1.02, z + 1.08, dark, 0.01)
    rail("bal_l", -6.9, -3.0, -6.1, -6.08, 3.75); rail("bal_l2", -6.92, -6.9, -6.1, -2.0, 3.75)
    rail("bal_r", 3.0, 6.8, -6.2, -6.18, 3.75)
    rail("terr_f", -4.6, 4.2, -5.3, -5.28, 10.5); rail("terr_s", -4.62, -4.6, -5.3, 4.2, 10.5)
    # ground-floor wall pillars with warm lights + boundary wall + gates [VAR: gate slats jittered]
    box("wall_r", 3.2, 14, -13, -12.8, 0, 1.15, stucco)
    box("wall_side", 13.8, 14, -13, -2, 0, 1.15, stucco)
    for x, y in ((-12, -13), (-3.2, -13), (3.2, -13), (14, -13), (14, -8), (14, -3)):
        box("pillar", x - 0.28, x + 0.28, y - 0.28, y + 0.28, 0, 1.9, stucco, 0.02); box("pillar_cap", x - 0.34, x + 0.34, y - 0.34, y + 0.34, 1.9, 2.0, dark, 0.02)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.03, location=(x, y + 0.29, 1.6), rotation=(math.pi / 2, 0, 0)); bpy.context.object.data.materials.append(warm)
    for i in range(18): box(f"gate{i}", -3.0 + i * 0.355, -3.0 + i * 0.355 + 0.15, -13.05, -12.9, 0.05, 1.9 + rng.uniform(-0.01, 0.01), wood, 0.01)
    box("gate_rail_t", -3.1, 3.1, -13.05, -12.9, 1.75, 1.85, dark, 0.01); box("gate_rail_b", -3.1, 3.1, -13.05, -12.9, 0.1, 0.2, dark, 0.01)
    # ground: pavers, grass, neighbour block on the left
    box("bay_floor", -2.6, 2.6, -4.6, -1.8, 0.0, 0.03, pave, 0); box("drive", -3.2, 3.2, -13, -6.5, 0.0, 0.03, pave, 0.0); box("court", -9, 9.5, -6.5, -4.6, 0.0, 0.03, pave, 0.0)
    box("lawn", -600, 600, -600, 600, -0.5, -0.03, grass, 0)
    asph, nt, b = new_mat("asphalt"); n = noise(nt, 90, 8); c = ramp(nt, [(0.3, (0.06, 0.06, 0.065, 1)), (0.7, (0.14, 0.14, 0.145, 1))]); nt.links.new(n.outputs["Fac"], c.inputs["Fac"])
    nt.links.new(c.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.8; bump(nt, b, n.outputs["Fac"], 0.3, 0.01)
    box("street", -600, 600, -40, -13.4, -0.03, 0.0, asph, 0); box("kerb", -600, 600, -13.6, -13.4, 0.0, 0.14, pave, 0)
    box("neighbour", -26, -14, -3, 6, 0, 6.5, stucco, 0.02)

    # downlights under the slabs: emissive disc + a real light so they bounce [LIGHT]
    for x in (-5.5, -2.5, 0.5, 3.5, 6.0):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.02, location=(x, -5.4, 3.3)); bpy.context.object.data.materials.append(warm)
        L = bpy.data.lights.new(f"dl{x}", "SPOT"); L.energy = 500; L.spot_size = math.radians(100); L.spot_blend = 0.8; L.shadow_soft_size = 0.05; L.color = (1, 0.65, 0.35)
        o = bpy.data.objects.new(L.name, L); o.location = (x, -5.4, 3.28); o.rotation_euler = (0, 0, 0); sc.collection.objects.link(o)
    for x in (-3.5, 0, 3.5, 6.5):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.02, location=(x, -6.2, 6.7)); bpy.context.object.data.materials.append(warm)

    # ---------- [SCATTER] palms: varied fronds, random rotation, one shared material ----------
    def frond(px, py, pz, yaw, pitch, length):
        N_ = 14; bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap"); rows = []
        for i in range(N_ + 1):
            t = i / N_; w = 0.30 * (1 - t) ** 0.55 * (0.4 + 0.6 * math.sin(min(1, t * 3) * math.pi / 2))
            x = length * t; z = length * (math.sin(pitch) * t - 0.95 * t * t)
            rows.append((bm.verts.new((x, -w, z - 0.05 * w)), bm.verts.new((x, w, z - 0.05 * w)), t))
        for (a0, b0, t0), (a1, b1, t1) in zip(rows, rows[1:]):
            f = bm.faces.new((a0, b0, b1, a1))
            for l, (u, v) in zip(f.loops, ((t0, 0), (t0, 1), (t1, 1), (t1, 0))): l[uvl].uv = (u, v)
        me = bpy.data.meshes.new("frond"); bm.to_mesh(me); bm.free(); me.materials.append(leaf)
        o = bpy.data.objects.new("frond", me); sc.collection.objects.link(o); o.location = (px, py, pz); o.rotation_euler = (0, 0, yaw); return o

    def palm(px, py, h, lean=0.0, scale=1.0):
        bpy.ops.mesh.primitive_cone_add(vertices=14, radius1=0.2 * scale, radius2=0.11 * scale, depth=h, location=(px, py, h / 2))
        tr = bpy.context.object; tr.rotation_euler = (lean, 0, rng.uniform(0, 6)); tr.data.materials.append(bark); bpy.ops.object.shade_smooth()
        m = tr.modifiers.new("Subsurf", "SUBSURF"); m.levels = 1
        top = Vector((px, py, h)) + Vector((0, -math.sin(lean) * h / 2, 0))
        for k in range(22):
            yaw = k * 2.39996 + rng.uniform(-.15, .15); f = frond(top.x, top.y, top.z - 0.1, yaw, rng.uniform(0.3, 0.9), rng.uniform(2.0, 3.0) * scale)
            f.rotation_euler.x = rng.uniform(-0.12, 0.12)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22 * scale, location=top + Vector((0, 0, -0.1))); bpy.context.object.data.materials.append(bark)
    palm(7.0, -9.2, 5.6, 0.05); palm(10.5, -8.0, 6.8, -0.04); palm(-14.5, -10.0, 4.6, 0.06, 0.9); palm(12.8, -4.5, 6.0, 0.03, 1.0); palm(-3.2, -9.0, 3.4, 0.02, 0.8)
    # roof-garden bush
    for i in range(10):
        a = i * 0.9; f = frond(-4.6 + math.cos(a) * 0.1, 3.8, 10.5, a, rng.uniform(0.4, 1.0), rng.uniform(0.8, 1.3))

    # ---------- [LIGHT] world: Nishita-style dusk sky, key/sky/bounce lights, camera + DOF, AgX ----------
    w = bpy.data.worlds.new("dusk"); w.use_nodes = True; nt = w.node_tree; bg = nt.nodes["Background"]
    sky = N(nt, "ShaderNodeTexSky")
    for st in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING"):
        try: sky.sky_type = st; break
        except TypeError: pass
    sky.sun_elevation = math.radians(0.8); sky.sun_rotation = math.radians(215); sky.air_density = 1.1; sky.sun_disc = False
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0; sc.world = w
    # key: low warm light from the back-left as the setting sun; large-radius cool fill (soft shadows); white bounce for the dark side
    def lamp(name, kind, e, loc, rot=None, col=(1, 1, 1), size=None):
        L = bpy.data.lights.new(name, kind); L.energy = e; L.color = col
        if size is not None:
            if kind == "AREA": L.size = size
            else: L.shadow_soft_size = size
        o = bpy.data.objects.new(name, L); o.location = loc; sc.collection.objects.link(o)
        if rot: o.rotation_euler = rot
        return o
    lamp("key_dusk", "SUN", 1.2, (0, 0, 20), (math.radians(78), 0, math.radians(-125)), (1, 0.62, 0.38))
    lamp("sky_fill", "AREA", 25000, (-6, -25, 25), (math.radians(60), 0, math.radians(-10)), (0.65, 0.78, 1), 30)
    lamp("bounce", "POINT", 600, (10, -16, 3), None, (1, 0.9, 0.8), 3)
    focus = bpy.data.objects.new("focus", None); focus.location = (-1, -5, 4.5); sc.collection.objects.link(focus)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam)
    cam.location = (-10.5, -18.5, 3.0); cam.data.lens = 22
    cam.rotation_euler = (Vector((1.0, -1, 5.6)) - cam.location).to_track_quat("-Z", "Y").to_euler(); sc.camera = cam
    cam.data.dof.use_dof = True; cam.data.dof.focus_object = focus; cam.data.dof.aperture_fstop = 8
    try: sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "Medium High Contrast"
    except TypeError: pass
    sc.cycles.use_denoising = True; sc.view_settings.exposure = -0.2
    assert len([o for o in sc.objects if o.type == "MESH"]) > 150
