import bpy

import json
from os.path import exists as file_exists
import os
from math import radians, sin, cos, pi
import numpy as np


class LogicGate:

  def __init__(self, name, stl_path, json_path = None):
    self.gate_obj = None
    self.name = name
    self.stl_path = stl_path
    self.json_path = os.path.splitext(self.stl_path)[0]+".json"

    if json_path != None:
      self.json_path = json_path

    self.port_list = {}
    self.port_abs_pos  = {}
    self.connection_list = []
    self.json_data = {}

    bpy.ops.mesh.primitive_cube_add()
    self.gate_obj = bpy.context.active_object

    # if no json file with same name, create one
    if not file_exists(self.json_path):
      print(f"Initial Json File not found")
      self.write_to_json()
    #   self.reconstruct_obj()
    # else:
    #   print(f"Initial Json File found")
    #   self.load_from_json()



  def write_to_json(self, file_name = None):
    self.data = {}
    self.data["Name"] = self.name
    # self.data["Object Dimension"] = tuple(self.gate_obj.dimensions)
    self.data["Object Dimension"] = (1,2,3)
    self.data["Port Info"] = self.port_list
    self.data["Connections"] = self.connection_list

    print(f"Current Properties: {json.dumps(self.data, indent=2)}")

    if not file_name:
      file_name = self.json_path
    else:
      if not file_exists(file_name):
        print(f"Error: Json Path {file_name} doesn't exist.")
        return
    with open(file_name, "w") as f:
      json.dump(self.data, f, indent=2)
      print(f"Wrote to file: {file_name}")



  def load_from_json(self, file_name = None):
    if not file_name:
      file_name = self.json_path
    else:
      if not file_exists(file_name):
        print(f"Error: Json Path {file_name} doesn't exist.")
        return
    with open(file_name, "r") as f:
      self.data = json.load(f)

      self.name = self.data["Name"]
      self.port_list = self.data["Port Info"]
      self.connection_list = self.data["Connections"]

      print(f"Loaded Properties: {json.dumps(self.data, indent=2)}")
      print(f"Loaded from file: {file_name}")
      # self.reconstruct_obj()









if __name__ == '__main__':
  gate = LogicGate("g1", "/home/lhwang/Documents/GitHub/Fluid-Circuit-Generator/STL/gate1.stl")
  gate.port_list["P1"] = (2,3,4)
  gate.port_list["P2"] = (3,4,5)
  gate.port_list["P3"] = (4,5,6)
  gate.connection_list.append(("P1", "P2"))
  gate.write_to_json()
  gate.load_from_json()
  print(gate.connection_list)
  print(gate.data)