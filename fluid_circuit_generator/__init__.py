
"""
__init__
Import all the modules
Have Info of the Addon
"""

import bpy

import fluid_circuit_generator.path_finding
import fluid_circuit_generator.pipe_system
import fluid_circuit_generator.import_gate
import fluid_circuit_generator.gate_assembly
import fluid_circuit_generator.ui_component


bl_info = {
  "name": "Fluid Circuit Generator",
  "author": "Lehong Wang",
  "version": (1, 0),
  "blender": (3, 2, 0),
  "location": "SpaceBar Search -> Add-on Preferences Example",
  "description": "This STREAM addon helps with auto generating 3D-printable fluid circuits.",
  "warning": "",
  "doc_url": "https://github.com/Lehong-Wang/Fluid-Circuit-Generator",
  "tracker_url": "",
  "category": "Mesh",
}





def register():
  """Register all the classes and properties"""
  for cls in fluid_circuit_generator.ui_component.class_to_register:
    bpy.utils.register_class(cls)
  fluid_circuit_generator.ui_component.register_properties()
  print("All Class Registered")

def unregister():
  """Unregister all the classes and properties"""
  for cls in fluid_circuit_generator.ui_component.class_to_register:
    bpy.utils.unregister_class(cls)
  fluid_circuit_generator.ui_component.unregister_properties()
  print("All Class UnRegistered")



