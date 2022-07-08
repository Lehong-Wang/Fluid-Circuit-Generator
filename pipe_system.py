import bpy

import importlib.util
import sys
spec = importlib.util.spec_from_file_location("path_finding.py", "/Users/lhwang/Documents/Blender Python Projects/Git Project Space/Fluid-Circuit-Generator/path_finding.py")
p = importlib.util.module_from_spec(spec)
sys.modules["path_finding.py"] = p
spec.loader.exec_module(p)




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

      self.grid = p.Grid(self.grid_dimention)

      # {(tip_coord, tip_coord) : pipe_object}
      self.pipe_object_dict = {}

      
    return self._instance

  
  def make_pipe(self, name, coord_list):
    if (len(coord_list) < 2):
      print(f"Error: Dot list {coord_list} too short")
      return

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

    bpy.ops.mesh.primitive_uv_sphere_add(radius = self.pipe_dimention[0] + self.pipe_dimention[1])
    junction_sphere = bpy.context.active_object
    junction_sphere.name = name
    junction_sphere.location = junction_coord
    junction_sphere.modifiers.new("Solidify", "SOLIDIFY").thickness = self.pipe_dimention[1]

    connection_object_list = []
    for key,value in self.pipe_object_dict.items():
      if junction_coord in key:
        connection_object_list.append(value)


    for connection_coord in connection_list:
      curve_data = bpy.data.curves.new(name, type = "CURVE")
      curve_data.dimensions = "3D"

      polyline = curve_data.splines.new("POLY")
      polyline.points.add(1)
      end_coord = tuple(map(lambda a,b: a + 0.1*(b-a), junction_coord, connection_coord))
      x,y,z = end_coord
      polyline.points[0].co = (x,y,z,1)
      x,y,z = connection_coord
      polyline.points[1].co = (x,y,z,1)
    
      curve_object = bpy.data.objects.new(name, curve_data)
      bpy.context.collection.objects.link(curve_object)

      curve_object.data.bevel_depth = self.pipe_dimention[0]
      curve_object.data.bevel_resolution = 2
      curve_object.data.use_fill_caps = True

      curve_object.select_set(True)
      bpy.context.view_layer.objects.active = curve_object
      bpy.ops.object.convert(target = "MESH")

      junction_sphere.modifiers.new("J_C", "BOOLEAN").object = curve_object
      junction_sphere.modifiers["J_C"].operation = 'DIFFERENCE'
      junction_sphere.modifiers["J_C"].solver = "FAST"
      junction_sphere.select_set(True)
      bpy.context.view_layer.objects.active = junction_sphere
      # bpy.ops.object.modifier_apply(modifier = "BOOLEAN")
      bpy.ops.object.modifier_apply(modifier="J_C")

      for pipe in connection_object_list:

        modifier_name = f"P_C{pipe.name}"
        pipe.modifiers.new(modifier_name, "BOOLEAN").object = curve_object
        pipe.modifiers[modifier_name].operation = 'DIFFERENCE'

        # pipe.modifiers[modifier_name].solver = "FAST"
        # pipe.select_set(True)
        # bpy.context.view_layer.objects.active = pipe
        # # bpy.ops.object.modifier_apply(modifier = "BOOLEAN")
        # bpy.ops.object.modifier_apply(modifier=modifier_name)

      # bpy.data.objects.remove(curve_object)
      curve_object.hide_set(True)

    for pipe in connection_object_list:
      for modifier in pipe.modifiers:
        modifier.solver = "EXACT"
        modifier.use_self = True
        modifier.use_hole_tolerant = True


      

  def test_make_everything(self):
    for key,value in self.grid.connection_dict.items():
      path_name = f"Path_{key[0].coord}-{key[1].coord}"
      # self.pipe_object_dict.append(self.make_pipe(path_name, list(map(lambda a: a.coord,value))))
      self.pipe_object_dict[(key[0].coord, key[1].coord)] = self.make_pipe(path_name, list(map(lambda a: a.coord,value)))
    
    for key,value in self.grid.saved_junction.items():
      junction_name = f"Junction_{key.coord}"
      self.make_junction(junction_name, key.coord, list(map(lambda a: a.coord,value)))









if __name__ == '__main__':

  bpy.ops.object.select_all(action='SELECT')
  bpy.ops.object.delete(use_global=False)

  pipe_system = PipeSystem()

  pipe_system.grid.connect_two_node((15,10,2), (0,10,3))
  pipe_system.grid.connect_two_node((2,13,3),(15,10,2))
  pipe_system.grid.connect_two_node((4,3,4), (0,10,3))
  pipe_system.grid.connect_two_node((0,9,3),(15,9,3))
  pipe_system.grid.connect_two_node((1,10,5), (20,10,3))
  pipe_system.grid.connect_two_node((5,9,3),(12,9,5))
  pipe_system.grid.connect_two_node((6,9,4),(11,9,5))
  pipe_system.grid.connect_two_node((7,9,5),(10,9,5))
  pipe_system.grid.connect_two_node((0,0,5), (10,10,5))
  pipe_system.grid.connect_two_node((8,11,5),(12,0,5))
  pipe_system.grid.connect_two_node((16,11,5),(12,0,5))
  pipe_system.grid.connect_two_node((0,0,5), (12,0,5))
  pipe_system.grid.connect_two_node((4,3,4), (0,0,5))
  pipe_system.grid.connect_two_node((4,3,4), (12,0,5))
  pipe_system.grid.connect_two_node((4,3,4), (3,0,5))
  pipe_system.grid.connect_two_node((12,0,5), (6,1,4))
  pipe_system.grid.connect_two_node((15,10,2), (6,1,4))
  pipe_system.grid.connect_two_node((20,10,3), (6,1,4))
  pipe_system.grid.connect_two_node((0,10,3), (6,1,4))


  pipe_system.grid.update_connection_dict()

  pipe_system.grid.print_connection_dict()
  pipe_system.grid.print_saved_junction()


  # pipe_system.grid.connect_two_node((1,0,0), (2,0,0))
  # pipe_system.grid.print_saved_path()
  # pipe_system.make_pipe("p", [(0,0,0), (0,0,2)])
  # pipe_system.make_junction("j", (0,0,0), [(0,0,1)])

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




