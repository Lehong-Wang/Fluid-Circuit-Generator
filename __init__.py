


import bpy

import test_whole_addon.path_finding
import test_whole_addon.pipe_system
import test_whole_addon.import_gate
import test_whole_addon.gate_assembly
import test_whole_addon.test_UI_copy


bl_info = {
  "name": "test whole addon",
  "author": "Name",
  "version": (1, 0),
  "blender": (3, 2, 0),
  "location": "SpaceBar Search -> Add-on Preferences Example",
  "description": "test whole addon",
  "warning": "",
  "doc_url": "",
  "tracker_url": "",
  "category": "Mesh",
}





def register():
  for cls in test_whole_addon.test_UI_copy.class_to_register:
    bpy.utils.register_class(cls)
  test_whole_addon.test_UI_copy.register_properties()
  print("All Class Registered")

def unregister():
  for cls in test_whole_addon.test_UI_copy.class_to_register:
    bpy.utils.unregister_class(cls)
  test_whole_addon.test_UI_copy.unregister_properties()
  print("All Class UnRegistered")



