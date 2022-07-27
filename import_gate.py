
"""
Import logic gate design as stl and construct the modle in Blender
Also need to provide port position and connection info etc in the form of json file
"""


import json
from os.path import exists as file_exists
import os
from math import radians, sin, cos
import numpy as np

import bpy


class LogicGate:
  """
  Logic Gate object
  Provide stl file, json file (optional) during decliration
  """

  def __init__(self, name, stl_path, json_path = None):
    self.gate_obj = None
    self.name = name
    self.stl_path = stl_path
    self.json_path = os.path.splitext(self.stl_path)[0]+".json"

    if json_path is not None:
      self.json_path = json_path

    self.default_dimention = None
    # {name : (pos)}
    self.port_dict = {}
    self.port_abs_pos  = {}
    # {name : [(name, propagation_delay)]}
    self.connection_dict = {}
    # data from json file
    # { ["Name"] : self.name,
    #   ["Object Dimension"] : self.default_dimention,
    #   ["Port Info"] : self.port_dict,
    #   ["Connections"] : self.connection_dict  }
    self.json_data = {}
    # [position, rotation, scale]
    self.obj_placement_data = [(0,0,0), (0,0,0), (1,1,1)]

    if not file_exists(self.stl_path):
      print(f"Error: Stl file Not Exist: {self.stl_path}")
      return

    # if no json file with same name, create one
    if not file_exists(self.json_path):
      print("Initial Json File not found")
      self.reconstruct_obj()
      self.write_to_json()
    else:
      print("Initial Json File found")
      self.load_from_json()



  def write_to_json(self, file_name = None):
    """Write current object info to json"""
    self.json_data = {}
    self.json_data["Name"] = self.name
    self.json_data["Object Dimension"] = tuple(self.gate_obj.dimensions)
    # self.json_data["Object Dimension"] = (1,2,3)
    self.json_data["Port Info"] = self.port_dict
    self.json_data["Connections"] = self.connection_dict

    # print(f"Current Properties: {json.dumps(self.json_data, indent=2)}")

    if not file_name:
      file_name = self.json_path
    else:
      if not file_exists(file_name):
        print(f"Error: Json Path {file_name} doesn't exist.")
        return
    with open(file_name, "w") as f:
      json.dump(self.json_data, f, indent=2)
      print(f"Wrote to file: {file_name}")



  def load_from_json(self, file_name = None):
    """Load info from json"""
    if not file_name:
      file_name = self.json_path
    else:
      if not file_exists(file_name):
        print(f"Error: Json Path {file_name} doesn't exist.")
        return
    with open(file_name, "r") as f:
      self.json_data = json.load(f)

      self.name = self.json_data["Name"]
      self.default_dimention = self.json_data["Object Dimension"]
      self.port_dict = self.json_data["Port Info"]
      self.connection_dict = self.json_data["Connections"]

      # print(f"Loaded Properties: {json.dumps(self.json_data, indent=2)}")
      print(f"Loaded from file: {file_name}")
      self.reconstruct_obj()


  def reconstruct_obj(self):
    """Reconstruct the model from current data"""
    # delete previous object
    try:
      bpy.data.objects.remove(self.gate_obj)
      print("Previous Object Removed")
    except (AttributeError, TypeError):
      print("Previous Object not Exist")

    bpy.ops.import_mesh.stl(filepath = self.stl_path)
    self.gate_obj = bpy.context.active_object
    # set object dimensions to default, without changing the scale
    if self.default_dimention:
      current_dimention = tuple(self.gate_obj.dimensions)
      bpy.ops.object.mode_set(mode = 'EDIT')
      bpy.ops.transform.resize(value = tuple(map(lambda x,y: x/y, self.default_dimention, current_dimention)))
      bpy.ops.object.mode_set(mode = 'OBJECT')
    else:
      self.default_dimention = tuple(self.gate_obj.dimensions)

    # apply move, scale, rotation
    self.gate_obj.rotation_mode = "XYZ"
    self.gate_obj.location = self.obj_placement_data[0]
    self.gate_obj.rotation_euler = self.obj_placement_data[1]
    self.gate_obj.dimensions = tuple(map(lambda x,y: x*y, self.default_dimention, self.obj_placement_data[2]))
    print(f"New Object at {self.gate_obj.location}, with rotation: {self.gate_obj.rotation_euler}, dimensions: {self.gate_obj.dimensions}")
    self.recalculte_port_abs_pos()


  # apply transformations to relative nuzzle pos
  def recalculte_port_abs_pos(self):
    """Recalculate the absolute port position"""
    print(f"Relative Port Pos for gate {self.name}: {self.port_dict.items()}")

    # Linear Algibra, Euler rotation
    x,y,z = self.obj_placement_data[1]
    # print("\n\nX,Y,Z to rotate",x,y,z)
    x_matrix = np.array([[1, 0, 0],\
                          [0, cos(x), -sin(x)],\
                          [0, sin(x), cos(x)]])

    y_matrix = np.array([[cos(y), 0, sin(y)],\
                          [0, 1, 0],\
                          [-sin(y), 0, cos(y)]])

    z_matrix = np.array([[cos(z), -sin(z), 0],\
                          [sin(z), cos(z), 0],\
                          [0, 0, 1]])

    # scale -> ratate -> move
    for name, port_pos in self.port_dict.items():
      scaled_pos = tuple(map(lambda a,b: a*b, port_pos, self.obj_placement_data[2]))

      vector_before = np.array([scaled_pos[0], scaled_pos[1], scaled_pos[2]])
      vector_after = np.dot(np.dot(z_matrix, y_matrix), np.dot(x_matrix, vector_before))
      rotated_pos = tuple(vector_after)

      moved_pos = tuple(map(lambda a,b: a+b, rotated_pos, self.obj_placement_data[0]))
      self.port_abs_pos[name] = moved_pos

    print(f"Absolute nuzzle Pos: {self.port_abs_pos.items()}")
    print("Absolute Nozzle Pos recalculated")



  def move_gate(self, x_loc, y_loc, z_loc):
    """Move gate"""
    self.obj_placement_data[0] = (x_loc, y_loc, z_loc)
    print(f"Gate {self.name} Location set to {self.obj_placement_data[0]}")
    self.reconstruct_obj()

  def rotate_gate(self, x_angle, y_angle, z_angle):
    """Rotate gate"""
    self.obj_placement_data[1] = (radians(x_angle), radians(y_angle), radians(z_angle))
    print(f"Gate {self.name} Rotation set to {self.obj_placement_data[1]}(rad), {(x_angle, y_angle, z_angle)}(deg)")
    self.reconstruct_obj()

  def scale_gate(self, x_scale, y_scale, z_scale):
    """Scale gate"""
    self.obj_placement_data[2] = (x_scale, y_scale, z_scale)
    print(f"Gate {self.name} Scale set to {self.obj_placement_data[2]}")
    self.reconstruct_obj()


  def get_port_coord(self, port_name):
    """Helper function"""
    if port_name in self.port_abs_pos:
      return self.port_abs_pos[port_name]
    else:
      print(f"ERROR: Port name: {port_name} doesn't exist in logic gate, which have port: {self.port_abs_pos.keys()}")




if __name__ == '__main__':
  bpy.ops.object.select_all(action='SELECT')
  bpy.ops.object.delete(use_global=False)

  gate = LogicGate("g1", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/STL/gate1.stl")


  # gate.connection_dict["Ring"] = [("Cube", 0.1)]
  # gate.connection_dict["Ring"].append(("Sphere", .2))
  # gate.write_to_json()

  gate.move_gate(33,24,15)
  gate.rotate_gate(15,26,37)
  gate.scale_gate(2,3,4)

  for pos in gate.port_abs_pos.values():
    bpy.ops.mesh.primitive_cube_add(size = 1, location = pos)

  gate2 = LogicGate("g2", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/STL/gate2.stl")

  # gate.port_dict["P1"] = (2,3,4)
  # gate.port_dict["P2"] = (3,4,5)
  # gate.port_dict["P3"] = (4,5,6)
  # gate.connection_dict["P1"] = ("P2", .1)
  # gate.write_to_json()
  # gate.load_from_json()
  # print(gate.connection_dict)
  # print(gate.gate_obj)
