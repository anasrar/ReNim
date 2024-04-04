from typing import cast
import bpy
from bpy.types import Context, Node, NodeSocket, Operator, PropertyGroup
from bpy.utils import register_class, unregister_class
from bpy import props
from nodeitems_utils import NodeItem, register_node_categories, unregister_node_categories
from . node import ReNimNode, ReNimNodeCategory
from . node_mapping import ReNimNodeMappingBone
from . editor_type_operator import ReNimOperatorAddAdditionalBoneToBake, ReNimOperatorBakeAction, ReNimOperatorConnectSelectedBoneNodes, ReNimOperatorCreateBoneNodeFromSelectedBones, ReNimOperatorLoadPreset, ReNimOperatorRemoveAdditionalBoneToBake, ReNimOperatorSavePreset, ReNimOperatorToggleBind


class ReNimGroupPropertyBakeBone(PropertyGroup):
    bone_name: props.StringProperty(default="")  # type: ignore
    translation: props.BoolVectorProperty(  # type: ignore
        size=3,
        subtype="TRANSLATION",
        default=[True, True, True]
    )


class ReNimNodeObjectSourceTarget(ReNimNode, Node):
    '''ReNim node source and target'''
    bl_idname = "ReNimNodeObjectSourceTarget"
    bl_label = "Target and Source Object"
    bl_icon = "OUTLINER_OB_ARMATURE"
    bl_width_default = 300

    action_name: props.StringProperty(default="BakeAction")  # type: ignore
    start_frame: props.IntProperty(default=1)  # type: ignore
    end_frame: props.IntProperty(default=250)  # type: ignore
    frame_step: props.IntProperty(default=1, min=1)  # type: ignore
    unbind_after_bake: props.BoolProperty(default=False)  # type: ignore
    additional_bone_to_bake: props.CollectionProperty(  # type: ignore
        type=ReNimGroupPropertyBakeBone)

    is_bind: props.BoolProperty(default=False)  # type: ignore

    def toggle_bind(self, context: Context, operator: Operator):
        if self.is_bind:
            self.unbind(context, operator)
        else:
            self.bind(context, operator)

    def bind(self, context: Context, operator: Operator):
        socket_object_out = cast(NodeSocket, self.outputs[0])
        assert isinstance(socket_object_out, NodeSocket)

        # create new bone collections
        bone_collections = socket_object_out.target_object.data.collections  # type: ignore
        bone_collection = bone_collections.new(  # type: ignore
            "ReNimHelperBones")
        bone_collection.is_visible = False

        # check output socket linked to some node
        if socket_object_out.is_linked:
            # bind all connected nodes bone
            # filter only bone nodes and not bind
            bone_nodes = [link.to_node for link in self.outputs[0].links if isinstance(
                link.to_node, ReNimNodeMappingBone) and not link.to_node.is_bind]

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

            # deselect all object
            bpy.ops.object.select_all(action="DESELECT")

            # select target and source object
            # commented becuse we don't really need to select the object
            # self.outputs[0].target_object.select_set(True)
            # self.outputs[0].source_object.select_set(True)

            # active object to target object
            context.view_layer.objects.active = self.outputs[0].target_object

            # change mode to edit to add bone (expose edit_bones)
            bpy.ops.object.mode_set(mode="EDIT")
            # disbale mirror for preventing symmetrize bone
            bpy.context.active_object.data.use_mirror_x = False  # type: ignore

            for node in bone_nodes:
                node.add_bone(bone_collection)

            # change mode to pose to add constraint and driver only on valid bone
            # commented becuse we don't really need to switch mode to pose
            # bpy.ops.object.mode_set(mode="POSE")
            # we can use update_from_editmode() to update pose_bones collection and still can do add constarint and driver in edit mode
            context.active_object.update_from_editmode()
            for node in bone_nodes:
                if node.is_bind_valid:
                    node.add_constraint_bone()

            # change mode back to object
            bpy.ops.object.mode_set(mode="OBJECT")

            # deselect all object
            bpy.ops.object.select_all(action="DESELECT")

            # restore selected objects
            for obj in selected_objects:
                obj.select_set(True)

            # change active object to old object
            context.view_layer.objects.active = old_active_object

            # change to old mode if not object
            if old_mode != "OBJECT":
                bpy.ops.object.mode_set(mode=old_mode)

        # set color node
        self.color = (0.1, 0.55, 0.25)
        self.use_custom_color = True

        self.is_bind = True
        operator.report({"INFO"}, "Bind Success")

    def unbind(self, context: Context, operator: Operator):
        socket_object_out = cast(NodeSocket, self.outputs[0])
        assert isinstance(socket_object_out, NodeSocket)

        # remove bone collections
        bone_collections = socket_object_out.target_object.data.collections  # type: ignore
        bone_collection = bone_collections.get("ReNimHelperBones")
        assert bone_collection
        bone_collections.remove(bone_collection)

        # check output socket linked to some node
        if socket_object_out.is_linked:
            # bind all connected nodes bone
            # filter only bone nodes and bind
            bone_nodes = [link.to_node for link in self.outputs[0].links if isinstance(
                link.to_node, ReNimNodeMappingBone) and link.to_node.is_bind]

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

            # deselect all object
            bpy.ops.object.select_all(action="DESELECT")

            # select target and source object
            # commented becuse we don't really need to select the object
            # self.outputs[0].target_object.select_set(True)
            # self.outputs[0].source_object.select_set(True)

            # active object to target object
            context.view_layer.objects.active = self.outputs[0].target_object

            # change mode to pose to remove constraint and driver only on valid bone
            # commented becuse we don't really need to switch mode to pose
            # bpy.ops.object.mode_set(mode='POSE')
            for node in bone_nodes:
                if node.is_bind_valid:
                    node.remove_constraint_bone()

            # change mode to edit to remove bone (expose edit_bones)
            bpy.ops.object.mode_set(mode="EDIT")
            # disbale mirror for preventing symmetrize bone
            # context.active_object.data.use_mirror_x = False

            for node in bone_nodes:
                if node.is_bind_valid:
                    node.remove_bone()

                node.is_bind_valid = False
                # set color node
                node.use_custom_color = False
                node.is_bind = False

            # change mode back to object
            bpy.ops.object.mode_set(mode="OBJECT")

            # deselect all object
            bpy.ops.object.select_all(action="DESELECT")

            # restore selected objects
            for obj in selected_objects:
                obj.select_set(True)

            # change active object to old object
            context.view_layer.objects.active = old_active_object

            # change to old mode if not object
            if old_mode != "OBJECT":
                bpy.ops.object.mode_set(mode=old_mode)
        # set color node
        self.use_custom_color = False

        self.is_bind = False
        operator.report({"INFO"}, "Unbind Success")

    def init(self, context):
        self.outputs.new("ReNimSocketSourceTarget",
                         "Target").display_shape = "DIAMOND"

    def copy(self, node):
        pass

    def free(self):
        node_tree_name = cast(str, self.id_data.name)  # type: ignore
        node_name = self.name
        assert isinstance(node_tree_name, str)

        if self.is_bind:
            bpy.ops.renim.toggle_bind(  # type: ignore
                node_tree_name=node_tree_name,
                node_source_target_name=node_name
            )

    def draw_buttons(self, context, layout):
        node_tree_name = cast(str, self.id_data.name)  # type: ignore
        node_name = self.name
        assert isinstance(node_tree_name, str)

        row = layout.row()
        row.enabled = bool(self.outputs[0].target_object) and bool(
            self.outputs[0].source_object)
        row.scale_y = 1.5
        operator_toggle_bind = cast(ReNimOperatorToggleBind, row.operator(  # I don't like it
            ReNimOperatorToggleBind.bl_idname, text="Bind" if not self.is_bind else "Unbind"))
        operator_toggle_bind.node_tree_name = node_tree_name
        operator_toggle_bind.node_source_target_name = node_name

        col = layout.column(align=True)
        col.scale_y = 1.5

        row = col.row(align=True)
        operator_connect_selected_bone_nodes = cast(ReNimOperatorConnectSelectedBoneNodes, row.operator(
            ReNimOperatorConnectSelectedBoneNodes.bl_idname))
        operator_connect_selected_bone_nodes.node_tree_name = node_tree_name
        operator_connect_selected_bone_nodes.node_source_target_name = node_name

        row = col.row(align=True)
        operator_create_bone_node_from_selected_bones = cast(ReNimOperatorCreateBoneNodeFromSelectedBones, row.operator(
            ReNimOperatorCreateBoneNodeFromSelectedBones.bl_idname))
        operator_create_bone_node_from_selected_bones.node_tree_name = node_tree_name
        operator_create_bone_node_from_selected_bones.node_source_target_name = node_name

        row = layout.row(align=True)
        row.scale_y = 1.5
        operator_load_preset = cast(ReNimOperatorLoadPreset, row.operator(ReNimOperatorLoadPreset.bl_idname,
                                                                          icon="EXPORT"))
        operator_load_preset.node_tree_name = node_tree_name
        operator_load_preset.node_source_target_name = node_name

        operator_save_preset = cast(ReNimOperatorSavePreset, row.operator(
            ReNimOperatorSavePreset.bl_idname, icon="IMPORT"))
        operator_save_preset.node_tree_name = node_tree_name
        operator_save_preset.node_source_target_name = node_name

        row = layout.row()
        split = row.split(factor=0.4)
        col = split.column()
        col.alignment = "RIGHT"
        col.label(text="Action Name")
        col.label(text="Start Frame")
        col.label(text="End Frame")
        col.label(text="Frame Step")
        col.label(text="Unbind After Bake")
        col = split.column()
        col.row().prop(self, "action_name", text="")
        col.row().prop(self, "start_frame", text="")
        col.row().prop(self, "end_frame", text="")
        col.row().prop(self, "frame_step", text="")
        col.row().prop(self, "unbind_after_bake", text="")

        row = layout.row()
        row.enabled = bool(self.outputs[0].target_object) and self.is_bind
        row.scale_y = 1.5
        operator_bake_action = cast(ReNimOperatorBakeAction, row.operator(
            ReNimOperatorBakeAction.bl_idname))
        operator_bake_action.node_tree_name = node_tree_name
        operator_bake_action.node_source_target_name = node_name
        operator_bake_action.action_name = self.action_name
        operator_bake_action.start_frame = self.start_frame
        operator_bake_action.end_frame = self.end_frame
        operator_bake_action.frame_step = self.frame_step
        operator_bake_action.unbind_after_bake = self.unbind_after_bake

        row = layout.row()
        row.label(text="Additional Bone To Bake")

        if self.additional_bone_to_bake:
            for index, data in enumerate(self.additional_bone_to_bake):
                col = layout.column(align=True)
                row = col.row(align=True)
                if self.outputs[0].target_object:
                    row.prop_search(
                        data, "bone_name", self.outputs[0].target_object.pose, "bones", text="")
                else:
                    row.prop(data, "bone_name", icon="BONE_DATA", text="")
                operator_remove_bone = cast(ReNimOperatorRemoveAdditionalBoneToBake, row.operator(
                    ReNimOperatorRemoveAdditionalBoneToBake.bl_idname, icon="X", text=""))
                operator_remove_bone.node_tree_name = node_tree_name
                operator_remove_bone.node_source_target_name = node_name
                operator_remove_bone.index = index
                row = col.row(align=True)
                row.prop(data, "translation", text="Location",
                         toggle=True, index=0)
                row.prop(data, "translation", text="Rotation",
                         toggle=True, index=1)
                row.prop(data, "translation", text="Scale",
                         toggle=True, index=2)

        row = layout.row()
        row.scale_y = 1.5
        operator_add_bone = cast(ReNimOperatorAddAdditionalBoneToBake, row.operator(
            ReNimOperatorAddAdditionalBoneToBake.bl_idname))
        operator_add_bone.node_tree_name = node_tree_name
        operator_add_bone.node_source_target_name = node_name

    def draw_label(self):
        return "Target and Source Object"


classes = [
    ReNimGroupPropertyBakeBone,
    ReNimNodeObjectSourceTarget,
]


node_categories = [
    ReNimNodeCategory("RENIM_OBJECT", "Object", items=[  # type: ignore
        NodeItem("ReNimNodeObjectSourceTarget")  # type: ignore
    ]),
]


def register():
    for x in classes:
        register_class(x)

    register_node_categories("RENIM_OBJECT_NODES", node_categories)


def unregister():
    unregister_node_categories("RENIM_OBJECT_NODES")

    for x in reversed(classes):
        unregister_class(x)
