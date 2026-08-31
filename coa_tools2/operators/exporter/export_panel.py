
import bpy
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
import math
from mathutils import Vector, Matrix, Quaternion, Euler
import shutil
from .texture_atlas_generator import TextureAtlasGenerator
from ... import constants



class COATOOLS2_PT_ExportPanel(bpy.types.Panel):
    bl_idname = "COATOOLS2_PT_export_panel"
    bl_label = "COA Export Panel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        self.scene = context.scene

        col = layout.column()
        col.prop(self.scene.coa_tools2, "project_name", text="Project Name")
        col.prop(self.scene.coa_tools2, "armature_name", text="Armature Name")
        col.prop(self.scene.coa_tools2, "export_path", text="Export Path")

        col = layout.column(align=True)
        row = col.row()
        row.prop(self.scene.coa_tools2, "runtime_format", expand=True)

        box = col.box()

        box_col = box.column()
        box_col.label(text="Atlas Settings:")
        row = box_col.row()
        row.prop(self.scene.coa_tools2, "atlas_mode", expand=True)
        subcol = box_col.column(align=True)
        subcol.prop(self.scene.coa_tools2, "sprite_scale", slider=True)
        if self.scene.coa_tools2.atlas_mode == "LIMIT_SIZE":
            subcol.prop(self.scene.coa_tools2, "atlas_resolution_x", text="X")
            subcol.prop(self.scene.coa_tools2, "atlas_resolution_y", text="Y")
        subcol.prop(self.scene.coa_tools2, "atlas_island_margin")
        # subcol.prop(self.scene.coa_tools2, "export_texture_bleed")

        row = subcol.row()
        row.prop(self.scene.coa_tools2, "image_format", expand=True)
        if self.scene.coa_tools2.image_format == "WEBP":
            subcol.prop(
                self.scene.coa_tools2, "image_quality", text="WebP Quality", slider=True
            )

        subcol.prop(self.scene.coa_tools2, "export_square_atlas")

        box_col.label(text="Data Settings:")
        subrow = box_col.row(align=True)

        runtime_format = self.scene.coa_tools2.runtime_format

        if runtime_format == "DRAGONBONES" or runtime_format == "GODOTSCENE":
            subrow.prop(self.scene.coa_tools2, "export_bake_anim")
            if self.scene.coa_tools2.export_bake_anim:
                subrow.prop(self.scene.coa_tools2, "export_bake_steps")

        if runtime_format == "GODOTSCENE":
            box_col.prop(self.scene.coa_tools2, "export_ik")

        if runtime_format != "GODOTSCENE":
            box_col.prop(self.scene.coa_tools2, "minify_json")
        box_col.prop(self.scene.coa_tools2, "armature_scale")

        if runtime_format == "CREATURE":
            op = col.operator("coa_tools2.export_creature", text="Export")
            op.export_path = self.scene.coa_tools2.export_path
            op.project_name = str(self.scene.coa_tools2.project_name).lower()

        elif runtime_format == "DRAGONBONES":
            op = col.operator("coa_tools2.export_dragon_bones", text="Export")
        elif runtime_format == "GODOTSCENE":
            op = col.operator("coa_tools2.export_godot_tscn", text="Export")
  
