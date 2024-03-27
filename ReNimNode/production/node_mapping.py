import bpy
from bpy.types import BoneCollection, Node
from bpy import props
from nodeitems_utils import NodeItem, register_node_categories, unregister_node_categories
from bpy.utils import register_class, unregister_class
from . node import ReNimNode, ReNimNodeCategory


class ReNimNodeMappingBone(ReNimNode, Node):
    """ReNim node bone map"""
    bl_idname = "ReNimNodeMappingBone"
    bl_label = "Bone"
    bl_icon = "GROUP_BONE"
    bl_width_default = 300

    use_location: props.BoolProperty(default=True)  # type: ignore
    location_axis: props.BoolVectorProperty(  # type: ignore
        size=3,
        subtype="XYZ",
        default=[True, True, True]
    )
    location_influence: props.FloatVectorProperty(  # type: ignore
        size=3,
        min=0.0,
        max=1.0,
        subtype="XYZ",
        default=[1.0, 1.0, 1.0]
    )
    location_multiply: props.FloatVectorProperty(  # type: ignore
        size=3,
        subtype="XYZ",
        default=[1.0, 1.0, 1.0]
    )
    location_offset: props.FloatVectorProperty(  # type: ignore
        size=3,
        subtype="XYZ",
        default=[0.0, 0.0, 0.0]
    )
    use_rotation_euler: props.BoolProperty(default=True)  # type: ignore
    rotation_euler_axis: props.BoolVectorProperty(  # type: ignore
        size=3,
        subtype="XYZ",
        default=[True, True, True]
    )
    rotation_euler_influence: props.FloatVectorProperty(  # type: ignore
        size=3,
        min=0.0,
        max=1.0,
        subtype="XYZ",
        default=[1.0, 1.0, 1.0]
    )
    rotation_euler_multiply: props.FloatVectorProperty(  # type: ignore
        size=3,
        subtype="XYZ",
        default=[1.0, 1.0, 1.0]
    )
    rotation_euler_offset: props.FloatVectorProperty(  # type: ignore
        size=3,
        unit="ROTATION",
        subtype="XYZ",
        default=[0.0, 0.0, 0.0]
    )
    use_scale: props.BoolProperty(default=True)  # type: ignore
    scale_axis: props.BoolVectorProperty(  # type: ignore
        size=3,
        subtype="XYZ",
        default=[True, True, True]
    )
    scale_influence: props.FloatVectorProperty(  # type: ignore
        size=3,
        min=0.0,
        max=1.0,
        subtype="XYZ",
        default=[1.0, 1.0, 1.0]
    )
    scale_multiply: props.FloatVectorProperty(  # type: ignore
        size=3,
        subtype="XYZ",
        default=[1.0, 1.0, 1.0]
    )
    scale_offset: props.FloatVectorProperty(  # type: ignore
        size=3,
        subtype="XYZ",
        default=[0.0, 0.0, 0.0]
    )
    mix_mode: props.EnumProperty(  # type: ignore
        name="Mix Mode",
        description="Specify how the copied and existing transformations are combined",
        items=[
            ("BEFORE", "Before Original", "Apply copied transformation before original, as if the constraint target is a parent. Scale is handled specially to avoid creating shear"),
            ("AFTER", "After Original", "Apply copied transformation after original, as if the constraint target is a child. Scale is handled specially to avoid creating shear")
        ],
        default="AFTER"
    )

    bone_target: props.StringProperty(default="")  # type: ignore
    bone_source: props.StringProperty(default="")  # type: ignore

    is_bind: props.BoolProperty(default=False)  # type: ignore
    is_bind_valid: props.BoolProperty(default=False)  # type: ignore

    old_update: props.BoolProperty(default=False)  # type: ignore

    def add_bone(self, bone_collection: BoneCollection):
        # get object socket
        socket = self.inputs[0].links[0].from_socket

        # target and source object
        target_object = socket.target_object
        source_object = socket.source_object

        # store object to socket input node for removing constraint and bone
        self.inputs[0].target_object = target_object
        self.inputs[0].source_object = source_object

        # edit bones target and source
        target_object_edit_bones = target_object.data.edit_bones
        # because we not select the source aramture, we can"t get edit_bones collection
        # instead we can use data bone, because we just need bone rotation relative to armature
        source_object_bones = source_object.data.bones
        # source_object_edit_bones = source_object.data.edit_bones

        # get bone target and source
        target_bone = target_object_edit_bones.get(self.bone_target)
        source_bone = source_object_bones.get(self.bone_source)

        # create bone helper for target and source if exist
        if target_bone and source_bone:
            # using node name, because its already unique name
            mimic_target_bone = target_object_edit_bones.new(
                "TARGET_" + self.name + "_" + self.bone_target)
            mimic_source_bone = target_object_edit_bones.new(
                "SOURCE_" + self.name + "_" + self.bone_source)

            # not deform
            mimic_target_bone.use_deform = False
            mimic_source_bone.use_deform = False

            # parent target to source
            mimic_target_bone.parent = mimic_source_bone

            # set length new bone
            mimic_target_bone.length = 0.001
            mimic_source_bone.length = 0.001

            # make bone unable to select
            mimic_target_bone.hide_select = True
            mimic_source_bone.hide_select = True

            # add to bone collection
            bone_collection.assign(mimic_target_bone)
            bone_collection.assign(mimic_source_bone)

            # get target and source rotation (quaternion)
            rotation_target_bone = target_bone.matrix.to_quaternion()
            rotation_source_bone = source_bone.matrix_local.to_quaternion()

            # change bone orientation base on rotation
            mimic_target_bone.matrix = rotation_target_bone.to_matrix().to_4x4()
            mimic_source_bone.matrix = rotation_source_bone.to_matrix().to_4x4()

            self.is_bind_valid = True
            # set color node
            self.color = (0.1, 0.55, 0.25)
        else:
            self.is_bind_valid = False
            # set color node
            self.color = (0.55, 0.1, 0.1)

        self.use_custom_color = True
        self.is_bind = True

    def remove_bone(self):
        # target and source object
        target_object = self.inputs[0].target_object
        # source_object = self.inputs[0].source_object

        # remove object from socket input node
        self.inputs[0].target_object = None
        self.inputs[0].source_object = None

        # edit bones target and source
        target_object_edit_bones = target_object.data.edit_bones
        # source_object_edit_bones = source_object.data.edit_bones

        # get mimic bone target and source
        mimic_target_bone = target_object_edit_bones.get(
            "TARGET_" + self.name + "_" + self.bone_target)
        mimic_source_bone = target_object_edit_bones.get(
            "SOURCE_" + self.name + "_" + self.bone_source)

        # remove mimic bone for target and source if exist
        if mimic_target_bone and mimic_source_bone:
            target_object_edit_bones.remove(mimic_target_bone)
            target_object_edit_bones.remove(mimic_source_bone)

    def add_constraint_bone(self):
        # get object socket
        socket = self.inputs[0].links[0].from_socket

        # target and source object
        target_object = socket.target_object
        source_object = socket.source_object

        # pose bones target and source
        target_object_pose_bones = target_object.pose.bones
        # source_object_pose_bones = source_object.pose.bones

        # get bone target and source
        target_bone = target_object_pose_bones.get(self.bone_target)
        mimic_target_bone = target_object_pose_bones.get(
            "TARGET_" + self.name + "_" + self.bone_target)
        mimic_source_bone = target_object_pose_bones.get(
            "SOURCE_" + self.name + "_" + self.bone_source)

        # add driver and constraint for target and source if exist
        if target_bone and mimic_target_bone and mimic_source_bone:
            # add constraint on target bone to copy transform from mimic target
            const_copy_transform_target_bone = target_bone.constraints.new(
                "COPY_TRANSFORMS")
            const_copy_transform_target_bone.show_expanded = False
            const_copy_transform_target_bone.name = "RENIM_TRANSFORM_" + self.name
            const_copy_transform_target_bone.subtarget = mimic_target_bone.name
            const_copy_transform_target_bone.target = target_object
            const_copy_transform_target_bone.owner_space = "LOCAL"
            const_copy_transform_target_bone.target_space = "LOCAL_WITH_PARENT"
            const_copy_transform_target_bone.mix_mode = "BEFORE"

            const_mix_mode_driver = const_copy_transform_target_bone.driver_add(
                "mix_mode").driver
            const_mix_mode_driver.type = "SCRIPTED"

            const_mix_mode_driver_var = const_mix_mode_driver.variables.new()
            const_mix_mode_driver_var.name = "mix_mode"
            const_mix_mode_driver_var.type = "SINGLE_PROP"
            const_mix_mode_driver_var_target = const_mix_mode_driver_var.targets[0]
            const_mix_mode_driver_var_target.id_type = "NODETREE"
            const_mix_mode_driver_var_target.id = self.id_data
            const_mix_mode_driver_var_target.data_path = "{}".format(
                self.path_from_id("mix_mode"))
            const_mix_mode_driver_var_target.rotation_mode = "AUTO"
            const_mix_mode_driver_var_target.transform_space = "LOCAL_SPACE"

            const_mix_mode_driver.expression = "mix_mode + 1"

            # change rotation mode to XYZ just to make it easier to add driver
            mimic_source_bone.rotation_mode = "XYZ"

            # add driver transform from source to mimic source
            for transform, prop_transform in [("LOC", "location"), ("ROT", "rotation_euler"), ("SCALE", "scale")]:
                for index, axis in enumerate(["X", "Y", "Z"]):
                    # add driver
                    mimic_source_bone_driver = mimic_source_bone.driver_add(
                        prop_transform, index).driver
                    mimic_source_bone_driver.type = "SCRIPTED"

                    # copy transform value variable
                    mimic_source_bone_driver_var_transform = mimic_source_bone_driver.variables.new()
                    mimic_source_bone_driver_var_transform.name = transform + "_" + axis
                    mimic_source_bone_driver_var_transform.type = "TRANSFORMS"
                    mimic_source_bone_driver_var_transform_target = mimic_source_bone_driver_var_transform.targets[
                        0]
                    # mimic_source_bone_driver_var_transform_target.id_type = "OBJECT"
                    mimic_source_bone_driver_var_transform_target.id = source_object
                    mimic_source_bone_driver_var_transform_target.bone_target = self.bone_source
                    mimic_source_bone_driver_var_transform_target.transform_type = transform + "_" + axis
                    mimic_source_bone_driver_var_transform_target.rotation_mode = "AUTO"
                    mimic_source_bone_driver_var_transform_target.transform_space = "LOCAL_SPACE"

                    # influence variable
                    mimic_source_bone_driver_var_influence = mimic_source_bone_driver.variables.new()
                    mimic_source_bone_driver_var_influence.name = "influence"
                    mimic_source_bone_driver_var_influence.type = "SINGLE_PROP"
                    mimic_source_bone_driver_var_influence_target = mimic_source_bone_driver_var_influence.targets[
                        0]
                    mimic_source_bone_driver_var_influence_target.id_type = "NODETREE"
                    mimic_source_bone_driver_var_influence_target.id = self.id_data
                    mimic_source_bone_driver_var_influence_target.data_path = "{}[{}]".format(
                        self.path_from_id(prop_transform + "_influence"), index)
                    mimic_source_bone_driver_var_influence_target.rotation_mode = "AUTO"
                    mimic_source_bone_driver_var_influence_target.transform_space = "LOCAL_SPACE"

                    # multiply variable
                    mimic_source_bone_driver_var_multiply = mimic_source_bone_driver.variables.new()
                    mimic_source_bone_driver_var_multiply.name = "multiply"
                    mimic_source_bone_driver_var_multiply.type = "SINGLE_PROP"
                    mimic_source_bone_driver_var_multiply_target = mimic_source_bone_driver_var_multiply.targets[
                        0]
                    mimic_source_bone_driver_var_multiply_target.id_type = "NODETREE"
                    mimic_source_bone_driver_var_multiply_target.id = self.id_data
                    mimic_source_bone_driver_var_multiply_target.data_path = "{}[{}]".format(
                        self.path_from_id(prop_transform + "_multiply"), index)
                    mimic_source_bone_driver_var_multiply_target.rotation_mode = "AUTO"
                    mimic_source_bone_driver_var_multiply_target.transform_space = "LOCAL_SPACE"

                    # offset variable
                    mimic_source_bone_driver_var_offset = mimic_source_bone_driver.variables.new()
                    mimic_source_bone_driver_var_offset.name = "offset"
                    mimic_source_bone_driver_var_offset.type = "SINGLE_PROP"
                    mimic_source_bone_driver_var_offset_target = mimic_source_bone_driver_var_offset.targets[
                        0]
                    mimic_source_bone_driver_var_offset_target.id_type = "NODETREE"
                    mimic_source_bone_driver_var_offset_target.id = self.id_data
                    mimic_source_bone_driver_var_offset_target.data_path = "{}[{}]".format(
                        self.path_from_id(prop_transform + "_offset"), index)
                    mimic_source_bone_driver_var_offset_target.rotation_mode = "AUTO"
                    mimic_source_bone_driver_var_offset_target.transform_space = "LOCAL_SPACE"

                    # use transform variable
                    mimic_source_bone_driver_var_use_transform = mimic_source_bone_driver.variables.new()
                    mimic_source_bone_driver_var_use_transform.name = "use_transform"
                    mimic_source_bone_driver_var_use_transform.type = "SINGLE_PROP"
                    mimic_source_bone_driver_var_use_transform_target = mimic_source_bone_driver_var_use_transform.targets[
                        0]
                    mimic_source_bone_driver_var_use_transform_target.id_type = "NODETREE"
                    mimic_source_bone_driver_var_use_transform_target.id = self.id_data
                    mimic_source_bone_driver_var_use_transform_target.data_path = "{}".format(
                        self.path_from_id("use_" + prop_transform))
                    mimic_source_bone_driver_var_use_transform_target.rotation_mode = "AUTO"
                    mimic_source_bone_driver_var_use_transform_target.transform_space = "LOCAL_SPACE"

                    # use axis variable
                    mimic_source_bone_driver_var_use_axis = mimic_source_bone_driver.variables.new()
                    mimic_source_bone_driver_var_use_axis.name = "use_axis"
                    mimic_source_bone_driver_var_use_axis.type = "SINGLE_PROP"
                    mimic_source_bone_driver_var_use_axis_target = mimic_source_bone_driver_var_use_axis.targets[
                        0]
                    mimic_source_bone_driver_var_use_axis_target.id_type = "NODETREE"
                    mimic_source_bone_driver_var_use_axis_target.id = self.id_data
                    mimic_source_bone_driver_var_use_axis_target.data_path = "{}[{}]".format(
                        self.path_from_id(prop_transform + "_axis"), index)
                    mimic_source_bone_driver_var_use_axis_target.rotation_mode = "AUTO"
                    mimic_source_bone_driver_var_use_axis_target.transform_space = "LOCAL_SPACE"

                    # add more variable for normalize location if source and target object has different scale

                    # source scale
                    mimic_source_bone_driver_var_scale_source = mimic_source_bone_driver.variables.new()
                    mimic_source_bone_driver_var_scale_source.name = "source_scale"
                    mimic_source_bone_driver_var_scale_source.type = "TRANSFORMS"
                    mimic_source_bone_driver_var_scale_source_target = mimic_source_bone_driver_var_scale_source.targets[
                        0]
                    # mimic_source_bone_driver_var_scale_source_target.id_type = "OBJECT"
                    mimic_source_bone_driver_var_scale_source_target.id = source_object
                    mimic_source_bone_driver_var_scale_source_target.bone_target = ""
                    mimic_source_bone_driver_var_scale_source_target.transform_type = "SCALE_" + axis
                    mimic_source_bone_driver_var_scale_source_target.rotation_mode = "AUTO"
                    mimic_source_bone_driver_var_scale_source_target.transform_space = "LOCAL_SPACE"

                    # target scale
                    mimic_source_bone_driver_var_scale_target = mimic_source_bone_driver.variables.new()
                    mimic_source_bone_driver_var_scale_target.name = "target_scale"
                    mimic_source_bone_driver_var_scale_target.type = "TRANSFORMS"
                    mimic_source_bone_driver_var_scale_target_target = mimic_source_bone_driver_var_scale_target.targets[
                        0]
                    # mimic_source_bone_driver_var_scale_target_target.id_type = "OBJECT"
                    mimic_source_bone_driver_var_scale_target_target.id = target_object
                    mimic_source_bone_driver_var_scale_target_target.bone_target = ""
                    mimic_source_bone_driver_var_scale_target_target.transform_type = "SCALE_" + axis
                    mimic_source_bone_driver_var_scale_target_target.rotation_mode = "AUTO"
                    mimic_source_bone_driver_var_scale_target_target.transform_space = "LOCAL_SPACE"

                    driver_expression_default = "(({value}*{influence})*{multiply})+{offset} if ({use_transform} and {use_axis}) else 0"
                    driver_expression_location = "((({value}/({target_scale}/{source_scale}))*{influence})*{multiply})+{offset} if ({use_transform} and {use_axis}) else 0"

                    mimic_source_bone_driver.expression = (driver_expression_location if transform == "LOC" else driver_expression_default).format(
                        value=transform + "_" + axis, target_scale="target_scale", source_scale="source_scale", influence="influence", multiply="multiply", offset="offset", use_transform="use_transform", use_axis="use_axis")

            # ssttt... this is secret between us

            # make bone unselectable
            mimic_target_bone.bone.hide_select = True
            mimic_source_bone.bone.hide_select = True

            # hide bone using driver
            mimic_target_bone_hide_driver = mimic_target_bone.bone.driver_add(
                "hide").driver
            mimic_target_bone_hide_driver.type = "SCRIPTED"
            mimic_target_bone_hide_driver.expression = "True"

            mimic_source_bone_hide_driver = mimic_source_bone.bone.driver_add(
                "hide").driver
            mimic_source_bone_hide_driver.type = "SCRIPTED"
            mimic_source_bone_hide_driver.expression = "True"

    def remove_constraint_bone(self):
        # target and source object
        target_object = self.inputs[0].target_object
        # source_object = self.inputs[0].source_object

        # pose bones target and source
        target_object_pose_bones = target_object.pose.bones
        # source_object_pose_bones = source_object.pose.bones

        # get bone target and source
        target_bone = target_object_pose_bones.get(self.bone_target)
        mimic_target_bone = target_object_pose_bones.get(
            "TARGET_" + self.name + "_" + self.bone_target)
        mimic_source_bone = target_object_pose_bones.get(
            "SOURCE_" + self.name + "_" + self.bone_source)

        # remove driver and constraint for target and source if exist
        if target_bone and mimic_target_bone and mimic_source_bone:
            # remove driver and constraint on target bone
            const_copy_transform_target_bone = target_bone.constraints.get(
                "RENIM_TRANSFORM_" + self.name)
            if const_copy_transform_target_bone:
                const_copy_transform_target_bone.driver_remove("mix_mode")
                target_bone.constraints.remove(
                    const_copy_transform_target_bone)

            # remove driver transform mimic source
            for _, prop_transform in [("LOC", "location"), ("ROT", "rotation_euler"), ("SCALE", "scale")]:
                mimic_source_bone.driver_remove(prop_transform)

            # remove hide driver
            mimic_target_bone.bone.driver_remove("hide")

            mimic_source_bone.bone.driver_remove("hide")

    def live_bind_bone(self):
        socket_input = self.inputs[0]

        # get node object
        node_object = socket_input.links[0].from_node

        # store current mode
        old_mode = "OBJECT"

        # store current active object
        old_active_object = bpy.context.active_object

        # change mode to object if current mode is not object
        if bpy.context.mode != "OBJECT":
            # overide current mode if not object
            old_mode = bpy.context.active_object.mode if bpy.context.active_object else bpy.context.mode
            bpy.ops.object.mode_set(mode="OBJECT")

        # store selected object for seamless binding
        selected_objects = bpy.context.selected_objects

        # deselect all object
        bpy.ops.object.select_all(action="DESELECT")

        # select target and source object
        # commented becuse we don't really need to select the object
        # node_object.outputs[0].target_object.select_set(True)
        # node_object.outputs[0].source_object.select_set(True)

        # active object to target object
        bpy.context.view_layer.objects.active = node_object.outputs[0].target_object

        # change mode to edit to add bone (expose edit_bones)
        bpy.ops.object.mode_set(mode="EDIT")
        # disbale mirror for preventing symmetrize bone
        bpy.context.active_object.data.use_mirror_x = False  # type: ignore

        self.add_bone()

        # change mode to pose to add constraint and driver
        # commented becuse we don't really need to switch mode to pose
        # bpy.ops.object.mode_set(mode="POSE")
        # we can use update_from_editmode() to update pose_bones collection and still can do add constarint and driver in edit mode
        bpy.context.active_object.update_from_editmode()
        if self.is_bind_valid:
            self.add_constraint_bone()

        # change mode back to object
        bpy.ops.object.mode_set(mode="OBJECT")

        # deselect all object
        bpy.ops.object.select_all(action="DESELECT")

        # restore selected objects
        for obj in selected_objects:
            obj.select_set(True)

        # change active object to old object
        bpy.context.view_layer.objects.active = old_active_object

        # change to old mode if not object
        if old_mode != "OBJECT":
            bpy.ops.object.mode_set(mode=old_mode)

    def live_unbind_bone(self):
        if self.is_bind:
            # target and source object
            target_object = self.inputs[0].target_object
            # source_object = self.inputs[0].source_object

            # store current mode
            old_mode = "OBJECT"

            # store current active object
            old_active_object = bpy.context.active_object

            # change mode to object if current mode is not object
            if bpy.context.mode != "OBJECT":
                old_mode = bpy.context.active_object.mode if bpy.context.active_object else bpy.context.mode
                bpy.ops.object.mode_set(mode="OBJECT")

            # store selected object for seamless binding
            selected_objects = bpy.context.selected_objects

            # deselect all object
            bpy.ops.object.select_all(action="DESELECT")

            # select target and source object
            # commented becuse we don't really need to select the object
            # target_object.select_set(True)
            # source_object.select_set(True)

            # active object to target object
            bpy.context.view_layer.objects.active = target_object

            # change mode to pose to remove constraint and driver only on valid bone
            # commented becuse we don't really need to switch mode to pose
            # bpy.ops.object.mode_set(mode="POSE")

            if self.is_bind_valid:
                self.remove_constraint_bone()

            # change mode to edit to remove bone (expose edit_bones)
            bpy.ops.object.mode_set(mode="EDIT")
            # disbale mirror for preventing symmetrize bone
            bpy.context.active_object.data.use_mirror_x = False  # type: ignore

            if self.is_bind_valid:
                self.remove_bone()

            self.is_bind_valid = False
            # set color node
            self.use_custom_color = False
            self.is_bind = False

            # change mode back to object
            bpy.ops.object.mode_set(mode="OBJECT")

            # deselect all object
            bpy.ops.object.select_all(action="DESELECT")

            # restore selected objects
            for obj in selected_objects:
                obj.select_set(True)

            # change active object to old object
            bpy.context.view_layer.objects.active = old_active_object

            # change to old mode if not object
            if old_mode != "OBJECT":
                bpy.ops.object.mode_set(mode=old_mode)

    def update(self):
        socket_input = self.inputs[0]
        # detect if node link change
        is_state_change = not (socket_input.is_linked == self.old_update)

        if is_state_change:
            if socket_input.is_linked:
                # get node object
                node_object = socket_input.links[0].from_node
                # check is source target node is bind and bind bone
                if node_object.is_bind:
                    self.live_bind_bone()
            else:
                # unbind bone if node is binded
                if self.is_bind:
                    self.live_unbind_bone()

        self.old_update = socket_input.is_linked

    def init(self, context):
        self.color = (0.1, 0.55, 0.25)
        self.use_custom_color = False
        self.inputs.new("ReNimSocketSourceTarget",
                        "Target").display_shape = "DIAMOND"

    def draw_buttons(self, context, layout):
        row = layout.row()
        split = row.split(factor=0.3)
        col = split.column()
        col.alignment = "RIGHT"
        col.label(text="Location", icon="CON_LOCLIKE")
        col.label(text="Influence")
        col.label(text="Multiply")
        col.label(text="Offset")
        col.label(text="Rotation", icon="CON_ROTLIKE")
        col.label(text="Influence")
        col.label(text="Multiply")
        col.label(text="Offset")
        col.label(text="Scale", icon="CON_SIZELIKE")
        col.label(text="Influence")
        col.label(text="Multiply")
        col.label(text="Offset")
        col.label(text="Mix")
        col.label(text="Bone Target")
        col.label(text="Bone Source")
        col = split.column()
        row = col.row(align=True)
        row.prop(self, "use_location", text="")
        sub_col = row.column()
        sub_col.row().prop(self, "location_axis", text="", toggle=True)
        sub_col.row().prop(self, "location_influence", text="", slider=True)
        sub_col.row().prop(self, "location_multiply", text="")
        sub_col.row().prop(self, "location_offset", text="")
        row = col.row(align=True)
        row.prop(self, "use_rotation_euler", text="")
        sub_col = row.column()
        sub_col.row().prop(self, "rotation_euler_axis", text="", toggle=True)
        sub_col.row().prop(self, "rotation_euler_influence", text="", slider=True)
        sub_col.row().prop(self, "rotation_euler_multiply", text="")
        sub_col.row().prop(self, "rotation_euler_offset", text="")
        row = col.row(align=True)
        row.prop(self, "use_scale", text="")
        sub_col = row.column()
        sub_col.row().prop(self, "scale_axis", text="", toggle=True)
        sub_col.row().prop(self, "scale_influence", text="", slider=True)
        sub_col.row().prop(self, "scale_multiply", text="")
        sub_col.row().prop(self, "scale_offset", text="")
        sub_col = col.column()
        sub_col.prop(self, "mix_mode", text="")
        col = col.column()
        col.enabled = not self.is_bind
        if self.inputs[0].is_linked:
            links = self.inputs[0].links

            if len(links) and links[0].from_socket.target_object is not None and links[0].from_socket.target_object.type == "ARMATURE":
                col.prop_search(
                    self, "bone_target", self.inputs[0].links[0].from_socket.target_object.pose, "bones", text="")
            else:
                col.prop(self, "bone_target", text="", icon="BONE_DATA")

            if len(links) and links[0].from_socket.source_object is not None and links[0].from_socket.source_object.type == "ARMATURE":
                col.prop_search(
                    self, "bone_source", self.inputs[0].links[0].from_socket.source_object.pose, "bones", text="")
            else:
                col.prop(self, "bone_source", text="", icon="BONE_DATA")
        else:
            col.prop(self, "bone_target", text="", icon="BONE_DATA")
            col.prop(self, "bone_source", text="", icon="BONE_DATA")

    def draw_label(self):
        return self.bone_target if self.bone_target else "Bone"


classes = [
    ReNimNodeMappingBone
]


node_categories = [
    ReNimNodeCategory("RENIM_MAPPING", "Mapping", items=[  # type: ignore
        NodeItem("ReNimNodeMappingBone")  # type: ignore
    ]),
    ReNimNodeCategory("RENIM_LAYOUT", "Layout", items=[  # type: ignore
        NodeItem("NodeFrame")  # type: ignore
    ])
]


def register():
    for x in classes:
        register_class(x)

    register_node_categories("RENIM_MAPPING_NODES", node_categories)


def unregister():
    unregister_node_categories("RENIM_MAPPING_NODES")

    for x in reversed(classes):
        unregister_class(x)
