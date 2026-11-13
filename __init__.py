# Bone Chain Renamer ver 1.0.1, made with love by Aesu <3

# dictionary
bl_info = {
    "name": "Bone Chain Renamer",
    "author": "Aesu3D",
    "version": (1, 0, 1),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar (N) > AESU > Bone Renamer",
    "description": "Rename bone chains with numbers, side suffixes and prefixes",
    "category": "Rigging",
}

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from mathutils import Vector

middle_gap = 0.0001
twin_reach = 0.002
alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


# settings
class AESU_RenamerSettings(bpy.types.PropertyGroup):
    base_name: StringProperty(
        name="Name",
        default="",
        description="Base name for the chain, numbers and sides are added after it",
    )
    first_number: IntProperty(
        name="Start At",
        default=1,
        min=0,
        description="Number given to the first bone of the chain",
    )
    prefix: StringProperty(
        name="Prefix",
        default="",
        description="Adds a prefix to the bone chain",
    )
    side_mode: EnumProperty(
        name="Side",
        items=[
            (
                "AUTO",
                "Auto",
                "Read _L/_R from the old name, otherwise from the bone position",
            ),
            ("NAME", "From Name", "Only use _L/_R found in the old name"),
            ("SPOT", "From Position", "Left of center is _L, right of center is _R"),
            ("NONE", "None", "Never add _L/_R"),
        ],
        default="AUTO",
    )
    do_twins: BoolProperty(
        name="Mirror Side Too",
        default=True,
        description="Also rename the matching chain on the other side",
    )
    pad_numbers: BoolProperty(
        name="Pad Numbers",
        default=False,
        description="Add pad numbers (01, 02, etc..)",
    )
    separator: StringProperty(
        name="Separator",
        default="",
        description="Adds a separator (- or _)",
    )


# helpers
def renamer_settings(context):
    return context.scene.aesu_bone_renamer


def bone_box(context):
    rig = context.active_object
    if rig.mode == "EDIT":
        return rig.data.edit_bones, rig.data.edit_bones.active
    return rig.data.bones, rig.data.bones.active


def bone_spot(bone):
    if isinstance(bone, bpy.types.EditBone):
        return bone.head
    return bone.head_local


def is_picked(rig, bone):
    if hasattr(bone, "select"):
        return bone.select
    pose_bone = rig.pose.bones.get(bone.name)
    if pose_bone is None:
        return False
    return pose_bone.select


# find which side the bone is on
def side_from_name(name):
    # ignore the ugly.001 blender adds to copies
    if "." in name:
        head, tail = name.rsplit(".", 1)
        if tail.isdigit():
            name = head

    low = name.lower().strip()

    # chop the name into pieces
    pieces = low.replace(".", " ").replace("_", " ").replace("-", " ").split()
    if "l" in pieces or "left" in pieces:
        return "_L"
    if "r" in pieces or "right" in pieces:
        return "_R"
    return ""


def side_from_spot(bone):
    x = bone_spot(bone).x
    if x > middle_gap:
        return "_L"
    if x < -middle_gap:
        return "_R"
    return ""


def which_side(bone, mode):
    if mode == "NONE":
        return ""
    if mode == "NAME":
        return side_from_name(bone.name)
    if mode == "SPOT":
        return side_from_spot(bone)
    side = side_from_name(bone.name)
    if side == "":
        side = side_from_spot(bone)
    return side


# branch & sorting
def branch_letter(index):
    # 0 = A, 1 = B ... 25 = Z, after that AA, AB, etc.!!
    if index < 26:
        return alphabet[index]
    return alphabet[index // 26 - 1] + alphabet[index % 26]


def kid_order(bone):
    spot = bone_spot(bone)
    return round(spot.y, 4), round(-spot.z, 4), round(abs(spot.x), 4), bone.name


# bone steppies (walk down the chain of bones)
def bone_steps(root, first_number):
    route = []
    to_do = [(root, "", first_number)]
    while to_do:
        bone, branch, number = to_do.pop()
        route.append((bone, branch, number))
        kids = sorted(bone.children, key=kid_order)
        for index in range(len(kids)):
            if len(kids) == 1:
                kid_branch = branch
            else:
                kid_branch = branch + branch_letter(index)
            to_do.append((kids[index], kid_branch, number + 1))
    return route


# mirrored bones
def find_twin(bones, bone):
    flipped = bpy.utils.flip_name(bone.name)
    if flipped != bone.name and flipped in bones:
        return bones[flipped]
    spot = bone_spot(bone)
    if abs(spot.x) <= middle_gap:
        return None  # bone is in the middle, no twin :(
    mirror_spot = Vector((-spot.x, spot.y, spot.z))
    closest = None
    closest_gap = twin_reach
    for other in bones:
        if other == bone:
            continue
        gap = (bone_spot(other) - mirror_spot).length
        if gap < closest_gap:
            closest = other
            closest_gap = gap
    return closest


# add prefix
def name_tag(settings, branch, number, side):
    clean_name = settings.base_name.strip()
    if settings.pad_numbers:
        shown_number = f"{number:02d}"
    else:
        shown_number = number
    return f"{settings.prefix}{clean_name}{settings.separator}{branch}{shown_number}{side}"


def plan_names(settings, root):
    plan = []
    for bone, branch, number in bone_steps(root, settings.first_number):
        side = which_side(bone, settings.side_mode)
        new_name = name_tag(settings, branch, number, side)
        plan.append((bone.name, new_name))
    return plan


# build n apply names
def make_names(bones, renames):
    waiting = []
    for old, new in renames:
        hold = f"__aesu_hold_{len(waiting)}"
        bones[old].name = hold
        waiting.append((hold, new))
    clashes = []
    for hold, new in waiting:
        bone = bones[hold]
        bone.name = new
        if bone.name != new:  # blender adds an ugly .001 again
            clashes.append(new)
    return clashes


def rig_ready(context):
    rig = context.active_object
    if rig is None:
        return False
    if rig.type != "ARMATURE":
        return False
    return rig.mode in {"OBJECT", "POSE", "EDIT"}


# buttons
class AESU_OT_rename_chain(bpy.types.Operator):
    bl_idname = "armature.aesu_rename_chain"
    bl_label = "Rename Chain"
    bl_description = "Rename the active bone and everything below it, numbered in order"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return rig_ready(context)

    def execute(self, context):
        settings = renamer_settings(context)
        if not settings.base_name.strip():
            self.report({"WARNING"}, "Type a name first")
            return {"CANCELLED"}
        bones, root = bone_box(context)  # get the bones n selected bone
        if root is None:
            self.report({"WARNING"}, "Click the first bone of the chain first")
            return {"CANCELLED"}

        renames = plan_names(settings, root)
        taken = []
        for old, new in renames:
            taken.append(old)

        if settings.do_twins:  # mirror
            twin = find_twin(bones, root)
            if twin is not None and twin.name not in taken:
                for old, new in plan_names(settings, twin):
                    if old not in taken:
                        renames.append((old, new))

        new_names = []  # safety check
        for old, new in renames:
            new_names.append(new)
        if len(set(new_names)) != len(new_names):
            self.report(
                {"WARNING"},
                "Two bones would get the same name, try Side: Auto or From Position",
            )
            return {"CANCELLED"}

        changes = []
        for old, new in renames:
            if old != new:
                changes.append((old, new))

        clashes = make_names(bones, changes)
        if clashes:
            self.report(
                {"WARNING"},
                f"Renamed {len(changes)} bones, but these names were already used elsewhere: {', '.join(clashes)}",
            )
        else:
            self.report({"INFO"}, f"Renamed {len(changes)} bones")
        return {"FINISHED"}


# add prefix buttons
class AESU_OT_stamp_prefix(bpy.types.Operator):
    bl_idname = "armature.aesu_stamp_prefix"
    bl_label = "Add Prefix"
    bl_description = "Add the prefix to the front of every selected bone"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return rig_ready(context)

    def execute(self, context):  # add prefix
        prefix = renamer_settings(context).prefix
        if not prefix:
            self.report({"WARNING"}, "Type a prefix first")
            return {"CANCELLED"}
        rig = context.active_object
        bones, active = bone_box(context)
        picked = []
        for bone in bones:
            if is_picked(rig, bone) and not bone.name.startswith(prefix):
                picked.append(bone.name)
        for name in picked:
            bones[name].name = prefix + name
        self.report({"INFO"}, f"Added '{prefix}' to {len(picked)} bones")
        return {"FINISHED"}


# remove prefix buttons
class AESU_OT_peel_prefix(bpy.types.Operator):
    bl_idname = "armature.aesu_peel_prefix"
    bl_label = "Remove Prefix"
    bl_description = "Remove the prefix from the front of every selected bone"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return rig_ready(context)

    def execute(self, context):
        prefix = renamer_settings(context).prefix
        if not prefix:
            self.report({"WARNING"}, "Type a prefix first")
            return {"CANCELLED"}
        rig = context.active_object
        bones, active = bone_box(context)
        picked = []
        for bone in bones:
            if not is_picked(rig, bone):
                continue
            if bone.name.startswith(prefix) and len(bone.name) > len(prefix):
                picked.append(bone.name)
        for name in picked:
            bones[name].name = name[len(prefix):]
        self.report({"INFO"}, f"Removed '{prefix}' from {len(picked)} bones")
        return {"FINISHED"}


# sidebar, note to self: PT = Panel Type
class AESU_PT_bone_renamer(bpy.types.Panel):
    bl_label = "Bone Chain Renamer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AESU"

    @classmethod  # only show when armature's selected. hashtag clean
    def poll(cls, context):
        return (
                context.active_object is not None
                and context.active_object.type == "ARMATURE"
        )

    def draw(self, context):
        settings = renamer_settings(context)
        layout = self.layout
        column = layout.column()

        active = None
        if rig_ready(context):
            bones, active = bone_box(context)
        if active:
            first_bone = active.name
        else:
            first_bone = "none"
        column.label(text=f"First bone: {first_bone}", icon="BONE_DATA")

        column.prop(settings, "base_name")
        column.prop(settings, "separator")
        column.prop(settings, "first_number")
        column.prop(settings, "prefix")
        column.prop(settings, "side_mode")
        column.prop(settings, "do_twins")
        column.prop(settings, "pad_numbers")

        if settings.side_mode == "NONE":
            example_side = ""
        else:
            example_side = "_L"
        preview = name_tag(settings, "", settings.first_number, example_side)
        column.label(text=f"Example: {preview}")

        column.operator(AESU_OT_rename_chain.bl_idname, icon="SORTALPHA")
        layout.separator()
        row = layout.row(align=True)
        row.operator(AESU_OT_stamp_prefix.bl_idname, icon="ADD")
        row.operator(AESU_OT_peel_prefix.bl_idname, icon="REMOVE")


# register/unregister
rig_classes = (  # tuple
    AESU_RenamerSettings,
    AESU_OT_rename_chain,
    AESU_OT_stamp_prefix,
    AESU_OT_peel_prefix,
    AESU_PT_bone_renamer,
)


def register():  # turn addon on
    for rig_class in rig_classes:
        bpy.utils.register_class(rig_class)
    bpy.types.Scene.aesu_bone_renamer = PointerProperty(type=AESU_RenamerSettings)


def unregister():  # turn addon off
    del bpy.types.Scene.aesu_bone_renamer
    for rig_class in reversed(rig_classes):
        bpy.utils.unregister_class(rig_class)


if __name__ == "__main__":
    register()
