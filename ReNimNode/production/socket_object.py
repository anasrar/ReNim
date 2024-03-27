from bpy import props, types
from bpy.utils import register_class, unregister_class
from bpy.types import NodeSocket
from . node_object import ReNimNodeObjectSourceTarget


class ReNimSocketSourceTarget(NodeSocket):
    '''Socket node for source and target'''
    bl_idname = "ReNimSocketSourceTarget"
    bl_label = "Socket Source Target"
    link_limit = 1

    target_object: props.PointerProperty(  # type: ignore
        type=types.Object,
        poll=lambda self, obj: obj.type == "ARMATURE" and obj is not self.source_object
    )

    source_object: props.PointerProperty(  # type: ignore
        type=types.Object,
        poll=lambda self, obj: obj.type == "ARMATURE" and obj is not self.target_object
    )

    def draw(self, context, layout, node, text):
        is_object_node = isinstance(node, ReNimNodeObjectSourceTarget)
        is_output = self.is_output
        is_linked = self.is_linked

        split = layout.split(factor=0.3)
        col = split.column()
        col.alignment = "RIGHT"
        col.label(text="Target")
        col.label(text="Source")

        col = split.column()
        # TARGET
        if is_output and is_object_node:
            row = col.row()
            row.enabled = not node.is_bind
            row.prop(self, "target_object", text="")
        else:
            links = node.inputs[0].links
            if is_linked and len(links):
                row = col.row()
                row.enabled = False
                row.prop(links[0].from_socket,
                         "target_object", text="")
            else:
                col.label(text="NONE")

        # SOURCE
        if is_output and is_object_node:
            row = col.row()
            row.enabled = not node.is_bind
            row.prop(self, "source_object", text="")
        else:
            links = node.inputs[0].links
            if is_linked and len(links):
                row = col.row()
                row.enabled = False
                row.prop(links[0].from_socket,
                         "source_object", text="")
            else:
                col.label(text="NONE")

    def draw_color(self, context, node):  # type: ignore
        return (0.1, 0.4, 0.8, 1)


classes = [
    ReNimSocketSourceTarget
]


def register():
    for x in classes:
        register_class(x)


def unregister():
    for x in reversed(classes):
        unregister_class(x)
