import bpy
from bpy.types import Operator
from bpy import props
from bpy.utils import register_class, unregister_class
from bpy_extras.io_utils import ExportHelper, ImportHelper
from mathutils import Vector
from . node_mapping import ReNimNodeMappingBone
import logging
import json


class ReNimOperator:
    bl_options = {"REGISTER", "UNDO"}

    node_tree_name: props.StringProperty(
        default="", options={"HIDDEN"})  # type: ignore
    node_source_target_name: props.StringProperty(
        default="", options={"HIDDEN"})  # type: ignore

    @classmethod
    def poll(cls, context):
        return context.space_data.type == "NODE_EDITOR" and context.space_data.tree_type == "ReNimNode"  # type: ignore


class ReNimOperatorToggleBind(ReNimOperator, Operator):
    """Bind armature from node object"""
    bl_idname = "renim.toggle_bind"
    bl_label = "Bind"

    def execute(self, context):
        node_tree_name = self.node_tree_name
        node_name = self.node_source_target_name

        assert node_tree_name
        assert node_name

        node_source_target = bpy.data.node_groups[node_tree_name].nodes[node_name]

        if callable(getattr(node_source_target, "toggle_bind")):
            node_source_target.toggle_bind(context, self)
        else:
            self.report({"ERROR"}, "Operator Can Only Call From ReNim Node")

        return {"FINISHED"}


class ReNimOperatorConnectSelectedBoneNodes(ReNimOperator, Operator):
    """Connect selected bone nodes to object node"""
    bl_idname = "renim.connect_selected_bone_nodes"
    bl_label = "Connect Selected Bone Nodes"

    def execute(self, context):
        node_tree_name = self.node_tree_name
        node_name = self.node_source_target_name

        assert node_tree_name
        assert node_name

        node_source_target = bpy.data.node_groups[node_tree_name].nodes[node_name]

        # node group
        node_group = node_source_target.id_data

        # links
        links = node_group.links

        # filter selected nodes
        bone_nodes = [
            node for node in context.selected_nodes if isinstance(node, ReNimNodeMappingBone)]

        # link bone node to object
        for bone_node in bone_nodes:
            links.new(node_source_target.outputs[0], bone_node.inputs[0])

        return {"FINISHED"}


class ReNimOperatorCreateBoneNodeFromSelectedBones(ReNimOperator, Operator):
    """Create bone node from selected bones"""
    bl_idname = "renim.create_bone_node_from_selected_bones"
    bl_label = "Create Bone Node From Selected Bones"

    @classmethod
    def poll(cls, context):
        return context.space_data.type == "NODE_EDITOR" and context.space_data.tree_type == "ReNimNode" and context.mode == "POSE" and (bool(context.selected_pose_bones) and len(context.selected_pose_bones) == 2 and len(list(set([pose_bone.id_data for pose_bone in context.selected_pose_bones]))) == 2)

    def execute(self, context):
        node_tree_name = self.node_tree_name
        node_name = self.node_source_target_name

        assert node_tree_name
        assert node_name

        node_source_target = bpy.data.node_groups[node_tree_name].nodes[node_name]

        # node group
        node_group = node_source_target.id_data

        # links
        links = node_group.links

        # target and source object
        target_object = node_source_target.outputs[0].target_object
        source_object = node_source_target.outputs[0].source_object

        # crate bone node
        bone_node = node_group.nodes.new("ReNimNodeMappingBone")

        # set location
        bone_node.location = Vector(
            (node_source_target.width + 100, 0)) + node_source_target.location

        # create tuple list pose bone for selected_pose_bones (object , bone name)
        selected_pose_bones = [(pose_bone.id_data, pose_bone.name)
                               for pose_bone in context.selected_pose_bones]

        # set bone from pose bone to node
        bone_node.bone_target = next(iter([pose_bone_name for pose_bone_object, pose_bone_name in selected_pose_bones if pose_bone_object ==
                                           target_object]), context.selected_pose_bones[1].name) if target_object else context.selected_pose_bones[1].name  # type: ignore
        bone_node.bone_source = next(iter([pose_bone_name for pose_bone_object, pose_bone_name in selected_pose_bones if pose_bone_object ==
                                           source_object]), context.selected_pose_bones[0].name) if source_object else context.selected_pose_bones[0].name  # type: ignore

        # unselect bone node
        bone_node.select = False

        # link node socket to bone node socket
        links.new(node_source_target.outputs[0], bone_node.inputs[0])

        return {"FINISHED"}


class ReNimOperatorLoadPreset(ReNimOperator, Operator, ImportHelper):  # type: ignore
    """Load bone node from json file"""
    bl_idname = "renim.load_preset"
    bl_label = "Load Preset Bone"

    filename_ext = ".json"

    filter_glob: props.StringProperty(  # type: ignore
        default="*.json",
        options={"HIDDEN"},
        maxlen=255
    )

    def execute(self, context):
        node_tree_name = self.node_tree_name
        node_name = self.node_source_target_name
        filepath = self.filepath  # type: ignore

        assert node_tree_name
        assert node_name
        assert filepath

        node_source_target = bpy.data.node_groups[node_tree_name].nodes[node_name]
        if hasattr(node_source_target, "additional_bone_to_bake"):
            # node group
            node_group = node_source_target.id_data

            # load the file
            file = open(filepath, "r")
            data_nodes = json.loads(file.read())
            file.close()

            for node_name, node_data in data_nodes["nodes"].items():
                # crate bone node
                node = node_group.nodes.new(node_data["type"])

                # set node to nodes data
                data_nodes["nodes"][node_name]["node"] = node

                # set label
                node.label = node_data["label"]

                # set width, height, and hide
                node.width = node_data["width"]
                node.height = node_data["height"]
                node.hide = node_data["hide"]

                # set location
                node.location = Vector(
                    node_data["location"]) + node_source_target.location

                # set parent
                node.parent = data_nodes["nodes"][node_data["parent"]
                                                  ]["node"] if node_data["parent"] else None

                # unselect bone node
                node.select = False

                if node_data["type"] == "ReNimNodeMappingBone":
                    node.bone_target = node_data["bone_target"]
                    node.bone_source = node_data["bone_source"]

                    node.use_location = node_data["use_location"]
                    node.location_axis = node_data["location_axis"]
                    node.location_influence = node_data["location_influence"]
                    node.location_multiply = node_data["location_multiply"]
                    node.location_offset = node_data["location_offset"]

                    node.use_rotation_euler = node_data["use_rotation_euler"]
                    node.rotation_euler_axis = node_data["rotation_euler_axis"]
                    node.rotation_euler_influence = node_data["rotation_euler_influence"]
                    node.rotation_euler_multiply = node_data["rotation_euler_multiply"]
                    node.rotation_euler_offset = node_data["rotation_euler_offset"]

                    node.use_scale = node_data["use_scale"]
                    node.scale_axis = node_data["scale_axis"]
                    node.scale_influence = node_data["scale_influence"]
                    node.scale_multiply = node_data["scale_multiply"]
                    node.scale_offset = node_data["scale_offset"]
                    node.mix_mode = node_data["mix_mode"]

            self.report({"INFO"}, "Load Preset Success")
        else:
            self.report({"ERROR"}, "Operator Can Only Call From ReNim Node")

        return {"FINISHED"}


class ReNimOperatorSavePreset(ReNimOperator, Operator, ExportHelper):  # type: ignore
    """Save current bone node to json file"""
    bl_idname = "renim.save_preset"
    bl_label = "Save Preset Bone"

    filename_ext = ".json"

    filter_glob: props.StringProperty(  # type: ignore
        default="*.json",
        options={"HIDDEN"},
        maxlen=255
    )

    def execute(self, context):
        node_tree_name = self.node_tree_name
        node_name = self.node_source_target_name
        filepath = self.filepath  # type: ignore

        assert node_tree_name
        assert node_name
        assert filepath

        node_source_target = bpy.data.node_groups[node_tree_name].nodes[node_name]

        if hasattr(node_source_target, "additional_bone_to_bake"):
            # node group
            node_group = node_source_target.id_data
            # get bone node and frame from node group
            nodes = [node for node in node_group.nodes if node.type ==
                     "FRAME" or isinstance(node, ReNimNodeMappingBone)]
            # nodes = [node for node in node_group.nodes if isinstance(node, ReNimNodeMappingBone)]
            data_to_save = {
                "version": [0, 0, 1],
                "nodes": {}
            }

            for node in nodes:
                location = list((node.location + node.parent.location) - node_source_target.location) if node.parent else list(  # type: ignore
                    node.location - node_source_target.location)  # type: ignore
                data_to_save["nodes"][node.name] = {
                    "type": "NodeFrame" if node.type == "FRAME" else "ReNimNodeMappingBone",
                    "label": node.label,
                    "location": location,
                    "width": node.width,
                    "height": node.height,
                    "hide": node.hide,
                    "parent": node.parent.name if node.parent else None,
                    "bone_target": getattr(node, "bone_target", ""),
                    "bone_source": getattr(node, "bone_source", ""),
                    "use_location": getattr(node, "use_location", None),
                    "location_axis": list(getattr(node, "location_axis", "")),
                    "location_influence": list(getattr(node, "location_influence", "")),
                    "location_multiply": list(getattr(node, "location_multiply", "")),
                    "location_offset": list(getattr(node, "location_offset", "")),
                    "use_rotation_euler": getattr(node, "use_rotation_euler", None),
                    "rotation_euler_axis": list(getattr(node, "rotation_euler_axis", "")),
                    "rotation_euler_influence": list(getattr(node, "rotation_euler_influence", "")),
                    "rotation_euler_multiply": list(getattr(node, "rotation_euler_multiply", "")),
                    "rotation_euler_offset": list(getattr(node, "rotation_euler_offset", "")),
                    "use_scale": getattr(node, "use_scale", None),
                    "scale_axis": list(getattr(node, "scale_axis", "")),
                    "scale_influence": list(getattr(node, "scale_influence", "")),
                    "scale_multiply": list(getattr(node, "scale_multiply", "")),
                    "scale_offset": list(getattr(node, "scale_offset", "")),
                    "mix_mode": getattr(node, "mix_mode", ""),
                }

            # save to the file
            file = open(filepath, "w+")
            file.write(json.dumps(data_to_save, indent=4))
            file.close()

            self.report({"INFO"}, "Save Preset Success")
        else:
            self.report({"ERROR"}, "Operator Can Only Call From ReNim Node")

        return {"FINISHED"}


class ReNimOperatorAddAdditionalBoneToBake(ReNimOperator, Operator):
    """Add additional bone to bake"""
    bl_idname = "renim.add_additional_bone_to_bake"
    bl_label = "Add Bone"

    def execute(self, context):
        node_tree_name = self.node_tree_name
        node_name = self.node_source_target_name

        assert node_tree_name
        assert node_name

        node_source_target = bpy.data.node_groups[node_tree_name].nodes[node_name]

        if hasattr(node_source_target, "additional_bone_to_bake"):
            node_source_target.additional_bone_to_bake.add()
        else:
            self.report({"ERROR"}, "Operator Can Only Call From ReNim Node")

        return {"FINISHED"}


class ReNimOperatorRemoveAdditionalBoneToBake(ReNimOperator, Operator):
    """Remove additional bone to bake"""
    bl_idname = "renim.remove_additional_bone_to_bake"
    bl_label = "Remove Bone"

    index: props.IntProperty(default=-1)  # type: ignore

    def execute(self, context):
        node_tree_name = self.node_tree_name
        node_name = self.node_source_target_name
        index = self.index

        assert node_tree_name
        assert node_name
        assert index > -1

        node_source_target = bpy.data.node_groups[node_tree_name].nodes[node_name]

        if hasattr(node_source_target, "additional_bone_to_bake"):
            node_source_target.additional_bone_to_bake.remove(index)
        else:
            self.report({"ERROR"}, "Operator Can Only Call From ReNim Node")

        return {"FINISHED"}


class ReNimOperatorBakeAction(ReNimOperator, Operator):
    """Bake animation to action"""
    bl_idname = "renim.bake_action"
    bl_label = "Bake Action"

    action_name: props.StringProperty(default="BakeAction")  # type: ignore
    start_frame: props.IntProperty(default=1)  # type: ignore
    end_frame: props.IntProperty(default=250)  # type: ignore
    frame_step: props.IntProperty(default=1)  # type: ignore
    unbind_after_bake: props.BoolProperty(default=False)  # type: ignore

    def execute(self, context):
        node_tree_name = self.node_tree_name
        node_name = self.node_source_target_name
        action_name = self.action_name
        start_frame = self.start_frame
        end_frame = self.end_frame
        frame_step = self.frame_step
        unbind_after_bake = self.unbind_after_bake

        assert node_tree_name
        assert node_name
        assert action_name
        assert start_frame < end_frame
        assert frame_step > 0

        node_source_target = bpy.data.node_groups[node_tree_name].nodes[node_name]

        if hasattr(node_source_target, "additional_bone_to_bake"):
            # get output socket node
            socket_node = node_source_target.outputs[0]

            # target and source object from socket
            target_object = socket_node.target_object
            # source_object = socket_node.source_object

            # store current mode
            old_mode = "OBJECT"

            # store current active object
            old_active_object = context.active_object

            # change mode to object if current mode is not object
            if bpy.context.mode != "OBJECT":
                # overide current mode if not object
                old_mode = context.active_object.mode if context.active_object else context.mode
                bpy.ops.object.mode_set(mode="OBJECT")

            # store selected object for seamless binding
            selected_objects = context.selected_objects

            # deselect all objects
            bpy.ops.object.select_all(action="DESELECT")

            # set target object as active object
            context.view_layer.objects.active = target_object

            # change to pose mode
            bpy.ops.object.mode_set(mode="POSE")

            # deselect all bones
            bpy.ops.pose.select_all(action="DESELECT")

            # target and source pose bones
            target_pose_bones = target_object.pose.bones
            # source_pose_bones = source_object.pose.bones

            # get bone nodes to bake for link socket and set to tuple list (bone name, *[transform to bake])
            bake_bone_from_nodes = [(link.to_node.bone_target, link.to_node.use_location, link.to_node.use_rotation_euler, link.to_node.use_scale)
                                    for link in socket_node.links if isinstance(link.to_node, ReNimNodeMappingBone) and link.to_node.is_bind_valid]

            # get additional bones to bake
            additional_bones = node_source_target.additional_bone_to_bake

            # set to tuple list (bone name, *[transform to bake])
            additional_bones = [(bone_group.bone_name, *bone_group.translation)
                                for bone_group in additional_bones]

            # merge bone nodes and additional bones
            bake_bones = bake_bone_from_nodes + additional_bones

            # remove duplicate
            bake_bones = list(set(bake_bones))

            # check if bone exist and add current transform space | tuple(pose bone, *[transform to bake], location, rotation, scale)
            bake_bones = [(target_pose_bones[bone_name], bake_location, bake_rotation, bake_scale, target_pose_bones[bone_name].location.copy(), target_pose_bones[bone_name].rotation_quaternion.copy() if target_pose_bones[bone_name].rotation_mode ==
                           "QUATERNION" else target_pose_bones[bone_name].rotation_euler.copy(), target_pose_bones[bone_name].scale.copy()) for bone_name, bake_location, bake_rotation, bake_scale in bake_bones if target_pose_bones.get(bone_name)]

            # create new action
            action = bpy.data.actions.new(action_name)

            # set fake user for action
            action.use_fake_user = True

            # set action to target object
            target_object.animation_data.action = action

            # store curent frame
            old_current_frame = context.scene.frame_current

            # start baking
            frame = self.start_frame
            while frame <= self.end_frame:
                context.scene.frame_set(frame)

                for pose_bone, is_bake_location, is_bake_rotation, is_bake_scale, ori_location, ori_rotation, ori_scale in bake_bones:
                    # set location transform value to original value prevent value from last keyframe
                    if is_bake_location:
                        pose_bone.location = ori_location

                    # set rotation transform value to original value prevent value from last keyframe
                    if is_bake_rotation:
                        # 2 rotation mode
                        if pose_bone.rotation_mode == "QUATERNION":
                            pose_bone.rotation_quaternion = ori_rotation
                        else:
                            pose_bone.rotation_euler = ori_rotation

                    # set scale transform value to original value prevent value from last keyframe
                    if is_bake_scale:
                        pose_bone.scale = ori_scale

                # update pose scene after set original transform
                # update scene once in loop for better performance
                context.view_layer.update()

                for pose_bone, is_bake_location, is_bake_rotation, is_bake_scale, ori_location, ori_rotation, ori_scale in bake_bones:
                    # bake location
                    if is_bake_location:
                        pose_bone.keyframe_insert(
                            "location", options={"INSERTKEY_VISUAL"}, group=pose_bone.name + " (loc)")

                    # bake rotation
                    if is_bake_rotation:
                        pose_bone.keyframe_insert("rotation_quaternion", options={
                                                  "INSERTKEY_VISUAL"}, group=pose_bone.name + " (rot quat)")
                        pose_bone.keyframe_insert("rotation_euler", options={
                                                  "INSERTKEY_VISUAL"}, group=pose_bone.name + " (rot euler)")

                    # bake scale
                    if is_bake_scale:
                        pose_bone.keyframe_insert(
                            "scale", options={"INSERTKEY_VISUAL"}, group=pose_bone.name + " (scale)")

                frame += self.frame_step

            # change interpolation to LINEAR
            for fcurve in action.fcurves:
                for keyFramePoints in fcurve.keyframe_points:
                    keyFramePoints.interpolation = "LINEAR"

            # unassign action from target object
            target_object.animation_data.action = None

            # restore current frame
            context.scene.frame_set(old_current_frame)

            # change to pose mode
            bpy.ops.object.mode_set(mode="OBJECT")

            # restore selected objects
            for obj in selected_objects:
                obj.select_set(True)

            # change active object to old object
            context.view_layer.objects.active = old_active_object

            # change to old mode if not object
            if old_mode != "OBJECT":
                bpy.ops.object.mode_set(mode=old_mode)

            if unbind_after_bake and callable(getattr(node_source_target, "unbind")):
                node_source_target.unbind(context, self)

            self.report({"INFO"}, "Bake Action Success")
        else:
            self.report({"ERROR"}, "Operator Can Only Call From ReNim Node")

        return {"FINISHED"}


classes = [
    ReNimOperatorToggleBind,
    ReNimOperatorConnectSelectedBoneNodes,
    ReNimOperatorCreateBoneNodeFromSelectedBones,
    ReNimOperatorLoadPreset,
    ReNimOperatorSavePreset,
    ReNimOperatorAddAdditionalBoneToBake,
    ReNimOperatorRemoveAdditionalBoneToBake,
    ReNimOperatorBakeAction,
]


def register():
    for x in classes:
        register_class(x)


def unregister():
    for x in reversed(classes):
        unregister_class(x)
