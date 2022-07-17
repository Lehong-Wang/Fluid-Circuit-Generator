import math
from queue import PriorityQueue
import bpy
import sys, os


#####################################  Node Class  ###################################

class Node:

  def __init__(self, coord, limit_coord):
    # First check if coordinate is within limit
    if not self.check_valid_coord(coord, limit_coord):
      print(f"Error: Node {coord} is out of limit {limit_coord}")
      print(f"Error: Node not Created")
      # del self
      return

    self.coord = coord
    self.limit_coord = limit_coord  # boundary of grid
    self.neighbors = []             # stores valid connections
    self.all_neighbors = []         # all neighbors within limit of grid
    self.blocked_neighbors = []     # neighbors blocked by other connection

    # F = G + H
    self.F = float("inf")
    self.G = float("inf")
    self.H = float("inf")

    self.last_visited = None
    self.visited = False

    self.make_neighbors()
    self.update_neighbors()
    # print(f"Node {self.coord} Neighbors: {self.neighbors}")

  

  def make_neighbors(self):
    primitive_list = []
    # down
    primitive_list.append((self.coord[0], self.coord[1], self.coord[2]-1))
    # down straight
    primitive_list.append((self.coord[0]+1, self.coord[1], self.coord[2]-1))
    primitive_list.append((self.coord[0], self.coord[1]+1, self.coord[2]-1))
    primitive_list.append((self.coord[0]-1, self.coord[1], self.coord[2]-1))
    primitive_list.append((self.coord[0], self.coord[1]-1, self.coord[2]-1))
    # down cross
    primitive_list.append((self.coord[0]+1, self.coord[1]+1, self.coord[2]-1))
    primitive_list.append((self.coord[0]-1, self.coord[1]+1, self.coord[2]-1))
    primitive_list.append((self.coord[0]-1, self.coord[1]-1, self.coord[2]-1))
    primitive_list.append((self.coord[0]+1, self.coord[1]-1, self.coord[2]-1))
    # straight
    primitive_list.append((self.coord[0]+1, self.coord[1], self.coord[2]))
    primitive_list.append((self.coord[0], self.coord[1]+1, self.coord[2]))
    primitive_list.append((self.coord[0]-1, self.coord[1], self.coord[2]))
    primitive_list.append((self.coord[0], self.coord[1]-1, self.coord[2]))
    # cross
    primitive_list.append((self.coord[0]+1, self.coord[1]+1, self.coord[2]))
    primitive_list.append((self.coord[0]-1, self.coord[1]+1, self.coord[2]))
    primitive_list.append((self.coord[0]-1, self.coord[1]-1, self.coord[2]))
    primitive_list.append((self.coord[0]+1, self.coord[1]-1, self.coord[2]))
    # up
    primitive_list.append((self.coord[0], self.coord[1], self.coord[2]+1))
    # up straight
    primitive_list.append((self.coord[0]+1, self.coord[1], self.coord[2]+1))
    primitive_list.append((self.coord[0], self.coord[1]+1, self.coord[2]+1))
    primitive_list.append((self.coord[0]-1, self.coord[1], self.coord[2]+1))
    primitive_list.append((self.coord[0], self.coord[1]-1, self.coord[2]+1))
    # up cross
    primitive_list.append((self.coord[0]+1, self.coord[1]+1, self.coord[2]+1))
    primitive_list.append((self.coord[0]-1, self.coord[1]+1, self.coord[2]+1))
    primitive_list.append((self.coord[0]-1, self.coord[1]-1, self.coord[2]+1))
    primitive_list.append((self.coord[0]+1, self.coord[1]-1, self.coord[2]+1))

    # filter with grid limit
    filtered_list = []
    for coord in primitive_list:
      if self.check_valid_coord(coord, self.limit_coord):
        filtered_list.append(coord)
    
    self.all_neighbors = filtered_list



  # return if G is updated
  def update_FGHL(self, from_node, dest_node):
    self.H = self.calculate_H(dest_node)
    # print(f"Calculated H {self.coord} -> {dest_node.coord}, dest_h = {self.H}")
    updated = self.update_G(from_node)
    self.calculate_F()
    # print(f"Updated All F G H L")
    return updated

  # F = G (lenght already traveled) + H (lenght excepted)
  def calculate_F(self):
    self.F = self.G + self.H
    # print(f"Calculated F from G + H: {self.F}")
    return self.F

  # max will make it go cross first, then straight (gather same direction segment)
  # plus some real distance so it head toward the target
  def calculate_H(self, dest_node):
    x1,y1,z1 = self.coord
    x2,y2,z2 = dest_node.coord
    dest_h = max(abs(x1-x2), abs(y1-y2), abs(z1-z2)) + 0.1*(self.square_root(self.coord, dest_node.coord))
    return dest_h

  # return if G is updated (decreased)
  def update_G(self, from_node):
    dis = self.get_from_dis(from_node)
    new_g = from_node.G + dis
    # print(f"Calculated G from Node {from_node.coord} to {self.coord}, new_g = {new_g}")
    if new_g < self.G:
      self.update_last_visited(from_node)
      # print(f"Update G: {self.G} -> {new_g}")
      self.G = new_g
      return True
    # print(f"G Not updated")
    return False
 
  def update_last_visited(self, from_node):
    # print(f"Update last_visited: {self.last_visited} -> {from_node.coord}")
    self.last_visited = from_node
    return

  def update_neighbors(self):
    self.neighbors = []
    for coord in self.all_neighbors:
      if self.blocked_neighbors.count(coord) == 0:
        self.neighbors.append(coord)
    return

  # reward for heading down and staying on the bottom
  def get_from_dis(self, from_node):
    # 1 -> 2, from -> this
    x1,y1,z1 = from_node.coord
    x2,y2,z2 = self.coord

    dis = self.square_root(from_node.coord, self.coord)
    if (z1 - z2) == 1: # heading down
      dis = self.square_root((x1,y1,z1), (x2,y2,z1))
    if (z2 == 0):
      dis -= .1
    return dis

  # add node to blocked_neighbors list
  def add_block_neighbors(self, neighbor):
    if self.all_neighbors.count(neighbor.coord) == 0:
      print(f"Error: {neighbor.coord} is not in neighbors list of Node {self.coord}")
      return None
    if self.blocked_neighbors.count(neighbor.coord) == 0:
      self.blocked_neighbors.append(neighbor.coord)
      self.update_neighbors()
    # print(f"Added {neighbor.coord} to Node {self.coord} blocked neighbor list")
    return


  # check if coord is in valid range
  def check_valid_coord(self, coord, limit_coord):
    valid = True
    for i in range(len(coord)):
      valid &= (coord[i] <= limit_coord[i] and coord[i] >= 0)
    return valid

  # helper for calculating distance between two nodes
  def square_root(self, coord_a, coord_b):
    a_x, a_y, a_z = coord_a
    b_x, b_y, b_z = coord_b
    dis = math.sqrt((a_x - b_x) ** 2 + (a_y - b_y) ** 2 + (a_z - b_z) ** 2)
    return dis

  # reset node for next path finding
  def reset_node(self):
    self.F = float("inf")
    self.G = float("inf")
    self.H = float("inf")
    self.last_visited = None
    self.visited = False
    self.blocked_neighbors = []
    self.update_neighbors()



#####################################  Grid Class  #########################################

class Grid:
  # singleton design pattern
  # only one Grid object can exist at a time
  _instance = None

  def __new__(self, dimention):
    # blockPrint()
    if not self._instance:
      self._instance = super(Grid, self).__new__(self)

      self.dimention = dimention
      self.node_grid = []
      self.node_grid = self.make_grid(self)

      # store all the ground paths
      # only ground path can merge together
      # {(start_node, end_node) : [path_node_list]}
      self.saved_path = {}
      # store all the junction info
      # {junction_ndoe : [connection_nodes]}
      self.saved_junction = {}
      # store all the tip_ground path
      # {tip_node : [ground_node, is_start, [path_node_list]]}
      self.tip_ground_table = {}
      # store all the connections
      # generated after all path are processed
      # {(start_node, end_node) : [path_node_list]}
      self.connection_dict = {}

      self.path_graph = {}

    return self._instance

    
  # make a grid of nodes
  def make_grid(self):
    X_list = []
    for x in range(self.dimention[0]+1):
      Y_list = []
      for y in range(self.dimention[1]+1):
        Z_list = []
        for z in range(self.dimention[2]+1):
          Z_list.append(Node((x,y,z), self.dimention))
        Y_list.append(Z_list)
      X_list.append(Y_list)
    return X_list


  ########################################  path finding  ########################################

  # A* path finding
  def path_finding(self, start_coord, end_coord):
    print(f"Looking for path from {start_coord} to {end_coord}")
    start_node = self.node_grid[start_coord[0]][start_coord[1]][start_coord[2]]
    end_node = self.node_grid[end_coord[0]][end_coord[1]][end_coord[2]]

    if start_node.visited:
      print(f"Error: Start Node {start_node.coord} is already in use")
      return []
    if end_node.visited:
      print(f"Error: End Node {end_node.coord} is already in use")
      return []  

    search_queue = PriorityQueue()
    # list that keep track of the nodes in the queue
    # update at the same time
    search_list = []

    search_queue.put((1, 0, start_node))
    search_list.append(start_node)

    start_node.G = 0
    node_count = 0
    processed_node_count = 0

    while not search_queue.empty():
      this_node = search_queue.get()[2]
      # print(f"\nWorking on Node {this_node.coord}")

      if this_node is end_node:
        print("Path Found")
        path = self.record_path(start_node, end_node)
        print(f"Searched {node_count} Nodes")
        print(f"Fully Processed {processed_node_count} Nodes")
        self.cut_all_crossover()
        return path


      for coord in this_node.neighbors:
        x,y,z = coord
        neighbor_node = self.node_grid[x][y][z]
        if not neighbor_node.visited:
          # calculate F,G,H value of neighbor and put in heap
          updated = neighbor_node.update_FGHL(this_node, end_node)
          # check if is in heap or updated G value
          if updated or search_list.count(neighbor_node) == 0:
            node_count += 1
            search_queue.put((1*neighbor_node.H + 0.2*neighbor_node.G, node_count, neighbor_node))
            search_list.append(neighbor_node)
            # print(f"Added Node {neighbor_node.coord}, F = {neighbor_node.F}, node_count = {node_count}")
          
      this_node.visited = True
      processed_node_count += 1
      # print(f"Processed Node {this_node.coord}")

    print("Error: No path found")
    return []


  # get the path by tracing backwards from end
  def record_path(self, start_node, end_node):
    # print(f"Recording Path from {start_node.coord} to {end_node.coord}")
    this_node = end_node
    path_node_list = []

    while this_node is not start_node:
      path_node_list.insert(0, this_node)
      this_node = this_node.last_visited
    path_node_list.insert(0, start_node)

    self.saved_path[(start_node, end_node)] = path_node_list
    self.reset_grid()

    print(f"Path: {list(map(lambda a: a.coord, path_node_list))}")
    return path_node_list


  #########################################  clean up  ############################################

  # reset grid for next path finding
  def reset_grid(self):
    for x in range(len(self.node_grid)):
      for y in range(len(self.node_grid[x])):
        for z in range(len(self.node_grid[x][y])):
          self.node_grid[x][y][z].reset_node()

    for key,value in self.saved_path.items():
      this_saved_path = value
      for node in this_saved_path:
        node.visited = True      
    
    for key,value in self.tip_ground_table.items():
      this_saved_path = value[2]
      for node in this_saved_path:
        node.visited = True

    self.cut_all_crossover()
    print("Grid Reset")



  # cut all the crossing/ half crossing connections
  def cut_all_crossover(self):
    for key, value in self.saved_path.items():
      this_saved_path = value
      node_coord_list = []
      for node in key:
        node_coord_list.append(node.coord)
      for i, this_node in enumerate(this_saved_path):
        if i == len(this_saved_path) - 1:
          # print(f"All cross are trimmed for path {node_coord_list}")
          break       
        next_node = this_saved_path[i+1]

        x1, y1, z1 = this_node.coord
        x2, y2, z2 = next_node.coord

        dx = x1 - x2
        dy = y1 - y2
        dz = z1 - z2
        difference = abs(dx) + abs(dy) + abs(dz)

        # staright
        if difference == 1:
          pass
        # 2D cross
        if difference == 2:
          # print(f"Flat cross detected at {this_node.coord} - {next_node.coord}")
          x0 = min(x1, x2)
          y0 = min(y1, y2)
          z0 = min(z1, z2)
          # y-z plane
          if not dx:
            self.unlink_nodes((x1,y1,z2), (x1,y2,z1))
            if x0 != self.dimention[0]:
              self.unlink_nodes((x0, y0, z0), (x0+1, y0+1, z0+1))
              self.unlink_nodes((x0+1, y0, z0), (x0, y0+1, z0+1))
              self.unlink_nodes((x0, y0+1, z0), (x0+1, y0, z0+1))
              self.unlink_nodes((x0+1, y0+1, z0), (x0, y0, z0+1))
            if x0 != 0:
              self.unlink_nodes((x0-1, y0, z0), (x0, y0+1, z0+1))
              self.unlink_nodes((x0, y0, z0), (x0-1, y0+1, z0+1))
              self.unlink_nodes((x0-1, y0+1, z0), (x0, y0, z0+1))
              self.unlink_nodes((x0, y0+1, z0), (x0-1, y0, z0+1))
          # x-z plane
          if not dy:
            self.unlink_nodes((x1,y1,z2), (x2,y1,z1))
            if y0 != self.dimention[1]:
              self.unlink_nodes((x0, y0, z0), (x0+1, y0+1, z0+1))
              self.unlink_nodes((x0+1, y0, z0), (x0, y0+1, z0+1))
              self.unlink_nodes((x0, y0+1, z0), (x0+1, y0, z0+1))
              self.unlink_nodes((x0+1, y0+1, z0), (x0, y0, z0+1))
            if y0 != 0:
              self.unlink_nodes((x0, y0-1, z0), (x0+1, y0, z0+1))
              self.unlink_nodes((x0+1, y0-1, z0), (x0, y0, z0+1))
              self.unlink_nodes((x0, y0, z0), (x0+1, y0-1, z0+1))
              self.unlink_nodes((x0+1, y0, z0), (x0, y0-1, z0+1))
          # x-y plane
          if not dz:
            self.unlink_nodes((x1,y2,z1), (x2,y1,z1))
            if z0 != self.dimention[2]:
              self.unlink_nodes((x0, y0, z0), (x0+1, y0+1, z0+1))
              self.unlink_nodes((x0+1, y0, z0), (x0, y0+1, z0+1))
              self.unlink_nodes((x0, y0+1, z0), (x0+1, y0, z0+1))
              self.unlink_nodes((x0+1, y0+1, z0), (x0, y0, z0+1))
            if z0 != 0:
              self.unlink_nodes((x0, y0, z0-1), (x0+1, y0+1, z0))
              self.unlink_nodes((x0+1, y0, z0-1), (x0, y0+1, z0))
              self.unlink_nodes((x0, y0+1, z0-1), (x0+1, y0, z0))
              self.unlink_nodes((x0+1, y0+1, z0-1), (x0, y0, z0))
        # 3D cross
        if difference == 3:
          # print(f"3D cross detected at {this_node.coord} - {next_node.coord}")
          x0 = min(x1, x2)
          y0 = min(y1, y2)
          z0 = min(z1, z2)
          # cross through center
          self.unlink_nodes((x0, y0, z0), (x0+1, y0+1, z0+1))
          self.unlink_nodes((x0+1, y0, z0), (x0, y0+1, z0+1))
          self.unlink_nodes((x0, y0+1, z0), (x0+1, y0, z0+1))
          self.unlink_nodes((x0+1, y0+1, z0), (x0, y0, z0+1))
          # half cross, but dis = 0.4
          self.unlink_nodes((x0, y0, z0), (x0, y0+1, z0+1))
          self.unlink_nodes((x0, y0, z0), (x0+1, y0, z0+1))
          self.unlink_nodes((x0, y0, z0), (x0+1, y0+1, z0))
          self.unlink_nodes((x0+1, y0, z0), (x0, y0, z0+1))
          self.unlink_nodes((x0+1, y0, z0), (x0+1, y0+1, z0+1))
          self.unlink_nodes((x0+1, y0, z0), (x0, y0+1, z0))
          self.unlink_nodes((x0, y0+1, z0), (x0, y0, z0+1))
          self.unlink_nodes((x0, y0+1, z0), (x0+1, y0+1, z0+1))
          self.unlink_nodes((x0, y0+1, z0), (x0+1, y0, z0))
          self.unlink_nodes((x0+1, y0+1, z0), (x0+1, y0, z0+1))
          self.unlink_nodes((x0+1, y0+1, z0), (x0, y0+1, z0+1))
          self.unlink_nodes((x0+1, y0+1, z0), (x0, y0, z0))

    print("All Cross Over Trimed")
    return

  # helper for cutting connections between two nodes
  def unlink_nodes(self, coord1, coord2):
    x1, y1, z1 = coord1
    x2, y2, z2 = coord2

    node1 = self.node_grid[x1][y1][z1]
    node2 = self.node_grid[x2][y2][z2]

    node1.add_block_neighbors(node2)
    node2.add_block_neighbors(node1)
    # print(f"Unlinked Node {node1.coord} and {node2.coord}") 
    return


  #####################################  junction  ###########################
  
  # kind of jump table to determin what to do
  def add_path(self, start_coord, end_coord):
    print("\n")
    print(f"Adding a new path from {start_coord} to {end_coord}")
    start_node = self.node_grid[start_coord[0]][start_coord[1]][start_coord[2]]
    end_node = self.node_grid[end_coord[0]][end_coord[1]][end_coord[2]]
    # get all the existing connection points in saved_path
    past_end_node_list = []
    for key in self.saved_path:
      past_end_node_list.append(key[0])
      past_end_node_list.append(key[1])
    
    start_node_in_list = bool(past_end_node_list.count(start_node))
    end_node_in_list = bool(past_end_node_list.count(end_node))
    
    # both new, find path
    if not (start_node_in_list or end_node_in_list):
      print(f"Both Node {start_node.coord}, {end_node.coord} are new, create new path")
      return self.path_finding(start_node.coord, end_node.coord)

    # start is existing path, flip and create junction
    if start_node_in_list and not end_node_in_list:      
      print(f"Node {start_node.coord} is end for other tubing, create junction")
      # if start is to_join(fliped), also flip is_start and path
      for key,value in self.tip_ground_table.items():
        if end_node in value:
          value[1] = True
          ground_end_path = value[2]
          fliped_end_ground_path = []
          for node in ground_end_path:
            fliped_end_ground_path.insert(0,node)
          value[2] = fliped_end_ground_path
      return self.create_junction_path(end_node.coord, start_node.coord)

    # end is existing path, create junction
    if end_node_in_list and not start_node_in_list:      
      print(f"Node {end_node.coord} is end for other tubing, create junction")
      return self.create_junction_path(start_node.coord, end_node.coord)

    # both are existing path, create bridge
    if start_node_in_list and end_node_in_list: 
      duplicate = False
      for end_point_tuple in self.saved_path:
        duplicate |= (start_node in end_point_tuple) and (end_node in end_point_tuple)
      
      if duplicate:
        print(f"Error: Path from {start_node.coord} to {end_node.coord} already exists")
        print("Nothing Added")
        return []

      print(f"Both Node {start_node.coord}, {end_node.coord} are end for other tubing, bridge two tubes")
      return self.create_bridge_path(start_node.coord, end_node.coord)



  # start node is free, end node is past_end, formated in add_path
  # return the created junction path
  # reset_grid at the end
  def create_junction_path(self, start_coord, end_coord):
    print(f"Looking for joinction path from {start_coord}(new) to {end_coord}")
    start_node = self.node_grid[start_coord[0]][start_coord[1]][start_coord[2]]
    end_node = self.node_grid[end_coord[0]][end_coord[1]][end_coord[2]]

    past_end_node_list = []
    for key in self.saved_path:
      past_end_node_list.append(key[0])
      past_end_node_list.append(key[1])
    
    if past_end_node_list.count(end_node) == 0:
      print(f"Error: End coord {end_node.coord} is not a existing path end")
      return []

    if start_node.visited:
      print(f"Error: Start Node {start_node.coord} is already in use")
      return []
    
    original_path_start_node = None
    original_path_end_node = None
    path_to_join = []
    # find the path to join in saved_path
    for key, value in self.saved_path.items():
      if end_node in key:
        original_path_start_node, original_path_end_node = key
        path_to_join = value
    if len(path_to_join) < 3:
      print(f"Error: Path {list(map(lambda a: a.coord, path_to_join))} is too short to be joined")

    # find point of junction
    distance = float("inf")
    junction_node = None
    for i,node in enumerate(path_to_join[1:-1]):
      dest_x, dest_y, dest_z = node.coord
      this_x, this_y, this_z = start_node.coord
      dis = math.sqrt((dest_x - this_x)**2 + (dest_y - this_y)**2 + (dest_z - this_z)**2) + .5*abs(len(path_to_join)/2 - i)
      if dis < distance:
        distance = dis
        junction_node = node
    print(f"Node {junction_node.coord} has the shortest distance")

    junction_node.visited = False
    new_juction_path = self.path_finding(start_node.coord, junction_node.coord)

    # this is not going to happen because we create new junction every path
    if junction_node in self.saved_junction:
      print(f"Node {junction_node.coord} is already a junction")
      self.saved_junction[junction_node].append(new_juction_path[-2])
      return new_juction_path

    connection_nodes = self.split_path((original_path_start_node, original_path_end_node), junction_node)
    start_junction_connect_node = connection_nodes[0]
    junction_end_connect_node = connection_nodes[1]
    new_jusction_connect_node = new_juction_path[-2]

    self.saved_junction[junction_node] = \
      [start_junction_connect_node, junction_end_connect_node, new_jusction_connect_node]
    print(f"Junction Added: {junction_node.coord}")
    print(f"Connection points: {[start_junction_connect_node.coord, junction_end_connect_node.coord, new_jusction_connect_node.coord]}")
    self.reset_grid()
    return new_juction_path

  
  # bridge two existing path, store result in saved_path, return bridge path
  # reset_grid at the end
  def create_bridge_path(self, start_coord, end_coord):
    print(f"Looking for bridging between path: {start_coord}(one path) to {end_coord}(another path)")
    start_node = self.node_grid[start_coord[0]][start_coord[1]][start_coord[2]]
    end_node = self.node_grid[end_coord[0]][end_coord[1]][end_coord[2]]
    
    # get the paths to bridge
    past_end_node_list = []
    for key in self.saved_path:
      past_end_node_list.append(key[0])
      past_end_node_list.append(key[1])
    if past_end_node_list.count(start_node) == 0:
      print(f"Error: End coord {start_node.coord} is not a existing path end")
      return []   
    if past_end_node_list.count(end_node) == 0:
      print(f"Error: End coord {end_node.coord} is not a existing path end")
      return []
    
    start_bridge_path = None
    end_bridge_path = None
    start_bridge_key = None
    end_bridge_key = None
    for key,value in self.saved_path.items():
      if start_node in key:
        start_bridge_path = value
        start_bridge_key = key
      if end_node in key:
        end_bridge_path = value
        end_bridge_key = key
    if start_bridge_path is end_bridge_path:
      print(f"Error: Path from {start_node.coord} to {end_node.coord} already exists")
      print("Nothing Added")   
      return []
    
    print(f"Start Node {start_node.coord} -> Path {list(map(lambda a: a.coord, start_bridge_path))}")
    print(f"End Node {end_node.coord} -> Path {list(map(lambda a: a.coord, end_bridge_path))}")
    if len(start_bridge_path) < 3 or len(end_bridge_path) < 3:
        print("Error: Path is too short to be joined")
        return []

    # find nodes to connect for bridge
    distance = float("inf")
    start_bridge_node = None
    end_bridge_node = None
    for i,from_node in enumerate(start_bridge_path[1:-1]):
      for dest_node in end_bridge_path[1:-1]:
        f_x,f_y,f_z = from_node.coord
        d_x,d_y,d_z = dest_node.coord
        dis = math.sqrt((f_x - d_x)**2 + (f_y - d_y)**2 + (f_z - d_z)**2) + .5*abs(len(start_bridge_path)/2 - i)

        if dis < distance:
          distance = dis
          start_bridge_node = from_node
          end_bridge_node = dest_node
    print(f"Node {start_bridge_node.coord} to Node {end_bridge_node.coord} has the shortest distance")

    # find path and split path
    start_bridge_node.visited = False
    end_bridge_node.visited = False
    new_bridge_path = self.path_finding(start_bridge_node.coord, end_bridge_node.coord)
    new_start_bridge_connection_node = new_bridge_path[1]
    new_end_bridge_connection_node = new_bridge_path[-2]

    start_bridge_connection_nodes = self.split_path(start_bridge_key, start_bridge_node)
    start_bridge_connection_nodes.append(new_start_bridge_connection_node)
    end_bridge_connection_nodes = self.split_path(end_bridge_key, end_bridge_node)
    end_bridge_connection_nodes.append(new_end_bridge_connection_node)
    
    self.saved_junction[start_bridge_node] = start_bridge_connection_nodes
    print(f"Junction Added: {start_bridge_node.coord}")
    print(f"Connection points: {list(map(lambda a: a.coord, start_bridge_connection_nodes))}")
    self.saved_junction[end_bridge_node] = end_bridge_connection_nodes
    print(f"Junction Added: {end_bridge_node.coord}")
    print(f"Connection points: {list(map(lambda a: a.coord, end_bridge_connection_nodes))}")
    self.reset_grid()
    return new_bridge_path



  # when a junction is created, split a path into two
  # store two new path in saved_path and remove original one
  # junction only generate on ground_ground path which is in save_path
  def split_path(self, path_key, split_node):
    print(f"Spliting path between {list(map(lambda a: a.coord, path_key))} with Node {split_node.coord}")
    start_node = path_key[0]
    end_node = path_key[1]
    path_to_split = None
    for key,value in self.saved_path.items():
      if key == path_key:
        if split_node not in value:
          print(f"Error: Split Node {split_node.coord} is not in path {list(map(lambda a: a.coord, key))}")
          return []
        path_to_split = value

    index = path_to_split.index(split_node)
    new_path_start_split = path_to_split[0:index+1]
    new_path_split_end = path_to_split[index:len(path_to_split)+1]

    self.saved_path[(start_node, split_node)] = new_path_start_split
    self.saved_path[(split_node, end_node)] = new_path_split_end 
    self.delete_path(start_node.coord, end_node.coord, True)
    start_connection_node = path_to_split[index-1]
    end_connection_node = path_to_split[index+1]
    return [start_connection_node, end_connection_node]

  
  # delete a path from saved_path
  # also handles the junction node after deleting the path
  # only used when spliting path for deleting the orginal path
  def delete_path(self, start_coord, end_coord, keep_junction = False):
    start_node = self.node_grid[start_coord[0]][start_coord[1]][start_coord[2]]
    end_node = self.node_grid[end_coord[0]][end_coord[1]][end_coord[2]]
    key_to_delete = None
    path_to_delete = None
    for key,value in self.saved_path.items():
      if start_node in key and end_node in key:
        key_to_delete = key
        path_to_delete = value

    if key_to_delete is None:
      print(f"Error: Path {start_node.coord}-{end_node.coord} don't exist in saved_path")
      return

    print(f"Deleted path from {key_to_delete[0].coord} to {key_to_delete[1].coord}")
    print(f"Path: {list(map(lambda a: a.coord, path_to_delete))}")
    self.saved_path.pop(key_to_delete)

    if not keep_junction:
      for key,value in self.saved_junction.items():
        if start_node is key:
          print(f"Start Node {start_node.coord} is a junction")
          self.delete_junction_connection(start_node, path_to_delete[1])
        if end_node is key:
          print(f"Start Node {end_node.coord} is a junction")
          self.delete_junction_connection(end_node, path_to_delete[-2])

    self.reset_grid()
    return


  def delete_junction_connection(self, junction_node, connection_node):
    print(f"Deleting junction {junction_node.coord} connection {connection_node.coord}")
    for key, value in self.saved_junction.items():
      if key is junction_node:
        if connection_node in value:
          print("Junction and Connection found")
          value.remove(connection_node)
          if len(value) < 2:
            print("Error: Junction have less than 2 connections")
            return
        print(f"Error: Connection Not Exist in connection list: {list(map(lambda a: a.coord, value))}")
        return
    print(f"Error: Junction Not Exist")






  ##################################   connect two points  ####################################

  # this will generate a path that goes to ground first, find path, and go up
  # save_path stores ground_ground path, 
  # temporary data from path_finding are removed immediately and grid reset
  # tip_ground_table stores tip_ground path
  # saved_junction stores the junction info generated
  def connect_two_node(self, start_coord, end_coord):
    print(f"\nConnecting Node {start_coord} and Node {end_coord} with default path")
    start_node = self.node_grid[start_coord[0]][start_coord[1]][start_coord[2]]
    end_node = self.node_grid[end_coord[0]][end_coord[1]][end_coord[2]]
    
    direction_sign_x = (end_node.coord[0] - start_node.coord[0]) > 0
    direction_sign_y = (end_node.coord[1] - start_node.coord[1]) > 0
    dir_x = 2*direction_sign_x - 1
    dir_y = 2*direction_sign_y - 1

    start_ground_node = None
    end_ground_node = None
    start_ground_node_is_new = False
    end_ground_node_is_new = False
    # if already in table, use that, else create one
    if start_node in self.tip_ground_table:
      print(f"Start Node {start_node.coord} is already in tip_ground_table")
      start_ground_node = self.tip_ground_table[start_node][0]
    else:
      start_ground_node = self.find_ground_node(start_node, dir_x, dir_y)
      start_ground_path = self.path_finding(start_node.coord, start_ground_node.coord)
      self.saved_path.pop((start_node, start_ground_node))
      self.reset_grid()
      print(f"Start-Ground path from {start_node.coord} to {start_ground_node.coord} is: {list(map(lambda a: a.coord, start_ground_path))}")
      self.tip_ground_table[start_node] = [start_ground_node, True, start_ground_path]
      start_ground_node_is_new = True
    
    if end_node in self.tip_ground_table:
      end_ground_node = self.tip_ground_table[end_node][0]
      print(f"End Node {end_node.coord} is already in tip_ground_table")
    else:
      end_ground_node = self.find_ground_node(end_node, -dir_x, -dir_y)
      ground_end_path_inverse = self.path_finding(end_node.coord, end_ground_node.coord)
      self.saved_path.pop((end_node, end_ground_node))
      self.reset_grid()
      ground_end_path = []
      for node in ground_end_path_inverse:
        ground_end_path.insert(0, node)
      print(f"Ground_End path from {end_ground_node.coord} to {end_node.coord} is: {list(map(lambda a: a.coord, ground_end_path))}")
      self.tip_ground_table[end_node] = [end_ground_node, False, ground_end_path]
      end_ground_node_is_new = True

    # if new, mark not visited
    # if old, mark visited to avoid collision
    if start_ground_node_is_new:
      start_ground_node.visited = False
    if end_ground_node_is_new:
      end_ground_node.visited = False
    # this handles all the conditions of new path, merge path, or bridge path
    ground_ground_path = self.add_path(start_ground_node.coord, end_ground_node.coord)

    print(f"Ground-Ground path from {start_ground_node.coord} to {end_ground_node.coord} is: {list(map(lambda a: a.coord, ground_ground_path))}")



  def is_visited(self, coord):
    try:
      node = self.node_grid[coord[0]][coord[1]][coord[2]]
    except IndexError:
      print(f"Error: Node {coord} is out of bound")
      return True
    return node.visited

  # given a node, return the ground node
  def find_ground_node(self, node, dir_x, dir_y):
    print(f"Looking for ground node for Node {node.coord} with dir_x = {dir_x}, dir_y = {dir_y}")
    ground_node = self.node_grid[node.coord[0]][node.coord[1]][0]
    while ground_node.visited:
      if self.is_visited((ground_node.coord[0]+dir_x, ground_node.coord[1], ground_node.coord[2])):
        if self.is_visited((ground_node.coord[0]+dir_x, ground_node.coord[1]+dir_y, ground_node.coord[2])):
          if self.is_visited((ground_node.coord[0], ground_node.coord[1]+dir_y, ground_node.coord[2])):
            ground_node = self.node_grid[ground_node.coord[0]][ground_node.coord[1]][ground_node.coord[2]+1]
            continue
          ground_node = self.node_grid[ground_node.coord[0]][ground_node.coord[1]+dir_y][ground_node.coord[2]]
          break
        ground_node = self.node_grid[ground_node.coord[0]+dir_x][ground_node.coord[1]+dir_y][ground_node.coord[2]]
        break
      ground_node = self.node_grid[ground_node.coord[0]+dir_x][ground_node.coord[1]][ground_node.coord[2]]
      break
    print(f"Found ground Node {ground_node.coord} for Node {node.coord}")
    return ground_node

  # a collection of all connections, combine path like start_ground and ground_ground
  def update_connection_dict(self):
    self.connection_dict.clear()
    self.connection_dict.update(self.saved_path)

    for key,value in self.tip_ground_table.items():
      tip_node = key
      ground_node = value[0]
      is_start = value[1]
      tip_ground_path = value[2]
      whole_path = []

      for path_key, path_value in self.saved_path.items():

        if ground_node in path_key:

          if path_key not in self.connection_dict:  # one to one path, no junction, so already removed by the other end
            print(f"Path starting at Node {tip_node.coord} have no merge/junction")
            for connection_key, connection_value in self.connection_dict.items():
              if ground_node in connection_key:
                ground_path = connection_value
                self.connection_dict.pop(connection_key)
                if is_start:
                  whole_path.extend(tip_ground_path)
                  whole_path.extend(ground_path[1:])
                  print(f"Retreved whole path: {tip_node.coord}-{ground_path[-1].coord}, path: {list(map(lambda a: a.coord, whole_path))}")
                  self.connection_dict[(tip_node, ground_path[-1])] = whole_path
                  break
                else:
                  whole_path.extend(ground_path)
                  whole_path.extend(tip_ground_path[1:])
                  print(f"Retreved whole path: {ground_path[-1].coord}-{tip_node.coord}, path: {list(map(lambda a: a.coord, whole_path))}")
                  self.connection_dict[(ground_path[0], tip_node)] = whole_path
                  break
            
            if len(ground_path) == 0:
              print(f"Error: Can't find ground path of path_key {list(map(lambda a: a.coord, path_key))}")
          else:
            # try:
            self.connection_dict.pop(path_key)
            # except KeyError:
            #   pass
            ground_path = path_value

            if is_start:
              whole_path.extend(tip_ground_path)
              whole_path.extend(ground_path[1:])
              print(f"Retreved whole path: {tip_node.coord}-{ground_path[-1].coord}, path: {list(map(lambda a: a.coord, whole_path))}")
              self.connection_dict[(tip_node, ground_path[-1])] = whole_path
              break
            else:
              whole_path.extend(ground_path)
              whole_path.extend(tip_ground_path[1:])
              print(f"Retreved whole path: {ground_path[-1].coord}-{tip_node.coord}, path: {list(map(lambda a: a.coord, whole_path))}")
              self.connection_dict[(ground_path[0], tip_node)] = whole_path
              break
      if len(whole_path) == 0:
        print(f"Error: Can't retreve whole path for tip Node {tip_node.coord}")

    path_num = len(self.saved_path)
    connection_num = len(self.connection_dict)
    if path_num != connection_num:
      print("Error: Connection_dict Not updated correctly")
      return

    print("Connection_dict updated successfully")
    self.smooth_out_path()

  # eliminate useless sharp turns, only affect connection_dict
  def smooth_out_path(self):
    for key,value in self.connection_dict.items():
      this_path = value
      to_remove_list = []
      for i,node in enumerate(this_path[1:-1]):
        last_node = this_path[i]
        next_node = this_path[i+2]

        if last_node.coord[2] == next_node.coord[2] and \
          abs(last_node.coord[1] - next_node.coord[1]) < 2 and \
            abs(last_node.coord[0] - next_node.coord[0]) < 2:
            to_remove_list.append(node)
            # move connection for junction if affected
            if last_node in self.saved_junction:
              connection_list = self.saved_junction[last_node]
              connection_list.remove(node)
              connection_list.append(next_node)
            if next_node in self.saved_junction:
              connection_list = self.saved_junction[next_node]
              connection_list.remove(node)
              connection_list.append(last_node)

      for node in to_remove_list:
        this_path.remove(node)

        print(f"Smoothed Node {node.coord} out of Path {list(map(lambda a: a.coord, key))}")
      self.connection_dict[key] = this_path
          


  def print_saved_path(self):
    print("\n")
    for key, value in self.saved_path.items():
      print("Saved Path:")
      print(f"{list(map(lambda a: a.coord, key))} : {list(map(lambda a: a.coord, value))}")

  def print_saved_junction(self):
    print("\n")
    for key,value in self.saved_junction.items():
      end_connection_list = value
      print(f"Junction: {key.coord}")
      print(f"Connection points: {list(map(lambda a: a.coord, end_connection_list))}")

  def print_tip_ground_table(self):
    print("\n")
    for key,value in self.tip_ground_table.items():
      tip_node = key
      ground_node = value[0]
      is_start = value[1]
      path = value[2]
      print(f"Tip: {tip_node.coord}, Ground: {ground_node.coord}, is_start = {is_start}")
      print(f"Path: {list(map(lambda a: a.coord, path))}")

  def print_connection_dict(self):
    print("\n")
    for key, value in self.connection_dict.items():
      print("Connection:")
      print(f"{list(map(lambda a: a.coord, key))} : {list(map(lambda a: a.coord, value))}")












# test algorithm by making make-shift tube and junction
class test_path_finding():

  def __init__(self, grid):
    self.grid = grid

  def make_pipe(self, name, dot_list):
    if (len(dot_list) < 2):
      print(f"Dot list {dot_list} too short")
      return

    curve_data = bpy.data.curves.new(name, type = "CURVE")
    curve_data.dimensions = "3D"

    polyline = curve_data.splines.new("POLY")
    polyline.points.add(len(dot_list)-1)
    for i, coord in enumerate(dot_list):
      x,y,z = coord
      polyline.points[i].co = (x,y,z,1)
    
    curve_object = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(curve_object)

    curve_object.data.bevel_depth = .2
    curve_object.data.bevel_resolution = 2

    curve_object.modifiers.new("Solidify", "SOLIDIFY").thickness = .1



  def make_junction(self, coord, connection_list):
    bpy.ops.mesh.primitive_cube_add(size = .7)
    cube = bpy.context.active_object
    cube.location = coord
    for connection in connection_list:
      bpy.ops.mesh.primitive_cube_add(size = 1)
      connection_cube = bpy.context.active_object
      connection_cube.location = tuple(map(lambda a,b: a+.25*(b-a), coord, connection))
      connection_cube.scale = (.5,.5,.5)



  def make_everything(self):
    pipe_list = []
    junction_list = []

    for key,value in self.grid.connection_dict.items():
      this_pipe = list(map(lambda a: a.coord, value))
      pipe_list.append(this_pipe)
    
    for key,value in self.grid.saved_junction.items():
      this_junction = [key.coord, list(map(lambda a: a.coord, value))]
      junction_list.append(this_junction)

    for i,pipe in enumerate(pipe_list):
      self.make_pipe(f"Pipe{i}", pipe)
    
    for i,junction_struct in enumerate(junction_list):
      self.make_junction(junction_struct[0], junction_struct[1])








# Disable
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore
def enablePrint():
    sys.stdout = sys.__stdout__




if __name__ == '__main__':

  bpy.ops.object.select_all(action='SELECT')
  bpy.ops.object.delete(use_global=False)


  # blockPrint()
  # node = Node((1,2),(1,3))
  grid = Grid((20,20,5))
  # print(node)
  # print(node.coord)
  # print(node.neighbors)

  # path1 = grid.add_path((0,0,0),(0,20,0))
  # path2 = grid.add_path((20,20,0),(20,0,0))
  # path3 = grid.add_path((1,15,5),(12,7,3))
  # path4 = grid.add_path((1,0,1),(14,10,0))
  # path5 = grid.add_path((6,0,0),(1,15,5))
  # path6 = grid.add_path((6,0,0),(20,20,0))
  # path7 = grid.add_path((6,18,2),(20,10,0))
  # path8 = grid.add_path((7,17,4),(20,20,0))
  # path9 = grid.add_path((0,10,0),(10,20,0))
  # path10 = grid.add_path((20,0,0),(20,20,0))
  # path11 = grid.add_path((0,0,0), (20,0,0))
  # grid.delete_path((0,1,0), (10,1,0))

  grid.connect_two_node((15,10,2), (0,10,3))
  grid.connect_two_node((2,13,3),(15,10,2))
  grid.connect_two_node((4,3,4), (0,10,3))
  grid.connect_two_node((0,9,3),(15,9,3))
  grid.connect_two_node((1,10,5), (20,10,3))
  grid.connect_two_node((5,9,3),(12,9,5))
  grid.connect_two_node((6,9,4),(11,9,5))
  grid.connect_two_node((7,9,5),(10,9,5))
  grid.connect_two_node((0,0,5), (10,10,5))
  grid.connect_two_node((8,11,5),(12,0,5))
  grid.connect_two_node((16,11,5),(12,0,5))
  grid.connect_two_node((0,0,5), (12,0,5))
  grid.connect_two_node((4,3,4), (0,0,5))
  grid.connect_two_node((4,3,4), (12,0,5))
  grid.connect_two_node((4,3,4), (3,0,5))
  grid.connect_two_node((12,0,5), (6,1,4))
  grid.connect_two_node((15,10,2), (6,1,4))
  grid.connect_two_node((20,10,3), (6,1,4))
  grid.connect_two_node((0,10,3), (6,1,4))




  # grid.connect_two_node((0,0,3), (10,10,4))
  # grid.connect_two_node((10,10,4), (6,1,4))
  # grid.connect_two_node((0,10,3), (10,10,4))
  # grid.connect_two_node((5,10,3), (0,0,3))


  # path = grid.path_finding((11,9,0),(12,10,5))
  # path_coord = list(map(lambda a: a.coord, path))
  # make_pipe("p", path_coord)

  grid.update_connection_dict()

  grid.print_saved_path()
  grid.print_saved_junction()
  grid.print_tip_ground_table()
  grid.print_connection_dict()

  test = test_path_finding(grid)
  test.make_everything()


