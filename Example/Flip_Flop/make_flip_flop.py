
import time
import sys
import importlib.util
import bpy


gate_assembly_spec = importlib.util.spec_from_file_location("gate_assembly.py", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/gate_assembly.py")
gate_assembly = importlib.util.module_from_spec(gate_assembly_spec)
sys.modules["pipe_system.py"] = gate_assembly
gate_assembly_spec.loader.exec_module(gate_assembly)


start_time = time.time()

assembly = gate_assembly.GateAssembly()

assembly.reset_blender()


and_gate_1 = assembly.add_gate("AND_gate_1", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/Example/Gate_Library/AND_gate.stl")
and_gate_2 = assembly.add_gate("AND_gate_2", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/Example/Gate_Library/AND_gate.stl")

nor_gate_1 = assembly.add_gate("NOR_gate_1", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/Example/Gate_Library/NOR_gate.stl")
nor_gate_2 = assembly.add_gate("NOR_gate_2", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/Example/Gate_Library/NOR_gate.stl")

and_gate_1.move_gate(5,10,5)
and_gate_2.move_gate(5,5,5)
nor_gate_1.move_gate(15,10,10)
nor_gate_2.move_gate(15,5,10)


assembly.add_free_end_port("Input_R", (0,15,5))
assembly.add_free_end_port("Input_C", (0,10,5))
assembly.add_free_end_port("Input_S", (0,5,5))
assembly.add_free_end_port("Output_Q1", (20,15,5))
assembly.add_free_end_port("Output_Q2", (20,5,5))


if assembly.prepare_for_connection(pipe_dimention = (.25,.1), unit_dimention = 1, tip_length = 1):
  assembly.add_connection(("FREE_END", "Input_R"), ("AND_gate_1", "Input_1"))
  assembly.add_connection(("FREE_END", "Input_C"), ("AND_gate_1", "Input_2"))
  assembly.add_connection(("FREE_END", "Input_C"), ("AND_gate_2", "Input_1"))
  assembly.add_connection(("FREE_END", "Input_S"), ("AND_gate_2", "Input_2"))

  assembly.add_connection(("AND_gate_1", "Output"), ("NOR_gate_1", "Input_1"))
  assembly.add_connection(("AND_gate_2", "Output"), ("NOR_gate_2", "Input_2"))

  assembly.add_connection(("NOR_gate_1", "Output"), ("NOR_gate_2", "Input_1"))
  assembly.add_connection(("NOR_gate_2", "Output"), ("NOR_gate_1", "Input_2"))

  assembly.add_connection(("NOR_gate_1", "Output"), ("FREE_END", "Output_Q1"))
  assembly.add_connection(("NOR_gate_2", "Output"), ("FREE_END", "Output_Q2"))

  assembly.update_connection_dict()
  assembly.add_stage()


delta_time = "{:.5f}".format(time.time() - start_time)
print(delta_time)




