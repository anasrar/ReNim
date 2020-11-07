import json
import bpy
from bpy.types import Operator
from bpy.utils import register_class, unregister_class
from mathutils import Vector
from bpy_extras.io_utils import ExportHelper, ImportHelper
from . node_mapping import NODE_BONE

class RENIM_OP_Base(Operator):
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        return context.space_data.type == "NODE_EDITOR" and context.space_data.tree_type == "ReNimNode"

class RENIM_OP_OBJCET_BIND(RENIM_OP_Base):
    """bind armature from node object"""
    bl_idname = "renim.bind"
    bl_label = "BIND"

    node_tree_name: bpy.props.StringProperty(default="")
    node_object_name: bpy.props.StringProperty(default="")

    @classmethod
    def poll(cls, context):
        return context.space_data.type == "NODE_EDITOR" and context.space_data.tree_type == "ReNimNode"

    def execute(self, context):
        # get node
        node = bpy.data.node_groups[self.node_tree_name].nodes[self.node_object_name]

        is_bind = node.is_bind

        if not is_bind:
            # BIND
            node.bind(context)
        else:
            # UNBIND
            node.unbind(context)

        return {'FINISHED'}

class RENIM_OP_OBJCET_CONNECT_SELECTED_BONE_NODES(RENIM_OP_Base):
    """connect selected bone nodes to object node"""
    bl_idname = "renim.conect_selected_bone_nodes"
    bl_label = "Connect Selected Bone Nodes"

    node_tree_name: bpy.props.StringProperty(default="")
    node_object_name: bpy.props.StringProperty(default="")

    @classmethod
    def poll(cls, context):
        return context.space_data.type == "NODE_EDITOR" and context.space_data.tree_type == "ReNimNode"

    def execute(self, context):
        # get node
        node = bpy.data.node_groups[self.node_tree_name].nodes[self.node_object_name]

        # node group
        node_group = node.id_data

        # links
        links = node_group.links

        # filter selected nodes
        bone_nodes = [node for node in context.selected_nodes if isinstance(node, NODE_BONE)]

        # link bone node to object
        for bone_node in bone_nodes:
            links.new(node.outputs[0], bone_node.inputs[0])

        return {'FINISHED'}

class RENIM_OP_OBJCET_CREATE_BONE_NODE_FROM_SELECTED_BONE(RENIM_OP_Base):
    """create bone node from selected bones"""
    bl_idname = "renim.create_bone_node_from_selected_bones"
    bl_label = "Create Bone Node From Selected Bones"

    @classmethod
    def poll(cls, context):
        return context.space_data.type == "NODE_EDITOR" and context.space_data.tree_type == "ReNimNode" and context.mode == "POSE" and (bool(context.selected_pose_bones) and len(context.selected_pose_bones) == 2 and len(list(set([pose_bone.id_data for pose_bone in context.selected_pose_bones]))) == 2)

    node_tree_name: bpy.props.StringProperty(default="")
    node_object_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        # get node
        node = bpy.data.node_groups[self.node_tree_name].nodes[self.node_object_name]

        # node group
        node_group = node.id_data

        # links
        links = node_group.links

        # target and source object
        target_object = node.outputs[0].target_object
        source_object = node.outputs[0].source_object

        # crate bone node
        bone_node = node_group.nodes.new('NODE_RENIM_BONE')

        # set location
        bone_node.location = Vector((node.width + 100, 0)) + node.location

        # create tuple list pose bone for selected_pose_bones (object , bone name)
        selected_pose_bones = [(pose_bone.id_data, pose_bone.name) for pose_bone in context.selected_pose_bones]

        # set bone from pose bone to node
        bone_node.bone_target = next(iter([pose_bone_name for pose_bone_object, pose_bone_name in selected_pose_bones if pose_bone_object == target_object]), context.selected_pose_bones[1].name) if target_object else context.selected_pose_bones[1].name
        bone_node.bone_source = next(iter([pose_bone_name for pose_bone_object, pose_bone_name in selected_pose_bones if pose_bone_object == source_object]), context.selected_pose_bones[0].name) if source_object else context.selected_pose_bones[0].name

        # unselect bone node
        bone_node.select = False

        # store selected object for seamless binding
        selected_objects = context.selected_objects

        # link node socket to bone node socket
        links.new(node.outputs[0], bone_node.inputs[0])

        # back to pose mode for seamless workflow
        # commented becuse we already handle in bone node
        # if node.is_bind:
        #     for obj in selected_objects:
        #         obj.select_set(True)
        #     bpy.ops.object.mode_set(mode='POSE')

        return {'FINISHED'}

class RENIM_OP_OBJCET_LOAD_PRESET(RENIM_OP_Base, ImportHelper):
    """load bone node from json file"""
    bl_idname = "renim.load_preset"
    bl_label = "Load Preset Bone"

    filename_ext = ".json"

    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255
    )

    node_tree_name: bpy.props.StringProperty(default="", options={'HIDDEN'})
    node_object_name: bpy.props.StringProperty(default="", options={'HIDDEN'})

    def execute(self, context):
        # get node
        node = bpy.data.node_groups[self.node_tree_name].nodes[self.node_object_name]

        # node group
        node_group = node.id_data

        # load the file
        file = open(self.filepath, "r")

        nodes_data = json.loads(file.read())

        file.close()

        for node_name, node_data in nodes_data['nodes'].items():
            # crate bone node
            new_node = node_group.nodes.new(('NodeFrame' if node_data['type'] == "FRAME" else 'NODE_RENIM_BONE'))

            # set node to nodes data
            nodes_data['nodes'][node_name]['node'] = new_node

            # set label
            new_node.label = node_data['label']

            # set width, height, and hide
            new_node.width = node_data['width']
            new_node.height = node_data['height']
            new_node.hide = node_data['hide']

            # set location
            new_node.location = (Vector(node_data['location']) + node.location)

            # set parent
            new_node.parent = nodes_data['nodes'][node_data['parent']]['node'] if node_data['parent'] else None

            # unselect bone node
            new_node.select = False

            if node_data['type'] == "NODE_BONE":
                new_node.bone_target = nodes_data['nodes'][node_name]['bone_target']
                new_node.bone_source = nodes_data['nodes'][node_name]['bone_source']

                new_node.use_location = nodes_data['nodes'][node_name]['use_location']
                new_node.location_axis = nodes_data['nodes'][node_name]['location_axis']
                new_node.location_influence = nodes_data['nodes'][node_name]['location_influence']
                new_node.location_multiply = nodes_data['nodes'][node_name]['location_multiply']
                new_node.location_offset = nodes_data['nodes'][node_name]['location_offset']

                new_node.use_rotation_euler = nodes_data['nodes'][node_name]['use_rotation_euler']
                new_node.rotation_euler_axis = nodes_data['nodes'][node_name]['rotation_euler_axis']
                new_node.rotation_euler_influence = nodes_data['nodes'][node_name]['rotation_euler_influence']
                new_node.rotation_euler_multiply = nodes_data['nodes'][node_name]['rotation_euler_multiply']
                new_node.rotation_euler_offset = nodes_data['nodes'][node_name]['rotation_euler_offset']

                new_node.use_scale = nodes_data['nodes'][node_name]['use_scale']
                new_node.scale_axis = nodes_data['nodes'][node_name]['scale_axis']
                new_node.scale_influence = nodes_data['nodes'][node_name]['scale_influence']
                new_node.scale_multiply = nodes_data['nodes'][node_name]['scale_multiply']
                new_node.scale_offset = nodes_data['nodes'][node_name]['scale_offset']

        # simple alert
        self.report({'INFO'}, "LOAD PRESET SUCCESS")

        return {'FINISHED'}

class RENIM_OP_OBJCET_SAVE_PRESET(RENIM_OP_Base, ExportHelper):
    """save current bone node to json file"""
    bl_idname = "renim.save_preset"
    bl_label = "Save Preset Bone"

    filename_ext = ".json"

    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255
    )

    node_tree_name: bpy.props.StringProperty(default="", options={'HIDDEN'})
    node_object_name: bpy.props.StringProperty(default="", options={'HIDDEN'})

    def execute(self, context):
        # get node
        node = bpy.data.node_groups[self.node_tree_name].nodes[self.node_object_name]

        # node group
        node_group = node.id_data

        # get bone node and frame from node group
        nodes_to_save = [nd for nd in node_group.nodes if nd.type == "FRAME" or isinstance(nd, NODE_BONE)]
        # nodes_to_save = [nd for nd in node_group.nodes if isinstance(nd, NODE_BONE)]

        # some dummy dict to convert to json
        string_data = {
            "version": [0, 0, 1],
            "nodes": {}
        }

        for nd in nodes_to_save:
            string_data["nodes"][nd.name] = {
                "type": "FRAME" if nd.type == "FRAME" else "NODE_BONE",
                "label": nd.label,
                "location": list((nd.location + nd.parent.location) - node.location) if nd.parent else (list(nd.location - node.location)),
                "width": nd.width,
                "height": nd.height,
                "hide": nd.hide,
                "parent": nd.parent.name if nd.parent else None,
                "bone_target": getattr(nd, "bone_target", ""),
                "bone_source": getattr(nd, "bone_source", ""),
                "use_location": getattr(nd, "use_location", None),
                "location_axis": list(getattr(nd, "location_axis", "")),
                "location_influence": list(getattr(nd, "location_influence", "")),
                "location_multiply": list(getattr(nd, "location_multiply", "")),
                "location_offset": list(getattr(nd, "location_offset", "")),
                "use_rotation_euler": getattr(nd, "use_rotation_euler", None),
                "rotation_euler_axis": list(getattr(nd, "rotation_euler_axis", "")),
                "rotation_euler_influence": list(getattr(nd, "rotation_euler_influence", "")),
                "rotation_euler_multiply": list(getattr(nd, "rotation_euler_multiply", "")),
                "rotation_euler_offset": list(getattr(nd, "rotation_euler_offset", "")),
                "use_scale": getattr(nd, "use_scale", None),
                "scale_axis": list(getattr(nd, "scale_axis", "")),
                "scale_influence": list(getattr(nd, "scale_influence", "")),
                "scale_multiply": list(getattr(nd, "scale_multiply", "")),
                "scale_offset": list(getattr(nd, "scale_offset", ""))
            }

        # save to the file
        file = open(self.filepath, "w+")
        file.write(json.dumps(string_data, indent=4))
        file.close()

        # simple alert
        self.report({'INFO'}, "SAVE PRESET SUCCESS")

        return {'FINISHED'}

class RENIM_OP_OBJCET_ADD_BONE_TO_BAKE(RENIM_OP_Base):
    """add bone to node object"""
    bl_idname = "renim.add_bone_to_bake"
    bl_label = "ADD BONE"

    node_tree_name: bpy.props.StringProperty(default="")
    node_object_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        # get node
        node = bpy.data.node_groups[self.node_tree_name].nodes[self.node_object_name]

        # add new bone collection
        node.additional_bone_to_bake.add()

        return {'FINISHED'}

class RENIM_OP_OBJCET_REMOVE_BONE_TO_BAKE(RENIM_OP_Base):
    """remove bone from node object"""
    bl_idname = "renim.remove_bone_to_bake"
    bl_label = "REMOVE BONE"

    node_tree_name: bpy.props.StringProperty(default="")
    node_object_name: bpy.props.StringProperty(default="")
    index: bpy.props.IntProperty(default=-1)

    def execute(self, context):
        # get node
        node = bpy.data.node_groups[self.node_tree_name].nodes[self.node_object_name]

        # remove bone from collection
        node.additional_bone_to_bake.remove(self.index)

        return {'FINISHED'}

class RENIM_OP_OBJCET_BAKE_ACTION(RENIM_OP_Base):
    """bake animation to action"""
    bl_idname = "renim.bake_action"
    bl_label = "BAKE ACTION"

    node_tree_name: bpy.props.StringProperty(default="")
    node_object_name: bpy.props.StringProperty(default="")

    action_name: bpy.props.StringProperty(default="BakeAction")
    start_frame: bpy.props.IntProperty(default=1)
    end_frame: bpy.props.IntProperty(default=250)
    frame_step: bpy.props.IntProperty(default=1)
    unbind_after_bake: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        # get node
        node = bpy.data.node_groups[self.node_tree_name].nodes[self.node_object_name]

        # get output socket node
        socket_node = node.outputs[0]

        # target and source object from socket
        target_object = socket_node.target_object
        source_object = socket_node.source_object

        # store current mode
        old_mode = 'OBJECT'

        # store current active object
        old_active_object = context.active_object

        # change mode to object if current mode is not object
        if bpy.context.mode != "OBJECT":
            # overide current mode if not object
            old_mode = context.active_object.mode if context.active_object else context.mode
            bpy.ops.object.mode_set(mode='OBJECT')

        # store selected object for seamless binding
        selected_objects = context.selected_objects

        # deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # set target object as active object
        context.view_layer.objects.active = target_object

        # change to pose mode
        bpy.ops.object.mode_set(mode='POSE')

        # deselect all bones
        bpy.ops.pose.select_all(action='DESELECT')

        # target and source pose bones
        target_pose_bones = target_object.pose.bones
        source_pose_bones = source_object.pose.bones

        # get bone nodes to bake for link socket and set to tuple list (bone name, *[transform to bake])
        bake_bone_from_nodes = [(link.to_node.bone_target, link.to_node.use_location, link.to_node.use_rotation_euler, link.to_node.use_scale) for link in socket_node.links if isinstance(link.to_node, NODE_BONE) and link.to_node.is_bind_valid]

        # get additional bones to bake
        additional_bones = node.additional_bone_to_bake

        # set to tuple list (bone name, *[transform to bake])
        additional_bones = [(bone_group.bone_name, *bone_group.translation) for bone_group in additional_bones]

        # merge bone nodes and additional bones
        bake_bones = bake_bone_from_nodes + additional_bones

        # remove duplicate
        bake_bones = list(set(bake_bones))

        # check if bone exist and add current transform space | tuple(pose bone, *[transform to bake], location, rotation, scale)
        bake_bones = [(target_pose_bones[bone_name], bake_location, bake_rotation, bake_scale, target_pose_bones[bone_name].location.copy(), target_pose_bones[bone_name].rotation_quaternion.copy() if target_pose_bones[bone_name].rotation_mode == "QUATERNION" else target_pose_bones[bone_name].rotation_euler.copy(), target_pose_bones[bone_name].scale.copy()) for bone_name, bake_location, bake_rotation, bake_scale in bake_bones if target_pose_bones.get(bone_name)]

        # create new action
        action = bpy.data.actions.new(self.action_name)

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

            for pose_bone , is_bake_location, is_bake_rotation, is_bake_scale, ori_location, ori_rotation, ori_scale in bake_bones:
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

            for pose_bone , is_bake_location, is_bake_rotation, is_bake_scale, ori_location, ori_rotation, ori_scale in bake_bones:
                # bake location
                if is_bake_location:
                    pose_bone.keyframe_insert("location", options={"INSERTKEY_VISUAL"}, group=pose_bone.name + " (loc)")

                # bake rotation
                if is_bake_rotation:
                    pose_bone.keyframe_insert("rotation_quaternion", options={"INSERTKEY_VISUAL"}, group=pose_bone.name + " (rot quat)")
                    pose_bone.keyframe_insert("rotation_euler", options={"INSERTKEY_VISUAL"}, group=pose_bone.name + " (rot euler)")

                # bake scale
                if is_bake_scale:
                    pose_bone.keyframe_insert("scale", options={"INSERTKEY_VISUAL"}, group=pose_bone.name + " (scale)")

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
        bpy.ops.object.mode_set(mode='OBJECT')

        # restore selected objects
        for obj in selected_objects:
            obj.select_set(True)

        # change active object to old object
        context.view_layer.objects.active = old_active_object

        # change to old mode if not object
        if old_mode != "OBJECT":
            bpy.ops.object.mode_set(mode=old_mode)

        if self.unbind_after_bake:
            # unnbind after bake its true
            bpy.ops.renim.bind(node_tree_name=self.node_tree_name, node_object_name=self.node_object_name)

        # simple alert
        self.report({'INFO'}, "BAKE ACTION SUCCESS")

        return {'FINISHED'}

classes = [
    RENIM_OP_OBJCET_BIND,
    RENIM_OP_OBJCET_CONNECT_SELECTED_BONE_NODES,
    RENIM_OP_OBJCET_CREATE_BONE_NODE_FROM_SELECTED_BONE,
    RENIM_OP_OBJCET_LOAD_PRESET,
    RENIM_OP_OBJCET_SAVE_PRESET,
    RENIM_OP_OBJCET_ADD_BONE_TO_BAKE,
    RENIM_OP_OBJCET_REMOVE_BONE_TO_BAKE,
    RENIM_OP_OBJCET_BAKE_ACTION
]

def register():
    for x in classes:
        register_class(x)

def unregister():
    for x in reversed(classes):
        unregister_class(x)