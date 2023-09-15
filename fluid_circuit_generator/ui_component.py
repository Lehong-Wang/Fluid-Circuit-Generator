
"""
UI Component
All the UI is in this file.
This file is mostly independent from the rest of the program
Only call functions form gate_assembly at the end when making the final module
All other functionalities can be run with this file alone
"""



import json
import os
from math import radians, degrees, sin, cos
import numpy as np
import bpy

import fluid_circuit_generator.gate_assembly as gate_assembly





bl_info = {
  "name": "test UI addon",
  "author": "Name",
  "version": (1, 0),
  "blender": (3, 2, 0),
  "location": "SpaceBar Search -> Add-on Preferences Example",
  "description": "test UI addon",
  "warning": "",
  "doc_url": "",
  "tracker_url": "",
  "category": "Mesh",
}



# change the maxium number of connection allowed here
MAX_NUM_OF_CONNECTIONS = 500


############################################################################
################################  Operater  ################################
############################################################################


class MESH_OT_reset_my_addon(bpy.types.Operator):
  """
  The Reset button at the top
  Delete all addon data
  Reset all your choices to default
  """
  bl_idname = "mesh.reset_my_addon"
  bl_label = "Reset My Addon"

  def execute(self, context):
    # remove all object
    # this will also clean related data like gate choices and gate object properties
    for obj in bpy.data.objects:
      bpy.data.objects.remove(obj)

    # clear connection_dict
    connect_prop = bpy.context.scene.connection_property
    connect_prop.connection_dict.clear()

    # clear info stored for making assembly
    bpy.types.MESH_OT_make_assembly.gate_list.clear()
    bpy.types.MESH_OT_make_assembly.connection_list.clear()
    bpy.types.MESH_OT_make_assembly.assembly = gate_assembly.GateAssembly()

    # reset property to default
    bpy.context.scene.property_unset("connection_property")
    bpy.context.scene.property_unset("pipe_property")
    bpy.context.scene.property_unset("ui_property")

    # clear privious object list
    bpy.context.scene.connection_property.gate_obj_list.clear()
    bpy.context.scene.connection_property.pipe_obj_list.clear()
    bpy.context.scene.connection_property.free_end_obj_list.clear()
    bpy.context.scene.connection_property.stage_obj_list.clear()
    bpy.context.scene.connection_property.tip_obj_list.clear()

    # clear error message list
    bpy.context.scene.ui_property.error_message_list.clear()

    print("Addon Reset")
    return {'FINISHED'}



class MESH_OT_add_gate_object(bpy.types.Operator):
  """
  Add a Logic Gate object by stl file
  Or add a free end pointer object
  """
  bl_idname = "mesh.add_gate_object"
  bl_label = "Add Logic Gate Object"

  # obj_count = 0

  def execute(self, context):
    # get fake props
    is_free_end = bpy.context.scene.ui_property.fake_is_free_end
    if is_free_end:
      file_path = FREE_END_STL
    else:
      file_path = bpy.context.scene.ui_property.fake_stl_file_path

    abs_path = bpy.path.abspath(file_path)
    root,ext = os.path.splitext(abs_path)
    # check validation of file path
    if ext != ".stl":
      self.report(
        {"ERROR"},
        f"File is Not an STL file, file: {abs_path}"
      )
      return {"CANCELLED"}

    try:
      bpy.ops.import_mesh.stl(filepath = abs_path)
    except FileNotFoundError:
      self.report(
        {"ERROR"},
        f"File Not Exist at {abs_path}"
        )
      return {"CANCELLED"}

    imported_object = bpy.context.active_object
    imported_object.gate_property.stl_file_path = abs_path
    imported_object.gate_property.is_free_end = is_free_end

    if is_free_end:
      # scale free end by dimention
      dim = bpy.context.scene.pipe_property.unit_dimention
      imported_object.scale = (dim, dim, dim)
      return {'FINISHED'}
    # check json file
    json_path = root + ".json"
    imported_object.gate_property.json_file_path = json_path
    if not os.path.exists(json_path):
      self.report(
        {"ERROR"},
        f"Corresponding Json file not found for file {abs_path}"
      )
      return {"CANCELLED"}

    # self.obj_count += 1
    return {"FINISHED"}






# Blender have problem supporting dynamic lists of properties
# To work around that, all the properties are pre-created
# If connection added, give value to pre-created property and display it
# This is why there is a limit of how many connections you can add
# Set the limit by changing the MAX_NUM_OF_CONNECTIONS at top of file
class MESH_OT_add_gate_connection(bpy.types.Operator):
  """
  Add a connection choice row
  Only show the properties with value assigned
  Which creates an illusion of dynamic lists
  """
  bl_idname = "mesh.add_gate_connection"
  bl_label = "Add gate connection"

  def execute(self, context):
    connect_prop = bpy.context.scene.connection_property
    name_list = connect_prop.generic_gate_name_list
    # if no active object, report error
    if bpy.context.active_object is None:
      self.report(
        {'ERROR'},
        "Select a gate object to add connection"
      )
      return {'CANCELLED'}
    # loop over all prop, display ones not all None
    for n in range(MAX_NUM_OF_CONNECTIONS):
      # row all empty
      prop_set_all_None = True
      for prop_name in name_list:
        # see if start/end_gate_n (Object) is None
        prop_value = getattr(connect_prop, f"{prop_name}{n}")
        if prop_value is not None:
          prop_set_all_None = False

      # add a gate at first non-empty row
      if prop_set_all_None:
        # make start_gate_n = active_object
        setattr(connect_prop, f"{name_list[0]}{n}", bpy.context.active_object)
        # if free_end, and a sphere
        if bpy.context.active_object.gate_property.is_free_end is True:
          Helper.place_current_selection_sphere(list(bpy.context.active_object.location))

        return {'FINISHED'}

    self.report(
      {'ERROR'},
      f"Reached maxium number of connections (currently set to {MAX_NUM_OF_CONNECTIONS})\nChange \"MAX_NUM_OF_CONNECTIONS\" variable in code to add more connections"
    )
    return {'CANCELLED'}






class MESH_OT_choose_connection_port(bpy.types.Operator):
  """
  Generic button to choose a port for a logic gate connection
  Pass in different arguments for different ports
  """
  bl_idname = "mesh.choose_connection_port"
  bl_label = "Choose Connection Port"

  row_index: bpy.props.IntProperty(default=0)
  gate_index: bpy.props.IntProperty(default=0)
  port_name: bpy.props.StringProperty(default="")
  selected_gate_name: bpy.props.StringProperty(default="")

  def execute(self, context):
    print(f"Choose row {self.row_index}, gate {self.gate_index}, port {self.port_name}")
    connect_prop = bpy.context.scene.connection_property
    connection_dict = connect_prop.connection_dict
    connection_dict[(self.row_index, self.gate_index)] = self.port_name
    # self.filter_free_port_from_dict()
    # print(connection_dict)

    # get current selected gate by name
    gate_obj = bpy.data.objects[self.selected_gate_name]
    print(f"Button {self.row_index, self.gate_index}, obj: {gate_obj}")
    if gate_obj is None:
      return {'CANCELLED'}
    # place sphere at selected port
    select_pos = Helper.get_abs_port_pos(gate_obj, self.port_name)
    Helper.place_current_selection_sphere(select_pos)

    return {'FINISHED'}





class MESH_OT_cancel_connection_port(bpy.types.Operator):
  """
  This button show up after pressing button for choosing port
  This operator delete the choice and allow reselect
  """
  bl_idname = "mesh.cancel_connection_port"
  bl_label = "Cancel Connection Port"

  row_index: bpy.props.IntProperty(default=0)
  gate_index: bpy.props.IntProperty(default=0)

  def execute(self, context):
    connect_prop = bpy.context.scene.connection_property
    connection_dict = connect_prop.connection_dict

    key = (self.row_index, self.gate_index)
    try:
      connection_dict.pop(key)
    except KeyError:
      self.report(
        {"ERROR"},
        f"Key {key} not exist in Dict {connection_dict}"
      )
      return {'CANCELLED'}
    # print(connection_dict)

    Helper.remove_current_selection_sphere()

    return {'FINISHED'}





class Helper():
  """
  Helper class
  Contains function for calculating port transformations and checking opsition
  """

  @staticmethod
  def calculate_abs_pos(placement_data, port_pos):
    """
    Helper function to calculate the absolute port position
    return pos as a List
    """
    # placement_data: ((loc), (rot), (scl))

    # Linear Algibra, Euler rotation
    x,y,z = placement_data[1]
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
    scaled_pos = list(map(lambda a,b: a*b, port_pos, placement_data[2]))

    vector_before = np.array([scaled_pos[0], scaled_pos[1], scaled_pos[2]])
    vector_after = np.dot(np.dot(z_matrix, y_matrix), np.dot(x_matrix, vector_before))
    rotated_pos = list(vector_after)

    moved_pos = list(map(lambda a,b: a+b, rotated_pos, placement_data[0]))
    rounded_pos = list(map(lambda a: round(a,2), moved_pos))

    print(f"Port Pos: {port_pos} -> {rounded_pos}")
    return rounded_pos


  @staticmethod
  def get_relative_port_pos(gate_obj, port_name):
    """return port ops from json"""
    json_file = gate_obj.gate_property.json_file_path
    with open(json_file, 'r') as f:
      json_data = json.load(f)
      port_pos = json_data["Port Info"][port_name]

    return port_pos

  @staticmethod
  def get_abs_port_pos(gate_obj, port_name):
    """return transformed port pos"""

    gate_pos = tuple(gate_obj.location)
    gate_rotation = tuple(gate_obj.rotation_euler)
    gate_scale = tuple(gate_obj.scale)
    print(f"Logic Gate: {gate_obj}", end="\t")

    placement_data = (gate_pos, gate_rotation, gate_scale)
    relative_port_pos = Helper.get_relative_port_pos(gate_obj, port_name)

    abs_port_pos = Helper.calculate_abs_pos(placement_data, relative_port_pos)
    return abs_port_pos



  @staticmethod
  def check_port_valid(gate_obj, port_name=None):
    """
    Given gate_obj and port_name(optional)
    check if port position is valid (in first corrdinate and one unit above ground)
      if port_name is not given, check all ports of gate
    return Error message string or None for check passed
    """

    unit_dim = bpy.context.scene.pipe_property.unit_dimention

    # free end
    if gate_obj.gate_property.is_free_end:
      free_end_pos = tuple(gate_obj.location)
      free_end_pos = tuple(map(lambda x: round(x,2), free_end_pos))

      if min(free_end_pos) < 0:
        return f"Free End: {gate_obj.name} is not in the first coordinate, location {free_end_pos}\nAll ports must have location(x,y,z) >= 0"

      if free_end_pos[2] < unit_dim:
        return f"Free End: {gate_obj.name}, is too close to ground,  location: {free_end_pos}\nAll ports much be more than 1 unit length({unit_dim}mm) above ground."


    # logic gate
    else:
      port_name_list = []
      if port_name is None:
        json_file = gate_obj.gate_property.json_file_path
        with open(json_file, 'r') as f:
          json_data = json.load(f)
          port_pos = json_data["Port Info"]
          port_name_list = list(port_pos.keys())
      else:
        port_name_list = [port_name]

      for this_port_name in port_name_list:
        port_pos = Helper.get_abs_port_pos(gate_obj, this_port_name)

        if min(port_pos) < 0:
          return f"Gate: {gate_obj.name}, Port: {this_port_name} is not in the first coordinate, location: {port_pos}\nAll ports must have location(x,y,z) >= 0"

        if port_pos[2] < unit_dim:
          return f"Gate: {gate_obj.name}, Port: {this_port_name} is too close to ground,  location: {port_pos}\nAll ports much be more than 1 unit length({unit_dim}mm) above ground."

    return None




  @staticmethod
  def place_current_selection_sphere(select_pos:list):
    """Place a sphere at selected port"""
    connect_prop = bpy.context.scene.connection_property

    Helper.remove_current_selection_sphere()

    select_scale = bpy.context.scene.pipe_property.unit_dimention
    bpy.ops.mesh.primitive_uv_sphere_add(
      radius=select_scale,
      location=select_pos,
      segments=16, ring_count=8)

    bpy.context.active_object.name = "Current Selection"
    bpy.context.active_object.display_type = 'WIRE'
    connect_prop.select_sphere_obj = bpy.context.active_object
    print(f"Sphere Obj: {connect_prop.select_sphere_obj}")


  @staticmethod
  def remove_current_selection_sphere():
    """Remove Sphere"""
    connect_prop = bpy.context.scene.connection_property
    # Delete previous selection sphere
    sphere_obj = connect_prop.select_sphere_obj
    if sphere_obj is not None:
      if sphere_obj.name in bpy.data.objects:
        bpy.data.objects.remove(sphere_obj)
    connect_prop.select_sphere_obj = None






class MESH_OT_check_connection_selection(bpy.types.Operator):
  """
  Helper Operator
  Check if user input for connection is complete and valid
  Called by other operators
  """
  bl_idname = "mesh.check_connection_selection"
  bl_label = "Check Connection Selection"

  def execute(self, context):

    if not self.check_gate_selected():
      return {'CANCELLED'}
    if not self.check_port_select():
      return {'CANCELLED'}
    if not self.check_port_position():
      # print("\n\n\nCheck Port Positsion Failed\n\n\n")
      return {'CANCELLED'}
    return {'FINISHED'}



  def check_gate_selected(self):
    """
    Check if full rows of gate are selected
    """
    connect_prop = bpy.context.scene.connection_property
    ui_prop = bpy.context.scene.ui_property

    name_list = connect_prop.generic_gate_name_list
    error_list = ui_prop.error_message_list

    something_selected = False

    for n in range(MAX_NUM_OF_CONNECTIONS):
      row_all_selected = True
      row_all_empty = True

      for gate_name in name_list:
        gate_obj = getattr(connect_prop, f"{gate_name}{n}")
        # none gate object selected
        if gate_obj and gate_obj.gate_property.stl_file_path == "":
          self.report(
            {'ERROR'},
            "Invalid object is selected"
          )
          # # operator that are not directly called can't show pop up error message
          # # store error in ui_prop, and the callee will report it
          # # However, still need to report error message to generate RuntimeError
          error_list.append("Invalid object is selected")
          return False
        if gate_obj:
          row_all_empty = False
          something_selected = True
        else:
          row_all_selected = False
      # partially selected
      if row_all_empty == row_all_selected:
        self.report(
          {'ERROR'},
          "Gate Object Not Properly Selected"
        )
        error_list.append("Gate Object Not Properly Selected")
        return False
    if not something_selected:
      self.report(
        {'ERROR'},
        "No Valid Connection"
      )
      error_list.append("No Valid Connection")
    print("Gate Properly Selected")
    return True



  def check_port_select(self):
    """
    Check of Logic Gate object have port selected
    """
    connect_prop = bpy.context.scene.connection_property
    error_list = bpy.context.scene.ui_property.error_message_list
    name_list = connect_prop.generic_gate_name_list
    connection_dict = connect_prop.connection_dict

    self.filter_free_port_from_dict()

    for n in range(MAX_NUM_OF_CONNECTIONS):

      for i,gate_name in enumerate(name_list):
        gate_obj = getattr(connect_prop, f"{gate_name}{n}")
        # not free end
        if gate_obj and not gate_obj.gate_property.is_free_end:
          key = (n,i)
          if not key in connection_dict:
            self.report(
              {'ERROR'},
              "Port Not Fully Selected"
            )
            error_list.append("Port Not Fully Selected")
            return False
    print("Port Properly Selected")
    return True


  def filter_free_port_from_dict(self):
    """
    Deals with a paticular bug where
      user first finished choosing gate and port,
      but then turn the gate to a free port and the port info is still there
    This function looks for that and delete them
    """
    connect_prop = bpy.context.scene.connection_property
    connection_dict = connect_prop.connection_dict
    name_list = connect_prop.generic_gate_name_list
    to_pop_key_list = []
    for key in connection_dict.keys():
      n,i = key
      gate_obj = getattr(connect_prop, f"{name_list[i]}{n}")
      if gate_obj and gate_obj.gate_property.is_free_end:
        to_pop_key_list.append(key)
    for key in to_pop_key_list:
      connection_dict.pop(key)


  def check_port_position(self):
    """
    Check if all ports are in the first coordinate
    If not, throw a warning
    """

    connect_prop = bpy.context.scene.connection_property
    name_list = connect_prop.generic_gate_name_list
    error_list = bpy.context.scene.ui_property.error_message_list

    for n in range(MAX_NUM_OF_CONNECTIONS):
      for i,gate_name in enumerate(name_list):
        gate_obj = getattr(connect_prop, f"{gate_name}{n}")
        if gate_obj is not None:
            # msg is None if no error
            msg = Helper.check_port_valid(gate_obj)
            # print(f"\nHelper.check_port_valid\nError Message:\n{msg}\n")
            if msg is not None:
              self.report({'ERROR'}, msg)
              error_list.append(msg)
              return False

    return True





class MESH_OT_make_assembly(bpy.types.Operator):
  """
  The magic button that does everything
  WARNING: Pressing this button is irreversable
    It will delete all your choices and make the logic gates invalid
    But it did give you the final product
    Only Press this after you checked everything is correct
    Ctrl + Z might appear to work, but it would actually mess up internal data and cause wield errors
    Please don't use Ctrl Z to redo
    If you did, please press Reset Addon Button to avoid nasty errors
  This button is the only connection between UI and backend
  It calls functions from gate_assembly to build the circuit
  """
  bl_idname = "mesh.make_assembly"
  bl_label = "Make Assembly"

  # [ (is_free_end, name, ...info), (...) ]
  gate_list = []
  # [ [(start_name, port_name), (end_name, port_name)], [...] ]
  connection_list = []
  assembly = gate_assembly.GateAssembly()

  def execute(self, context):


    # check valid input
    try:
      bpy.ops.mesh.check_connection_selection()
    except RuntimeError:
      error_list = bpy.context.scene.ui_property.error_message_list
      for message in error_list:
        self.report({"ERROR"}, message)
      error_list.clear()
      return {'CANCELLED'}

    self.get_all_gates()
    self.get_all_connections()

    # remove connection selection
    bpy.context.scene.connection_property.connection_dict.clear()

    self.assembly.reset_blender()

    gate_obj_list = []
    pipe_obj_list = []
    free_end_obj_list = []
    stage_obj_list = []
    tip_obj_list = []

    print("\nPositioning all gates")
    gate_obj_list = self.place_all_gates()
    self.add_all_connections()

    if bpy.context.scene.pipe_property.add_stage:
      stage_obj_list = self.assembly.add_stage()

    if bpy.context.scene.pipe_property.add_custom_tip:
      tip_stl = bpy.context.scene.pipe_property.tip_stl_path
      tip_obj_list = self.assembly.add_tip(tip_stl)

    free_end_obj_list = self.place_free_end_points()

    for obj in bpy.data.objects:
      if obj not in gate_obj_list\
        and obj not in free_end_obj_list\
          and obj not in stage_obj_list\
            and obj not in tip_obj_list:
              pipe_obj_list.append(obj)

    # print(f"gate_obj_list: {gate_obj_list}")
    # print(f"pipe_obj_list: {pipe_obj_list}")

    connect_prop = bpy.context.scene.connection_property
    connect_prop.gate_obj_list.extend(gate_obj_list)
    connect_prop.pipe_obj_list.extend(pipe_obj_list)
    connect_prop.free_end_obj_list.extend(free_end_obj_list)
    connect_prop.stage_obj_list.extend(stage_obj_list)
    connect_prop.tip_obj_list.extend(tip_obj_list)


    bpy.context.scene.ui_property.confirm_make_assembly = False
    bpy.context.scene.ui_property.assembly_is_made = True

    return {'FINISHED'}





  def get_all_gates(self):
    """
    Collect all the gate / free_end info and put into gate_list
    """
    connect_prop = bpy.context.scene.connection_property
    name_list = connect_prop.generic_gate_name_list

    recorded_gate_list = []

    for n in range(MAX_NUM_OF_CONNECTIONS):
      for gate_name in name_list:
        gate_obj = getattr(connect_prop, f"{gate_name}{n}")
        # not recorded
        if gate_obj is not None and not (gate_obj in recorded_gate_list):
          # free end
          if gate_obj.gate_property.is_free_end:
            # add free end
            free_end_name = gate_obj.name
            free_end_pos = tuple(gate_obj.location)
            print(f"Free end: {gate_obj}, pos: {free_end_pos}")

            record_unit = (True, free_end_name, free_end_pos)

          # logic gate
          else:
            stl_path = gate_obj.gate_property.stl_file_path
            gate_pos = list(gate_obj.location)
            gate_rotation = list(gate_obj.rotation_euler)
            gate_scale = list(gate_obj.scale)
            gate_name = gate_obj.name
            print(f"Logic Gate: {gate_obj}, name: {gate_name}, pos: {gate_pos}, rotation: {gate_rotation}, scale: {gate_scale}")
            print(f"\tStl: {stl_path}")

            record_unit = (False, gate_name, stl_path, gate_pos, gate_rotation, gate_scale)


          self.gate_list.append(record_unit)
          recorded_gate_list.append(gate_obj)

    print(self.gate_list)




  def get_all_connections(self):
    """
    Collect all the connection_info and put into connection_list
    """
    connect_prop = bpy.context.scene.connection_property
    name_list = connect_prop.generic_gate_name_list
    connection_dict = connect_prop.connection_dict

    for n in range(MAX_NUM_OF_CONNECTIONS):
      connection_unit = []
      for i,gate_name in enumerate(name_list):
        gate_obj = getattr(connect_prop, f"{gate_name}{n}")
        if gate_obj:
          # gate
          if not gate_obj.gate_property.is_free_end:
            port_name = connection_dict[(n,i)]
            connection_unit.append((gate_obj.name, port_name))
          # free end
          else:
            connection_unit.append(("FREE_END", gate_obj.name))
      if connection_unit:
        print(f"Added connection unit {connection_unit}")
        self.connection_list.append(connection_unit)

    print(self.connection_list)



  def place_all_gates(self):
    """
    Add Logic Gate and Free End
    """
    gate_obj_list = []

    for gate_info in self.gate_list:
      is_free_end = gate_info[0]

      if is_free_end:
        self.assembly.add_free_end_port(gate_info[1], gate_info[2])

      else:
        imported_gate = self.assembly.add_gate(gate_info[1], gate_info[2])
        imported_gate.move_gate(gate_info[3][0], gate_info[3][1], gate_info[3][2])
        imported_gate.rotate_gate(degrees(gate_info[4][0]), degrees(gate_info[4][1]), degrees(gate_info[4][2]))
        imported_gate.scale_gate(gate_info[5][0], gate_info[5][1], gate_info[5][2])
        imported_gate.gate_obj.gate_property.stl_file_path = gate_info[2]
        root,ext = os.path.splitext(gate_info[2])
        json_path = root + ".json"
        imported_gate.gate_obj.gate_property.json_file_path = json_path

        gate_obj_list.append(imported_gate.gate_obj)
    return gate_obj_list


  def add_all_connections(self):
    """
    Add Connections
    """
    pipe_prop = bpy.context.scene.pipe_property
    inner_radius = pipe_prop.pipe_inner_radius
    thickness = pipe_prop.pipe_thickness
    unit_dim = pipe_prop.unit_dimention
    stage_height = pipe_prop.stage_height
    stage_margin = pipe_prop.stage_rim_size
    tip_offset = pipe_prop.tip_offset
    # tip_len = pipe_prop.tip_length
    tip_len = unit_dim / 2
    if self.assembly.prepare_for_connection(
      pipe_dimention = (inner_radius,thickness),
      unit_dimention = unit_dim,
      tip_length = tip_len,
      stage_height = stage_height,
      stage_margin = stage_margin,
      tip_offset = tip_offset):

      for connection_unit in self.connection_list:

        self.assembly.add_connection(connection_unit[0], connection_unit[1])

    self.assembly.make_connections()
    self.assembly.update_connection_dict()

    print(self.assembly.get_warning_message())
    print(self.assembly.get_error_message())



  def place_free_end_points(self):
    """Place free end objects"""
    dim = bpy.context.scene.pipe_property.unit_dimention
    free_end_obj_list = []
    for gate_packet in self.gate_list:
      is_free_end = gate_packet[0]
      if is_free_end:
        name = gate_packet[1]
        pos = gate_packet[2]
        rounded_pos = tuple(map(lambda x: round(x,2), pos))
        bpy.ops.import_mesh.stl(filepath = FREE_END_STL)
        obj = bpy.context.active_object
        # if "free_end_pointer" in name:
        #   obj.name = f"FreeEnd_{rounded_pos}"
        obj.name = name
        obj.location = pos
        obj.scale = (dim, dim, dim)
        obj.gate_property.stl_file_path = FREE_END_STL
        root, ext = os.path.splitext(FREE_END_STL)
        json_path = root + ".json"
        obj.gate_property.json_file_path = json_path
        obj.gate_property.is_free_end = True
        # obj.hide_set(True)
        free_end_obj_list.append(obj)
    return free_end_obj_list







class MESH_OT_make_preview_pipe(bpy.types.Operator):
  """
  Makes a example section of pipe,
    so user can get a feel for the dimensions of the pipe, tip, stage, etc
  """
  bl_idname = "mesh.make_preview_pipe"
  bl_label = "Make Preview Pipe"

  def execute(self, context):

    pipe_prop = bpy.context.scene.pipe_property
    inner_radius = pipe_prop.pipe_inner_radius
    thickness = pipe_prop.pipe_thickness
    unit_dim = pipe_prop.unit_dimention
    fillet_dim = .7 * (inner_radius + thickness)
    # dot list for example pipe
    dot_list = [
      (0, 2*unit_dim, 0),
      (0, fillet_dim, 0),
      (fillet_dim, 0, 0),
      (unit_dim-fillet_dim, 0, 0),
      (unit_dim, 0, fillet_dim),
      (unit_dim, 0, 2*unit_dim),
    ]
    pipe_name = "Test Tube"
    stage_name = "Test Stage"
    tip_name = "Test Tip"


    # make pipe
    curve_data = bpy.data.curves.new(pipe_name, type = "CURVE")
    curve_data.dimensions = "3D"

    polyline = curve_data.splines.new("POLY")
    polyline.points.add(len(dot_list)-1)
    for i, coord in enumerate(dot_list):
      x,y,z = coord
      polyline.points[i].co = (x,y,z,1)

    curve_object = bpy.data.objects.new(pipe_name, curve_data)
    bpy.context.collection.objects.link(curve_object)

    curve_object.data.bevel_depth = inner_radius + thickness
    curve_object.data.bevel_resolution = 2
    solidify_modifier_name = "Solidify"
    curve_object.modifiers.new(solidify_modifier_name, "SOLIDIFY").thickness = thickness
    pipe_prop.preview_obj_list.append(curve_object)

    # add stage
    if pipe_prop.add_stage:

      height = pipe_prop.stage_height
      length = 2*(pipe_prop.stage_rim_size + inner_radius + thickness)
      offset = pipe_prop.tip_offset
      tip_pos = dot_list[-1]
      stage_pos = (tip_pos[0], tip_pos[1], tip_pos[2]-offset-height/2)

      bpy.ops.mesh.primitive_cube_add()
      stage_cube = bpy.context.active_object
      stage_cube.name = stage_name
      stage_cube.dimensions = (length, length, height)
      stage_cube.location = stage_pos
      pipe_prop.preview_obj_list.append(stage_cube)


    # add tip
    if pipe_prop.add_custom_tip:
      stl_path = pipe_prop.tip_stl_path
      offset = pipe_prop.tip_offset
      tip_pos = dot_list[-1]

      # handles tip stl
      abs_path = bpy.path.abspath(stl_path)
      root,ext = os.path.splitext(abs_path)

      if ext != ".stl":
        self.report(
          {"ERROR"},
          f"File is Not an STL file, file: {abs_path}"
          )
        return {"CANCELLED"}

      try:
        bpy.ops.import_mesh.stl(filepath = abs_path)
      except FileNotFoundError:
        self.report(
          {"ERROR"},
          f"File Not Exist at {abs_path}"
          )
        return {"CANCELLED"}

      tip_obj = bpy.context.active_object

      json_path = root + ".json"
      if not os.path.exists(json_path):
        self.report(
          {"ERROR"},
          f"Corresponding Json file not found for file {abs_path}"
        )
        return {"CANCELLED"}

      with open(json_path, 'r') as f:
        json_data = json.load(f)
        obj_dim = list(json_data["Object Dimension"])
        pipe_dim = list(json_data["Pipe Dimension"])
        tip_radius = pipe_dim[0] + pipe_dim[1]

      inner_radius = pipe_prop.pipe_inner_radius
      thickness = pipe_prop.pipe_thickness
      target_radius = inner_radius + thickness
      target_scale = target_radius / tip_radius

      tip_obj.name = tip_name
      tip_obj.scale = (target_scale, target_scale, target_scale)
      tip_obj.location = (tip_pos[0], tip_pos[1], tip_pos[2]-offset)
      pipe_prop.preview_obj_list.append(tip_obj)

    pipe_prop.preview_is_shown = True
    return {'FINISHED'}



class MESH_OT_delete_preview_pipe(bpy.types.Operator):
  """
  Delete previously made preview pipe
  """
  bl_idname = "mesh.delete_preview_pipe"
  bl_label = "Delete Preview Pipe"

  def execute(self, context):
    obj_list = bpy.context.scene.pipe_property.preview_obj_list
    for obj in obj_list:
      try:
        bpy.data.objects.remove(obj)
      except ReferenceError:
        self.report(
          {"WARNING"},
          "Preview Object Already Deleted"
        )
    obj_list.clear()
    bpy.context.scene.pipe_property.preview_is_shown = False
    return {'FINISHED'}




PREVIEW_PIPE_NAME = "Preview Pipe"


class MESH_OT_make_preview_connection(bpy.types.Operator):
  """
  Makes a staight line for all the connections,
    so it's easier for the user to check if connections are correct
  """
  bl_idname = "mesh.make_preview_connection"
  bl_label = "Make Preview Connection"

  # { gate_name : [ (port_name, [pos]), ... ] }
  gate_port_dict = {}
  # { (gate_name, port_name) : [pos] }
  gate_port_abs_dict = {}
  # [ [(start_name, port_name), (end_name, port_name)], [...] ]
  connection_list = []

  def execute(self, context):

    try:
      bpy.ops.mesh.check_connection_selection()
      error_list = bpy.context.scene.ui_property.error_message_list

      print(f"\nFinished check_connection_selection\n{error_list}\n")
    except RuntimeError:


      error_list = bpy.context.scene.ui_property.error_message_list

      # print(f"\ncheck_connection_selection failed\n{error_list}\n")

      for message in error_list:
        self.report({"ERROR"}, message)
      error_list.clear()
      return {'CANCELLED'}
    # clear previous data
    self.gate_port_dict.clear()
    self.gate_port_abs_dict.clear()
    self.connection_list.clear()


    if not self.collect_port_info():
      return {'CANCELLED'}

    self.update_port_pos()
    self.update_free_end_pos()
    self.get_all_connections()
    self.make_preview_connections()

    # mark the preview is made, show the delete button
    bpy.context.scene.ui_property.preview_is_shown = True
    bpy.context.scene.ui_property.assembly_is_made = False

    return {'FINISHED'}


  def collect_port_info(self):
    """
    Collect all the gate port info and put into gate_port_dict
    """
    have_valid_gate = False
    for obj in bpy.context.scene.objects:
      stl_path = obj.gate_property.stl_file_path
      # is valid gate object
      if stl_path and stl_path != FREE_END_STL:
        have_valid_gate = True

        json_path = obj.gate_property.json_file_path
        # print(obj, "\n\n", stl_path,"\n", json_path,"\n", FREE_END_STL)
        with open(json_path, 'r') as f:
          json_data = json.load(f)
          port_list = list(json_data["Port Info"].items())
          # print(port_list)
          self.gate_port_dict[obj.name] = port_list
      elif stl_path and stl_path == FREE_END_STL:
        have_valid_gate = True
    # print("Gate Port Dict:")
    # print(self.gate_port_dict)
    if not have_valid_gate:
      self.report(
        {'ERROR'},
        "No Valid Gate Object"
      )
      return False
    return True


  def update_port_pos(self):
    """
    Calculate all the absolute port position and store in gate_port_abs_dict
    """
    for key,value in self.gate_port_dict.items():
      gate_obj = bpy.context.scene.objects[key]
      gate_pos = list(gate_obj.location)
      gate_rot = list(gate_obj.rotation_euler)  # euler angles are already in radians
      # gate_rot_radians = list(map(radians, gate_rot))
      gate_scl = list(gate_obj.scale)
      calculate_abs_pos = Helper.calculate_abs_pos

      placement_data = (gate_pos, gate_rot, gate_scl)
      # print(f"{gate_obj.name} Placement data: {placement_data}")
      # print(f"Rot: {gate_rot}, Radians: {gate_rot_radians}")
      for port_unit in value:
        port_name = port_unit[0]
        port_pos = port_unit[1]
        abs_port_pos = calculate_abs_pos(placement_data, port_pos)

        self.gate_port_abs_dict[(key, port_name)] = abs_port_pos

    print("Port abs Dict:")
    print(self.gate_port_abs_dict)




  def update_free_end_pos(self):
    """
    Collect free_end port info and put into gate_port_dict
    """
    for obj in bpy.context.scene.objects:
      if obj.gate_property.is_free_end:
        obj_name = obj.name
        obj_pos = obj.location
        self.gate_port_abs_dict[("FREE_END", obj_name)] = obj_pos




  def get_all_connections(self):
    """
    Collect all the connection info and put into connection_list
    """
    connect_prop = bpy.context.scene.connection_property
    name_list = connect_prop.generic_gate_name_list
    connection_dict = connect_prop.connection_dict

    for n in range(MAX_NUM_OF_CONNECTIONS):
      connection_unit = []
      for i,gate_name in enumerate(name_list):
        gate_obj = getattr(connect_prop, f"{gate_name}{n}")
        if gate_obj:
          # gate
          if not gate_obj.gate_property.is_free_end:
            port_name = connection_dict[(n,i)]
            connection_unit.append((gate_obj.name, port_name))
          # free end
          else:
            connection_unit.append(("FREE_END", gate_obj.name))
      if connection_unit:
        print(f"Added connection unit {connection_unit}")
        self.connection_list.append(connection_unit)

    print(self.connection_list)


  def make_preview_connections(self):
    """
    Use info form connect_list and gate_port_abs_dict to make preview connections
    """
    for connection_unit in self.connection_list:
      start_port = connection_unit[0]
      end_port = connection_unit[1]

      start_pos = self.gate_port_abs_dict[start_port]
      end_pos = self.gate_port_abs_dict[end_port]

      preview_connection = [start_pos, end_pos]
      # print(start_port, end_port)
      # print(preview_connection)
      # for pos in preview_connection:
      #   bpy.ops.mesh.primitive_cube_add(size=1, location=pos)

      # make pipe
      curve_data = bpy.data.curves.new(PREVIEW_PIPE_NAME, type = "CURVE")
      curve_data.dimensions = "3D"

      polyline = curve_data.splines.new("POLY")
      polyline.points.add(len(preview_connection)-1)
      for i, coord in enumerate(preview_connection):
        x,y,z = coord
        polyline.points[i].co = (x,y,z,1)

      curve_object = bpy.data.objects.new(PREVIEW_PIPE_NAME, curve_data)
      bpy.context.collection.objects.link(curve_object)

      line_thickness = bpy.context.scene.ui_property.preview_pipe_thickness * bpy.context.scene.pipe_property.unit_dimention
      curve_object.data.bevel_depth = line_thickness
      curve_object.data.bevel_resolution = 2

      bpy.context.scene.ui_property.preview_obj_list.append(curve_object)

      Helper.remove_current_selection_sphere()




class MESH_OT_delete_preview_connection(bpy.types.Operator):
  """
  Delete the preview connections
  The button only shows when the preview_connections are made
  """
  bl_idname = "mesh.delete_preview_connection"
  bl_label = "Delete Preview Connection"

  def execute(self, context):
    # for obj in bpy.context.scene.objects:
    #   obj_name = obj.name
    #   if PREVIEW_PIPE_NAME in obj_name:
    #     bpy.data.objects.remove(obj)

    for obj in bpy.context.scene.ui_property.preview_obj_list:
      try:
        bpy.data.objects.remove(obj)
      except ReferenceError:
        self.report(
          {"WARNING"},
          f"Preview Object: {obj} Already Deleted"
        )
    bpy.context.scene.ui_property.preview_obj_list.clear()
    bpy.context.scene.ui_property.preview_is_shown = False
    return {'FINISHED'}





class MESH_OT_choose_propergation_port(bpy.types.Operator):
  """
  Generic button to choose a port for calculate propegation delay
  Pass in different arguments for different ports
  """
  bl_idname = "mesh.choose_propergation_port"
  bl_label = "Choose Propergation Port"

  is_start: bpy.props.BoolProperty(default=False)
  port_name: bpy.props.StringProperty(default="")

  def execute(self, context):
    if self.is_start:
      start_end_text = "Start"
    else:
      start_end_text = "End"
    print(f"Choose {start_end_text} Port {self.port_name}")

    ui_prop = bpy.context.scene.ui_property
    if self.is_start:
      ui_prop.start_port = self.port_name
    else:
      ui_prop.end_port = self.port_name

    return {'FINISHED'}


class MESH_OT_cancel_propergation_port(bpy.types.Operator):
  """
  Cancel choice of port
  """
  bl_idname = "mesh.cancel_propergation_port"
  bl_label = "Cancel Propergation Port"

  is_start: bpy.props.BoolProperty(default=False)

  def execute(self, context):
    if self.is_start:
      start_end_text = "Start"
    else:
      start_end_text = "End"
    print(f"Cancel {start_end_text} Port")

    ui_prop = bpy.context.scene.ui_property
    if self.is_start:
      ui_prop.property_unset("start_port")
    else:
      ui_prop.property_unset("end_port")

    return {'FINISHED'}




class MESH_OT_calculate_propegation_delay(bpy.types.Operator):
  """
  Calculate propegation delay between two given ports
  This method also calls the assembly class
  """
  bl_idname = "mesh.calculate_propegation_delay"
  bl_label = "Calculate Propegation Delay"

  # propegation_delay: bpy.props.FloatProperty(default=0)
  propegation_delay = 0

  def execute(self, context):
    ui_prop = bpy.context.scene.ui_property
    start_is_free_end = ui_prop.start_gate.gate_property.is_free_end
    end_is_free_end = ui_prop.end_gate.gate_property.is_free_end

    if start_is_free_end:
      start_gate_name = "FREE_END"
      start_port_name = ui_prop.start_gate.name
    else:
      start_gate_name = ui_prop.start_gate.name
      start_port_name = ui_prop.start_port
    if end_is_free_end:
      end_gate_name = "FREE_END"
      end_port_name = ui_prop.end_gate.name
    else:
      end_gate_name = ui_prop.end_gate.name
      end_port_name = ui_prop.end_port

    assembly = bpy.types.MESH_OT_make_assembly.assembly
    delay = assembly.get_propagation_delay((start_gate_name, start_port_name), (end_gate_name, end_port_name))
    if delay == float('inf'):
      self.report({'WARNING'}, "Ports not connected, unable to calculate propagation delay")
      bpy.context.scene.ui_property.propegation_delay = 0
    elif delay == float('-inf'):
      self.report({'ERROR'}, "Problem occured calculating propagation delay")
      bpy.context.scene.ui_property.propegation_delay = 0
    elif delay == 0:
      self.report({'WARNING'}, "Two Port are the same.")
      bpy.context.scene.ui_property.propegation_delay = 0
    else:
      bpy.context.scene.ui_property.propegation_delay = delay
    return {'FINISHED'}




class MESH_OT_change_group_visibility(bpy.types.Operator):
  """
  Change the visibility of a given group name
  """
  bl_idname = "mesh.change_group_visibility"
  bl_label = "Change Group Visibility"

  group_name: bpy.props.StringProperty(default="")
  # ui_prop.show_...
  # if true -> is shown -> click button to hide
  # visibility_status: bpy.props.BoolProperty(default=True)

  def execute(self, context):
    connect_prop = bpy.context.scene.connection_property
    ui_prop = bpy.context.scene.ui_property
    visibility_status = getattr(ui_prop, f"show_{self.group_name}")
    group_obj_list = getattr(connect_prop, f"{self.group_name}_obj_list")
    for obj in group_obj_list:
      obj.hide_set(visibility_status)

    setattr(ui_prop, f"show_{self.group_name}", not visibility_status)
    print(f"Button {self.group_name.capitalize()} Pressed, visibility_status: {visibility_status}->{not visibility_status}")

    return {'FINISHED'}




class MESH_OT_save_current_progress(bpy.types.Operator):
  """
  Save current progress to json file in current working folder
  Will save gate / free_end objects, connections, pipe settings
  Won't save stuff only for UI like preview pipes
  """
  bl_idname = "mesh.save_current_progress"
  bl_label = "Save Current Progress"

  def execute(self, context):

    progress_data = {}
    # {obj_name : [[pos], [rot], [scl], [is_free_end, stl_path, json_path]]}
    progress_data["Objects"] = {}
    # {"Name List" : generic_gate_name_list, index : [gate_name, port_name]}
    progress_data["Connection"] = {}
    #
    progress_data["Pipe"] = {}

    # save only gate / free_end objects in scene
    for obj in bpy.context.scene.objects:
      if obj.gate_property.stl_file_path:
        pos = list(obj.location)
        rot = list(obj.rotation_euler)
        scl = list(obj.scale)
        gate_prop = obj.gate_property
        gate_prop_list = [gate_prop.is_free_end, gate_prop.stl_file_path, gate_prop.json_file_path]

        progress_data["Objects"][obj.name] = [pos, rot, scl, gate_prop_list]

    # save all connections
    connect_prop = bpy.context.scene.connection_property
    name_list = connect_prop.generic_gate_name_list
    connect_dict = connect_prop.connection_dict

    progress_data["Connection"]["Name List"] = name_list
    # loop through connection_dict, will save all connection with selected ports
    for key,value in connect_dict.items():
      n,i = key
      current_port_name = value
      current_gate_var_name = f"{name_list[i]}{n}"
      current_gate_obj = getattr(connect_prop, current_gate_var_name)
      # key for json can't be tuple
      # convert (n,i) to index
      # parse by i = index % len, n = index // len
      index = n * len(name_list) + i
      # Filter ghost ports (gate deleted, post still there)
      if current_gate_obj is not None:
        progress_data["Connection"][index] = (current_gate_obj.name, current_port_name)

    # loop again to get free_ends
    # do this because when you choose port, then change object to free_end
    # the port info is still there
    # by getting the gate first, then free_end will avoid this problem
    # I know this is not good practice, but it's 2am and i'm really tired right now
    for n in range(MAX_NUM_OF_CONNECTIONS):
      for i,gate_name in enumerate(name_list):
        # not gate port
        if not (n,i) in connect_dict:
          current_gate_var_name = f"{name_list[i]}{n}"
          current_gate_obj = getattr(connect_prop, current_gate_var_name)
          # not empty, is free_end
          if current_gate_obj is not None:
            print(current_gate_obj)
            index = n * len(name_list) + i
            progress_data["Connection"][index] = (current_gate_obj.name, "null")


    # save all pipe settings
    pipe_prop = bpy.context.scene.pipe_property
    progress_data["Pipe"]["pipe_inner_radius"] = pipe_prop.pipe_inner_radius
    progress_data["Pipe"]["pipe_thickness"] = pipe_prop.pipe_thickness
    progress_data["Pipe"]["tip_length"] = pipe_prop.tip_length
    progress_data["Pipe"]["unit_dimention"] = pipe_prop.unit_dimention
    progress_data["Pipe"]["add_stage"] = pipe_prop.add_stage
    progress_data["Pipe"]["stage_height"] = pipe_prop.stage_height
    progress_data["Pipe"]["stage_rim_size"] = pipe_prop.stage_rim_size
    progress_data["Pipe"]["add_custom_tip"] = pipe_prop.add_custom_tip
    progress_data["Pipe"]["tip_offset"] = pipe_prop.tip_offset
    progress_data["Pipe"]["tip_stl_path"] = pipe_prop.tip_stl_path


    # print(json.dumps(progress_data, indent=2))

    with open(PROGRESS_FILE, 'w') as f:
      json.dump(progress_data, f, indent=2)

    self.report(
      {"INFO"},
      f"Saved progress to {PROGRESS_FILE}"
      )
    return {'FINISHED'}



class MESH_OT_load_saved_progress(bpy.types.Operator):
  """
  Load progress file into work space
  """
  bl_idname = "mesh.load_saved_progress"
  bl_label = "Load Saved Progress"

  def execute(self, context):
    ui_prop = bpy.context.scene.ui_property
    connect_prop = bpy.context.scene.connection_property
    progress_file_path = ui_prop.progress_file_path

    root,ext = os.path.splitext(progress_file_path)
    if ext != ".json":
      self.report(
        {"ERROR"},
        f"File is Not an JSON file, file: {progress_file_path}"
      )
      return {"CANCELLED"}

    # # reset addon, erase everything
    # bpy.ops.mesh.reset_my_addon()

    try:
      with open(progress_file_path, 'r') as f:
        progress_data = json.load(f)
        # print(progress_data)
    except FileNotFoundError:
      self.report(
        {"ERROR"},
        f"File Not Exist at path: {progress_file_path}"
      )
      return {"CANCELLED"}

    # get existing name
    existing_obj_name = []
    for obj in bpy.data.objects:
      existing_obj_name.append(obj.name)

    # get existing number of connections
    n_lines = 0
    # check if a line of connection selection is empty
    def connect_line_is_empty(n_lines):
      connect_var_name = []
      for var in connect_prop.generic_gate_name_list:
        connect_var_name.append(f"{var}{n_lines}")
      is_empty = True
      # print("Var_names:", connect_var_name)
      for var in connect_var_name:
        if connect_prop.get(var).__class__ is bpy.types.Object:
          is_empty = False
      return is_empty

    while not connect_line_is_empty(n_lines) and n_lines < MAX_NUM_OF_CONNECTIONS:
      n_lines += 1
    print("Num of existing connections:\n", n_lines)

    # load objects
    # none gate / free_end objects are ignored
    loaded_obj_dict = progress_data["Objects"]
    change_name_dict = {}
    for key,value in loaded_obj_dict.items():
      obj_name = key
      obj_pos = value[0]
      obj_rot = value[1]
      obj_scl = value[2]
      obj_is_free_end = value[3][0]
      obj_stl_file_path = value[3][1]
      obj_json_file_path = value[3][2]

      # is gate / free_end object
      if obj_stl_file_path:
        try:
          bpy.ops.import_mesh.stl(filepath = obj_stl_file_path)
        except FileNotFoundError:
          self.report(
            {"ERROR"},
            f"File Not Exist at {obj_stl_file_path}"
            )
          return {"CANCELLED"}
        # load object properties
        imported_object = bpy.context.active_object
        # imported_object.name = obj_name
        imported_object.location = obj_pos
        imported_object.rotation_euler = obj_rot
        imported_object.scale = obj_scl
        imported_object.gate_property.is_free_end = obj_is_free_end
        imported_object.gate_property.stl_file_path = obj_stl_file_path
        imported_object.gate_property.json_file_path = obj_json_file_path

        # avoid name collision
        ii = 0
        changed_obj_name = obj_name
        while changed_obj_name in existing_obj_name:
          changed_obj_name = f"{obj_name}_{ii}"
          ii += 1
        if ii > 0:
          change_name_dict[obj_name] = changed_obj_name

        imported_object.name = changed_obj_name



    # load connections
    loaded_connect_dict = progress_data["Connection"]
    # get generic_gate_name_list
    connect_prop.generic_gate_name_list = loaded_connect_dict["Name List"]
    name_list = connect_prop.generic_gate_name_list
    del loaded_connect_dict["Name List"]

    for key,value in loaded_connect_dict.items():
      index = int(key)
      n = index // len(name_list) + n_lines   # append to existing connections
      i = index % len(name_list)

      connection_gate_name, connection_port_name = value
      if connection_gate_name in change_name_dict:
        connection_gate_name = change_name_dict[connection_gate_name]

      gate_name = connection_gate_name
      port_name = connection_port_name

      try:
        gate_obj = bpy.data.objects[gate_name]
      except KeyError:
        self.report(
          {"ERROR"},
          f"Object with name {gate_name} not found in bpy.data.objects"
          )
        return {"CANCELLED"}

      gate_var_name = f"{name_list[i]}{n}"
      setattr(connect_prop, gate_var_name, gate_obj)
      # not free_end, add port selection
      if port_name != "null":
        connect_prop.connection_dict[(n,i)] = port_name


    # load pipe settings
    pipe_prop = bpy.context.scene.pipe_property

    pipe_prop.pipe_inner_radius = progress_data["Pipe"]["pipe_inner_radius"]
    pipe_prop.pipe_thickness = progress_data["Pipe"]["pipe_thickness"]
    pipe_prop.tip_length = progress_data["Pipe"]["tip_length"]
    pipe_prop.unit_dimention = progress_data["Pipe"]["unit_dimention"]
    pipe_prop.add_stage = progress_data["Pipe"]["add_stage"]
    pipe_prop.stage_height = progress_data["Pipe"]["stage_height"]
    pipe_prop.stage_rim_size = progress_data["Pipe"]["stage_rim_size"]
    pipe_prop.add_custom_tip = progress_data["Pipe"]["add_custom_tip"]
    pipe_prop.tip_offset = progress_data["Pipe"]["tip_offset"]
    pipe_prop.tip_stl_path = progress_data["Pipe"]["tip_stl_path"]


    self.report(
      {"INFO"},
      "Successfully loaded from progress file."
      )
    return {'FINISHED'}





############################################################################
################################  Properties ###############################
############################################################################



def get_addon_dir():
  """Helper Function"""
  script_file = os.path.realpath(__file__)
  directory = os.path.dirname(script_file)
  print(directory)
  return str(directory)

ADDON_DIR = get_addon_dir() + "/"
GATE_LIBRARY_PATH = ADDON_DIR + "Val_Library/"
FREE_END_STL = GATE_LIBRARY_PATH + "free_end_pointer.stl"
DEFAULT_TIP_STL = GATE_LIBRARY_PATH + "press_fit_tip.stl"
PROGRESS_FILE = ADDON_DIR + "saved_progress.json"

class GatePropertyGroup(bpy.types.PropertyGroup):
  """
  Gate Property Group
  Avaliable in each obejct
  Stores property related to logic gates
  """
  is_free_end: bpy.props.BoolProperty(default=False)
  stl_file_path: bpy.props.StringProperty(subtype='FILE_PATH', default="")
  json_file_path: bpy.props.StringProperty(subtype='FILE_PATH', default="")



class ConnectionPropertyGroup(bpy.types.PropertyGroup):
  """
  Connection Property Group
  Avaliable in bpy.context.scene
  Stores property related to pipe connections
  """
  generic_gate_name_list = [
    "start_gate_",
    "end_gate_",
  ]
  # stores connection info for making final circuit
  connection_dict = {}
  # pre-create all the virables used to store conneciton choices
  for n in range(MAX_NUM_OF_CONNECTIONS):
    for prop_name in generic_gate_name_list:
      exec(f"{prop_name}{n} : bpy.props.PointerProperty(type=bpy.types.Object)")

  gate_obj_list = []
  pipe_obj_list = []
  free_end_obj_list = []
  stage_obj_list = []
  tip_obj_list = []
  # a sphere object that marks the currently selected port pos
  select_sphere_obj: bpy.props.PointerProperty(type=bpy.types.Object)
  # select_gate_obj: bpy.props.PointerProperty(type=bpy.types.Object)


def flip_is_free_end(self, context):
  """Helper Function"""
  print("my test function flip_is_free_end", self)
  ui_prop = bpy.context.scene.ui_property
  # if is_logic_gate is True, free_end is False
  if ui_prop.fake_is_logic_gate:
    ui_prop.fake_is_free_end = False
  # if both False, the other is True
  if not ui_prop.fake_is_logic_gate and not ui_prop.fake_is_free_end:
    ui_prop.fake_is_free_end = True

def flip_is_logic_gate(self, context):
  """Helper Function"""
  print("my test function flip_is_logic_gate", self)
  ui_prop = bpy.context.scene.ui_property
  if ui_prop.fake_is_free_end:
    ui_prop.fake_is_logic_gate = False
  if not ui_prop.fake_is_logic_gate and not ui_prop.fake_is_free_end:
    ui_prop.fake_is_logic_gate = True

class UIPropertyGroup(bpy.types.PropertyGroup):
  """
  UI Property Group
  Avaliable in bpy.context.scene
  Stores property related to UI components
  """
  # main pannel
  confirm_reset_addon: bpy.props.BoolProperty(default=False)
  progress_file_path: bpy.props.StringProperty(subtype='FILE_PATH', default=PROGRESS_FILE)
  # import gate
  fake_is_free_end: bpy.props.BoolProperty(default=False, update=flip_is_logic_gate)
  fake_is_logic_gate: bpy.props.BoolProperty(default=True, update=flip_is_free_end)
  fake_stl_file_path: bpy.props.StringProperty(subtype='FILE_PATH', default=GATE_LIBRARY_PATH)
  # make assembly and preview
  confirm_make_assembly: bpy.props.BoolProperty(default=False)
  preview_pipe_thickness: bpy.props.FloatProperty(default=.3, min=0, soft_max=1)
  preview_is_shown: bpy.props.BoolProperty(default=False)
  preview_obj_list = []
  # propegation delay
  assembly_is_made: bpy.props.BoolProperty(default=False)
  start_gate: bpy.props.PointerProperty(type=bpy.types.Object)
  end_gate: bpy.props.PointerProperty(type=bpy.types.Object)
  start_port: bpy.props.StringProperty(default="")
  end_port: bpy.props.StringProperty(default="")
  propegation_delay: bpy.props.FloatProperty(default=0)
  # visibility control
  show_gate: bpy.props.BoolProperty(default=True)
  show_pipe: bpy.props.BoolProperty(default=True)
  show_free_end: bpy.props.BoolProperty(default=True)
  show_stage: bpy.props.BoolProperty(default=True)
  show_tip: bpy.props.BoolProperty(default=True)
  # error message
  error_message_list = []


class PipePropertyGroup(bpy.types.PropertyGroup):
  """
  Pipe Property Group
  Avaliable in bpy.context.scene
  Stores property related to pipe settings
  """
  pipe_inner_radius: bpy.props.FloatProperty(
    default = 1.6,
    min = 0,
    soft_max = 3
  )
  pipe_thickness: bpy.props.FloatProperty(
    default = 1.4,
    min = 0.01,
    soft_max = 3
  )
  tip_length: bpy.props.FloatProperty(
    default = 1,
    min = 0,
    soft_max = 2
  )
  unit_dimention: bpy.props.IntProperty(
    default = 7,
    min = 1,
    soft_max = 10
  )

  preview_obj_list = []
  preview_is_shown: bpy.props.BoolProperty(default=False)

  add_stage: bpy.props.BoolProperty(default = True)

  stage_height: bpy.props.FloatProperty(
    default = .5,
    min = 0,
    soft_max = 5
  )
  stage_rim_size: bpy.props.FloatProperty(
    default = 5,
    min = 0,
    soft_max = 5
  )

  add_custom_tip: bpy.props.BoolProperty(default = True)

  tip_offset: bpy.props.FloatProperty(
    default = 3,
    min = 0,
    soft_max = 5
  )
  tip_stl_path: bpy.props.StringProperty(
    subtype = 'FILE_PATH',
    default = DEFAULT_TIP_STL
  )




############################################################################
#################################  Pannel  #################################
############################################################################




ADDON_PANNEL_LABEL = "Fluid Circuit Generator"




class VIEW3D_PT_addon_main_panel(bpy.types.Panel):
  """
  Main Panel
  Has Create Monkey and Reset Addon
  """
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'UI'
  bl_category = ADDON_PANNEL_LABEL
  bl_label = "Main Panel"
  # bl_options = {'DEFAULT_CLOSED'}

  def draw(self, context):
    layout = self.layout
    # Monkey !!!!!!
    layout.operator("mesh.primitive_monkey_add", text="", icon='MONKEY')
    # add confirm before reset addon
    if not bpy.context.scene.ui_property.confirm_reset_addon:
      layout.prop(bpy.context.scene.ui_property, "confirm_reset_addon", toggle=1, text="Reset Addon")
    else:
      reset_addon_row = layout.row()
      reset_addon_row.prop(bpy.context.scene.ui_property, "confirm_reset_addon", toggle=1, text="Cancel")
      reset_addon_row.operator("mesh.reset_my_addon", text="Reset")

    progress_row = layout.row()
    progress_row.operator("mesh.save_current_progress")
    progress_row.operator("mesh.load_saved_progress")
    progress_row.prop(bpy.context.scene.ui_property, "progress_file_path")




    # script_file = os.path.realpath(__file__)
    # directory = os.path.dirname(script_file)
    # print(directory)






class VIEW3D_PT_add_gate_panel(bpy.types.Panel):
  """
  Add Gate Panel
  Add Logic Gate or Free End
  Also shows transformation info
  """
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'UI'
  bl_category = ADDON_PANNEL_LABEL
  bl_label = "Add Components"
  # bl_options = {'DEFAULT_CLOSED'}

  def draw(self, context):
    layout = self.layout
    # is_free_end | path
    select_gate_row = layout.row()
    is_free_end_row = select_gate_row.row()
    select_path_row = layout.row()

    is_free_end_row.prop(bpy.context.scene.ui_property, "fake_is_free_end", toggle=1, text="Free End")
    is_free_end_row.prop(bpy.context.scene.ui_property, "fake_is_logic_gate", toggle=1, text="Logic Gate")
    select_path_row.prop(bpy.context.scene.ui_property, "fake_stl_file_path", text="Import Stl File")

    if bpy.context.scene.ui_property.fake_is_free_end:
      select_path_row.enabled = False

    layout.operator("mesh.add_gate_object", text="Add Object")

    transform_box = layout.box()

    obj = bpy.context.active_object
    if not obj:
      label_row = transform_box.row()
      label_row.alignment = 'CENTER'
      label_row.label(text="- no active object -")
    else:
      location_row = transform_box.row()
      location_row.prop(obj, "location")
      # normal gate have rotate and scale
      if not obj.gate_property.is_free_end:
        rotation_row = transform_box.row()
        rotation_row.prop(obj, "rotation_euler", text="Rotation:")
        scale_row = transform_box.row()
        scale_row.prop(obj, "scale")





class VIEW3D_PT_add_connection_panel(bpy.types.Panel):
  """
  Add Connection Panel
  A table of connection choices
  Add row by pressing Add button
  Remove a row by crossing out all the gate selections in a row
  """
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'UI'
  bl_category = ADDON_PANNEL_LABEL
  bl_label = "Add Connections"
  # bl_options = {'DEFAULT_CLOSED'}

  # connection_dict = {"hi":"hello"}

  def draw(self, context):
    layout = self.layout

    # draw title
    connection_box = layout.box()
    title_row = connection_box.row(align=True)
    start_row = title_row.row()
    start_row.alignment = 'CENTER'
    end_row = title_row.row()
    end_row.alignment = 'CENTER'
    start_row.label(text="Start")
    end_row.label(text="End")
    # table columns
    connection_inner_row = connection_box.row()
    start_col = connection_inner_row.column()
    start_col.ui_units_x = 4
    middle_col = connection_inner_row.column()
    middle_col.ui_units_x = .5
    end_col = connection_inner_row.column()
    end_col.ui_units_x = 4

    connection_col_list = [start_col, end_col]

    connect_prop = bpy.context.scene.connection_property
    name_list = connect_prop.generic_gate_name_list

    # if not all row None, draw a row for connection
    for n in range(MAX_NUM_OF_CONNECTIONS):
      gate_row_all_None = True
      for gate_name in name_list:
        gate_obj = getattr(connect_prop, f"{gate_name}{n}")
        if gate_obj is not None:
          gate_row_all_None = False

      if not gate_row_all_None:
        ui_height = self.draw_connection_selection(n, connection_col_list)

        middle_col.label(icon='FORWARD')
        for _ in range(ui_height-1):
          middle_col.label(text="")

    # add connection button at bottom
    layout.operator("mesh.add_gate_connection", text="Add Connections")



  def draw_connection_selection(self, n, connection_col_list):
    """
    Draw a selection row
    Also handles uneven height between left, middle, right column
    """
    connect_prop = bpy.context.scene.connection_property
    name_list = connect_prop.generic_gate_name_list
    # return the height of this UI part
    ui_height = [0,0]
    # loop over gate list in each row
    for i,gate_name in enumerate(name_list):
      current_ui_height = 0

      connection_row = connection_col_list[i].row()

      connection_row.prop(connect_prop, f"{gate_name}{n}", text="")

      gate_obj = getattr(connect_prop, f"{gate_name}{n}")

      # not gate/port object added by pannel
      if gate_obj and gate_obj.gate_property.stl_file_path == "":
        connection_row.label(text="- not a valid gate/end object -")
        current_ui_height = 1

      # gate selected and not free end
      elif gate_obj and not gate_obj.gate_property.is_free_end:

        connection_dict = connect_prop.connection_dict
        # not selected
        if not (n,i) in connection_dict:
          # get port name
          gate_json = gate_obj.gate_property.json_file_path
          with open(gate_json, 'r') as f:
            json_data = json.load(f)
            port_list = list(json_data["Port Info"].keys())
          # print(port_list)
          if not port_list:
            connection_row.label(text="- no port found -")
            return
          port_col = connection_row.column()
          # port_col.ui_units_x = 1
          for port_name in port_list:
            port_button = port_col.operator("mesh.choose_connection_port", text=port_name)
            port_button.row_index = n
            port_button.gate_index = i
            port_button.port_name = port_name
            port_button.selected_gate_name = gate_obj.name
            # connect_prop.select_gate_obj = gate_obj
            # print(f"connect_prop.select_gate_obj: {connect_prop.select_gate_obj}")
            current_ui_height += 1

        else:
          selected_port = connection_dict[(n,i)]
          # port_col = connection_row.column()
          # port_col.ui_units_x = 1
          reselect_button = connection_row.operator("mesh.cancel_connection_port", text=selected_port)
          reselect_button.row_index = n
          reselect_button.gate_index = i
          current_ui_height = 1


      else:
        current_ui_height = 1

      ui_height[i] = current_ui_height

    if ui_height[0] < ui_height[1]:
      diff = ui_height[1] - ui_height[0]
      for _ in range(diff):
        connection_col_list[0].label(text="")

    if ui_height[0] > ui_height[1]:
      diff = ui_height[0] - ui_height[1]
      for _ in range(diff):
        connection_col_list[1].label(text="")

    return max(ui_height)




class VIEW3D_PT_pipe_property_pannel(bpy.types.Panel):
  """
  Pipe Property Panel
  A table of pipe properties
  Can create a preview pipe to visualize your choices
  """
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'UI'
  bl_category = ADDON_PANNEL_LABEL
  bl_label = "Tubing Properties"
  # bl_options = {'DEFAULT_CLOSED'}

  def draw(self, context):
    layout = self.layout
    layout_row = layout.row()
    pipe_dimention_col = layout_row.column()
    pipe_dimention_col.ui_units_x = 1
    stage_col = layout_row.column()
    stage_col.ui_units_x = 1
    tip_col = layout_row.column()
    tip_col.ui_units_x = 1

    pipe_prop = bpy.context.scene.pipe_property
    pipe_dimention_col.prop(pipe_prop, "pipe_inner_radius", text="inner radius (mm)")
    pipe_dimention_col.prop(pipe_prop, "pipe_thickness", text="thickness (mm)")
    pipe_dimention_col.prop(pipe_prop, "unit_dimention", text="unit length (mm)")

    stage_col.prop(pipe_prop, "add_stage", text="add stage block")
    add_stage = getattr(pipe_prop, "add_stage")
    if add_stage:
      stage_col.prop(pipe_prop, "stage_height", text="height (mm)")
      stage_col.prop(pipe_prop, "stage_rim_size", text="rim size (mm)")

    # tip_col.prop(pipe_prop, "tip_length")
    tip_col.prop(pipe_prop, "add_custom_tip", text="add custom tip")
    add_custom_tip = getattr(pipe_prop, "add_custom_tip")
    if add_custom_tip:
      tip_col.prop(pipe_prop, "tip_offset", text="offset (mm)")
      tip_col.prop(pipe_prop, "tip_stl_path", text="stl file")

    if pipe_prop.preview_is_shown:
      layout.operator("mesh.delete_preview_pipe", text="Hide Preview Tubing")
    else:
      layout.operator("mesh.make_preview_pipe", text="Make Preview Tubing")







class VIEW3D_PT_make_assembly_panel(bpy.types.Panel):
  """
  Make Assembly Pannel
  Where you make your final circuit
  First press the Make Preview Connection button to check if the connections are right
    preview can be generated without affecting your choices
  When everything look right, check the confirm box to display the Make Assembly button
  WARNING: Pressing the Make Assembly button is irreversiable
    only do so when everything looks right
    it will delete all objects and your choices
    you will need to restart again if something is wrong
  """
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'UI'
  bl_category = ADDON_PANNEL_LABEL
  bl_label = "Generate Assembly"
  # bl_options = {'DEFAULT_CLOSED'}


  def draw(self, context):
    ui_prop = bpy.context.scene.ui_property
    layout = self.layout
    row = layout.row()
    row.prop(ui_prop, "confirm_make_assembly", text="Confirm Changes")
    confirm = getattr(ui_prop, 'confirm_make_assembly')
    if confirm:
      row.operator("mesh.make_assembly", text="Generate Assembly")
    else:
      preview_shown = ui_prop.preview_is_shown
      if not preview_shown:
        col = row.column()
        col.operator("mesh.make_preview_connection", text="Preview Connecitons")
        # col.prop(ui_prop, "preview_pipe_thickness", text="line thickness (mm)")
      else:
        row.operator("mesh.delete_preview_connection", text="Hide Preview")





class VIEW3D_PT_calculate_propergation_delay_panel(bpy.types.Panel):
  """
  Calculate Propergation Delay Panel
  Choose ports and calculate the propergation delay between them
  """
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'UI'
  bl_category = ADDON_PANNEL_LABEL
  bl_label = "Calculate Propergation Delay"
  # bl_options = {'DEFAULT_CLOSED'}

  def draw(self, context):
    ui_prop = bpy.context.scene.ui_property
    layout = self.layout

    if not ui_prop.assembly_is_made:
      row = layout.row()
      row.alignment = 'CENTER'
      row.label(text="- no Gate Assembly made -")
      return

    box = layout.box()
    path_select_row = box.row()
    start_row = path_select_row.row()
    start_row.ui_units_x = 4
    mid_col = path_select_row.column()
    mid_col.ui_units_x = 0.5
    mid_col.label(icon='FORWARD')
    end_row = path_select_row.row()
    end_row.ui_units_x = 4

    start_row.prop(ui_prop, "start_gate", text="")
    end_row.prop(ui_prop, "end_gate", text="")

    start_gate = getattr(ui_prop, "start_gate")
    end_gate = getattr(ui_prop, "end_gate")

    self.add_port_choices(is_start=True, gate_obj=start_gate, row=start_row)
    self.add_port_choices(is_start=False, gate_obj=end_gate, row=end_row)

    button_row = layout.row()
    button_row.operator("mesh.calculate_propegation_delay")
    delay = getattr(ui_prop, "propegation_delay")
    button_row.label(text=f"Propegation Delay:      {round(delay,4)} s")




  def add_port_choices(self, is_start, gate_obj, row):
    """Helper Function"""
    ui_prop = bpy.context.scene.ui_property

    if gate_obj:
      # if free end, don't show port choices
      if gate_obj.gate_property.is_free_end:
        return
      # if port is not selected, show choices, else show cancel
      is_selected = False
      if is_start:
        is_selected = bool(ui_prop.start_port)
      else:
        is_selected = bool(ui_prop.end_port)
      # not selected
      if not is_selected:
        is_valid_gate = bool(gate_obj.gate_property.stl_file_path)
        if not is_valid_gate:
          row.label(text="- not valid gate -")
        else:
          is_free_end = gate_obj.gate_property.is_free_end
          # free end
          if is_free_end:
            # print(f"{gate_obj}is free end")
            # ui_prop.start_port = gate_obj.name
            pass
          # logic gate
          else:
            start_port_list = self.get_port_list(gate_obj)
            choose_port_col = row.column()
            for port_name in start_port_list:
              choose_button = choose_port_col.operator("mesh.choose_propergation_port", text=port_name)
              choose_button.port_name = port_name
              choose_button.is_start = is_start
      # selected
      else:
        if is_start:
          cancel_text = ui_prop.start_port
        else:
          cancel_text = ui_prop.end_port
        cancel_button = row.operator("mesh.cancel_propergation_port", text=cancel_text)
        cancel_button.is_start = is_start



  def get_port_list(self, gate_obj):
    """Helper Function"""
    json_path = gate_obj.gate_property.json_file_path
    with open(json_path, 'r') as f:
      json_data = json.load(f)
      port_list = list(json_data["Port Info"].keys())
    return port_list





class VIEW3D_PT_set_group_visibility_panel(bpy.types.Panel):
  """
  Set Group Visibility Panel
  Choose which group of object you want to turn invisible
  Useful when exporting stl files
  """
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'UI'
  bl_category = ADDON_PANNEL_LABEL
  bl_label = "Set Group Visibility"
  # bl_options = {'DEFAULT_CLOSED'}

  def draw(self, context):
    layout = self.layout
    row = layout.row()

    self.add_show_hide_button("gate", row)
    self.add_show_hide_button("pipe", row)
    self.add_show_hide_button("free_end", row)
    self.add_show_hide_button("stage", row)
    self.add_show_hide_button("tip", row)

  def add_show_hide_button(self, group_name, row):
    """Helper Function"""
    connect_prop = bpy.context.scene.connection_property
    ui_prop = bpy.context.scene.ui_property

    visibility_status = getattr(ui_prop, f"show_{group_name}")
    button_text = f"{self.get_show_hide_text(visibility_status)} {group_name.capitalize()}"
    button = row.operator("mesh.change_group_visibility", text=button_text)

    button.group_name = group_name
    # button.visibility_status = getattr(ui_prop, f"show_{group_name}")

    # print(f"Button {group_name.capitalize()} {self.get_show_hide_text(visibility_status)} Drawn")

  def get_show_hide_text(self, visibility_status):
    """Helper Function"""
    if visibility_status:
      return "Hide"
    return "Show"




############################################################################
###############################  Regester  #################################
############################################################################



class_to_register = [

  MESH_OT_reset_my_addon,
  MESH_OT_add_gate_object,
  MESH_OT_add_gate_connection,
  MESH_OT_choose_connection_port,
  MESH_OT_cancel_connection_port,
  MESH_OT_check_connection_selection,
  MESH_OT_make_assembly,
  MESH_OT_make_preview_pipe,
  MESH_OT_delete_preview_pipe,
  MESH_OT_make_preview_connection,
  MESH_OT_delete_preview_connection,
  MESH_OT_choose_propergation_port,
  MESH_OT_cancel_propergation_port,
  MESH_OT_calculate_propegation_delay,
  MESH_OT_change_group_visibility,
  MESH_OT_save_current_progress,
  MESH_OT_load_saved_progress,

  GatePropertyGroup,
  ConnectionPropertyGroup,
  UIPropertyGroup,
  PipePropertyGroup,

  VIEW3D_PT_addon_main_panel,
  VIEW3D_PT_add_gate_panel,
  VIEW3D_PT_add_connection_panel,
  VIEW3D_PT_pipe_property_pannel,
  VIEW3D_PT_make_assembly_panel,
  VIEW3D_PT_calculate_propergation_delay_panel,
  VIEW3D_PT_set_group_visibility_panel,

]



def register_properties():
  """Register Properties"""
  bpy.types.Object.gate_property = bpy.props.PointerProperty(type=GatePropertyGroup)
  bpy.types.Scene.connection_property = bpy.props.PointerProperty(type=ConnectionPropertyGroup)
  bpy.types.Scene.ui_property = bpy.props.PointerProperty(type=UIPropertyGroup)
  bpy.types.Scene.pipe_property = bpy.props.PointerProperty(type=PipePropertyGroup)
  print("Properties Registered")



def unregister_properties():
  """unregister Properties"""
  del bpy.types.Object.gate_property
  del bpy.types.Scene.connection_property
  del bpy.types.Scene.ui_property
  del bpy.types.Scene.pipe_property
  print("Properties UnRegistered")




def register():
  """Register"""
  for cls in class_to_register:
    bpy.utils.register_class(cls)
  register_properties()
  print("All Class Registered")




def unregister():
  """UnRegister"""
  for cls in class_to_register:
    bpy.utils.unregister_class(cls)
  unregister_properties()
  print("All Class UnRegistered")



