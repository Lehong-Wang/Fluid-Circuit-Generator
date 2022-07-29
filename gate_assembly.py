"""
Manage the whole Assembly including Logic Gates and Pipe System
Handles high level analysis and claculations like propagation delay
Keeps track of gates, connections, and check for duplicates
"""


import sys
import importlib.util
import bpy

pipe_system_spec = importlib.util.spec_from_file_location("pipe_system.py", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/pipe_system.py")
pipe_system = importlib.util.module_from_spec(pipe_system_spec)
sys.modules["pipe_system.py"] = pipe_system
pipe_system_spec.loader.exec_module(pipe_system)

import_gate_spec = importlib.util.spec_from_file_location("import_gate.py", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/import_gate.py")
import_gate = importlib.util.module_from_spec(import_gate_spec)
sys.modules["import_gate.py"] = import_gate
import_gate_spec.loader.exec_module(import_gate)



class GateAssembly:
  """
  Gate Assembly object
  Only create one, have one Pipe System object and a dictionary of Logic Gate object
  """

  def __init__(self):

    self.pipe_system = pipe_system.PipeSystem()
    # {gate_name : gate_object}
    self.logic_gate_dict = {}
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


  def prepare_for_connection(self, pipe_dimention=None, unit_dimention=1, tip_length=None):
    """
    Set grid to fit gate ports
    Check if ports are in valid position
    Call this function before making connections
    Don't make connection if this return False
    """
    max_real_dimention = (0,0,0)
    is_port_valid = True
    for gate in self.logic_gate_dict.values():
      max_real_dimention = tuple(map(max, max_real_dimention, gate.get_max_pos()))
      is_port_valid &= gate.check_port_valid()

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

    self.pipe_system.connect_two_port(start_port, end_port)


  def get_gate_port_coord(self, gate_name, port_name):
    """Helper function"""
    if gate_name in self.logic_gate_dict:
      return self.logic_gate_dict[gate_name].get_port_coord(port_name)
    else:
      print(f"Error: Gate name: {gate_name} doesn't exist in logic_gate_dict: {self.logic_gate_dict.keys()}")
      return None



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



  def get_propagation_delay(self, start_gate_port, end_gate_port):
    """Find path between two given ports and return the propagation delay"""
    if start_gate_port == end_gate_port:
      self.register_warning_message(f"WARNING: Looking for propergation delay to the same port {start_gate_port}")
      return 0

    start_coord = self.get_gate_port_coord(start_gate_port[0], start_gate_port[1])
    end_coord = self.get_gate_port_coord(end_gate_port[0], end_gate_port[1])

    if not start_coord or not end_coord:
      return 0

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
            return 0
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
  bpy.ops.object.select_all(action='SELECT')
  bpy.ops.object.delete(use_global=False)

  a = GateAssembly()

  gate1 = a.add_gate("g1", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/STL/gate1.stl")
  gate2 = a.add_gate("g2", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/STL/gate2.stl")
  gate1.move_gate(33,53,26)
  gate1.rotate_gate(15,26,37)
  gate1.scale_gate(1,3,.8)
  gate2.move_gate(13,17,20)
  gate2.scale_gate(.3,.7,.5)

  if a.prepare_for_connection(pipe_dimention = (.5,.3), unit_dimention = 3, tip_length = 4):

    a.add_connection((gate1.name, "Sphere"), ("g2", "Cube"))
    a.add_connection((gate1.name, "Cube"), ("g2", "Cube"))
    a.add_connection(("g1", "Ring"), ("g2", "Ring"))
    a.add_connection(("g2", "Ring"), ("g2", "IcoSphere"))
    print(a.connection_group_list)

    a.add_connection(("g1", "Ring"), ("g2", "IcoSphere"))

    a.update_connection_dict()

    a.get_propagation_delay(("g2", "IcoSphere"), ("g1", "Cube"))
    a.get_propagation_delay(("g2", "IcoSphere"), ("g2", "Cube"))

    a.print_connection_group()
    print(a.get_warning_message())
    print(a.get_error_message())












