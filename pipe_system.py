import bpy

import importlib.util
import sys
spec = importlib.util.spec_from_file_location("path_finding.py", "/Users/lhwang/Documents/Blender Python Projects/Git Project Space/Fluid-Circuit-Generator/path_finding.py")
p = importlib.util.module_from_spec(spec)
sys.modules["path_finding.py"] = p
spec.loader.exec_module(p)

from math import sqrt




class PipeSystem:

  _instance = None

  def __new__(self):

    if not self._instance:
      self._instance = super(PipeSystem, self).__new__(self)

      self.grid_dimention = (20,20,5)
      # ()
      self.pipe_dimention = (.2, .15)
      # self.junction_dimention = (.4, .2)
      self.unit_dimention = 1

      self.tip_length = 1

      self.grid = p.Grid(self.grid_dimention)

      self.connection_dict = {}
      self.junction_dict = {}

      # {(tip_coord, tip_coord) : [(tip_connection_coord, tip_connection_coord), pipe_object]}
      self.pipe_object_dict = {}

      
    return self._instance


  def connect_two_port(self, start_port_coord, end_port_coord):
    print("\n")
    print(f"Connecting Ports {start_port_coord} - {end_port_coord}")
    start_tip_coord = (start_port_coord[0], start_port_coord[1], start_port_coord[2]-self.tip_length)
    end_tip_coord = (end_port_coord[0], end_port_coord[1], end_port_coord[2]-self.tip_length)
    
    start_grid_coord, end_grid_coord = self.snap_to_grid(start_tip_coord, end_tip_coord)
    print(f"Corrisponding Grid coord: {start_grid_coord} - {end_grid_coord}")
    self.grid.connect_two_node(start_grid_coord, end_grid_coord)



  def snap_to_grid(self, start_port_coord, end_port_coord):
    dim = self.unit_dimention
    dir_x = (end_port_coord[0] - start_port_coord[0]) > 0
    dir_y = (end_port_coord[1] - start_port_coord[1]) > 0


    # if exact on grid, don't modify
    start_grid_coord = (start_port_coord[0]//dim + bool(start_port_coord[0]%dim)*dir_x, start_port_coord[1]//dim + bool(start_port_coord[1]%dim)*dir_y, start_port_coord[2]//dim)
    end_grid_coord = (end_port_coord[0]//dim + bool(end_port_coord[0]%dim)*(not dir_x), end_port_coord[1]//dim + bool(end_port_coord[1]%dim)*(not dir_y), end_port_coord[2]//dim)
    return (start_grid_coord, end_grid_coord)


  def fetch_grid_data(self):
    for key,value in self.grid.connection_dict.items():
      grid_tip_coord = tuple(map(lambda a: a.coord, key))
      real_coord = []
      for coord in grid_tip_coord:
        real_coord.append(tuple(map(lambda a: a*self.unit_dimention, coord)))
      real_coord = tuple(real_coord)

      grid_path_coord = list(map(lambda a: a.coord, value))
      real_path = []
      for coord in grid_path_coord:
        real_path.append(list(map(lambda a: a*self.unit_dimention, coord)))

      self.connection_dict[real_coord] = real_path

    for key,value in self.grid.saved_junction.items():
      real_junction_coord = tuple(map(lambda a: a*self.unit_dimention, key.coord))
      real_connection_coord_list = []
      connection_coord = list(map(lambda a: a.coord, value))
      for coord in connection_coord:
        real_connection_coord_list.append(list(map(lambda a: a*self.unit_dimention, coord)))
      
      self.junction_dict[real_junction_coord] = real_connection_coord_list









  
  def make_pipe(self, name, coord_list):
    if (len(coord_list) < 2):
      print(f"Error: Dot list {coord_list} too short")
      return
    coord_list = self.make_fillet(coord_list)

    curve_data = bpy.data.curves.new(name, type = "CURVE")
    curve_data.dimensions = "3D"

    polyline = curve_data.splines.new("POLY")
    polyline.points.add(len(coord_list)-1)
    for i, coord in enumerate(coord_list):
      x,y,z = coord
      polyline.points[i].co = (x,y,z,1)
    
    curve_object = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(curve_object)

    curve_object.data.bevel_depth = self.pipe_dimention[0] + self.pipe_dimention[1]
    curve_object.data.bevel_resolution = 2
    curve_object.modifiers.new("Solidify", "SOLIDIFY").thickness = self.pipe_dimention[1]
    curve_object.select_set(True)
    bpy.context.view_layer.objects.active = curve_object
    bpy.ops.object.convert(target = "MESH")
    return curve_object


  def make_junction(self, name, junction_coord, connection_list):

    bpy.ops.mesh.primitive_uv_sphere_add(radius = 1*(self.pipe_dimention[0] + self.pipe_dimention[1]), segments=16, ring_count=8)
    junction_sphere = bpy.context.active_object
    junction_sphere.name = name
    junction_sphere.location = junction_coord
    junction_sphere.modifiers.new("Solidify", "SOLIDIFY").thickness = self.pipe_dimention[1]

    connection_object_dict = {}
    for key,value in self.pipe_object_dict.items():
      if junction_coord in key:
        connection_object_dict[key] = value


    for connection_coord in connection_list:
      curve_data = bpy.data.curves.new(name, type = "CURVE")
      curve_data.dimensions = "3D"

      polyline = curve_data.splines.new("POLY")
      polyline.points.add(1)
      end_coord = tuple(map(lambda a,b: a + 0.01*(b-a), junction_coord, connection_coord))
      x,y,z = end_coord
      polyline.points[0].co = (x,y,z,1)
      x,y,z = connection_coord
      polyline.points[1].co = (x,y,z,1)
    
      curve_object = bpy.data.objects.new(name, curve_data)
      bpy.context.collection.objects.link(curve_object)

      curve_object.data.bevel_depth = self.pipe_dimention[0]
      curve_object.data.bevel_resolution = 1
      curve_object.data.use_fill_caps = True

      curve_object.select_set(True)
      bpy.context.view_layer.objects.active = curve_object
      bpy.ops.object.convert(target = "MESH")

      junction_modifier_name = "J_C"
      junction_sphere.modifiers.new(junction_modifier_name, "BOOLEAN").object = curve_object
      junction_sphere.modifiers[junction_modifier_name].operation = 'DIFFERENCE'
      junction_sphere.modifiers[junction_modifier_name].solver = "EXACT"
      # junction_sphere.modifiers[junction_modifier_name].use_self = True
      # junction_sphere.modifiers[junction_modifier_name].use_hole_tolerant = True
      junction_sphere.select_set(True)
      bpy.context.view_layer.objects.active = junction_sphere
      # bpy.ops.object.modifier_apply(modifier = "BOOLEAN")
      bpy.ops.object.modifier_apply(modifier = junction_modifier_name)

      for key,value in connection_object_dict.items():
        pipe = value[1]
        pipe_connections = value[0]
        if not connection_coord in pipe_connections:

          modifier_name = f"P_C{pipe.name}"
          pipe.modifiers.new(modifier_name, "BOOLEAN").object = curve_object
          pipe.modifiers[modifier_name].operation = 'DIFFERENCE'

        # pipe.modifiers[modifier_name].solver = "FAST"
          # pipe.select_set(True)
          # bpy.context.view_layer.objects.active = pipe
        # # bpy.ops.object.modifier_apply(modifier = "BOOLEAN")
          # bpy.ops.object.modifier_apply(modifier = modifier_name)

      # bpy.data.objects.remove(curve_object)
      curve_object.hide_set(True)

    for key,value in connection_object_dict.items():
      pipe = value[1]
      pipe.select_set(True)
      bpy.context.view_layer.objects.active = pipe
      for this_modifier in pipe.modifiers:
        this_modifier.solver = "EXACT"
        this_modifier.use_self = True
        this_modifier.use_hole_tolerant = True
        bpy.ops.object.modifier_apply(modifier = this_modifier.name)






      

  def test_make_everything(self):
    for key,value in self.connection_dict.items():
      path_name = f"Path_{key[0]}-{key[1]}"
      # self.pipe_object_dict.append(self.make_pipe(path_name, list(map(lambda a: a.coord,value))))
      self.pipe_object_dict[(key[0], key[1])] = [(value[1], value[-2]), self.make_pipe(path_name, value)]
    
    for key,value in self.junction_dict.items():
      junction_name = f"Junction_{key}"
      self.make_junction(junction_name, key, value)

    for object in bpy.data.objects:
      object.select_set(True)
      bpy.context.view_layer.objects.active = object
      bpy.ops.object.mode_set(mode = 'EDIT')
      bpy.ops.mesh.select_all(action='SELECT')
      bpy.ops.mesh.vert_connect_nonplanar(angle_limit=0.01)
      bpy.ops.mesh.select_all(action='SELECT')
      bpy.ops.mesh.vert_connect_concave()
      bpy.ops.mesh.select_all(action='SELECT')
      bpy.ops.mesh.remove_doubles(threshold=0.02)
      bpy.ops.object.mode_set(mode = 'OBJECT')






  def make_fillet(self, coord_list):
    new_coord_list = []
    fillet_size = .7 * (self.pipe_dimention[0] + self.pipe_dimention[1])

    for i, this_coord in enumerate(coord_list):
      if (i == 0 or i == len(coord_list) - 1):
        new_coord_list.append(this_coord)
      else:
        last_coord = coord_list[i - 1]
        next_coord = coord_list[i + 1]
        # last <-v1- coord -v2-> next
        v1 = tuple(map(lambda a,b: a-b, last_coord, this_coord))
        v2 = tuple(map(lambda a,b: a-b, next_coord, this_coord))

        l_v1 = sqrt(v1[0]**2 + v1[1]**2 + v1[2]**2)
        l_v2 = sqrt(v2[0]**2 + v2[1]**2 + v2[2]**2)

        # dot product
        dot_product = v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]
        cos = dot_product / (l_v1 * l_v2)

        # angle > 120
        if (cos < -.5):
          new_coord_list.append(this_coord)
        else:
          d1 = tuple(map(lambda a: a/l_v1*fillet_size, v1)) 
          d2 = tuple(map(lambda a: a/l_v2*fillet_size, v2)) 

          new_coord1 = tuple(map(lambda a,b: a+b, this_coord, d1))
          new_coord2 = tuple(map(lambda a,b: a+b, this_coord, d2))

          new_coord_list.append(new_coord1)
          new_coord_list.append(new_coord2)
        
    return new_coord_list










if __name__ == '__main__':

  bpy.ops.object.select_all(action='SELECT')
  bpy.ops.object.delete(use_global=False)

  pipe_system = PipeSystem()

  # pipe_system.connect_two_port((15,10,2), (0,10,3))
  # pipe_system.connect_two_port((2,13,3),(15,10,2))
  # pipe_system.connect_two_port((4,3,4), (0,10,3))
  # pipe_system.connect_two_port((0,9,3),(15,9,3))
  # pipe_system.connect_two_port((1,10,5), (20,10,3))
  # pipe_system.connect_two_port((5,9,3),(12,9,5))
  # pipe_system.connect_two_port((6,9,4),(11,9,5))
  # pipe_system.connect_two_port((7,9,5),(10,9,5))
  # pipe_system.connect_two_port((0,0,5), (10,10,5))
  # pipe_system.connect_two_port((8,11,5),(12,0,5))
  # pipe_system.connect_two_port((16,11,5),(12,0,5))
  # pipe_system.connect_two_port((0,0,5), (12,0,5))
  # pipe_system.connect_two_port((4,3,4), (0,0,5))
  # pipe_system.connect_two_port((4,3,4), (12,0,5))
  # pipe_system.connect_two_port((4,3,4), (3,0,5))
  # pipe_system.connect_two_port((12,0,5), (6,1,4))
  # pipe_system.connect_two_port((15,10,2), (6,1,4))
  # pipe_system.connect_two_port((20,10,3), (6,1,4))
  # pipe_system.connect_two_port((0,10,3), (6,1,4))

  pipe_system.unit_dimention = 3

  pipe_system.connect_two_port((35,20,2), (16,11,14))
  pipe_system.connect_two_port((20,10,13), (16,11,14))
  pipe_system.connect_two_port((0,10,13), (16,1,4))


  pipe_system.grid.update_connection_dict()

  pipe_system.grid.print_connection_dict()
  pipe_system.grid.print_saved_junction()


  # pipe_system.grid.connect_two_node((1,0,0), (2,0,0))
  # pipe_system.grid.print_saved_path()
  # pipe_system.make_pipe("p", [(0,0,0), (0,0,2)])
  # pipe_system.make_junction("j", (0,0,0), [(0,0,1)])

  pipe_system.fetch_grid_data()
  pipe_system.test_make_everything()















# #enable relative imports:
# if __name__ == '__main__': #makes sure this only happens when you run the script from inside Blender
    
#     # INCREASE THIS VALUE IF YOU WANT TO ACCESS MODULES IN PARENT FOLDERS (for using something like "from ... import someModule") 
#     number_of_parents = 3 # default = 1
    
#     original_path = pathlib.Path(bpy.data.filepath)
#     parent_path = original_path.parent
    
#     for i in range(number_of_parents):
#         parent_path = parent_path.parent
    
    
#     str_parent_path = str(parent_path.resolve()) # remember, paths only work if they're strings
#     #print(str_parent_path)    
#     if not str_parent_path in sys.path:
#         sys.path.append(str_parent_path)

#     # building the correct __package__ name
#     relative_path = original_path.parent.relative_to(parent_path)
#     with_dots = '.'.join(relative_path.parts)
#     #print(with_dots)
#     __package__ = with_dots


# #the relative imports don't have to be in the if clause above, they should work for other scripts that import this file as well.
# from . import printHello  # a dot is a relative path
# from .. import something # is in a directory above, only works if number_of_parents is at least 2 




