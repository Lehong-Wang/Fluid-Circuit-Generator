
import sys
import importlib.util
import bpy

gate_assembly_spec = importlib.util.spec_from_file_location("gate_assembly.py", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/gate_assembly.py")
gate_assembly = importlib.util.module_from_spec(gate_assembly_spec)
sys.modules["pipe_system.py"] = gate_assembly
gate_assembly_spec.loader.exec_module(gate_assembly)




assembly = gate_assembly.GateAssembly()

assembly.reset_blender()

val_path = "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/Example/Bi_Stable_Val/bi_stable_val_1.stl"

gate_1 = assembly.add_gate("gate_1", val_path)
gate_2 = assembly.add_gate("gate_2", val_path)
gate_3 = assembly.add_gate("gate_3", val_path)


gate_1.move_gate(5,10,5)
gate_2.move_gate(15,10,5)
gate_3.move_gate(25,10,5)

gate_1.scale_gate(2,2,2)
gate_2.scale_gate(2,2,2)
gate_3.scale_gate(2,2,2)



assembly.add_free_end_port("Supply", (0,0,5))
assembly.add_free_end_port("Output", (30,15,5))



if assembly.prepare_for_connection(pipe_dimention = (.25,.1), unit_dimention = 1, tip_length = 1):

  assembly.add_connection(("FREE_END", "Supply"), ("gate_1", "Port_5"))
  assembly.add_connection(("FREE_END", "Supply"), ("gate_2", "Port_5"))
  assembly.add_connection(("FREE_END", "Supply"), ("gate_3", "Port_5"))

  assembly.add_connection(("gate_1", "Port_1"), ("gate_1", "Port_6"))
  assembly.add_connection(("gate_2", "Port_1"), ("gate_2", "Port_6"))
  assembly.add_connection(("gate_3", "Port_1"), ("gate_3", "Port_6"))

  assembly.add_connection(("gate_1", "Port_1"), ("gate_2", "Port_3"))
  assembly.add_connection(("gate_1", "Port_2"), ("gate_3", "Port_1"))

  assembly.add_connection(("gate_2", "Port_1"), ("gate_3", "Port_3"))

  assembly.add_connection(("gate_3", "Port_6"), ("FREE_END", "Output"))

  assembly.make_connections()

  assembly.update_connection_dict()
  assembly.add_stage()

  # assembly.print_to_connect_list()


