# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from . production import editor_type, editor_type_operator, socket_object, node_object, node_mapping

bl_info = {
    "name": "ReNim Node",
    "author": "Anas Rin",
    "description": "Node-Based Retarget Animation",
    "blender": (4, 1, 0),
    "version": (0, 1, 4),
    "location": "Editor Type > Retarget Animation Node",
    "warning": "",
    "wiki_url": "https://github.com/anasrar/ReNim",  # 2.82 below
    "doc_url": "https://github.com/anasrar/ReNim",  # 2.83 above
    "tracker_url": "https://github.com/anasrar/ReNim/issues",
    "support": "COMMUNITY",
    "category": "Animation",
}


submodules = [
    editor_type,
    editor_type_operator,
    socket_object,
    node_object,
    node_mapping,
]


def register():
    for x in submodules:
        if callable(getattr(x, "register")):
            x.register()


def unregister():
    for x in reversed(submodules):
        if callable(getattr(x, "unregister")):
            x.unregister()
