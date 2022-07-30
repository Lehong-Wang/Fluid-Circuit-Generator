
import sys
import importlib.util
import bpy

gate_assembly_spec = importlib.util.spec_from_file_location("gate_assembly.py", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/gate_assembly.py")
gate_assembly = importlib.util.module_from_spec(gate_assembly_spec)
sys.modules["pipe_system.py"] = gate_assembly
gate_assembly_spec.loader.exec_module(gate_assembly)







assembly = gate_assembly.GateAssembly()

assembly.reset_blender()

and_gate = assembly.add_gate("AND_gate", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/Example/Set_Reset_Latch/STL/AND_gate.stl")
not_gate = assembly.add_gate("NOT_gate", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/Example/Set_Reset_Latch/STL/NOT_gate.stl")
or_gate = assembly.add_gate("OR_gate", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/Example/Set_Reset_Latch/STL/OR_gate.stl")

and_gate.move_gate(20,10,10)
or_gate.move_gate(10,15,10)
not_gate.move_gate(10,5,10)


assembly.add_free_end_port("Input_set", (1,15,10))
assembly.add_free_end_port("Input_reset", (1,5,10))
assembly.add_free_end_port("Output", (20,0,10))


if assembly.prepare_for_connection(pipe_dimention = (.25,.1), unit_dimention = 1, tip_length = 1):


  assembly.add_connection(("FREE_END", "Input_set"), ("OR_gate", "Input_2"))
  assembly.add_connection(("FREE_END", "Input_reset"), ("NOT_gate", "Input_1"))
  assembly.add_connection(("AND_gate", "Output"), ("FREE_END", "Output"))

  assembly.add_connection(("OR_gate", "Output"), ("AND_gate", "Input_1"))
  assembly.add_connection(("NOT_gate", "Output"), ("AND_gate", "Input_2"))
  assembly.add_connection(("AND_gate", "Output"), ("OR_gate", "Input_1"))


  assembly.update_connection_dict()


