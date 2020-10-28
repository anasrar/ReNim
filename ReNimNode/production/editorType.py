import bpy
from bpy.types import NodeTree
from bpy.utils import register_class, unregister_class

class editorType(NodeTree):
    '''Retarget animation node'''
    bl_idname = 'ReNimNode'
    bl_label = "Retarget Animation Node"
    bl_icon = 'NODE_SEL'

classes = [
    editorType
]

def register():
    for x in classes:
        register_class(x)

def unregister():
    for x in reversed(classes):
        unregister_class(x)