"""
Manage the whole Assembly including Logic Gates and Pipe System
Handles high level analysis and claculations like propagation delay
Keeps track of gates, connections, and check for duplicates
"""


import json
import os
import sys
import importlib.util
import bpy

# pipe_system_spec = importlib.util.spec_from_file_location("pipe_system.py", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/pipe_system.py")
# pipe_system = importlib.util.module_from_spec(pipe_system_spec)
# sys.modules["pipe_system.py"] = pipe_system
# pipe_system_spec.loader.exec_module(pipe_system)

# import_gate_spec = importlib.util.spec_from_file_location("import_gate.py", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/import_gate.py")
# import_gate = importlib.util.module_from_spec(import_gate_spec)
# sys.modules["import_gate.py"] = import_gate
# import_gate_spec.loader.exec_module(import_gate)

import fluid_circuit_generator.pipe_system as pipe_system
import fluid_circuit_generator.import_gate as import_gate



class GateAssembly:
  """
  Gate Assembly object
  Only create one, have one Pipe System object and a dictionary of Logic Gate object
  """

  stage_height = 1
  stage_margin = .5
  tip_offset = 0.1


  def __init__(self):

    self.pipe_system = pipe_system.PipeSystem()
    # {gate_name : gate_object}
    self.logic_gate_dict = {}
    # {port_name : coord}
    # gate_name for free end port is "FREE_END"
    self.free_end_port_dict = {}
    # [(start_coord, end_coord)]
    self.to_connect_list = []
    # {start : [(end, propagation_delay) ] }
    self.connection_dict = {}
    # list of all connection grounps (ports that are interconnected)
    # store as (gate_name, port_name)
    self.connection_group_list = []

    # stores user related error messages
    self.error_message_list = []
    # stores user related warning messages
    self.warning_message_list = []




  def add_gate(self, name, stl_path):
    """Add logic gate"""
    new_gate = import_gate.LogicGate(name, stl_path)
    self.logic_gate_dict[name] = new_gate
    return new_gate


  def add_free_end_port(self, port_name, port_coord):
    """Add free end port"""
    if port_name in self.free_end_port_dict:
      self.register_warning_message(f"WARNING: Port name {port_name}, coord {self.free_end_port_dict[port_name]} already exists in free_end_port_dict, now replaced with coord {port_coord}")
    self.free_end_port_dict[port_name] = port_coord
    return port_coord


  def prepare_for_connection(self, pipe_dimention=None, unit_dimention=1, tip_length=None, stage_height=1, stage_margin=.5, tip_offset=.1):
    """
    Set grid to fit gate ports
    Check if ports are in valid position
    Call this function before making connections
    Don't make connection if this return False
    """
    self.stage_height = stage_height
    self.stage_margin = stage_margin
    self.tip_offset = tip_offset

    max_real_dimention = (0,0,0)
    is_port_valid = True  # within valid dimensions
    # check gates
    for gate in self.logic_gate_dict.values():
      max_real_dimention = tuple(map(max, max_real_dimention, gate.get_max_pos()))
      is_port_valid &= gate.check_port_valid()
    # check free_end_port_dict
    for port_coord in self.free_end_port_dict.values():
      max_real_dimention = tuple(map(max, max_real_dimention, port_coord))

    max_grid_dimention = tuple(map(lambda x: int(x//unit_dimention)+1, max_real_dimention))

    self.pipe_system.reset_grid(max_grid_dimention, pipe_dimention, unit_dimention, tip_length)
    return is_port_valid



  def add_connection(self, gate_port_start, gate_port_end):
    """
    Function to connect two ports with (gate_name, port_name)
    Also check if connection already exists
    """
    start_in_group = None
    end_in_group = None
    for group in self.connection_group_list:
      if gate_port_start in group:
        start_in_group = group
      if gate_port_end in group:
        end_in_group = group

    # both new
    if not start_in_group and not end_in_group:
      self.connection_group_list.append([gate_port_start, gate_port_end])
    # start new
    elif not start_in_group and end_in_group:
      end_in_group.append(gate_port_start)
    # end new
    elif start_in_group and not end_in_group:
      start_in_group.append(gate_port_end)
    # in same group
    elif start_in_group and end_in_group and start_in_group is end_in_group:
      self.register_warning_message(f"WARNING: Connection already exists between {gate_port_start} and {gate_port_end}")
      return
    # in different group
    elif start_in_group and end_in_group and start_in_group is not end_in_group:
      start_in_group.extend(end_in_group)
      self.connection_group_list.remove(end_in_group)

    self.create_port_connection(gate_port_start, gate_port_end)


  def create_port_connection(self, gate_port_start, gate_port_end):
    """Helper Function"""
    gate_start, port_start = gate_port_start
    gate_end, port_end = gate_port_end
    start_port = self.get_gate_port_coord(gate_start, port_start)
    end_port = self.get_gate_port_coord(gate_end, port_end)

    self.to_connect_list.append((start_port, end_port))
    # self.pipe_system.connect_two_port(start_port, end_port)


  def get_gate_port_coord(self, gate_name, port_name):
    """Helper function"""
    if gate_name == "FREE_END":
      return self.free_end_port_dict[port_name]

    if gate_name in self.logic_gate_dict:
      return self.logic_gate_dict[gate_name].get_port_coord(port_name)
    else:
      print(f"Error: Gate name: {gate_name} doesn't exist in logic_gate_dict: {self.logic_gate_dict.keys()}")
      return None


  def make_connections(self):
    self.pipe_system.to_connect_list = self.to_connect_list[:]
    for connection in self.to_connect_list:
      self.pipe_system.connect_two_port(connection[0], connection[1])




  def update_connection_dict(self):
    """Load connection info from pipe_system and logic_gate into connection_dict with propagation delay"""
    self.pipe_system.finish_up_everything()
    # get connection from pipe_system.connection_graph
    for key,value in self.pipe_system.connection_graph.items():
      connection_list = []
      for connection in value:
        path = connection[1]
        # calculate propagation_delay
        propagation_delay = len(path) * .05

        connection_list.append((connection[0], propagation_delay))
      self.connection_dict[key] = connection_list
    print("Gate Assembly connection_dict updated from Pipe System connection_graph")

    # get connection form logic_gate.connection_dict
    for gate in self.logic_gate_dict.values():
      for key,value in gate.connection_dict.items():
        key_port_coord = gate.get_port_coord(key)
        connection_list = []
        for connection in value:
          port_coord = gate.get_port_coord(connection[0])
          propagation_delay = connection[1]
          connection_list.append((port_coord, propagation_delay))
        if key_port_coord in self.connection_dict:
          self.connection_dict[key_port_coord].extend(connection_list)
        else:
          self.connection_dict[key_port_coord] = connection_list
    print("Gate Assembly connection_dict updated from Logic Gate connection_dict")

    print("Gate Assembly connection_dict fully updated")
    self.print_connection_dict()


  def round_coord(self, coord):
    """Helper function"""
    return tuple(map(lambda x: round(x,2), coord))
    # return coord



  def get_propagation_delay(self, start_gate_port, end_gate_port):
    """Find path between two given ports and return the propagation delay"""
    if start_gate_port == end_gate_port:
      self.register_warning_message(f"WARNING: Looking for propergation delay to the same port {start_gate_port}")
      return 0

    start_coord = self.get_gate_port_coord(start_gate_port[0], start_gate_port[1])
    end_coord = self.get_gate_port_coord(end_gate_port[0], end_gate_port[1])

    if (not start_coord) or (not end_coord):  # either don't exist
      return float('-inf')

    # Breath First Search
    search_queue = []
    visited_list = []
    last_visited = {}

    search_queue.append(start_coord)

    while search_queue:
      this_coord = search_queue.pop(0)

      # found
      if this_coord is end_coord:
        found_path = []
        total_propegation_delay = 0
        current_coord = this_coord
        # trace back and get delay
        while current_coord is not start_coord:
          found_path.insert(0, current_coord)
          last_visited_coord = last_visited[current_coord]
          current_delay = self.get_delay(last_visited_coord, current_coord)
          if current_delay is None:
            print("Error: Problem with get_delay")
            return float('-inf')
          total_propegation_delay += current_delay
          current_coord = last_visited_coord

        total_propegation_delay = round(total_propegation_delay,4)
        print(f"Found path: {found_path}")
        print(f"Total Propegation Delay: {total_propegation_delay}")
        return total_propegation_delay

      # get neighbor list
      this_neighbor_list = []
      for dest in self.connection_dict[this_coord]:
        this_neighbor_list.append(dest[0])
      # add neighbors to search queue
      for neighbor in this_neighbor_list:
        if not (neighbor in visited_list) and (neighbor not in search_queue):
          search_queue.append(neighbor)
          last_visited[neighbor] = this_coord

      visited_list.append(this_coord)

    return float('inf')


  def get_delay(self, coord, dest):
    """Helper Function"""
    if coord not in self.connection_dict:
      print(f"Error: Coord {coord} not in connection_dict")
      return None
    dest_list = self.connection_dict[coord]
    for this_dest, this_delay in dest_list:
      if dest == this_dest:
        return this_delay
    print(f"Error: Destination {dest} not in dest_list of {coord}, dest_list: {dest_list}")
    return None


  def add_stage(self):
    """
    Call this function to auto generate stage under each logic gate
    Only call after update_connection_dict()
    Note: this process will significantly add to program run time
    """
    offset = self.tip_offset
    stage_obj_list = []

    for gate in self.logic_gate_dict.values():
      # calculate stage dimentions
      gate_max_pos = gate.get_max_pos()
      gate_min_pos = gate.get_min_pos()
      stage_margin = 2 * (self.stage_margin + self.pipe_system.pipe_dimention[0] + self.pipe_system.pipe_dimention[1])
      stage_x_dim = gate_max_pos[0] - gate_min_pos[0] + stage_margin
      stage_y_dim = gate_max_pos[1] - gate_min_pos[1] + stage_margin
      stage_z_dim = min(self.stage_height, gate_min_pos[2]-offset)   # stage lower bounded by xy plane

      stage_x_pos = (gate_max_pos[0] + gate_min_pos[0])/2
      stage_y_pos = (gate_max_pos[1] + gate_min_pos[1])/2
      stage_z_pos = gate_min_pos[2] - offset - stage_z_dim/2

      bpy.ops.mesh.primitive_cube_add()
      stage_object = bpy.context.active_object
      stage_object.dimensions = (stage_x_dim, stage_y_dim, stage_z_dim)
      stage_object.location = (stage_x_pos, stage_y_pos, stage_z_pos)

      # stage_min_range = tuple(map(lambda a,b: a-b/2-1, (stage_x_pos, stage_y_pos, stage_z_pos), (stage_x_dim, stage_y_dim, stage_z_dim)))
      # stage_max_range = tuple(map(lambda a,b: a+b/2+1, (stage_x_pos, stage_y_pos, stage_z_pos), (stage_x_dim, stage_y_dim, stage_z_dim)))
      # print(f"STAGE: pos: {(stage_x_pos, stage_y_pos, stage_z_pos)}, range: {stage_min_range}-{stage_max_range}")

      to_cut_path_list = []
      for path_coord_list in self.pipe_system.connection_dict.values():
        # collect path within range of stage
        to_cut_coord = []
        for coord in path_coord_list:
          if self.in_stage_range((stage_x_dim, stage_y_dim, stage_z_dim), (stage_x_pos, stage_y_pos, stage_z_pos), coord):
            to_cut_coord.append(coord)
          else:
            if to_cut_coord:
              to_cut_path_list.append(to_cut_coord[:])
            to_cut_coord.clear()
        # clear list at the end
        if to_cut_coord:
          to_cut_path_list.append(to_cut_coord[:])
      print(f"Path in range of stage at {(stage_x_pos, stage_y_pos, stage_z_pos)}, Path list: {to_cut_path_list}")

      for to_cut_path in to_cut_path_list:
        if len(to_cut_path) < 2:
          continue
        # make solid tube from to_cut_path_list and cut out from stage
        to_cut_sylinder = self.make_solid_sylinder(f"Cut_{(stage_x_pos, stage_y_pos, stage_z_pos)}", to_cut_path)
        self.cut_out_with_boolean(stage_object, to_cut_sylinder)

      stage_obj_list.append(stage_object)
    return stage_obj_list



  def in_stage_range(self, stage_dim, stage_pos, coord):
    """Helper Function"""
    stage_min_range = tuple(map(lambda a,b: a-b/2-1, stage_pos, stage_dim))
    stage_max_range = tuple(map(lambda a,b: a+b/2+1, stage_pos, stage_dim))
    in_range = tuple(map(lambda a,b,c: a<=c and c<=b, stage_min_range, stage_max_range, coord))
    return in_range[0] & in_range[1] & in_range[2]


  def make_solid_sylinder(self, name, coord_list):
    """Helper Function"""
    # standard create tube
    curve_data = bpy.data.curves.new(name, type = "CURVE")
    curve_data.dimensions = "3D"

    polyline = curve_data.splines.new("POLY")
    polyline.points.add(len(coord_list)-1)
    for i, coord in enumerate(coord_list):
      x,y,z = coord
      polyline.points[i].co = (x,y,z,1)

    curve_object = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(curve_object)

    curve_object.data.bevel_depth = self.pipe_system.pipe_dimention[0] + self.pipe_system.pipe_dimention[1]/2
    curve_object.data.bevel_resolution = 2
    curve_object.data.use_fill_caps = True

    curve_object.select_set(True)
    bpy.context.view_layer.objects.active = curve_object
    bpy.ops.object.convert(target = "MESH")
    return curve_object


  def cut_out_with_boolean(self, stage_object, to_cut_sylinder):
    """Helper Function"""
    # need exact solver for all
    junction_modifier_name = "Boolean"
    stage_object.modifiers.new(junction_modifier_name, "BOOLEAN").object = to_cut_sylinder
    stage_object.modifiers[junction_modifier_name].operation = 'DIFFERENCE'
    stage_object.modifiers[junction_modifier_name].solver = "EXACT"
    # fully select before apply
    stage_object.select_set(True)
    bpy.context.view_layer.objects.active = stage_object
    bpy.ops.object.modifier_apply(modifier = junction_modifier_name)

    bpy.data.objects.remove(to_cut_sylinder)
    # to_cut_sylinder.hide_set(True)





  def add_tip(self, stl_path):

    # handles tip stl
    abs_path = bpy.path.abspath(stl_path)
    root,ext = os.path.splitext(abs_path)

    if not os.path.exists(abs_path):
      self.register_error_message(f"File Not Exist at {abs_path}")
      return

    if ext != ".stl":
      self.register_error_message(f"File is Not an STL file, file: {abs_path}")
      return

    json_path = root + ".json"
    if not os.path.exists(json_path):
      self.register_error_message(f"Corresponding Json file not found for file {abs_path}")
      return

    with open(json_path, 'r') as f:
      json_data = json.load(f)
      obj_base_name = json_data["Name"]
      obj_dim = list(json_data["Object Dimension"])
      pipe_dim = list(json_data["Pipe Dimension"])
      tip_radius = pipe_dim[0] + pipe_dim[1]

    target_radius = self.pipe_system.pipe_dimention[0] + self.pipe_system.pipe_dimention[1]
    target_scale = target_radius / tip_radius
    offset = self.tip_offset
    # add tip to each port
    added_coord = []
    tip_obj_list = []
    for connection in self.to_connect_list:
      for coord in connection:
        if coord not in added_coord:
          added_coord.append(coord)
          rounded_coord = tuple(map(lambda x: round(x,2), coord))
          bpy.ops.import_mesh.stl(filepath = abs_path)
          tip_obj = bpy.context.active_object
          tip_obj.name = f"{obj_base_name}-{rounded_coord}"
          tip_obj.scale = (target_scale, target_scale, 1)
          tip_obj.location = (coord[0], coord[1], coord[2]-offset)
          tip_obj_list.append(tip_obj)

    return tip_obj_list







  def reset_blender(self):
    """Call this function before everything to reset blender"""
    # delete all object (including invisible ones)
    for obj in bpy.data.collections.data.objects:
      bpy.data.objects.remove(obj)
    # set to object mode
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.object.mode_set(mode = "OBJECT")
    # delete cube
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # move cursor to origin
    bpy.context.scene.cursor.location = (0,0,0)
    # # scale using cursor as origin
    # bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'







  ##############################################  Print Helper  ##################################################


  def print_connection_dict(self):
    """Helper function"""
    print("\nConnection Dict:")
    for key,value in self.connection_dict.items():
      print(f"\tStart: {self.round_coord(key)}")
      for connection in value:
        print(f"Dest: {self.round_coord(connection[0])}, Propegation delay: {round(connection[1],4)}")

  def print_connection_group(self):
    """Helper function"""
    print("\nConnection Group:")
    for i,group in enumerate(self.connection_group_list):
      print(f"\tGroup {i}: {group}")

  def print_to_connect_list(self):
    """Helper function"""
    print("\nTo Connect list:")
    for item in self.to_connect_list:
      print(item)

  def register_error_message(self, error_message):
    """Helper Function"""
    self.error_message_list.append(error_message)
    print(error_message)

  def register_warning_message(self, warning_message):
    """Helper Function"""
    self.warning_message_list.append(warning_message)
    print(warning_message)

  def get_error_message(self):
    """Helper Function"""
    pipe_error_message = self.pipe_system.get_error_message()
    gate_error_message = []
    for gate in self.logic_gate_dict.values():
      gate_error_message.extend(gate.get_error_message())
    self.error_message_list.extend(pipe_error_message)
    self.error_message_list.extend(gate_error_message)
    return self.error_message_list

  def get_warning_message(self):
    """Helper Function"""
    pipe_warning_message = self.pipe_system.get_warning_message()
    gate_warning_message = []
    for gate in self.logic_gate_dict.values():
      gate_warning_message.extend(gate.get_warning_message())
    self.warning_message_list.extend(pipe_warning_message)
    self.warning_message_list.extend(gate_warning_message)
    return self.warning_message_list






if __name__ == '__main__':
  # bpy.ops.object.select_all(action='SELECT')
  # bpy.ops.object.delete(use_global=False)

  a = GateAssembly()

  a.reset_blender()

  gate1 = a.add_gate("g1", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/STL/gate1.stl")
  gate2 = a.add_gate("g2", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/STL/gate2.stl")
  gate1.move_gate(33,53,26)
  gate1.rotate_gate(15,26,37)
  gate1.scale_gate(1,3,.8)
  gate2.move_gate(13,17,20)
  gate2.scale_gate(.7,.7,.5)
  gate2.rotate_gate(5,5,30)

  a.add_free_end_port("f1", (10,40,10))
  a.add_free_end_port("f2", (45,10,10))

  if a.prepare_for_connection(pipe_dimention = (.5,.3), unit_dimention = 3, tip_length = 4, stage_height = 20, stage_margin = 2, tip_offset = 3):

    a.add_connection((gate1.name, "Sphere"), ("g2", "Cube"))
    a.add_connection((gate1.name, "Cube"), ("g2", "Cube"))
    a.add_connection(("g1", "Ring"), ("g2", "Ring"))
    a.add_connection(("g2", "Ring"), ("g2", "IcoSphere"))

    a.add_connection(("g1", "Ring"), ("g2", "IcoSphere"))
    a.add_connection(("g2", "Cone"), ("FREE_END", "f1"))
    a.add_connection(("FREE_END", "f2"), ("FREE_END", "f1"))

    a.make_connections()

    # print(a.connection_group_list)

    a.update_connection_dict()

    a.add_stage()
    a.add_tip("/Users/lhwang/Desktop/pipe_tip.stl")

    a.get_propagation_delay(("g2", "IcoSphere"), ("g1", "Cube"))
    a.get_propagation_delay(("g2", "IcoSphere"), ("g2", "Cube"))

    a.print_connection_group()
    print(a.get_warning_message())
    print(a.get_error_message())












