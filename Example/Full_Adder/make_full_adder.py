
import sys
import importlib.util
import bpy

gate_assembly_spec = importlib.util.spec_from_file_location("gate_assembly.py", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/gate_assembly.py")
gate_assembly = importlib.util.module_from_spec(gate_assembly_spec)
sys.modules["pipe_system.py"] = gate_assembly
gate_assembly_spec.loader.exec_module(gate_assembly)




assembly = gate_assembly.GateAssembly()

assembly.reset_blender()

xor_gate_1 = assembly.add_gate("XOR_gate_1", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/Example/Gate_Library/XOR_gate.stl")
xor_gate_2 = assembly.add_gate("XOR_gate_2", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/Example/Gate_Library/XOR_gate.stl")
and_gate_1 = assembly.add_gate("AND_gate_1", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/Example/Gate_Library/AND_gate.stl")
and_gate_2 = assembly.add_gate("AND_gate_2", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/Example/Gate_Library/AND_gate.stl")
or_gate = assembly.add_gate("OR_gate", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/Example/Gate_Library/OR_gate.stl")

xor_gate_1.move_gate(5,15,3)
xor_gate_2.move_gate(15,15,3)
and_gate_1.move_gate(10,10,3)
and_gate_2.move_gate(10,5,3)
or_gate.move_gate(18,8,3)


assembly.add_free_end_port("Input_A", (0,15,5))
assembly.add_free_end_port("Input_B", (0,12,5))
assembly.add_free_end_port("Input_C", (0,8,5))
assembly.add_free_end_port("Output_S", (25,15,5))
assembly.add_free_end_port("Output_C", (25,8,5))



if assembly.prepare_for_connection(pipe_dimention = (.25,.1), unit_dimention = 1, tip_length = 1):

  assembly.add_connection(("FREE_END", "Input_A"), ("XOR_gate_1", "Input_1"))
  assembly.add_connection(("FREE_END", "Input_A"), ("AND_gate_2", "Input_1"))
  assembly.add_connection(("FREE_END", "Input_B"), ("XOR_gate_1", "Input_2"))
  assembly.add_connection(("FREE_END", "Input_B"), ("AND_gate_2", "Input_2"))
  assembly.add_connection(("FREE_END", "Input_C"), ("XOR_gate_2", "Input_2"))
  assembly.add_connection(("FREE_END", "Input_C"), ("AND_gate_1", "Input_1"))

  assembly.add_connection(("XOR_gate_1", "Output"), ("XOR_gate_2", "Input_1"))
  assembly.add_connection(("XOR_gate_1", "Output"), ("AND_gate_1", "Input_2"))

  assembly.add_connection(("XOR_gate_2", "Output"), ("FREE_END", "Output_S"))
  assembly.add_connection(("AND_gate_1", "Output"), ("OR_gate", "Input_1"))
  assembly.add_connection(("AND_gate_2", "Output"), ("OR_gate", "Input_2"))

  assembly.add_connection(("OR_gate", "Output"), ("FREE_END", "Output_C"))

  assembly.update_connection_dict()
