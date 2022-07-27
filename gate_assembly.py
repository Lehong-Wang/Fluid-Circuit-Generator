


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


# p = pipe_system.PipeSystem()
# g = import_gate.LogicGate("g2", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/STL/gate2.stl")


class GateAssembly:

  _instance = None

  def __new__(cls):
    if not cls._instance:
      cls._instance = super(GateAssembly, cls).__new__(cls)

      cls.pipe_system = pipe_system.PipeSystem()
      cls.logic_gate_dict = {}
      # {start : [(end, propagation_delay) ] }
      cls.connection_dict = {}
      # list of all connection grounps (ports that are interconnected)
      # store as (gate_name, port_name)
      cls.connection_group_list = []


    return cls._instance


  def add_gate(self, name, stl_path):
    new_gate = import_gate.LogicGate(name, stl_path)
    self.logic_gate_dict[name] = new_gate
    return new_gate



  def add_connection(self, gate_port_start, gate_port_end):
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
      print(f"WARNING: Connection already exists between {gate_port_start} and {gate_port_end}")
      return
    # in different group
    elif start_in_group and end_in_group and start_in_group is not end_in_group:
      start_in_group.extend(end_in_group)
      self.connection_group_list.remove(end_in_group)

    self.create_port_connection(gate_port_start, gate_port_end)


  def create_port_connection(self, gate_port_start, gate_port_end):
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
      print(f"ERROR: Gate name: {gate_name} doesn't exist in logic_gate_dict: {self.logic_gate_dict.keys()}")



  def update_connection_dict(self):
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


  def print_connection_dict(self):
    """Helper function"""
    print("\nConnection Dict:")
    for key,value in self.connection_dict.items():
      print(f"\tStart: {self.round_coord(key)}")
      for connection in value:
        print(f"Dest: {self.round_coord(connection[0])}, Propegation delay: {round(connection[1],4)}")

  def round_coord(self, coord):
    """Helper function"""
    return tuple(map(lambda x: round(x,2), coord))






if __name__ == '__main__':
  bpy.ops.object.select_all(action='SELECT')
  bpy.ops.object.delete(use_global=False)

  a = GateAssembly()

  gate1 = a.add_gate("g1", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/STL/gate1.stl")
  gate2 = a.add_gate("g2", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/STL/gate2.stl")
  gate1.move_gate(3,3,6)
  gate1.rotate_gate(15,26,37)
  gate1.scale_gate(.2,.2,.1)
  gate2.move_gate(6,7,7)
  gate2.scale_gate(.3,.3,.1)

  a.add_connection((gate1.name, "Sphere"), ("g2", "Cube"))
  a.add_connection((gate1.name, "Cube"), ("g2", "Cube"))
  a.add_connection(("g1", "Ring"), ("g2", "Ring"))
  a.add_connection(("g2", "Ring"), ("g2", "IcoSphere"))
  print(a.connection_group_list)

  a.add_connection(("g1", "Ring"), ("g2", "IcoSphere"))

  a.update_connection_dict()

  print(a.connection_group_list)











