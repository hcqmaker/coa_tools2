

import bpy,time
import bmesh
import json
from bpy.props import (
    FloatProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    CollectionProperty,
    FloatVectorProperty,
    EnumProperty,
    IntVectorProperty,
)
from collections import OrderedDict
from ...functions import *
import math,hashlib,time,random
from mathutils import Vector, Matrix, Quaternion, Euler
import shutil
from .texture_atlas_generator import TextureAtlasGenerator
from ... import constants


#=============
# default
#=============
animation_data = OrderedDict(
    {
        "duration": 0,
        "playTimes": 0,
        "name": "Anim Name",
        "zOrder": {},           ## z_index
        "bone": [],             ## frame bones 
        "frame": [],            ## timeline event 
        "slot": [],             ## bone frames 
        "ffd": [],              ## Shapekeys
    }
)


"""
"zOrder": {
    frame:[
        {
            duration:,
            zOrder:[]   {name:,z:}
        }
    ]
},           
"bone": [
    {
        name:,
        translateFrame:[
            {
                duration:
                x:
                y:
                curve:  [4 float]
            }
        ],
        rotateFrame:[
            {
                duration:
                curve: [4 float]
                rotate:
            }
        ],
        scaleFrame:[
            {
                duration:
                x:
                y:
                curve:  [4 float]
            }
        ]
    }
],             
"frame": [      ## timeline event
    {
        duration:frame,
        sound:,
        action:,
        events:[
            {
                name:,
                bone:,
                ints:[],
                floats:[],
                strings:[]
            }
        ]
    }
],            
"slot": [           ## sprite frames
    {
        name: slot.name
        colorFrame:[
            {
                duration:,
                tweenEasing:,
                value:[r,g,b,a],
            },
        ],
         displayFrame:[  # slot.coa_tools2.slot_index ??? untest
            {
                duration:,
                name:
                value:  
            }
        ]
    }
],             
"ffd": [        ## Shapekeys
    {
        name: slot.data.name
        slot: slot.name
        frame:[
            {
                duration:
                curve: [ 4 float]
                vertices:
            }
        ]
    }

],              

"""

#==============
# 
#==============

atlas_data = {}


bone_default_pos = {}
bone_default_rot = {}
bone_uses_constraints = {}
vert_coords_default = {}
tex_pathes = {}
img_names = {}  ### exported image names
tmp_slots_data = {}


def _in_use_constraint(pose_bone_name):
    if pose_bone_name in bone_uses_constraints and bone_uses_constraints[pose_bone_name]:
        return True
    return False

def _in_get_key():
    dt = int(time.time() * 1000 + random.random() * 1000)
    return hashlib.md5(str(dt).encode(encoding='UTF-8')).hexdigest()[:5]

def _in_get_godot_res_root(export_path):
    godot_project_file = 'project.godot'

    tmp_path = export_path
    while True:
        dest_path = os.path.join(tmp_path, godot_project_file)
        if (os.path.isfile(dest_path)):
            return tmp_path
        
        tmp_old_path = tmp_path
        tmp_path = os.path.dirname(tmp_path)
        if (tmp_path == tmp_old_path):
            break

    return ''

### get mesh vertex corrseponding uv vertex
def _in_uv_from_vert_first(uv_layer, v):
    for l in v.link_loops:
        uv_data = l[uv_layer]
        return uv_data.uv
    return None


def _in_get_sprite_image_data(sprite_data):
    # mat = sprite.active_material
    mat = sprite_data.materials[0]
    for node in mat.node_tree.nodes:
        if (
            node.type == "GROUP"
            and node.node_tree.name == constants.COA_NODE_GROUP_NAME
        ):
            links = node.inputs[0].links
            tex_node = links[0].from_node
            img = (
                tex_node.image
                if len(links) > 0 and tex_node.type == "TEX_IMAGE"
                else None
            )

    return mat, img



def _in_copy_textures(self, sprites, texture_dir_path, tmp_kv):
    global img_names
    img_names = {}
    ii_key = 1
    for sprite in sprites:
        if sprite.type == "MESH":
            imgs = []
            if sprite.coa_tools2.type == "MESH":
                if len(sprite.data.materials) > 0:
                    mat, img = _in_get_sprite_image_data(sprite.data)
                    if img != None:
                        imgs.append({"img": img, "key": sprite.data.name})
            elif sprite.coa_tools2.type == "SLOT":
                for slot in sprite.coa_tools2.slot:
                    if len(slot.mesh.materials) > 0:
                        mat, img = _in_get_sprite_image_data(slot.mesh)
                        if img != None:
                            imgs.append({"img": img, "key": slot.mesh.name})

            for data in imgs:
                img = data["img"]
                key = data["key"]

                src_path = bpy.path.abspath(img.filepath)
                img_name = os.path.basename(src_path)
                dst_path = os.path.join(texture_dir_path, img_name)

                if (img.name not in tmp_kv):
                    tmp_kv[img.name] = {"path":dst_path, "key":f"{ii_key}_{_in_get_key()}"}
                    ii_key += 1

                img_names[key] = img_name[: img_name.rfind(".")]

                if self.scene.coa_tools2.export_image_mode == "IMAGES":
                    if os.path.isfile(src_path):
                        shutil.copyfile(src_path, dst_path)
                    else:
                        img.save_render(dst_path)


def _in_get_polygons_data(sprite):
    polygons = []
    mesh = sprite.data
    for polygon in mesh.polygons:
        # polygon_vertices = [vertex for vertex in polygon.vertices]
        polygons.append(f"PackedInt32Array({join_array(polygon.vertices)})")
    return polygons


### get mesh vertex corrseponding uv vertex
def _in_uv_from_vert_first(uv_layer, v):
    for l in v.link_loops:
        uv_data = l[uv_layer]
        return uv_data.uv
    return None


### get uv information
def _in_get_uv_data(bm):
    uvs = []
    uv_layer = bm.loops.layers.uv.active

    ### first get the total dimensions of the uv
    left = 0
    top = 0
    bottom = 1
    right = 1
    for vert in bm.verts:
        uv_first = _in_uv_from_vert_first(uv_layer, vert)
        for i, val in enumerate(uv_first):
            if i == 0:
                left = max(left, val)
                right = min(right, val)
            else:
                top = max(top, val)
                bottom = min(bottom, val)
    height = top - bottom
    width = left - right
    ### get uv coordinates and map them from 0 to 1 to total dimension that have been calculated before
    for vert in bm.verts:
        uv_first = _in_uv_from_vert_first(uv_layer, vert)
        for i, val in enumerate(uv_first):
            if i == 1:
                value = -val + height
                final_value = round((value + bottom) / height, 3)
                uvs.append(final_value)
            else:
                value = val
                final_value = round((value - right) / width, 3)
                uvs.append(final_value)
    return uvs

def _in_normalize_weights(obj, armature, threshold):
    for vert in obj.data.vertices:
        weight_total = 0.0
        groups = []
        for group in vert.groups:
            vgroup = obj.vertex_groups[group.group]
            group_name = vgroup.name
            if (group.weight > threshold and armature == None) or (
                group.weight > threshold
                and armature != None
                and group_name in armature.data.bones
            ):
                groups.append(group)

        for group in groups:
            vgroup = obj.vertex_groups[group.group]
            weight_total += group.weight
        for group in groups:
            group.weight = 1 * (group.weight / weight_total)

def _in_get_sprite_image_data(sprite_data):
    # mat = sprite.active_material
    mat = sprite_data.materials[0]
    for node in mat.node_tree.nodes:
        if (
            node.type == "GROUP"
            and node.node_tree.name == constants.COA_NODE_GROUP_NAME
        ):
            links = node.inputs[0].links
            tex_node = links[0].from_node
            img = (
                tex_node.image
                if len(links) > 0 and tex_node.type == "TEX_IMAGE"
                else None
            )

    return mat, img


def _in_remove_base_sprite(obj):
    bpy.context.view_layer.objects.active = obj
    obj.hide_set(False)
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    verts = []

    if "coa_base_sprite" in obj.vertex_groups and obj.data.coa_tools2.hide_base_sprite:
        v_group_idx = obj.vertex_groups["coa_base_sprite"].index
        for i, vert in enumerate(obj.data.vertices):
            for g in vert.groups:
                if g.group == v_group_idx:
                    verts.append(bm.verts[i])
                    break

    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY", ngon_method="BEAUTY")

    bmesh.ops.delete(bm, geom=verts, context="VERTS")
    bm = bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode="OBJECT")


def _in_get_bone_with_most_influence(armature, sprite):
    vertex_groups = sprite.vertex_groups
    max_weight = 0
    bone = None
    for v_group in vertex_groups:
        if v_group.name in armature.data.bones:
            total_weight = 0
            for i, vert in enumerate(sprite.data.vertices):
                try:
                    total_weight += v_group.weight(vert.index)
                except:
                    pass
            if total_weight > max_weight:
                max_weight = float(total_weight)
                bone = armature.data.bones[v_group.name]
    return bone


### get weight data
def _in_get_bone_weight_data(self, obj, armature):
    weights = {} # {"name":,weights:[{index:,weight:}]]}

    num = len(obj.data.vertices)
    weight_data = make_array(num, "0")

    for vert in obj.data.vertices:
        tmp_groups = []
        for group in vert.groups:
            group_name = obj.vertex_groups[group.group].name
            if group_name in armature.data.bones:
                tmp_groups.append({"group": group, "group_name": group_name})

        for group in tmp_groups:
            bone_weight = round(group["group"].weight, 3)

            use_bname = group["group_name"]
            if use_bname not in weights:
                weights[use_bname] = weight_data.copy()
            weights[use_bname][vert.index] = str(bone_weight)

    return weights

def _in_get_get_mesh_center(sprite, scale):
    average_vert = Vector((0, 0, 0))
    for i, vert in enumerate(sprite.data.vertices):
        average_vert += vert.co
    average_vert /= len(sprite.data.vertices)
    pos = (sprite.matrix_world @ average_vert) * scale
    pos_2d = Vector((pos[0], pos[2]))
    return pos

def _in_get_parents(sprite):
    parents = []
    tmp_parent = sprite.parent
    while True:
        if tmp_parent is None: break
        parents.append(tmp_parent)
        tmp_parent = tmp_parent.parent
    return parents


# copy from godot-2d-bridge2\gd2db_scene_parsing.py:347
def _relative_object_transforms(sprite, scale_px):
    tmp_parents = _in_get_parents(sprite)
    world_matrix = sprite.matrix_world
    transforms = {
        "loc_offset": Vector((0, 0, 0)),
        "rot_offset": Vector((0, 0, 0)),
        "scale_offset": Vector((1, 1, 1)),
        "global_loc": world_matrix.translation,
        "global_rot": Vector(tuple(world_matrix.to_euler())),
        "global_scale": world_matrix.to_scale()
    }

    # get the sum of transforms from exported parents
    object_parents = [x for x in tmp_parents if isinstance(x, bpy.types.Object)]
    for parent in object_parents:
        transforms["loc_offset"] += parent.location
        transforms["rot_offset"] += Vector(tuple(parent.rotation_euler))
        transforms["scale_offset"] *= parent.scale

    # eliminate rounding errors
    for key in transforms.keys():
        transforms[key] = Vector((
            round(transforms[key].x, 6),
            round(transforms[key].y, 6),
            round(transforms[key].z, 6),
        ))

    # calculate transforms from their parent offsets
    location = transforms["global_loc"] - transforms["loc_offset"]
    rotation = transforms["global_rot"] - transforms["rot_offset"]
    scale = Vector((transforms["global_scale"][x] / transforms["scale_offset"][x] for x in range(3)))

    # parse the transform strings
    rlocation = [location.x * scale_px, -location.z * scale_px]
    rscale = [scale.x, scale.z]

    rrotation = -rotation.y

    return rlocation, rrotation, rscale

### get skin data
def _in_get_skin_slot(self, sprite, armature, scale, slot_data=None):
    context = bpy.context
    sprite_name = str(sprite.name)
    sprite_data_name = sprite.data.name if slot_data == None else slot_data.name

    zOrder = _in_get_z_value(self, sprite)

    ### make a sprite duplicate and make it active
    if slot_data == None:
        sprite_data = sprite.data.copy()
    else:
        sprite_data = slot_data.copy()
    sprite = sprite.copy()
    sprite.data = sprite_data
    context.collection.objects.link(sprite)
    context.view_layer.objects.active = sprite

    ### normalize weights
    _in_normalize_weights(sprite, armature, 0.0)
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            for region in area.regions:
                with bpy.context.temp_override(object=sprite, edit_object=sprite):
                    bpy.ops.object.vertex_group_clean(
                        group_select_mode="ALL", keep_single=True
                    )
    ###

    global tmp_sprites
    tmp_slots_data[sprite_data_name] = {
        "data": sprite_data,
        "object": sprite,
        "name": sprite_data_name,
    }

    ### get sprite material, texture and img data
    mat, img = _in_get_sprite_image_data(sprite_data)
    if sprite_data_name in img_names:
        tex_path = os.path.join(
            self.scene.coa_tools2.project_name + "_texture", img_names[sprite_data_name]
        )
        tex_pathes[sprite_name] = tex_path
    ### delete basesprite mesh in sprite duplicate
    _in_remove_base_sprite(sprite)

    ### get display data of a sprite
    bpy.ops.object.mode_set(mode="EDIT")
    # bm = bmesh.from_edit_mesh(sprite.data)

    ### generate display data dictionary
    display_data = OrderedDict()

    ### get general skin information
    tt_loc, tt_rot, tt_sca = _relative_object_transforms(sprite, scale)

    # print("====>", tt_loc, tt_rot, tt_sca)
    display_data["zOrder"] = zOrder
    display_data["name"] = sprite_data_name  # sprite_name

    display_data["x"] = tt_loc[0]
    display_data["y"] = tt_loc[1]

    display_data["sx"] = tt_sca[0]
    display_data["sy"] = tt_sca[1]

    display_data["rot"] = tt_rot
        
    if self.scene.coa_tools2.export_image_mode == "IMAGES":
        display_data["path"] = img_names[sprite_data_name]

    if self.scene.coa_tools2.export_image_mode == "IMAGES":
        display_data["width"] = int(img.size[0])
        display_data["height"] = int(img.size[1])
    elif self.scene.coa_tools2.export_image_mode == "ATLAS":
        display_data["width"] = atlas_data[sprite_data_name]["width"]
        display_data["height"] = atlas_data[sprite_data_name]["height"]

    if len(sprite.data.vertices) != 4:
        display_data["type"] = "mesh"

        verts = _in_get_mixed_vertex_data(sprite)
        vert_coords_default[sprite_name] = verts
        display_data["vertices"] = _in_convert_vertex_data_to_pixel_space(verts)
        display_data["polygons"] = _in_get_polygons_data(sprite)

        bm = bmesh.from_edit_mesh(sprite.data)
        display_data["uvs"] = _in_get_uv_data(bm)
        display_data["weights"] = _in_get_bone_weight_data(self, sprite, armature)
    else:
        bind_bone = _in_get_bone_with_most_influence(armature, sprite)
        sprite_center_pos = _in_get_get_mesh_center(sprite, 1.0)
        if bind_bone != None:
            sprite_pos_final = (
                bind_bone.matrix_local.inverted() @ sprite_center_pos
            ) * scale
        else:
            sprite_pos_final = sprite_center_pos * scale
            
        display_data["type"] = "sprite"

        display_data["x"] = -sprite_pos_final.x
        display_data["y"] = -sprite_pos_final.y
 
        display_data["bone"] = ''
        if (bind_bone != None):
            display_data["bone"] = bind_bone.name

   
    bpy.ops.object.mode_set(mode="OBJECT")

    # bpy.data.objects.remove(sprite,do_unlink=True)
    return display_data

def _in_get_skin_data(self, sprites, armature, scale):
    context = bpy.context

    global tex_pathes
    tex_pathes = {}

    ### skin data array
    skin_data = [{"slot": []}]

    for sprite in sprites:
        ### create slot data
        slot_data = OrderedDict()
        slot_data["name"] = sprite.name
        slot_data["display"] = []

        if sprite.type == "MESH":
            if sprite.coa_tools2.type == "MESH":
                data2 = _in_get_skin_slot(self, sprite, armature, scale)
                slot_data["display"].append(data2)
            elif sprite.coa_tools2.type == "SLOT":
                for slot in sprite.coa_tools2.slot:
                    data2 = _in_get_skin_slot(
                        self, sprite, armature, scale, slot_data=slot.mesh
                    )
                    slot_data["display"].append(data2)

            skin_data[0]["slot"].append(slot_data)
    return skin_data

edit_bone_matrices = {}

def _in_get_bone_transformation(armature, bone):
        global edit_bone_matrices
        pose_bone = armature.pose.bones[bone.name]

        edit_bone_matrix = edit_bone_matrices[bone.name]

        mat_local = pose_bone.matrix
        scale = mat_local.decompose()[2]
        scale_mat = Matrix.Identity(4)
        scale_mat[0][0] = scale[0]
        scale_mat[1][1] = scale[1]
        scale_mat[2][2] = scale[2]
        mat_local = (mat_local @ (edit_bone_matrix @ scale_mat).inverted()) @ scale_mat
        return mat_local

def _in_get_bone_bvh_matrix(armature, bone):
    pose_bone = armature.pose.bones[bone.name]
    
    trans = Matrix.Translation(bone.head_local)
    itrans = Matrix.Translation(-bone.head_local)

    if bone.parent:
        parent_bone = bone.parent
        parent_pose_bone = armature.pose.bones[bone.parent.name]

        # mat_final = dbone.parent.rest_arm_mat @ dbone.parent.pose_imat @ dbone.pose_mat @ dbone.rest_arm_imat
        # mat_final = itrans @ mat_final @ trans
        # loc = mat_final.to_translation() + (dbone.rest_bone.head_local - dbone.parent.rest_bone.head_local)
    
        mat_final = parent_bone.matrix_local @ parent_pose_bone.matrix.inverted() @ pose_bone.matrix @ bone.matrix_local.inverted()
        mat_final = itrans @ mat_final @ trans
        loc = mat_final.to_translation() + (bone.head_local - parent_bone.head_local)
    
    else:
        mat_final = pose_bone.matrix @ bone.matrix_local.inverted()
        mat_final = itrans @ mat_final @ trans
        loc = mat_final.to_translation() + bone.head

    # if not dbone.skip_position:
    #    file.write("%.6f %.6f %.6f " % (loc * global_scale)[:])

    # rot = mat_final.to_euler(dbone.rot_order_str_reverse, dbone.prev_euler)
    # rot = mat_final.to_euler()
    return mat_final

def _in_get_bone_matrix(armature, bone):
    if bone.parent != None:
        mat_local = _in_get_bone_transformation(armature,bone.parent).inverted() * _in_get_bone_transformation(armature,bone)
    else:
        mat_local = _in_get_bone_transformation(armature,bone)
    return mat_local

#########-------->>>-------------
def _in_rest_bone_location(armature, pose_bone, scale):
    edit_bone = pose_bone.bone
    position = Vector((edit_bone.head_local.x, edit_bone.head_local.z))
    if edit_bone.parent:
        parent_position = Vector((edit_bone.parent.head_local.x, edit_bone.parent.head_local.z))
    else:
        parent_position = Vector((0.0, 0.0))

    loc = position - parent_position
    return Vector((loc[0] * scale, -loc[1] * scale))

def _in_reset_bone_scale(armature, bone, relative=True):
    pose_bone = armature.pose.bones[bone.name]
    
    if bone.parent != None and not relative:
        local_mat = _in_get_bone_transformation(armature, bone.parent).inverted() * _in_get_bone_transformation(armature, bone)
    else:
        local_mat = _in_get_bone_transformation(armature, bone)
    bone_scale = local_mat.decompose()[2]
    bone_scale_2d = [bone_scale[1], bone_scale[1]]
    return bone_scale_2d

def _in_reset_bone_rotation(armature, bone, relative=True):
    pose_bone = armature.pose.bones[bone.name]
    
    if bone.parent != None and not relative:
            local_mat = _in_get_bone_transformation(armature, bone.parent).inverted() * _in_get_bone_transformation(armature, bone)
    else:
        local_mat = _in_get_bone_transformation(armature, bone)
    bone_euler_rot = local_mat.decompose()[1].to_euler()

    degrees = round(math.degrees(bone_euler_rot.y), 2)
    return -math.radians(degrees)


def _in_get_chains_num(pose_bone, num):
    tmp_parents = [x.name for x in (pose_bone.parent_recursive)]
    if num > 0:
        rs_parents = [pose_bone.name]
        for i in range(0, num-1):
            rs_parents.append(tmp_parents[i])
        return rs_parents
    if (num == 0):
        return tmp_parents
    return []


def _in_get_ik_bones_info(armature, ik_bones):
    rs_ik_info = []

    ik_dict = {} # key: target, value:{"subtarget":}
    ik_transform_dict = {}

    ik_use_types = {'COPY_LOCATION','COPY_ROTATION','COPY_SCALE'}

    for i,pose_name in enumerate(ik_bones):
        pbone = armature.pose.bones[pose_name]
        # lnum = len(pbone.constraints)

        for j,constr in enumerate(pbone.constraints):

            ctr_type = constr.type
            # ctr_target = constr.target
            ctr_subtarget = constr.subtarget

            if (ctr_type == 'IK'):
                ik_dict[ctr_subtarget] = {"bone_name":pose_name, "chain_bones":_in_get_chains_num(pbone, constr.chain_count)}
            elif ctr_type in ik_use_types:
                if (ctr_subtarget not in ik_transform_dict):
                    ik_transform_dict[ctr_subtarget] = {"bone_name":pose_name}
                if ctr_type == 'COPY_LOCATION':
                    ik_transform_dict[ctr_subtarget]['loc'] = True
                if ctr_type == 'COPY_ROTATION':
                    ik_transform_dict[ctr_subtarget]['rot'] = True
                if ctr_type == 'COPY_SCALE':
                    ik_transform_dict[ctr_subtarget]['sca'] = True

    for ik_bone_name in ik_transform_dict:
        val_tran = ik_transform_dict[ik_bone_name]
        use_ik_bone = val_tran["bone_name"]
        one_ik_info = {}
        one_ik_info["target"] = ik_bone_name
        one_ik_info["tip"] = use_ik_bone
        if (ik_bone_name in ik_dict):
            val = ik_dict[ik_bone_name]
            chain_bones = val["chain_bones"]
            chain_array = []
            for bone_name in chain_bones:
                chain_array.append(bone_name)
            if (len(chain_array) > 0):
                one_ik_info["chains"] = chain_array
                rs_ik_info.append(one_ik_info)

    return rs_ik_info


def _in_get_bone_data(self, armature, sprite_object, scale):
    bone_data = []
    
    for bone in armature.data.bones:

        pose_bone = armature.pose.bones[bone.name]
        relative = True if bone_uses_constraints[pose_bone.name] else False

        data = {}
        data["name"] = bone.name
        data['x'] = 0
        data['y'] = 0
        data["rot"] = 0
        data["length"] = int((bone.head - bone.tail).length * scale)

        ### get bone position
        pos = _in_rest_bone_location(armature, pose_bone, scale)
        data['rest_to'] = pos
        bone_default_pos[bone.name] = Vector(pos)
        if pos != Vector((0, 0)):
            data["x"] = round(pos[0], 2)
            data["y"] = round(pos[1], 2)
            
        ### get bone angle
        angle = _in_reset_bone_rotation(armature, bone, relative)
        bone_default_rot[bone.name] = angle
        if angle != 0:
            data["rot"] = round(angle, 2)

        ### get bone scale
        sca = _in_reset_bone_scale(armature, bone, relative)
    
        if bone.parent != None:
            data["parent"] = bone.parent.name
        else:
            data["parent"] = sprite_object.name

        bone_data.append(data)
    return bone_data


def _in_get_z_value(self, slot):
    return slot.coa_tools2.z_value

### LOCATION, ROTATION, SCALE, ANY
def _in_bone_key_on_frame(bone, frame, animation_data, type="LOCATION"):  

    action = animation_data.action if animation_data != None else None
    type = "." + type.lower()
    if action != None:
        if b_version_smaller_than((4, 4, 0)):
            for fcurve in action.fcurves:
                if bone.name in fcurve.data_path and (
                    type in fcurve.data_path or type == ".any"
                ):
                    for keyframe in fcurve.keyframe_points:
                        if keyframe.co[0] == frame:
                            return True
        else:
            for layer in action.layers:
                for strip in layer.strips:
                    for slot in action.slots:
                        for fcurve in strip.channelbag(slot).fcurves:
                            # if slot.name in fcurve.data_path and (
                            if bone.name in fcurve.data_path and (
                                type in fcurve.data_path or type == ".any"
                            ):
                                for keyframe in fcurve.keyframe_points:
                                    if keyframe.co[0] == frame:
                                        return True
    return False


def _in_property_key_on_frame(obj, prop_names, frame, type="PROPERTY"):
    if type == "SHAPEKEY":
        obj = obj.shape_keys

    if obj != None and obj.animation_data != None:
        ### check if property has a key set
        action = obj.animation_data.action
        if action != None:
            if b_version_smaller_than((4, 4, 0)):
                for fcurve in action.fcurves:
                    for prop_name in prop_names:
                        if prop_name in fcurve.data_path:
                            for keyframe in fcurve.keyframe_points:
                                if keyframe.co[0] == frame:
                                    return True
            else:
                for layer in action.layers:
                    for strip in layer.strips:
                        for slot in action.slots:
                            for fcurve in strip.channelbag(slot).fcurves:
                                for prop_name in prop_names:
                                    if prop_name in fcurve.data_path:
                                        for keyframe in fcurve.keyframe_points:
                                            if keyframe.co[0] == frame:
                                                return True
        ### check if property has a bone driver and bone has a key set
        for driver in obj.animation_data.drivers:
            for prop_name in prop_names:
                if prop_name in driver.data_path:
                    for var in driver.driver.variables:
                        armature = var.targets[0].id
                        if armature != None:
                            bone_target = var.targets[0].bone_target
                            if bone_target in armature.data.bones:
                                bone = armature.data.bones[bone_target]
                                pbone = armature.pose.bones[bone_target]
                                key_on_frame = _in_bone_key_on_frame(
                                    bone, frame, armature.animation_data, type="ANY"
                                )
                                if key_on_frame:
                                    return key_on_frame
                                for const in pbone.constraints:
                                    if const.type == "ACTION":
                                        bone = (
                                            armature.data.bones[const.subtarget]
                                            if const.subtarget in armature.data.bones
                                            else None
                                        )
                                        if bone != None:
                                            key_on_frame = _in_bone_key_on_frame(
                                                bone,
                                                frame,
                                                armature.animation_data,
                                                type="ANY",
                                            )
                                        if key_on_frame:
                                            return key_on_frame
    return False

def _in_convert_color_channel(c):
    if c < 0.0031308:
        srgb = 0.0 if c < 0.0 else c * 12.92
    else:
        srgb = 1.055 * math.pow(c, 1.0 / 2.4) - 0.055

    return srgb


def _in_get_modulate_color(sprite):
    color = sprite.coa_tools2.modulate_color
    r = _in_convert_color_channel(color.r)
    g = _in_convert_color_channel(color.g)
    b = _in_convert_color_channel(color.b)

    alpha = sprite.coa_tools2.alpha
    # color_data = {
    #     "rM": int(100 * r),
    #     "gM": int(100 * g),
    #     "bM": int(100 * b),
    #     "aM": int(100 * alpha),
    # }
    color_data = [r,g,b,alpha]
    return color_data


def _in_get_mixed_vertex_data(obj):
    shapes = obj.data.shape_keys
    verts = []
    index = int(obj.active_shape_key_index)
    shape_key = obj.shape_key_add(name="tmp_mixed_mesh", from_mix=True)
    for vert in shape_key.data:
        coord = obj.matrix_world @ vert.co
        verts.append([vert.co[0], vert.co[1], vert.co[2]])
    obj.shape_key_remove(shape_key)
    obj.active_shape_key_index = index
    return verts

 # returns a map of the indexes of vertices in blender to the index of those vertices expected in Godot
 # motify from godot-2d-bridge2\gd2db_scene_parsing.py

def _in_convert_vertex_data_to_pixel_space(verts):
    data = []
    for vert in verts:
        for i, coord in enumerate(vert):
            if i in [0, 2]:
                multiplier = 1
                if i == 2:
                    multiplier = -1
                value = round(multiplier * coord * 100, 2)
                data.append(value)
    return data


def get_driver_bone_target(driver):
    targets = []
    for v in driver.driver.variables:
        if v.targets[0].bone_target != "":
            targets.append(v.targets[0].bone_target)
    return targets



def create_copy_transform_constraints(self, armature_from, armature_to):
    for bone in armature_to.pose.bones:
        for const in bone.constraints:
            bone.constraints.remove(const)
        if bone.name in armature_from.pose.bones:
            const = bone.constraints.new("COPY_TRANSFORMS")
            const.target = armature_from
            const.subtarget = bone.name
            const.target_space = "POSE"
            const.owner_space = "POSE"


def bone_is_deform_bone(self, bone, sprites):
    for sprite in sprites:
        if sprite.type == "MESH":
            init_mesh = sprite.data
            meshes = []
            ### get a list of all meshes in sprite -> slot objects containt multiple meshes
            if sprite.coa_tools2.type == "MESH":
                meshes.append(sprite.data)
            elif sprite.coa_tools2.type == "SLOT":
                for slot in sprite.coa_tools2.slot:
                    meshes.append(slot.mesh)

            ### check all meshes if bone is deforming that mesh
            for mesh in meshes:
                sprite.data = mesh
                if sprite.parent_bone == bone.name:
                    sprite.data = init_mesh
                    return True
                if not bone.name in sprite.vertex_groups:
                    break
                else:
                    v_group = sprite.vertex_groups[bone.name]
                    for vert in sprite.data.vertices:
                        try:
                            weight = v_group.weight(vert.index)
                            if weight > 0:
                                sprite.data = init_mesh
                                return True
                        except:
                            pass
            sprite.data = init_mesh
    return False


def check_if_bone_uses_constraints(pbone):
    return pbone.is_in_ik_chain or len(pbone.constraints) > 0


def bone_is_driver(bone, sprites):
    for sprite in sprites:
        if sprite.type == "MESH":
            meshes = []
            if sprite.coa_tools2.type == "MESH":
                meshes.append(sprite.data)
            elif sprite.coa_tools2.type == "SLOT":
                for slot in sprite.coa_tools2.slot:
                    meshes.append(slot.mesh)

            all_bone_targets = []
            if sprite.animation_data != None:
                for driver in sprite.animation_data.drivers:
                    bone_targets = get_driver_bone_target(driver)
                    all_bone_targets += bone_targets
            for mesh in meshes:
                if mesh.animation_data != None:
                    for driver in mesh.animation_data.drivers:
                        bone_targets = get_driver_bone_target(driver)
                        all_bone_targets += bone_targets
                if mesh.shape_keys != None and mesh.shape_keys.animation_data != None:
                    for driver in mesh.shape_keys.animation_data.drivers:
                        bone_targets = get_driver_bone_target(driver)
                        all_bone_targets += bone_targets
                if bone.name in all_bone_targets:
                    return True
    return False


def bone_is_constraint_target(bone, armature):
    for pbone in armature.pose.bones:
        for const in pbone.constraints:
            if hasattr(const, "subtarget") and const.subtarget == bone.name:
                return True
    return False

def ensure_rot_order(rot_order_str):
    if set(rot_order_str) != {'X', 'Y', 'Z'}:
        rot_order_str = "XYZ"
    return rot_order_str

def collect_armature_info(self, armature, sprites):
# def create_cleaned_armature_copy(self, armature, sprites):
    context = bpy.context
    if armature != None:
        scene = bpy.context.scene

        ### store armature rest position. Relevant for later animation calculations
        scale = 1 / get_addon_prefs(context).sprite_import_export_scale

        global edit_bone_matrices
        edit_bone_matrices = {}
        active_object = context.active_object
        context.view_layer.objects.active = armature
        mode = armature.mode
        bpy.ops.object.mode_set(mode="EDIT")
    
        for bone in armature.data.bones:
            pbone = armature.pose.bones[bone.name]
            bone_uses_constraints[pbone.name] = check_if_bone_uses_constraints(pbone)
                    
            edit_bone = armature.data.edit_bones[bone.name]
            edit_bone_matrices[bone.name] = edit_bone.matrix.to_4x4()
    
        bpy.ops.object.mode_set(mode=mode)
        context.view_layer.objects.active = active_object
        

        # armature_copy.data.pose_position = "REST"
        armature.data.pose_position = "REST"
        bpy.context.scene.frame_set(bpy.context.scene.frame_current)
        for bone in armature.data.bones:
            pose_bone = armature.pose.bones[bone.name]
            relative = True if _in_use_constraint(pose_bone.name) else False
    
            transformations = {}
            transformations["bone_pos"] = _in_rest_bone_location(armature, pose_bone, scale)
            transformations["bone_rot"] = _in_reset_bone_rotation(armature, bone, relative)
            transformations["bone_scale"] = _in_reset_bone_scale(armature, bone, relative)

            self.armature_restpose[bone.name] = transformations
        
        armature.data.pose_position = "POSE"

def _in_get_animation_data(self, sprite_object, armature):
    context = bpy.context
    scale = 1 / get_addon_prefs(context).sprite_import_export_scale
    anims = sprite_object.coa_tools2.anim_collections

    animations = []


    # tmp_anims = ["Idle","Run","Color_down","Attack"]
    # tmp_bones = ['Bone_M_02']

    # tmp_excludes = ["NO ACTION","Restpose"]
    tmp_excludes = ["NO ACTION"]

    for anim_index, anim in enumerate(anims):
        if anim.name not in tmp_excludes and anim.export:
            ### set animation
            sprite_object.coa_tools2.anim_collections_index = anim_index
      
            restpose = False
            if anim.name == 'Restpose':
                armature.data.pose_position = "REST"
                restpose = True
            else:
                armature.data.pose_position = "POSE"

            begin_frame = 0
            end_frame = anim.frame_end

            if (restpose):
                begin_frame = 0
                end_frame = 0

            anim_data = animation_data.copy()
            anim_data["duration"] = anim.frame_end
            anim_data["playTimes"] = 0
            anim_data["name"] = anim.name
            anim_data["bone"] = []
            anim_data["slot"] = []
            anim_data["zOrder"] = {}
            anim_data["ffd"] = []
            animation_data["frame"] = []

            # print("-------------->>>",anim.name,"-------------")

            ### append all slots to list
            ffd_keyframe_duration = {}
            ffd_last_frame_values = {}


            for slot in self.sprites:
                if slot.type == "MESH":
                    anim_data["slot"].append({"name": slot.name, "colorFrame": [], "displayFrame": []})

                    if slot.coa_tools2.type == "MESH":
                        anim_data["ffd"].append({"name": slot.data.name, "slot": slot.name, "frame": []})
                        ffd_keyframe_duration[slot.data.name] = {"ffd_duration": 0}
                        ffd_last_frame_values[slot.data.name] = None

                    elif slot.coa_tools2.type == "SLOT":
                        for slot2 in slot.coa_tools2.slot:
                            anim_data["ffd"].append({"name": slot2.mesh.name,"slot": slot.name,"frame": [],})
                            ffd_keyframe_duration[slot2.mesh.name] = {"ffd_duration": 0}
                            ffd_last_frame_values[slot2.mesh.name] = None

            ### gather timeline events
            for i, timeline_event in enumerate(anim.timeline_events):
                if i == 0:
                    if timeline_event.frame != 0:
                        anim_data["frame"].append({"duration": timeline_event.frame})

                if i < len(anim.timeline_events) - 1:
                    next_event = anim.timeline_events[i + 1]

                    duration = next_event.frame - timeline_event.frame
                else:
                    duration = anim.frame_end - timeline_event.frame

                event_data = {}
                event_data["duration"] = duration
                for event in timeline_event.event:
                    if event.type == "SOUND":
                        event_data["sound"] = event.value
                    elif event.type == "ANIMATION":
                        event_data["action"] = event.animation
                    elif event.type == "EVENT":
                        if "events" not in event_data:
                            event_data["events"] = []
                        custom_event = {}
                        custom_event["name"] = event.value
                        if event.target != "":
                            custom_event["bone"] = event.target
                        if event.int != "":
                            custom_event["ints"] = [int(event.int)]
                        if event.float != "":
                            custom_event["floats"] = [float(event.float)]
                        if event.string != "":
                            custom_event["strings"] = [event.string]
                        event_data["events"].append(custom_event)

                anim_data["frame"].append(event_data)

            ### check if slot has animation data. if so, store for later usage
            SHAPEKEY_ANIMATION = {}
            for i in range(begin_frame, end_frame + 1):
                frame = anim.frame_end - i
                slot_data = None
                for slot in self.sprites:
                    if slot.type == "MESH":
                        slot_data = []
                        if slot.coa_tools2.type == "MESH":
                            slot_data = [tmp_slots_data[slot.data.name]]
                        elif slot.coa_tools2.type == "SLOT":
                            for slot2 in slot.coa_tools2.slot:
                                slot_data.append(tmp_slots_data[slot2.mesh.name])
                if slot_data != None:
                    for item in slot_data:
                        data = item["data"]
                        data_name = item["name"]

                        key_blocks = []
                        if data.shape_keys != None:
                            for key in data.shape_keys.key_blocks:
                                key_blocks.append(key.name)
                        if _in_property_key_on_frame(
                            data, key_blocks, frame, type="SHAPEKEY"
                        ):
                            SHAPEKEY_ANIMATION[slot.name] = True
                            break

            ### append all bones to list
            # kv_bone_rot_order = {}
            if armature != None:
                for bone in armature.data.bones:
                    
                    anim_data["bone"].append(
                        {
                            "name": bone.name,
                            "translateFrame": [],
                            "rotateFrame": [],
                            "scaleFrame": [],
                        }
                    )

            for i in range(begin_frame, end_frame + 1):
                frame = end_frame - i
                context.scene.frame_set(frame)

                #### HANDLE SLOT ANIMATION
                j = 0
                for slot in self.sprites:
                    if slot.type == "MESH":

                        if restpose or _in_property_key_on_frame(slot, ["coa_tools2.z_value"], frame):

                            one_zorder = {}
                            one_zorder["duration"] = frame
                            one_zorder["zOrder"] = []
                            one_zorder["zOrder"].append({"name":slot.name, "z":_in_get_z_value(self, slot)})

                            if "frame" not in anim_data["zOrder"]:
                                anim_data["zOrder"]["frame"] = []

                            anim_data["zOrder"]["frame"].insert(0, one_zorder)

                        if restpose or _in_property_key_on_frame(slot,["coa_tools2.alpha", "coa_tools2.modulate_color"], frame,):
                            one_frame = {}
                            one_frame["duration"] = frame
                            one_frame["tweenEasing"] = 0
                            one_frame["value"] = _in_get_modulate_color(slot)

                            anim_data["slot"][j]["colorFrame"].insert(0, one_frame)

                        if restpose or _in_property_key_on_frame(slot, ["coa_tools2.slot_index"], frame) or frame in [0, anim.frame_end]:
                            one_frame = {}
                            one_frame["duration"] = frame
                            # one_frame["name"] = slot.name
                            one_frame["value"] = slot.coa_tools2.slot_index

                            anim_data["slot"][j]["displayFrame"].insert(0, one_frame)

                        j += 1
                #### HANDLE BONE ANIMATION
                if armature != None:
                    for j, bone in enumerate(armature.data.bones):

                        pose_bone = armature.pose.bones[bone.name]
                        const_len = len(pose_bone.constraints)
                        in_ik_chain = pose_bone.is_in_ik_chain

                        #---->>>>>>>>>>>
                        # # copy from godot-2d-bridge2\gd2db_scene_parsing.py:347
                        trans = Matrix.Translation(bone.head_local)
                        itrans = Matrix.Translation(-bone.head_local)
                        if bone.parent:
                            parent_bone = bone.parent
                            parent_pose_bone = armature.pose.bones[bone.parent.name]
                    
                            # mat_final = dbone.parent.rest_arm_mat @ dbone.parent.pose_imat @ dbone.pose_mat @ dbone.rest_arm_imat
                            # mat_final = itrans @ mat_final @ trans
                            # loc = mat_final.to_translation() + (dbone.rest_bone.head_local - dbone.parent.rest_bone.head_local)
                        
                            mat_final = parent_bone.matrix_local @ parent_pose_bone.matrix.inverted() @ pose_bone.matrix @ bone.matrix_local.inverted()
                            mat_final = itrans @ mat_final @ trans
                            loc = mat_final.to_translation() + (bone.head_local - parent_bone.head_local)
                        
                        else:
                            # mat_final = dbone.pose_mat @ dbone.rest_arm_imat
                            # mat_final = itrans @ mat_final @ trans
                            # loc = mat_final.to_translation() + dbone.rest_bone.head

                            mat_final = pose_bone.matrix @ bone.matrix_local.inverted()
                            mat_final = itrans @ mat_final @ trans
                            loc = mat_final.to_translation() + bone.head


                        bone_pos_2d = [loc[0] * scale, -loc[2] * scale]

                        rot = mat_final.decompose()[1].to_euler()
                        bone_rot_degree = round(math.degrees(rot.y), 2)

                        sca = mat_final.decompose()[2]
                        bone_scale_2d = [sca[0], sca[2]]


                        # if not dbone.skip_position:
                        #    file.write("%.6f %.6f %.6f " % (loc * global_scale)[:])
                    
                        # rot = mat_final.to_euler(dbone.rot_order_str_reverse, dbone.prev_euler)
                        # rot = mat_final.to_euler()

                        # print
                        # if anim.name in tmp_anims and bone.name in tmp_bones:
                        #       print("===>pos:", bone.name, frame, bone_pos_2d)
                        #       print("===>rot:", bone.name, frame, rot)
                        
                        #----<<<<<<<<<<<<<<<<<

                        bake_anim = (
                            self.scene.coa_tools2.export_bake_anim
                            and frame % self.scene.coa_tools2.export_bake_steps == 0
                        )

                        ### bone position
                        if (
                            _in_bone_key_on_frame(bone,frame,armature.animation_data,type="LOCATION",)
                            # or frame in [0, anim.frame_end]
                            or const_len > 0
                            or in_ik_chain
                            or bake_anim or restpose  
                        ):

                            bone_pos = (bone_pos_2d)

                            one_frame = {}
                            one_frame["duration"] = frame
                            one_frame["curve"] = ([0.5, 0, 0.5, 1] if bake_anim == False else [0, 0, 1, 1])
                            one_frame["x"] = round(bone_pos[0], 2)
                            one_frame["y"] = round(bone_pos[1], 2)

                            anim_data["bone"][j]["translateFrame"].insert(0, one_frame)

                        ### bone rotation
                        if (
                            _in_bone_key_on_frame(bone,frame,armature.animation_data, type="ROTATION",)
                            # or frame in [0, anim.frame_end]
                            or const_len > 0
                            or in_ik_chain
                            or bake_anim or restpose  
                        ):
                        
                            bone_rot = bone_rot_degree

                            one_frame = {}
                            one_frame["duration"] = frame
                            one_frame["curve"] = ([0.5, 0, 0.5, 1] if bake_anim == False else [0, 0, 1, 1])
                            one_frame["rotate"] = round(bone_rot, 2)
    
                            keyframe_rotate = one_frame["rotate"]
                            one_frame["rotate"] = round(math.radians(one_frame["rotate"]), 2)
                            anim_data["bone"][j]["rotateFrame"].insert(0, one_frame)

                        ### bone scale
                        if (
                            _in_bone_key_on_frame(bone, frame, armature.animation_data,type="SCALE",)
                            # or frame in [0, anim.frame_end]
                            or const_len > 0
                            or in_ik_chain
                            or bake_anim or restpose  
                        ):

                            bone_scale = bone_scale_2d

                            one_frame = {}
                            one_frame["duration"] = frame
                            one_frame["curve"] = ([0.5, 0, 0.5, 1] if bake_anim == False else [0, 0, 1, 1])
                            one_frame["x"] = round(bone_scale[0], 2)
                            one_frame["y"] = round(bone_scale[1], 2)

                            anim_data["bone"][j]["scaleFrame"].insert(0, one_frame)

                #### HANDLE FFD Transformations (Blender Shapekeys)
                # TODO  here is do nothing godot Polygon2D nothing for Shapekeys
                j = 0
                for slot in self.sprites:
                    if slot.type == "MESH":
                        slot_data = []
                        if slot.coa_tools2.type == "MESH":
                            slot_data = [tmp_slots_data[slot.data.name]]
                        elif slot.coa_tools2.type == "SLOT":
                            for slot2 in slot.coa_tools2.slot:
                                slot_data.append(tmp_slots_data[slot2.mesh.name])

                        for item in slot_data:
                            data = item["data"]
                            data_name = item["name"]

                            bake_anim = (
                                self.scene.coa_tools2.export_bake_anim
                                and frame % self.scene.coa_tools2.export_bake_steps == 0
                            )

                            if data.shape_keys != None:
                                ffd_keyframe_duration[data_name]["ffd_duration"] += 1

                                key_blocks = []
                                for key in data.shape_keys.key_blocks:
                                    key_blocks.append(key.name)
                                if _in_property_key_on_frame(data, key_blocks, frame, type="SHAPEKEY"
                                ) or (
                                    frame in [0, anim.frame_end]
                                    and data_name in SHAPEKEY_ANIMATION
                                ):  # or bake_anim:
                                    ffd_data = {}
                                    ffd_data["duration"] = ffd_keyframe_duration[data_name]["ffd_duration"]
                                    ffd_data["curve"] = ([0.5, 0, 0.5, 1] if bake_anim == False else [0, 0, 1, 1])
                                    #                                    if bake_anim == False:
                                    #                                        ffd_data["curve"] = [.5,0,.5,1]
                                    #                                    else:
                                    #                                        ffd_data["tweenEasing"] = 0

                                    verts = _in_get_mixed_vertex_data(item["object"])
                                    verts_relative = []
                                    for i, co in enumerate(verts):
                                        verts_relative.append(Vector(co)- Vector(vert_coords_default[slot.name][i]))

                                    ffd_data["vertices"] = ( _in_convert_vertex_data_to_pixel_space(verts_relative))

                                    if (frame in [0, anim.frame_end]) or (ffd_last_frame_values[data_name]!= ffd_data["vertices"]):
                                        # ### if previous keyframe differs and keyframe duration is greater 1 add an extra keyframe inbetween
                                        # if ffd_data["duration"] > 1 and (ffd_last_frame_values[data_name] != ffd_data["vertices"]):
                                        #     ffd_data_last = {}
                                        #     ffd_data_last["duration"] = ffd_keyframe_duration[data_name]["ffd_duration"]-1
                                        #     ffd_data_last["curve"] = [.5,0,.5,1]
                                        #     ffd_data_last["vertices"] = ffd_last_frame_values[data_name]
                                        #
                                        #     anim_data["ffd"][j]["frame"].insert(0,ffd_data_last)
                                        #     ffd_data["duration"] = 1

                                        anim_data["ffd"][j]["frame"].insert(0, ffd_data)
                                        ffd_keyframe_duration[data_name][ "ffd_duration"] = 0
                                        ffd_last_frame_values[data_name] = ffd_data["vertices"]
                            j += 1
                
            ### cleanup animation data
            delete_keys = []
            for key in anim_data:
                data = anim_data[key]
                if type(data) == list:
                    if len(data) == 0:
                        delete_keys.append(key)
                    else:
                        for item in data:
                            delete_keys2 = []
                            if type(item) == dict:
                                for key2 in item:
                                    data2 = item[key2]
                                    if type(data2) == list:
                                        if len(data2) == 0:
                                            # del item[key2]
                                            delete_keys2.append(key2)
                            for key2 in delete_keys2:
                                del item[key2]
            for key in delete_keys:
                del anim_data[key]

            animations.append(anim_data)
    return animations


def _str_float(v):
    return f"{v:.2f}"

def _str_name(n):
    return n.replace(".","_")

def _get_bone_base(self, bone_name):
    pose_bone = self.armature.pose.bones[bone_name]
    tmp_paths = []
    tmp_paths += [x.name for x in reversed(pose_bone.parent_recursive)] + [bone_name]
    return _str_name("/".join(tmp_paths))

def _get_sprite_parents(armature, arm_name, sprite_name):
    if sprite_name not in bpy.data.objects:
        return ''
    sprite = bpy.data.objects[sprite_name]
    if sprite.parent is not None:
        print("==>", sprite_name, sprite.parent.name)
        if sprite.parent.name in armature.pose.bones:
            return _get_bone_path(armature, arm_name, sprite.parent.name)
    return arm_name

def _get_bone_parents(armature, arm_name, bone_name):
    pose_bone = armature.pose.bones[bone_name]
    tmp_paths = []
    tmp_paths += [arm_name] + [x.name for x in reversed(pose_bone.parent_recursive)]
    return _str_name("/".join(tmp_paths))

def _get_bone_path(armature, arm_name, bone_name):
    pose_bone = armature.pose.bones[bone_name]
    tmp_paths = []
    if (arm_name != '' and arm_name != None):
        tmp_paths += [arm_name]
    tmp_paths +=  [x.name for x in reversed(pose_bone.parent_recursive)] + [bone_name]
    return _str_name("/".join(tmp_paths))

def _get_bone_index(armature, bone_name):
    pose_bone = armature.pose.bones[bone_name]
    return len(pose_bone.parent_recursive)

def _in_mix_AnimationArray_string(ii, dict, rs):
    for sn in dict:
        sd = dict[sn]
        vals = sd['values']
        # if (len(sd['times']) != len(vals)):
        #     print(sd['path'])
        if (len(vals) > 0):
            rs += (
                f"tracks/{ii}/type = \"value\"",
                f"tracks/{ii}/imported = false",
                f"tracks/{ii}/enabled = true",
                f"tracks/{ii}/path = NodePath(\"{sd['path']}\")",
                f"tracks/{ii}/interp = 1",
                f"tracks/{ii}/loop_wrap = true",
                "tracks/"+str(ii)+"/keys = {",
                f"\"times\": PackedFloat32Array({", ".join(sd['times'])}),",
                f"\"transitions\": PackedFloat32Array({", ".join(sd['transitions'])}),",
                f"\"update\": 0,",
                f"\"values\": [{", ".join(vals)}], ",
                "}",
                "",
            )
            ii += 1
    return ii


## KinematicConstraint
def _in_mix_SkeletonModification2DCCDIK(armature, ik_bones, rs):
    tmp_ik_infos = _in_get_ik_bones_info(armature, ik_bones)
    len_ik = len(tmp_ik_infos)
    rs_next = []
    rs_out = []
    if (len_ik > 0):
        for i, info in enumerate(tmp_ik_infos):

            key_sub_ik = f"SkeletonModification2DCCDIK_{_in_get_key()}"
            rs_next.append(f"modifications/{i} = SubResource(\"{key_sub_ik}\")")

            n_target = info["target"]
            n_tip = info["tip"]
            n_chains = info["chains"]

            # bone = armature.data.bones[pose_name]
            target_nodepath = _get_bone_path(armature, '', n_target) #f"Bone/IK_Top_R_02_001" 
            tip_nodepath = _get_bone_path(armature, '', n_tip)#f"Bone/Root/Middle/Top/Top_R_01/Top_R_02/Top_R_02_001"

            lnum = len(n_chains)

            rs_out += (
                f"[sub_resource type=\"SkeletonModification2DCCDIK\" id=\"{key_sub_ik}\"]",
                f"enabled = true",
                f"target_nodepath = NodePath(\"{target_nodepath}\")",
                f"tip_nodepath = NodePath(\"{tip_nodepath}\")",
                f"ccdik_data_chain_length = {lnum}",
            )

            for j,pose_name in enumerate(n_chains):
                path_chain = _get_bone_path(armature, '', pose_name)#'Bone/Root/Middle/Top/Top_R_01'
                bone_index = _get_bone_index(armature, pose_name)
                rs_out += (
                    f"joint_data/{j}/bone_index = {bone_index}",
                    f"joint_data/{j}/bone2d_node = NodePath(\"{path_chain}\")",
                    f"joint_data/{j}/rotate_from_joint = false",
                    f"joint_data/{j}/enable_constraint = false",
                    f"joint_data/{j}/editor_draw_gizmo = true",
                )

        rs_out.append("")
        key_stack_ik = f"SkeletonModificationStack2D_{_in_get_key()}"

        rs_out += (
            f"[sub_resource type=\"SkeletonModificationStack2D\" id=\"{key_stack_ik}\"]",
            f"enabled = true",
            f"modification_count = {len_ik}",
        )

        rs_out += rs_next
        rs_out.append("")

        rs += rs_out
        return True,key_stack_ik
    return False,''

class COATOOLS2_OT_GodotTscnExport(bpy.types.Operator):
    bl_idname = "coa_tools2.export_godot_tscn"
    bl_label = "Godot Scene Export"
    bl_description = ""
    bl_options = {"REGISTER"}

    scene = None
    sprite_object = None
    armature = None
    sprites = None
    scale = 0.0
    armature_restpose = {}


    def get_init_state(self, context):
        self.selected_objects = context.selected_objects[:]
        self.active_object = context.active_object
        self.sprite_object = get_sprite_object(context.active_object)

        self.animation_index = self.sprite_object.coa_tools2.anim_collections_index
        self.frame_current = context.scene.frame_current

    def set_init_state(self, context):
        for obj in context.scene.objects:
            if obj in self.selected_objects:
                obj.select_set(True)
            else:
                obj.select_set(False)
        context.view_layer.objects.active = self.active_object

        if len(self.sprite_object.coa_tools2.anim_collections) > 0:
            self.sprite_object.coa_tools2.anim_collections_index = self.animation_index
        context.scene.frame_current = self.frame_current


    def execute(self, context):
        bpy.ops.ed.undo_push(message="Export to GodotScene")
        global tmp_slots_data
        tmp_slots_data = {}
        
        #=====================
        # set self
        self.get_init_state(context)
        self.scene = context.scene

        self.scale = 1 / get_addon_prefs(context).sprite_import_export_scale
        tmp_sprite_scale = self.scene.coa_tools2.sprite_scale

        tmp_margin = self.scene.coa_tools2.atlas_island_margin
        tmp_texture_bleed = self.scene.coa_tools2.export_texture_bleed
        tmp_square = self.scene.coa_tools2.export_square_atlas

        tmp_img_width = self.scene.coa_tools2.atlas_resolution_x
        tmp_img_height = self.scene.coa_tools2.atlas_resolution_y
        tmp_export_ik = self.scene.coa_tools2.export_ik

        tmp_anim_lib_key = _in_get_key()

        project_name = self.scene.coa_tools2.project_name
        export_path = to_linux_path(bpy.path.abspath(self.scene.coa_tools2.export_path))

        ### check if export dir exists
        if not os.path.exists(export_path):
            self.report({"WARNING"}, "Please define a valid export path.")
            return {"FINISHED"}


        coa_nla_mode = str(self.scene.coa_tools2.nla_mode)
        self.scene.coa_tools2.nla_mode = "ACTION"

        #=============================
        #  base get info
        #=============================

        rs_scene = ['[gd_scene format=3]',""]
        rs_ext = []

        kv_textures = {} # key: texture path value: key
        kv_atlas = {}       # key: sprite name value: {x,y,w,h}
        key_texture_altas = ''
        
        self.sprite_object = get_sprite_object(context.active_object)
        self.armature = get_armature(self.sprite_object)
        ### get export, project and json path
        
        texture_dir_path = to_linux_path(os.path.join(export_path, project_name + "_texture"))

        godot_res_root = _in_get_godot_res_root(export_path)
        texture_prefix = export_path.replace(godot_res_root, '')

        path_scene_tscn = os.path.join(export_path, project_name + ".tscn")

        self.sprites = get_children(context, self.sprite_object, [])

        self.sprites = sorted(self.sprites, key=lambda obj: obj.location[1], reverse=True)  

        collect_armature_info(self, self.armature, self.sprites)

        is_atlas = self.scene.coa_tools2.export_image_mode == "ATLAS"
        is_images = self.scene.coa_tools2.export_image_mode == "IMAGES"
        #=============================
        #  texture, or atlas texture
        #=============================
        ### export texture atlas
        if is_atlas:
            sprites = [sprite for sprite in self.sprites if sprite.type == "MESH"]
            if len(sprites) > 0:
                texture_atlas = _in_generate_texture_atlas(
                    self,
                    sprites,
                    project_name,
                    export_path,
                    square = tmp_square,
                    texture_bleed = tmp_texture_bleed,
                    img_width = tmp_img_width,
                    img_height = tmp_img_height,
                    sprite_scale = tmp_sprite_scale,
                    margin = tmp_margin,
                )
                # kv_textures[]
                
                uSubTexture = texture_atlas["SubTexture"]
                atlas_name = texture_atlas["imagePath"]

                atlas_texture_path = export_path + "/" + atlas_name
                key_texture_altas = f"1_{_in_get_key()}"

                kv_textures[atlas_name] = {"path":atlas_texture_path,"key":key_texture_altas}

                for sprite_data in uSubTexture:
                    uname = sprite_data["name"]
                    x_px = sprite_data["x"]
                    y_px = sprite_data["y"]
                    width_px = sprite_data["width"]
                    height_px = sprite_data["height"]

                    kv_atlas[uname] = {"name":uname, "x":x_px, "y":y_px, "width":width_px, "height":height_px}
                # print(kv_atlas)
        ### create texture directory
        if is_images:
            if os.path.exists(texture_dir_path):
                shutil.rmtree(texture_dir_path)
            os.makedirs(texture_dir_path)

            ### copy all textures to texture directory
            _in_copy_textures(self, self.sprites, texture_dir_path, kv_textures)

        for img_name in kv_textures:
            uobj = kv_textures[img_name]
            dest_path  = to_linux_path(uobj["path"])
            ukey = uobj["key"]

            upath = dest_path.replace(export_path, '')
            if texture_prefix != '':
                upath = to_join_path(texture_prefix, upath)

            rs_ext.append(f"[ext_resource type=\"Texture2D\" path=\"res://{upath}\" id=\"{ukey}\"]")

        #=============================
        #  animation
        #=============================
        if self.armature != None:
            self.armature.data.pose_position = "REST"

        tmp_fps = self.scene.render.fps
        frame_time = 1.0/tmp_fps

        # set bone path
        kv_bone_path = {}
        kv_bone_base_path = {}
        for bone in self.armature.data.bones:
            bone_path = _get_bone_path(self.armature, 'Skeleton2D', bone.name)
            kv_bone_path[bone.name] = bone_path
            kv_bone_base_path[bone.name] = _get_bone_base(self, bone.name)

        tmp_skin_array = _in_get_skin_data(self, self.sprites, self.armature, self.scale)  
        tmp_bone_array = _in_get_bone_data(self, self.armature, self.sprite_object, self.scale)

        if self.armature != None:
            self.armature.data.pose_position = "POSE"
            
        tmp_anim_array = _in_get_animation_data(self, self.sprite_object, self.armature)
        #========
        # animation & # animation library
        is_has_event = False
        tmp_anim_rs = []
        rs_anim = []
        for tmp_ad in tmp_anim_array:
            
            uduration = tmp_ad["duration"]
            uname = tmp_ad['name']

            if (uname == 'Restpose'): ## for godot reset anim
                uname = 'RESET'

            # tmp_ad["playTimes"] = 0
            ubone = tmp_ad["bone"]
            uslot = tmp_ad["slot"]
            uzOrder = tmp_ad["zOrder"]
            uframeEvents = []

            if "frame" in tmp_ad:
                uframeEvents = tmp_ad["frame"]

            ukey = _in_get_key()
            tmp_anim_rs.append(f"&\"{uname}\": SubResource(\"Animation_{ukey}\")")

            rs_anim.append(f"[sub_resource type=\"Animation\" id=\"Animation_{ukey}\"]")
            rs_anim.append(f"length = {_str_float(uduration * frame_time)}")

            #######======> zOrder <========
            ii = 0
            if ("frame" in uzOrder):
                frame_array = uzOrder["frame"]
                slot_frame_dict = {} 
                frame_array.sort(key=lambda x:x["duration"])
                for tmp_zorder in frame_array:
                    tduration = tmp_zorder["duration"]
                    tzOrder = tmp_zorder["zOrder"]

                    utime = (tduration) * frame_time

                    for slot_data in tzOrder:
                        slot_name = slot_data["name"]
                        slot_z = slot_data["z"]

                        if (slot_name not in slot_frame_dict):
                            slot_NodePath = f'Skeleton2D/{_str_name(slot_name)}:z_index'
                            slot_frame_dict[slot_name] = {"path":slot_NodePath, "times":[], "transitions":[],"values":[]}

                        slot_frame_dict[slot_name]["times"].append(_str_float(utime))
                        slot_frame_dict[slot_name]["transitions"].append("1")
                        slot_frame_dict[slot_name]["values"].append(str(slot_z))

                ii = _in_mix_AnimationArray_string(ii, slot_frame_dict, rs_anim)

            #######======> color & display <========
            slot_color_dict = {}
            slot_display_dict = {}
            for tmp_slot in uslot:

                slot_name = tmp_slot["name"]

                if slot_name not in slot_color_dict:
                    slot_NodePath = f'Skeleton2D/{_str_name(slot_name)}:color'
                    slot_color_dict[slot_name] = {"path":slot_NodePath, "times":[], "transitions":[],"values":[]}
 
                colorFrames = []
                if 'colorFrame' in tmp_slot:
                    colorFrames = tmp_slot["colorFrame"]
                    colorFrames.sort(key=lambda x:x['duration'])

                for cf in colorFrames:
                    duration = cf["duration"]
                    tweenEasing = cf["tweenEasing"]
                    val = cf["value"]

                    utime = (duration) * frame_time

                    r = _str_float(val[0])
                    g = _str_float(val[1])
                    b = _str_float(val[2])
                    a = _str_float(val[3])

                    slot_color_dict[slot_name]["times"].append(_str_float(utime))
                    slot_color_dict[slot_name]["transitions"].append("1")
                    slot_color_dict[slot_name]["values"].append(f"Color({r}, {g}, {b}, {a})") # Color(1, 1, 1, 1)

                # TODO 
                ###displayFrames = tmp_slot["displayFrame"]
                if (slot_name not in slot_display_dict):
                    slot_NodePath = f'Skeleton2D/{_str_name(slot_name)}:visible'
                    slot_display_dict[slot_name] = {"path":slot_NodePath, "times":[], "transitions":[],"values":[]}

                displayFrames = []
                if 'displayFrame' in tmp_slot:
                    displayFrames = tmp_slot['displayFrame']
                    displayFrames.sort(key=lambda x:x['duration'])
                
                for df in displayFrames:
                    duration = df["duration"]
                    # tweenEasing = df["tweenEasing"]
                    val = df["value"]

                    utime = (duration) * frame_time

                    dis = val

                    slot_display_dict[slot_name]["times"].append(_str_float(utime))
                    slot_display_dict[slot_name]["transitions"].append("1")
                    slot_display_dict[slot_name]["values"].append(dis)

                
                pass

            ii = _in_mix_AnimationArray_string(ii, slot_color_dict, rs_anim)

            # TODO unfinish
            ### ii = _in_mix_AnimationArray_string(ii, slot_display_dict, rs_anim)
            

            #######======> bone pose animations <========
            
            bone_loc_dict = {}
            bone_rot_dict = {}
            bone_sca_dict = {}

            for tmp_bone in ubone:
                ubone_name = tmp_bone["name"]
                translateFrames = []
                rotateFrames = []
                scaleFrames = []

                if 'translateFrame' in tmp_bone: translateFrames = tmp_bone["translateFrame"]
                if 'rotateFrame' in tmp_bone: rotateFrames = tmp_bone["rotateFrame"]
                if 'scaleFrame' in tmp_bone: scaleFrames = tmp_bone["scaleFrame"]

                translateFrames.sort(key=lambda x:x["duration"])
                rotateFrames.sort(key=lambda x:x["duration"])
                scaleFrames.sort(key=lambda x:x["duration"])

                bone_path = kv_bone_path[ubone_name]

                if ubone_name not in bone_loc_dict:
                    bone_loc_dict[ubone_name] = {"path":bone_path+":position", "times":[], "transitions":[],"values":[]}
                    bone_rot_dict[ubone_name] = {"path":bone_path+":rotation", "times":[], "transitions":[],"values":[]}
                    bone_sca_dict[ubone_name] = {"path":bone_path+":scale", "times":[], "transitions":[],"values":[]}

                # print("translateFrames===>",ubone_name, len(translateFrames))
                for tf in translateFrames:
                    duration = tf["duration"]
                    tx = tf["x"]
                    ty = tf["y"]
                    # val = tf["curve"]
                    utime = (duration) * frame_time

                    bone_loc_dict[ubone_name]["times"].append(_str_float(utime))
                    bone_loc_dict[ubone_name]["transitions"].append("1")
                    bone_loc_dict[ubone_name]["values"].append(f"Vector2({_str_float(tx)}, {_str_float(ty)})")

                    pass

                for rf in rotateFrames:
                    duration = rf["duration"]
                    tr = rf["rotate"]
                    # val = rf["curve"]
                    utime = (duration) * frame_time

                    bone_rot_dict[ubone_name]["times"].append(_str_float(utime))
                    bone_rot_dict[ubone_name]["transitions"].append("1")
                    bone_rot_dict[ubone_name]["values"].append(_str_float((tr)))
                    pass

                for sf in scaleFrames:
                    duration = sf["duration"]
                    sx = sf["x"]
                    sy = sf["y"]
                    # val = sf["curve"]
                    utime = (duration) * frame_time

                    bone_sca_dict[ubone_name]["times"].append(_str_float(utime))
                    bone_sca_dict[ubone_name]["transitions"].append("1")
                    bone_sca_dict[ubone_name]["values"].append(f"Vector2({_str_float(sx)},{_str_float(sy)})")

                    pass


                pass

            ii = _in_mix_AnimationArray_string(ii, bone_loc_dict, rs_anim)
            ii = _in_mix_AnimationArray_string(ii, bone_rot_dict, rs_anim)
            ii = _in_mix_AnimationArray_string(ii, bone_sca_dict, rs_anim)

            #######======> events <========
            format_str = "{\"args\": [\"{0}\", \"{1}\"],\"method\": &\"handle_events\"}"
            for tmp_event in uframeEvents:
                event_array = []
                duration = tmp_event['duration']

                utime = (duration) * frame_time
                
                if 'sound' in tmp_event:
                    event_array.append(string_replace(format_str, ['sound', tmp_event['sound']]))
                if 'action' in tmp_event:
                    event_array.append(string_replace(format_str, ['action', tmp_event['action']]))
                if 'events' in tmp_event:
                    for sev in tmp_event['events']:
                        ev_name = sev['name']
                        ev_vals = []
                        if 'bone' in sev: ev_vals.append(sev['bone'])
                        if 'ints' in sev: ev_vals.append(str(sev['ints'][0]))
                        if 'floats' in sev: ev_vals.append(str(sev['floats'][0]))
                        if 'strings' in sev: ev_vals.append(str(sev['strings'][0]))
                        event_array.append(string_replace(format_str, [ev_name, ",".join(ev_vals)]))
                
                is_has_event = True
                for one_event in event_array:
                    rs_anim += (
                        f"tracks/{ii}/type = \"method\"",
                        f"tracks/{ii}/imported = false",
                        f"tracks/{ii}/enabled = true",
                        f"tracks/{ii}/path = NodePath(\".\")",
                        f"tracks/{ii}/interp = 1",
                        f"tracks/{ii}/loop_wrap = true",
                        "tracks/"+str(ii)+"/keys = {",
                        f"\"times\": PackedFloat32Array({_str_float(utime)}),",
                        f"\"transitions\": PackedFloat32Array(1),",
                        f"\"values\": [{one_event}]",
                        "}",
                    )

                    ii += 1

                pass

        rs_anim += (
            f"[sub_resource type=\"AnimationLibrary\" id=\"AnimationLibrary_{tmp_anim_lib_key}\"]",
            "_data = {"
        )
        rs_anim.append(",\n".join(tmp_anim_rs))
        rs_anim.append("}")
        rs_anim.append("\n")

        rs_node_begin = []
        rs_node_begin.append("[node name=\"Node2D\" type=\"Node2D\" ]")
        if (is_has_event):
            key_gdscript = f"{len(rs_ext) + 1}_{_in_get_key()}"
            rs_node_begin.append(f"script = ExtResource(\"{key_gdscript}\")")
            rs_node_begin.append("")

            script_name = project_name + ".gd"
            upath = to_join_path(texture_prefix, script_name)
            rs_ext.append(f"[ext_resource type=\"Script\" path=\"res://{upath}\" id=\"{key_gdscript}\"]")

            # write script
            script_str = [
                "extends Node2D",
                "",
                "func handle_events(event_type:String, event_value:String) -> void:",
                "	print(event_type, event_value)",
                "",
            ]
            str_script = '\n'.join(script_str)
            path_script = os.path.join(export_path, script_name)
            text_file = open(path_script, "w")
            text_file.write(str_script)
            text_file.close()

            pass
        

        rs_node_begin.append("[node name=\"Skeleton2D\" type=\"Skeleton2D\" parent=\".\" ]")

        # #========
        # meshs
        rs_sprites = []
        rs_skin = []
        tmp_uskin_array = tmp_skin_array[0]["slot"]
        for tmp_skin in tmp_uskin_array:

            name = tmp_skin['name']

            display_datas = tmp_skin["display"]
            for display_data in display_datas:

                sprite_name = display_data['name']
                utype = display_data["type"]

                twidth = display_data["width"]
                theight = display_data["height"]

                z_index = display_data["zOrder"]
                tx = display_data['x']
                ty = display_data['y']
                
                sx = display_data["sx"]
                sy = display_data["sy"]
                rot = display_data["rot"]

                ofx = 0
                ofy = 0

                ukey = 'undefined'

                if is_images:
                    uobj = kv_textures[name]
                    ukey = uobj["key"]
                if is_atlas:
                    ukey = key_texture_altas
                    
                if (utype == 'mesh'):
                    vertices = display_data['vertices']
                    polygons = display_data['polygons']
                    uvs = display_data['uvs']

                    weights = display_data['weights'] #[bone_name]= [weight,...]

                    vertices_string = join_array(vertices)
                    weights_string = ''
                    to_uvs = uvs
                    
                    if is_atlas:
                        one_atlas = kv_atlas[name]
    
                        uv_x = one_atlas['x']
                        uv_y = one_atlas['y']
                        uv_w = one_atlas['width']
                        uv_h = one_atlas['height']
    
                        new_uvs = []
    
                        uv_ln = len(uvs)
                        for ii in range(0, uv_ln, 2):
    
                            uv_u = uvs[ii]
                            uv_v = uvs[ii+1]
    
                            new_uvs.append(round(uv_x + uv_u * uv_w, 3))
                            new_uvs.append(round(uv_y + uv_v * uv_h, 3))
    
                        to_uvs = new_uvs
                        pass
                        
                    uvs_string = join_array(to_uvs)
                    tmp_rs = []
                    for bone_name in weights:
                        vals = weights[bone_name]
                        path = kv_bone_base_path[bone_name]
                        tmp_rs.append(f"\"{path}\"")
                        tmp_rs.append('PackedFloat32Array(' + ','.join(vals) + ')')
                    weights_string = ','.join(tmp_rs)

                    rs_skin += (
                        f"[node name=\"{_str_name(name)}\" type=\"Polygon2D\" parent=\"Skeleton2D\" ]",
                        f"z_index = {z_index}",
                        f"position = Vector2({tx}, {ty})",
                        f"scale = Vector2({sx}, {sy})",
                        f"offset = Vector2({ofx}, {ofy})",
                        f"texture = ExtResource(\"{ukey}\")",
                        f"skeleton = NodePath(\"..\")",
                        f"polygon = PackedVector2Array({vertices_string})",
                        f"uv = PackedVector2Array({uvs_string})",
                        f"polygons = [{",".join(polygons)}] ",
                        f"bones = [{weights_string}]",
                        "",
                        )
                else:
                    bind_bone_name = display_data['bone']
                    sprite_parent_path = _get_bone_path(self.armature, 'Skeleton2D', bind_bone_name)
                    rs_sprites += (
                        f"[node name=\"{_str_name(name)}\" type=\"Sprite2D\" parent=\"{sprite_parent_path}\" ]",
                        f"z_index = {z_index}",
                        f"position = Vector2({tx}, {ty})",
                        f"scale = Vector2({sx}, {sy})",
                        f"offset = Vector2({ofx}, {ofy})",
                        f"texture = ExtResource(\"{ukey}\")",
                    )

                    if is_atlas:
                        one_atlas = kv_atlas[name]
    
                        uv_x = one_atlas['x']
                        uv_y = one_atlas['y']
                        uv_w = one_atlas['width']
                        uv_h = one_atlas['height']
                        rs_sprites += (
                            f"region_enabled = true",
                            f"region_rect = Rect2({uv_x}, {uv_y}, {uv_w}, {uv_h})",
                        )
                        rs_sprites.append("")
                    pass


        # #========
        # # bones SkeletonModification2DCCDIK
        rs_sub_ik = []
        if tmp_export_ik:
            tmp_ik_bone_array = []
            for pose_bone_name in bone_uses_constraints:
                if bone_uses_constraints[pose_bone_name]:
                    tmp_ik_bone_array.append(pose_bone_name)

            # print(tmp_ik_bone_array)
            is_has_ik,key_stack_ik = _in_mix_SkeletonModification2DCCDIK(self.armature, tmp_ik_bone_array, rs_sub_ik)
            if (is_has_ik):
                rs_node_begin.append(f"modification_stack = SubResource(\"{key_stack_ik}\")")

        rs_node_begin.append("")
        
        # #========
        # # bones
        rs_bone = []
        for tmp_bone in tmp_bone_array:

            bone_name = tmp_bone["name"]
            tx = tmp_bone["x"]
            ty = tmp_bone["y"]

            rest_to = tmp_bone["rest_to"]
            length = tmp_bone['length']
            uparent = _get_bone_parents(self.armature, 'Skeleton2D', bone_name)

            rs_bone += (
                f"[node name=\"{_str_name(bone_name)}\" type=\"Bone2D\" parent=\"{uparent}\" ]",
                f"position = Vector2({tx},{ty})",
                f"rest = Transform2D(1, 0, 0, 1, {_str_float(rest_to[0])}, {_str_float(rest_to[1])})",
                f"auto_calculate_length_and_angle = false",
                f"length = {length}",
                f"bone_angle = 0.0",
                ""
            )

        # player
        rs_player = []
        rs_player.append("[node name=\"AnimationPlayer\" type=\"AnimationPlayer\" parent=\".\" ]")
        rs_player.append("callback_mode_process = 0")
        rs_player.append(f"libraries/ = SubResource(\"AnimationLibrary_{tmp_anim_lib_key}\")")
        rs_player.append("")

        rs_ext.append("\n")

        rs_scene += rs_ext
        rs_scene += rs_sub_ik
        rs_scene += rs_anim
        rs_scene += rs_node_begin
        rs_scene += rs_skin
        rs_scene += rs_bone
        rs_scene += rs_sprites
        rs_scene += rs_player

        str_out_scene = '\n'.join(rs_scene)
        text_file = open(path_scene_tscn, "w")
        text_file.write(str_out_scene)
        text_file.close()

        self.set_init_state(context)
        self.scene.coa_tools2.nla_mode = coa_nla_mode

        # cleanup scene and add an undo history step
        bpy.ops.ed.undo_push(message="Export Godot scene tscn")
        bpy.ops.ed.undo()
        bpy.ops.ed.undo_push(message="Export Godot scene tscn")

        self.report({"INFO"}, "Export successful.")
        return {"FINISHED"}

def _in_generate_texture_atlas(
    self,
    sprites,
    atlas_name,
    img_path,
    square,
    texture_bleed,
    img_width=512,
    img_height=1024,
    sprite_scale=1.0,
    margin=1
):
    global atlas_data
    atlas_data = {}

    context = bpy.context

    ### deselect all objects
    for obj in context.scene.objects:
        obj.select_set(False)

    ### get a list of all sprites and containing slots
    slots = []
    for sprite in sprites:
        if sprite.type == "MESH":
            if sprite.coa_tools2.type == "MESH":
                slots.append({"sprite": sprite, "slot": sprite.data})
            elif sprite.coa_tools2.type == "SLOT":
                for i, slot in enumerate(sprite.coa_tools2.slot):
                    slots.append({"sprite": sprite, "slot": slot.mesh})

    ### loop over all slots and create an object with slot assigned
    for slot in slots:
        dupli_sprite = slot["sprite"].copy()
        dupli_sprite.data = slot["slot"].copy()
        context.collection.objects.link(dupli_sprite)
        dupli_sprite.hide_set(False)
        dupli_sprite.select_set(True)
        context.view_layer.objects.active = dupli_sprite

        ### delete shapekeys
        if dupli_sprite.data.shape_keys != None:
            shapekeys = dupli_sprite.data.shape_keys.key_blocks
            for i in range(len(shapekeys)):
                shapekeys = dupli_sprite.data.shape_keys.key_blocks
                dupli_sprite.shape_key_remove(shapekeys[len(shapekeys) - 1])
        ### apply/delete modifieres
        for modifier in dupli_sprite.modifiers:
            if modifier.name == "coa_base_sprite" and modifier.type == "MASK":
                if len(dupli_sprite.data.vertices) > 4:
                    modifier.invert_vertex_group = True
                    with bpy.context.temp_override(
                        object=dupli_sprite, active_object=dupli_sprite
                    ):
                        if b_version_smaller_than((2, 90, 0)):
                            bpy.ops.object.modifier_apply(
                                apply_as="DATA", modifier=modifier.name
                            )
                        else:
                            bpy.ops.object.modifier_apply(modifier=modifier.name)
        for modifier in dupli_sprite.modifiers:
            dupli_sprite.modifiers.remove(modifier)

        ### delete vertex_groups
        for group in dupli_sprite.vertex_groups:
            dupli_sprite.vertex_groups.remove(group)

        ### assign mesh as vertex group
        dupli_sprite.vertex_groups.new(name=slot["slot"].name)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action="SELECT")
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                for region in area.regions:
                    if region.type == "WINDOW":
                        with bpy.context.temp_override(
                            area=area,
                            edict_object=dupli_sprite,
                            active_object=dupli_sprite,
                            object=dupli_sprite,
                            region=region,
                        ):
                            bpy.ops.object.vertex_group_assign()
                        break

        bpy.ops.object.mode_set(mode="OBJECT")

    img_atlas, tex_atlas_obj, atlas = TextureAtlasGenerator.generate_uv_layout(
        name="COA_UV_ATLAS",
        objects=context.selected_objects,
        width=2,
        height=2,
        max_width=img_width,
        max_height=img_height,
        margin=margin,
        texture_bleed=texture_bleed,
        square=square,
        output_scale=sprite_scale,
    )

    img_width = atlas.width
    img_height = atlas.height

    ### get uv coordinates
    bpy.ops.object.mode_set(mode="EDIT")

    bm = bmesh.from_edit_mesh(tex_atlas_obj.data)
    uv_layer = bm.loops.layers.uv["COA_UV_ATLAS"]

    sprite_data = []

    for group in tex_atlas_obj.vertex_groups:
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                for region in area.regions:
                    if region.type == "WINDOW":
                        override = context.copy()
                        with bpy.context.temp_override(
                            area=area,
                            edit_object=tex_atlas_obj,
                            active_object=tex_atlas_obj,
                            object=tex_atlas_obj,
                            region=region,
                        ):
                            bpy.ops.object.vertex_group_set_active(group=group.name)
                            bpy.ops.mesh.select_all(action="DESELECT")
                            bpy.ops.object.vertex_group_select()
                        break
        bmesh.update_edit_mesh(tex_atlas_obj.data)
        x = 1.0
        y = 1.0
        width = 0.0
        height = 0.0
        for vert in bm.verts:
            if vert.select:
                uv = _in_uv_from_vert_first(uv_layer, vert)
                x = min(uv[0], x)
                y = min(1 - uv[1], y)
                width = max(uv[0], width)
                height = max(1 - uv[1], height)
        width = width - x
        height = height - y

        x_px = int(img_width * x)
        y_px = int(img_height * y)
        width_px = abs(int(img_width * width))
        height_px = abs(int(img_height * height))

        sprite = {}
        sprite["name"] = group.name
        sprite["x"] = x_px
        sprite["y"] = y_px
        sprite["width"] = width_px
        sprite["height"] = height_px
        sprite_data.append(sprite)
        atlas_data[group.name] = {
            "width": width_px,
            "height": height_px,
            "output_scale": atlas.output_scale,
        }

    bpy.ops.object.mode_set(mode="OBJECT")
    ### collect sprite atlas data
    texture_atlas = {}
    texture_atlas["width"] = img_width
    texture_atlas["height"] = img_height
    texture_atlas["imagePath"] = atlas_name + "_tex.png"
    texture_atlas["name"] = self.scene.coa_tools2.project_name
    texture_atlas["SubTexture"] = sprite_data

    # if self.reduce_size:
    #     json_file = json.dumps(texture_atlas, separators=(",", ":"))
    # else:
    #     json_file = json.dumps(texture_atlas, indent="\t", sort_keys=False)

    # json_path = os.path.join(img_path, atlas_name + "_tex.json")
    # text_file = open(json_path, "w")
    # text_file.write(json_file)
    # text_file.close()

    compression_rate = int(context.scene.render.image_settings.compression)
    context.scene.render.image_settings.compression = 85
    texture_path = os.path.join(img_path, atlas_name + "_tex.png")
    img_atlas.save_render(texture_path)
    context.scene.render.image_settings.compression = compression_rate

    bpy.data.objects.remove(tex_atlas_obj, do_unlink=True)

    return texture_atlas
