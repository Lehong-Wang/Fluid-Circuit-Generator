

"""
Pipe System
Interface between imaginary grid and real world coordinates
"""


import sys
from math import sqrt
import importlib.util
import bpy

spec = importlib.util.spec_from_file_location("path_finding.py", "/Users/lhwang/Documents/GitHub/RMG Project/Fluid-Circuit-Generator/path_finding.py")
p = importlib.util.module_from_spec(spec)
sys.modules["path_finding.py"] = p
spec.loader.exec_module(p)





class PipeSystem:
  """
  PipeSystem object
  Only one can exist, have one Grid object within
  """

  grid_dimention = (20,20,20)
  pipe_dimention = (.2, .15)
  unit_dimention = 1
  tip_length = 1


  def __init__(self):

    self.grid = p.Grid(self.grid_dimention)

    # {(start_coord, end_coord) : [path_coord_list]}
    self.connection_dict = {}
    # {junction_coord : [connection_coords]}
    self.junction_dict = {}
    # {port_coord : [port, tip, grid]}
    self.port_dict = {}
    # {(tip_coord, tip_coord) : [(tip_connection_coord, tip_connection_coord), pipe_object]}
    self.pipe_object_dict = {}
    # {coord : [(dest_coord, [path])]}
    self.connection_graph = {}
    # stores user related error messages
    self.error_message_list = []
    # stores user related warning messages
    self.warning_message_list = []


  def reset_grid(self, grid_dimention=None, pipe_dimention=None, unit_dimention=None, tip_length=None):
    """Top level function to Addjust dimentions of the grid and pipe system"""
    if grid_dimention is not None:
      self.grid_dimention = grid_dimention
    if pipe_dimention is not None:
      self.pipe_dimention = pipe_dimention
    if unit_dimention is not None:
      self.unit_dimention = unit_dimention
    if tip_length is not None:
      self.tip_length = tip_length
    self.__init__()
    print(f"Pipe System Reset with grid_dimention={self.grid_dimention}, pipe_dimention={self.pipe_dimention}, unit_dimention={self.unit_dimention}, tip_length={self.tip_length}")





  # snap to grid, then call grid.connect_two_node()
  def connect_two_port(self, start_port_coord, end_port_coord):
    """
    Top level function
    Use this to connect two ports
      Convert real coordinates to grid coordinates
      Connect grid coodinates with Grid Object functions
    """

    print("\n")
    print(f"Connecting Ports {start_port_coord} - {end_port_coord}")
    start_tip_coord = (start_port_coord[0], start_port_coord[1], start_port_coord[2]-self.tip_length)
    end_tip_coord = (end_port_coord[0], end_port_coord[1], end_port_coord[2]-self.tip_length)

    direction_sign_x = (end_port_coord[0] - start_port_coord[0]) > 0
    direction_sign_y = (end_port_coord[1] - start_port_coord[1]) > 0

    # if port-grid connection not exist, create new one
    if start_port_coord in self.port_dict:
      real_start_grid_coord = self.port_dict[start_port_coord][2]
      start_grid_coord = tuple(map(lambda a: a//self.unit_dimention, real_start_grid_coord))
      print(f"Start port already have real_grid_coord {real_start_grid_coord}")
    else:
      start_grid_coord = self.snap_to_grid(start_tip_coord, direction_sign_x, direction_sign_y)
      real_start_grid_coord = tuple(map(lambda a: a*self.unit_dimention, start_grid_coord))
      self.port_dict[start_port_coord] = [start_port_coord, start_tip_coord, real_start_grid_coord]

    if end_port_coord in self.port_dict:
      real_end_grid_coord = self.port_dict[end_port_coord][2]
      end_grid_coord = tuple(map(lambda a: a//self.unit_dimention, real_end_grid_coord))
      print(f"End port already have real_grid_coord {real_end_grid_coord}")
    else:
      end_grid_coord = self.snap_to_grid(end_tip_coord, not direction_sign_x, not direction_sign_y)
      real_end_grid_coord = tuple(map(lambda a: a*self.unit_dimention, end_grid_coord))
      self.port_dict[end_port_coord] = [end_port_coord, end_tip_coord, real_end_grid_coord]

    print(f"Corresponding Grid coord: {start_grid_coord} - {end_grid_coord}")

    self.grid.connect_two_node(start_grid_coord, end_grid_coord)


  # snap to grid towards destination, if not available, check around till z<0
  def snap_to_grid(self, coord, direction_sign_x, direction_sign_y):
    """Find the corrisponding ground coordinate for a real world coordinate"""
    dim = self.unit_dimention
    # if already on grid, not change
    dir_x = bool(coord[0]%dim)*direction_sign_x
    dir_y = bool(coord[1]%dim)*direction_sign_y

    grid_coord = (int(coord[0]//dim + dir_x), int(coord[1]//dim + dir_y), int(coord[2]//dim))
    # self.print_port_dict()

    while self.grid_coord_in_use(grid_coord):
      if self.grid_coord_in_use((grid_coord[0]-dir_x, grid_coord[1], grid_coord[2])):
        if self.grid_coord_in_use((grid_coord[0], grid_coord[1]-dir_y, grid_coord[2])):
          if self.grid_coord_in_use((grid_coord[0]-dir_x, grid_coord[1]-dir_y, grid_coord[2])):
            grid_coord = (grid_coord[0]-dir_x, grid_coord[1]-dir_y, grid_coord[2]-1)
            if grid_coord[2] < 0:
              self.register_error_message(f"ERROR: can't find snap point for Tip_Coord{coord}")
              return
            continue
          grid_coord = (grid_coord[0]-dir_x, grid_coord[1]-dir_y, grid_coord[2])
          break
        grid_coord = (grid_coord[0], grid_coord[1]-dir_y, grid_coord[2])
        break
      grid_coord = (grid_coord[0]-dir_x, grid_coord[1], grid_coord[2])
      break

    real_grid_coord = tuple(map(lambda a: a*dim, grid_coord))
    print(f"Snap: {coord}-{grid_coord}-{real_grid_coord}")
    return grid_coord


  # check both grid.visited and port_dict for if is used
  def grid_coord_in_use(self, grid_coord):
    """Helper Function"""
    real_grid_coord = tuple(map(lambda a: a*self.unit_dimention, grid_coord))
    if self.grid.is_visited(grid_coord):
      return True
    for key,value in self.port_dict.items():
      if real_grid_coord in value:
        # print("IN")
        return True
    return False


  # get connection_dict and saved_junction data from grid
  # apply unit_dimention and snap to node.coords
  def fetch_grid_data(self):
    """Get path data from Grid Object after all path finding is finished"""
    # get connection_dict
    for key,value in self.grid.connection_dict.items():
      grid_tip_coord = tuple(map(lambda a: a.coord, key))
      real_coord = []
      for coord in grid_tip_coord:
        real_coord.append(tuple(map(lambda a: a*self.unit_dimention, coord)))
      real_coord = tuple(real_coord)

      grid_path_coord = tuple(map(lambda a: a.coord, value))
      real_path = []
      for coord in grid_path_coord:
        real_path.append(tuple(map(lambda a: a*self.unit_dimention, coord)))

      self.connection_dict[real_coord] = real_path

    # get junction_dict
    for key,value in self.grid.saved_junction.items():
      real_junction_coord = tuple(map(lambda a: a*self.unit_dimention, key.coord))
      real_connection_coord_list = []
      connection_coord = tuple(map(lambda a: a.coord, value))
      for coord in connection_coord:
        real_connection_coord_list.append(tuple(map(lambda a: a*self.unit_dimention, coord)))

      self.junction_dict[real_junction_coord] = real_connection_coord_list

    # add port_tip_grid_path to connections
    for key,value in self.port_dict.items():
      port_coord = key
      tip_coord = value[1]
      grid_coord = value[2]
      # check in connection_dict for ports to add
      for path_key, path_value in self.connection_dict.items():
        start_grid_coord = path_key[0]
        end_grid_coord = path_key[1]
        path = path_value
        if start_grid_coord == grid_coord:
          path.insert(0, tip_coord)
          path.insert(0, port_coord)
        if end_grid_coord == grid_coord:
          path.append(tip_coord)
          path.append(port_coord)

    # look in connection_dict key
    # change the start/end grid coord to port coord if is port
    port_list = []
    grid_list = []
    for key,value in self.port_dict.items():
      port_list.append(key)
      grid_list.append(value[2])

    new_dict = {}
    for key,value in self.connection_dict.items():
      new_key = list(key)
      for i,coord in enumerate(key):
        if coord in grid_list:
          index = grid_list.index(coord)
          new_key[i] = port_list[index]
      new_dict[tuple(new_key)] = value

    self.connection_dict = new_dict




####################################  make modle  ############################################


  def make_pipe(self, name, coord_list):
    """Make pipe module from given list of coordinates"""
    if len(coord_list) < 2:
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

    solidify_modifier_name = "Solidify"
    curve_object.modifiers.new(solidify_modifier_name, "SOLIDIFY").thickness = self.pipe_dimention[1]
    # curve_object.modifiers[solidify_modifier_name].use_quality_normals = True
    # curve_object.modifiers[solidify_modifier_name].use_even_offset = True

    # fully select object
    curve_object.select_set(True)
    bpy.context.view_layer.objects.active = curve_object
    bpy.ops.object.convert(target = "MESH")
    return curve_object


  def make_junction(self, name, junction_coord, connection_list):
    """Create junction module from pipe locations"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius = 1*(self.pipe_dimention[0] + self.pipe_dimention[1]), segments=16, ring_count=8)
    junction_sphere = bpy.context.active_object
    junction_sphere.name = name
    junction_sphere.location = junction_coord
    junction_sphere.modifiers.new("Solidify", "SOLIDIFY").thickness = self.pipe_dimention[1]

    connection_object_dict = {}
    for key,value in self.pipe_object_dict.items():
      if junction_coord in key:
        connection_object_dict[key] = value

    cut_out_object_list = []
    for connection_coord in connection_list:
      curve_data = bpy.data.curves.new(name, type = "CURVE")
      curve_data.dimensions = "3D"

      polyline = curve_data.splines.new("POLY")
      polyline.points.add(1)
      # prevent too much overlap
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
      # need exact solver for all
      junction_modifier_name = "Boolean"
      junction_sphere.modifiers.new(junction_modifier_name, "BOOLEAN").object = curve_object
      junction_sphere.modifiers[junction_modifier_name].operation = 'DIFFERENCE'
      junction_sphere.modifiers[junction_modifier_name].solver = "EXACT"
      # fully select before apply
      junction_sphere.select_set(True)
      bpy.context.view_layer.objects.active = junction_sphere
      bpy.ops.object.modifier_apply(modifier = junction_modifier_name)
      # cut from other pipes
      for key,value in connection_object_dict.items():
        pipe = value[1]
        pipe_connections = value[0]
        if not connection_coord in pipe_connections:
          modifier_name = f"P_C{pipe.name}"
          pipe.modifiers.new(modifier_name, "BOOLEAN").object = curve_object
          pipe.modifiers[modifier_name].operation = 'DIFFERENCE'

      # bpy.data.objects.remove(curve_object)
      curve_object.hide_set(True)
      cut_out_object_list.append(curve_object)

    # set all modifier to EXACT, use_self, and use_hole_tolerant
    for key,value in connection_object_dict.items():
      pipe = value[1]
      pipe.select_set(True)
      bpy.context.view_layer.objects.active = pipe
      for this_modifier in pipe.modifiers:
        this_modifier.solver = "EXACT"
        this_modifier.use_self = True
        this_modifier.use_hole_tolerant = True
        bpy.ops.object.modifier_apply(modifier = this_modifier.name)
    # delete all object made to cut out junction
    for obj in cut_out_object_list:
      bpy.data.objects.remove(obj)



  def make_everything(self):
    """Make all the modules after all the calculations are finished"""

    for key,value in self.connection_dict.items():
      # path_name = f"Path_{key[0]}-{key[1]}"
      start_coord_rounded = tuple(map(lambda x: round(x,2), key[0]))
      end_coord_rounded = tuple(map(lambda x: round(x,2), key[1]))
      path_name = f"Path_{start_coord_rounded}-{end_coord_rounded}"
      self.pipe_object_dict[(key[0], key[1])] = [(value[1], value[-2]), self.make_pipe(path_name, value)]

    for key,value in self.junction_dict.items():
      junction_name = f"Junction_{key}"
      self.make_junction(junction_name, key, value)

    # mesh clean up
    for obj in bpy.data.objects:
      obj.select_set(True)
      bpy.context.view_layer.objects.active = obj
      bpy.ops.object.mode_set(mode = 'EDIT')
      bpy.ops.mesh.select_all(action='SELECT')
      bpy.ops.mesh.vert_connect_nonplanar(angle_limit=0.01)
      bpy.ops.mesh.select_all(action='SELECT')
      bpy.ops.mesh.vert_connect_concave()
      bpy.ops.mesh.select_all(action='SELECT')
      bpy.ops.mesh.remove_doubles(threshold=0.02)
      bpy.ops.object.mode_set(mode = 'OBJECT')



  # add fillet to turns < 120
  def make_fillet(self, coord_list):
    """Make fillet in pipe for turns < 120 degrees"""
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

        l_v1 = sqrt(v1[0]**2 + v1[1]**2 + v1[2]**2) + 0.001   # prevent division by 0
        l_v2 = sqrt(v2[0]**2 + v2[1]**2 + v2[2]**2) + 0.001

        # dot product
        dot_product = v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]
        cos = dot_product / (l_v1 * l_v2)

        # angle > 120
        if cos < -.5:
          new_coord_list.append(this_coord)
        else:
          d1 = tuple(map(lambda a: a/l_v1*fillet_size, v1))
          d2 = tuple(map(lambda a: a/l_v2*fillet_size, v2))

          new_coord1 = tuple(map(lambda a,b: a+b, this_coord, d1))
          new_coord2 = tuple(map(lambda a,b: a+b, this_coord, d2))

          new_coord_list.append(new_coord1)
          new_coord_list.append(new_coord2)

    return new_coord_list





####################################  construct graph  #####################################

  # make a graph of connections from connection_dict
  def construct_graph(self):
    """Construct a graph of connections from path finding results"""
    self.connection_graph = {}

    for key,value in self.connection_dict.items():
      start_coord = key[0]
      end_coord = key[1]
      path = value
      inverse_path = []
      for coord in path:
        inverse_path.insert(0, coord)

      # add connections both ways
      if start_coord in self.connection_graph:
        self.connection_graph[start_coord].append((end_coord, path))
      else:
        self.connection_graph[start_coord] = [(end_coord, path)]

      if end_coord in self.connection_graph:
        self.connection_graph[end_coord].append((start_coord, inverse_path))
      else:
        self.connection_graph[end_coord] = [(start_coord, inverse_path)]


  # get the full path from two coords
  # should not use this, but use one in Gate Assembly
  def get_path_from_graph(self, start_coord, end_coord):
    """
    Triverse the graph to find path between two real world coordinates
    DO NOT USE this one, use the one in gate assembly
    That one also considers internal connection of logic gates
    """
    print(f"\nGetting path from {start_coord} to {end_coord}")

    if start_coord not in self.connection_graph:
      print(f"Error: start_coord {start_coord} not in connection graph")
      return []
    if end_coord not in self.connection_graph:
      print(f"Error: end_coord {end_coord} not in connection graph")
      return []

    # Breth First Search
    search_queue = []
    search_queue.append(start_coord)
    visited_list = []
    last_visited = {}

    while len(search_queue) != 0:
      this_coord = search_queue.pop(0)

      if this_coord == end_coord:
        print("Path Found")
        # record the full path
        path = []
        current_coord = end_coord
        last_coord = None
        while current_coord != start_coord:
          if current_coord != end_coord:
            current_path = []
            # get current_path from connection_graph
            for connection in self.connection_graph[current_coord]:
              if last_coord == connection[0]:
                current_path = connection[1][:]   # copy list so it don't affect original list (list is mutable)
            if len(path) != 0:
              path.pop(0)
            path = current_path + path
          last_coord = current_coord
          current_coord = last_visited[current_coord]

        current_path = []
        for connection in self.connection_graph[current_coord]:
          if last_coord == connection[0]:
            current_path = connection[1][:]
        if len(path) != 0:
          path.pop(0)
        path = current_path + path

        print(f"Path: {path}")
        return path

      # get neighbors
      neighbor_list = []
      for connection in self.connection_graph[this_coord]:
        neighbor_list.append(connection[0])
      # print(f"{this_coord} neighbors: {neighbor_list}")

      for next_coord in neighbor_list:
        if next_coord not in visited_list:
          if next_coord not in search_queue:
            search_queue.append(next_coord)
            last_visited[next_coord] = this_coord
            # print(f"\tQueue added {this_coord}")


      visited_list.append(this_coord)

    print(f"Error: Path Not Found for {start_coord}-{end_coord}")
    return []


  def finish_up_everything(self):
    """
    Top level function
    Only call after finishing all the connectings
    Freeze all the connection data and organize them into usable form (graph)
    Construct 3d module from the connection information
    This is NOT Reversable
    Call once at the end
    """
    self.grid.update_connection_dict()
    self.fetch_grid_data()
    self.construct_graph()
    self.make_everything()




###############################  Print Helpers  #################################


  def print_connection_dict(self):
    """Helper function"""
    print("\nConnection dict:")
    for key,value in self.connection_dict.items():
      print("Connection Path:")
      print(f"{key[0]}, {key[1]}: {value}")

  def print_junction_dict(self):
    """Helper function"""
    print("\nJunction dict:")
    for key,value in self.junction_dict.items():
      print(f"Junction: {key}, Connections: {value}")

  def print_port_dict(self):
    """Helper function"""
    print("\nPort dict:")
    for key,value in self.port_dict.items():
      print(f"Port: {key}, Path: {value}")

  def print_connection_graph(self):
    """Helper function"""
    print("\nConnection graph:")
    for key,value in self.connection_graph.items():
      print(f"\tStart: {key}")
      for connection in value:
        print(f"Dest:{connection[0]}, Path:{connection[1]}")

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
    grid_error_message = self.grid.get_error_message()
    self.error_message_list.extend(grid_error_message)
    return self.error_message_list

  def get_warning_message(self):
    """Helper Function"""
    grid_warning_message = self.grid.get_warning_message()
    self.warning_message_list.extend(grid_warning_message)
    return self.warning_message_list





# if __name__ == '__main__':
#   bpy.ops.object.select_all(action='SELECT')
#   bpy.ops.object.delete(use_global=False)

#   pi = PipeSystem()

#   print(pi.grid)
#   print(pi.grid.dimention)
#   pi.connect_two_port((18,19,3), (20,20,4))
#   pi.grid.update_connection_dict()
#   pi.fetch_grid_data()
#   pi.print_connection_dict()

#   pi.reset_grid(grid_dimention = (30,30,20), unit_dimention = 3)
#   print(pi.grid)
#   print(pi.grid.dimention)
#   pi.connect_two_port((21,9,6), (30,30,7))
#   pi.grid.update_connection_dict()
#   pi.fetch_grid_data()
#   pi.print_connection_dict()
#   pi.grid.print_connection_dict()

#   print(pi.get_error_message())
#   print(pi.get_warning_message())







if __name__ == '__main__':

  bpy.ops.object.select_all(action='SELECT')
  bpy.ops.object.delete(use_global=False)

  pipe_system = PipeSystem()
  pipe_system.unit_dimention = 1


  pipe_system.connect_two_port((15,10,2), (0,10,3))
  pipe_system.connect_two_port((2,13,3),(15,10,2))
  pipe_system.connect_two_port((4,3,4), (0,10,3))
  pipe_system.connect_two_port((0,9,3),(15,9,3))
  pipe_system.connect_two_port((1,10,5), (20,10,3))
  pipe_system.connect_two_port((5,9,3),(12,9,5))
  pipe_system.connect_two_port((6,9,4),(11,9,5))
  pipe_system.connect_two_port((7,9,5),(10,9,5))
  pipe_system.connect_two_port((0,0,5), (10,10,5))
  pipe_system.connect_two_port((8,11,5),(12,0,5))
  pipe_system.connect_two_port((16,11,5),(12,0,5))
  pipe_system.connect_two_port((0,0,5), (12,0,5))
  pipe_system.connect_two_port((4,3,4), (0,0,5))
  pipe_system.connect_two_port((4,3,4), (12,0,5))
  pipe_system.connect_two_port((4,3,4), (3,0,5))
  pipe_system.connect_two_port((12,0,5), (6,1,4))
  pipe_system.connect_two_port((15,10,2), (6,1,4))
  pipe_system.connect_two_port((20,10,3), (6,1,4))
  pipe_system.connect_two_port((0,10,3), (6,1,4))


#   pipe_system.connect_two_port((15.5,10,12.3), (6,11.5,4))
#   pipe_system.connect_two_port((20.5,10.8,13), (6,11.5,4))
#   pipe_system.connect_two_port((0.5,10,13), (6,1,4))
#   pipe_system.connect_two_port((5.5,7,9.9), (6,11.5,4))
#   # pipe_system.connect_two_port((5.5,7,9.9), (15.5,10,12.3))
  # pipe_system.update_everything()

#   pipe_system.connect_two_port((5.5,8,8.7), (0,0,10))
#   pipe_system.connect_two_port((6.5,7,9), (20,0.1,9))
#   pipe_system.connect_two_port((6.5,8,9), (1.5,0.8,9))
#   pipe_system.connect_two_port((10,3.4,9.5), (0.5,10,11.2))
#   pipe_system.connect_two_port((5.5,7,9.9), (5.5,8,8.7))
#   # pipe_system.connect_two_port((5.5,7,9.9), (5.5,8,8.7))


  pipe_system.finish_up_everything()
#   # pipe_system.grid.update_connection_dict()

#   pipe_system.grid.print_connection_dict()
#   pipe_system.grid.print_saved_junction()


#   # pipe_system.grid.connect_two_node((1,0,0), (2,0,0))
#   # pipe_system.grid.print_saved_path()
#   # pipe_system.make_pipe("p", [(0,0,0), (0,0,2)])
#   # pipe_system.make_junction("j", (0,0,0), [(0,0,1)])

#   # pipe_system.fetch_grid_data()
#   # pipe_system.construct_graph()



#   # print("Connection Dictionary:")
#   # print(pipe_system.connection_dict)
#   # print("Port Dictionary:")
#   # print(pipe_system.port_dict)
#   pipe_system.print_connection_dict()
#   pipe_system.print_port_dict()
#   pipe_system.print_junction_dict()
#   pipe_system.print_connection_graph()


#   path1 = pipe_system.get_path_from_graph((15.5,10,12.3), (6,11.5,4))
#   path2 = pipe_system.get_path_from_graph((0,0,10), (20.5,10.8,13))



  # pipe_system.make_everything()


#   pipe_system.pipe_dimention = (.5,.01)
#   pipe_system.make_pipe("p1", path1)
#   pipe_system.make_pipe("p2", path2)














