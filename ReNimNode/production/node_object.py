import bpy
from bpy.utils import register_class, unregister_class
from . node import Node, NodeCategory
from . node_mapping import NODE_BONE

class GROUP_PROP_ADTTIONAL_BAKE_BONE(bpy.types.PropertyGroup):
    bone_name: bpy.props.StringProperty(default="")
    translation: bpy.props.BoolVectorProperty(
        size=3,
        subtype="TRANSLATION",
        default=[True, True, True]
    )

class NODE_OBJECT(Node):
    '''A custom node'''
    bl_idname = 'NODE_RENIM_OBJECT'
    bl_label = "Target and Source Object"
    bl_icon = 'OUTLINER_OB_ARMATURE'
    bl_width_default = 300

    action_name: bpy.props.StringProperty(default="BakeAction")
    start_frame: bpy.props.IntProperty(default=1)
    end_frame: bpy.props.IntProperty(default=250)
    frame_step: bpy.props.IntProperty(default=1, min=1)
    unbind_after_bake: bpy.props.BoolProperty(default=False)
    additional_bone_to_bake: bpy.props.CollectionProperty(type=GROUP_PROP_ADTTIONAL_BAKE_BONE)

    is_bind: bpy.props.BoolProperty(default=False)

    def bind(self, context):
        socket_object_out = self.outputs[0]
        # check output socket linked to some node
        if socket_object_out.is_linked:
            # bind all connected nodes bone
            # filter only bone nodes and not bind
            bone_nodes = [link.to_node for link in self.outputs[0].links if isinstance(link.to_node, NODE_BONE) and not link.to_node.is_bind]

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

            # deselect all object
            bpy.ops.object.select_all(action='DESELECT')

            # select target and source object
            # commented becuse we don't really need to select the object
            # self.outputs[0].target_object.select_set(True)
            # self.outputs[0].source_object.select_set(True)

            # active object to target object
            context.view_layer.objects.active = self.outputs[0].target_object

            # change mode to edit to add bone (expose edit_bones)
            bpy.ops.object.mode_set(mode='EDIT')
            # disbale mirror for preventing symmetrize bone
            context.active_object.data.use_mirror_x = False

            for node in bone_nodes:
                node.add_bone(context)

            # change mode to pose to add constraint and driver only on valid bone
            # commented becuse we don't really need to switch mode to pose
            # bpy.ops.object.mode_set(mode='POSE')
            # we can use update_from_editmode() to update pose_bones collection and still can do add constarint and driver in edit mode
            context.active_object.update_from_editmode()
            for node in bone_nodes:
                if node.is_bind_valid:
                    node.add_constraint_bone(context)

            # change mode back to object
            bpy.ops.object.mode_set(mode='OBJECT')

            # deselect all object
            bpy.ops.object.select_all(action='DESELECT')

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

    def unbind(self, context):
        socket_object_out = self.outputs[0]
        # check output socket linked to some node
        if socket_object_out.is_linked:
            # bind all connected nodes bone
            # filter only bone nodes and bind
            bone_nodes = [link.to_node for link in self.outputs[0].links if isinstance(link.to_node, NODE_BONE) and link.to_node.is_bind]

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

            # deselect all object
            bpy.ops.object.select_all(action='DESELECT')

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
                    node.remove_constraint_bone(context)

            # change mode to edit to remove bone (expose edit_bones)
            bpy.ops.object.mode_set(mode='EDIT')
            # disbale mirror for preventing symmetrize bone
            context.active_object.data.use_mirror_x = False

            for node in bone_nodes:
                if node.is_bind_valid:
                    node.remove_bone(context)

                node.is_bind_valid = False
                # set color node
                node.use_custom_color = False
                node.is_bind = False

            # change mode back to object
            bpy.ops.object.mode_set(mode='OBJECT')

            # deselect all object
            bpy.ops.object.select_all(action='DESELECT')

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

    def init(self, context):
        self.outputs.new('SOCKET_RENIM_OBJECT', "Target").display_shape = 'DIAMOND'

    def copy(self, node):
        print("Copying from node ", node)

    def free(self):
        print("Removing node ", self, ", Goodbye!")

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.enabled = bool(self.outputs[0].target_object) and bool(self.outputs[0].source_object)
        row.scale_y = 1.5
        op = row.operator("renim.bind", text="BIND" if not self.is_bind else "UNBIND")
        op.node_tree_name = self.id_data.name
        op.node_object_name = self.name

        col = layout.column(align=True)
        col.scale_y = 1.5

        row = col.row(align=True)
        op = row.operator("renim.conect_selected_bone_nodes")
        op.node_tree_name = self.id_data.name
        op.node_object_name = self.name

        row = col.row(align=True)
        op = row.operator("renim.create_bone_node_from_selected_bones")
        op.node_tree_name = self.id_data.name
        op.node_object_name = self.name

        row = layout.row(align=True)
        row.scale_y = 1.5
        op = row.operator("renim.load_preset", text="Load Preset Bone", icon="EXPORT")
        op.node_tree_name = self.id_data.name
        op.node_object_name = self.name

        op = row.operator("renim.save_preset", icon="IMPORT")
        op.node_tree_name = self.id_data.name
        op.node_object_name = self.name

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
        op = row.operator("renim.bake_action", text="BAKE ACTION")
        op.node_tree_name = self.id_data.name
        op.node_object_name = self.name
        op.action_name = self.action_name
        op.start_frame = self.start_frame
        op.end_frame = self.end_frame
        op.frame_step = self.frame_step
        op.unbind_after_bake = self.unbind_after_bake

        row = layout.row()
        row.label(text="Aditional Bone To Bake")

        if self.additional_bone_to_bake:
            for index, data in enumerate(self.additional_bone_to_bake):
                col = layout.column(align=True)
                row = col.row(align=True)
                if self.outputs[0].target_object:
                    row.prop_search(data, "bone_name", self.outputs[0].target_object.pose, "bones", text="")
                else:
                    row.prop(data, "bone_name", icon="BONE_DATA", text="")
                op = row.operator("renim.remove_bone_to_bake", icon="X", text="")
                op.node_tree_name = self.id_data.name
                op.node_object_name = self.name
                op.index = index
                row = col.row(align=True)
                row.prop(data, "translation", text="Location", toggle=True, index=0)
                row.prop(data, "translation", text="Rotation", toggle=True, index=1)
                row.prop(data, "translation", text="Scale", toggle=True, index=2)

        row = layout.row()
        row.scale_y = 1.5
        op = row.operator("renim.add_bone_to_bake")
        op.node_tree_name = self.id_data.name
        op.node_object_name = self.name

    def draw_label(self):
        return "Target and Source Object"

classes = [
    GROUP_PROP_ADTTIONAL_BAKE_BONE,
    NODE_OBJECT
]

import nodeitems_utils
from nodeitems_utils import NodeItem

node_categories = [
    NodeCategory('RENIM_OBJECT', "Object", items=[
        NodeItem("NODE_RENIM_OBJECT")
    ])
]

def register():
    for x in classes:
        register_class(x)

    nodeitems_utils.register_node_categories('RENIM_OBJECT_NODES', node_categories)

def unregister():
    nodeitems_utils.unregister_node_categories('RENIM_OBJECT_NODES')

    for x in reversed(classes):
        unregister_class(x)