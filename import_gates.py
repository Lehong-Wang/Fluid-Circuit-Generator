
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

    self.Obj_Pos = (0,0,0)
    self.Obj_Scale = (1,1,1)
    self.Obj_Rotation = (0,0,0)

    self.Power_Pos = (0,0,0)
    self.Const_High_Pos = (0,0,0)
    self.Input_1_Pos = (0,0,0)
    self.Input_2_Pos = (0,0,0)
    self.Output_Pos = (0,0,0)

    self.Abs_Power_Pos = (0,0,0)
    self.Abs_Const_High_Pos = (0,0,0)
    self.Abs_Input_1_Pos = (0,0,0)
    self.Abs_Input_2_Pos = (0,0,0)
    self.Abs_Output_Pos = (0,0,0) 

    self.Actrual_Dimension = (1,1,1)

    self.data = {}

    # if no json file with same name, create one
    if not file_exists(self.json_path):
      print(f"Initial Json File not found")
      self.write_to_json()
      self.reconstruct_obj()
    else:
      print(f"Initial Json File found")
      self.load_from_json()



  def write_to_json(self):
    self.data = {}
    self.data["Name"] = self.name
    self.data["Actural Dimension"] = self.Actrual_Dimension
    tube_pos_dict = {}
    tube_pos_dict["Power_Pos"] = self.Power_Pos
    tube_pos_dict["Const_High_Pos"] = self.Const_High_Pos
    tube_pos_dict["Input_1_Pos"] = self.Input_1_Pos
    tube_pos_dict["Input_2_Pos"] = self.Input_2_Pos
    tube_pos_dict["Output_Pos"] = self.Output_Pos
    self.data["Tube Position"] = tube_pos_dict

    # print(f"Current Properties: {json.dumps(self.data, indent=2)}")

    file_name = self.name + ".json"
    with open(file_name, "w") as f:
      json.dump(self.data, f, indent=2)
      print(f"Wrote to file: {file_name}")





  def load_from_json(self):
    file_name = self.json_path
    with open(file_name, "r") as f:
      self.data = json.load(f)

      self.name = self.data["Name"]
      self.Actrual_Dimension = self.data["Actural Dimension"]
      self.Power_Pos = self.data["Tube Position"]["Power_Pos"]
      self.Const_High_Pos = self.data["Tube Position"]["Const_High_Pos"]
      self.Input_1_Pos = self.data["Tube Position"]["Input_1_Pos"]
      self.Input_2_Pos = self.data["Tube Position"]["Input_2_Pos"]
      self.Output_Pos = self.data["Tube Position"]["Output_Pos"]

      # print(f"Loaded Properties: {json.dumps(self.data, indent=2)}")
      print(f"Loaded from file: {file_name}")
      self.reconstruct_obj()
  

  def load_from_another_json(self, file_path):
    with open(file_path, "r") as f:
      self.data = json.load(f)

      self.name = self.data["Name"]
      self.Actrual_Dimension = self.data["Actural Dimension"]
      self.Power_Pos = self.data["Tube Position"]["Power_Pos"]
      self.Const_High_Pos = self.data["Tube Position"]["Const_High_Pos"]
      self.Input_1_Pos = self.data["Tube Position"]["Input_1_Pos"]
      self.Input_2_Pos = self.data["Tube Position"]["Input_2_Pos"]
      self.Output_Pos = self.data["Tube Position"]["Output_Pos"]

      # print(f"Loaded Properties: {json.dumps(self.data, indent=2)}")
      print(f"Loaded from file: {file_path}")
      self.reconstruct_obj()
    

  def reconstruct_obj(self):
    # delete previous object
    try:
      bpy.data.objects.remove(self.gate_obj)
      print("Previous Object Removed")
    except (AttributeError, TypeError):
      print("Previous Object not Exist")

    bpy.ops.import_mesh.stl(filepath = self.stl_path)
    self.gate_obj = bpy.context.active_object
    # apply move, scale, rotation
    self.gate_obj.rotation_mode = "XYZ"
    self.gate_obj.location = self.Obj_Pos
    self.gate_obj.dimensions = self.Actrual_Dimension
    self.gate_obj.scale = self.Obj_Scale
    self.gate_obj.rotation_euler = self.Obj_Rotation
    print(f"New Object at {self.gate_obj.location}, with dimensions: {self.Actrual_Dimension}")
    self.recalculte_nozzle_pos()

  # apply transformations to relative nuzzle pos
  def recalculte_nozzle_pos(self):
    nuzzle_list = [self.Power_Pos, self.Const_High_Pos, self.Input_1_Pos, self.Input_2_Pos, self.Output_Pos]
    Abs_nuzzle_list = []
    print(f"Relative nuzzle Pos for gate {self.name}: {nuzzle_list}")
    # Linear Algibra, Euler rotation
    x,y,z = self.Obj_Rotation
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
    for nuzzle_pos in nuzzle_list:
      scaled_pos = tuple(map(lambda a,b: a*b, nuzzle_pos, self.Obj_Scale))

      vector_before = np.array([scaled_pos[0], scaled_pos[1], scaled_pos[2]])
      vector_after = np.dot(np.dot(z_matrix, y_matrix), np.dot(x_matrix, vector_before))
      rotated_pos = tuple(vector_after)

      moved_pos = tuple(map(lambda a,b: a+b, rotated_pos, self.Obj_Pos))
      Abs_nuzzle_list.append(moved_pos)

    print(f"Absolute nuzzle Pos: {Abs_nuzzle_list}")
    self.Abs_Power_Pos = Abs_nuzzle_list[0]
    self.Abs_Const_High_Pos = Abs_nuzzle_list[1]
    self.Abs_Input_1_Pos = Abs_nuzzle_list[2]
    self.Abs_Input_2_Pos = Abs_nuzzle_list[3]
    self.Abs_Output_Pos = Abs_nuzzle_list[4]   
    print(f"Absolute Nozzle Pos recalculated")


  def move_gate(self, x_loc, y_loc, z_loc):
    self.Obj_Pos = (x_loc, y_loc, z_loc)
    print(f"Gate {self.name} Location set to {self.Obj_Pos}")
    self.reconstruct_obj()

  def rotate_gate(self, x_angle, y_angle, z_angle):
    self.Obj_Rotation = (radians(x_angle), radians(y_angle), radians(z_angle))
    print(f"Gate {self.name} scale set to {self.Obj_Rotation}(rad), {(x_angle, y_angle, z_angle)}(deg)")
    self.reconstruct_obj()

  def scale_gate(self, x_scale, y_scale, z_scale):
    self.Obj_Scale = (x_scale, y_scale, z_scale)
    print(f"Gate {self.name} Scale set to {self.Obj_Scale}")
    self.reconstruct_obj()


  def get_x_limit(self):
    x_limit = 0
    x_limit = self.Abs_Power_Pos[0] if self.Abs_Power_Pos[0] > x_limit else x_limit
    x_limit = self.Abs_Const_High_Pos[0] if self.Abs_Const_High_Pos[0] > x_limit else x_limit
    x_limit = self.Abs_Input_1_Pos[0] if self.Abs_Input_1_Pos[0] > x_limit else x_limit
    x_limit = self.Abs_Input_2_Pos[0] if self.Abs_Input_2_Pos[0] > x_limit else x_limit
    x_limit = self.Abs_Output_Pos[0] if self.Abs_Output_Pos[0] > x_limit else x_limit
    print(f"X_limit for gate {self.name} is {x_limit}")
    return x_limit

  def get_y_limit(self):
    y_limit = 0
    y_limit = self.Abs_Power_Pos[1] if self.Abs_Power_Pos[1] > y_limit else y_limit
    y_limit = self.Abs_Const_High_Pos[1] if self.Abs_Const_High_Pos[1] > y_limit else y_limit
    y_limit = self.Abs_Input_1_Pos[1] if self.Abs_Input_1_Pos[1] > y_limit else y_limit
    y_limit = self.Abs_Input_2_Pos[1] if self.Abs_Input_2_Pos[1] > y_limit else y_limit
    y_limit = self.Abs_Output_Pos[1] if self.Abs_Output_Pos[1] > y_limit else y_limit
    print(f"Y_limit for gate {self.name} is {y_limit}")
    return y_limit

  def get_z_limit(self):
    z_limit = 0
    z_limit = self.Abs_Power_Pos[2] if self.Abs_Power_Pos[2] > z_limit else z_limit
    z_limit = self.Abs_Const_High_Pos[2] if self.Abs_Const_High_Pos[2] > z_limit else z_limit
    z_limit = self.Abs_Input_1_Pos[2] if self.Abs_Input_1_Pos[2] > z_limit else z_limit
    z_limit = self.Abs_Input_2_Pos[2] if self.Abs_Input_2_Pos[2] > z_limit else z_limit
    z_limit = self.Abs_Output_Pos[2] if self.Abs_Output_Pos[2] > z_limit else z_limit
    print(f"Z_limit for gate {self.name} is {z_limit}")
    return z_limit




if __name__ == '__main__':
  this_stl_path = "/Users/lhwang/Documents/Blender Python Projects/Git Project Space/Robotic-Materials-Lab-Project/gate_data/test_modle.stl"
  l = LogicGate("obj1", this_stl_path)
  print("DATA:")
  print(l.data)
  # l.Obj_Pos = (0,0,100)
  # l.recalculte_nozzle_pos()

  # l.Actrual_Dimension = (10,20,10)
  # l.reconstruct_obj()

  # l.Power_Pos = (100,0,0)
  # l.Obj_Pos = (10,20,0)
  # l.Actrual_Dimension = (26,26,29.6)
  # l.write_to_json()
  # print("loading")
  # l.load_from_json()
  # another_json = "/Users/lhwang/Documents/Blender Python Projects/Git Project Space/Robotic-Materials-Lab-Project/test.json"
  # l.load_from_another_json(another_json)