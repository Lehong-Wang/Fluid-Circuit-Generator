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

      # dictionary of all the path 
      # {(start_node, end_node) : path_node_list}
      self.saved_path = {}

      self.saved_junction = {}

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
    path_coord_list = []

    while this_node is not start_node:
      path_node_list.insert(0, this_node)
      this_node = this_node.last_visited
    path_node_list.insert(0, start_node)

    self.saved_path[(start_node, end_node)] = path_node_list
    self.reset_grid()
    for node in path_node_list:
      path_coord_list.append(node.coord)
    print(f"Path: {path_coord_list}")

    return path_node_list


  #########################################  clean up  ############################################

  # reset grid for next path finding
  def reset_grid(self):
    for x in range(len(self.node_grid)):
      for y in range(len(self.node_grid[x])):
        for z in range(len(self.node_grid[x][y])):
          self.node_grid[x][y][z].reset_node()

    for key, value in self.saved_path.items():
      this_saved_path = value
      for node in this_saved_path:
        node.visited = True
        # print(f"Node {node.coord} is visited")
    self.cut_all_crossover()
    print(f"Grid Reset")


  def delete_path(self, start_coord, end_coord):
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

    past_end_node_list = []
    for key in self.saved_path:
      past_end_node_list.append(key[0])
      past_end_node_list.append(key[1])
    
    start_node_in_list = bool(past_end_node_list.count(start_node))
    end_node_in_list = bool(past_end_node_list.count(end_node))

    if not (start_node_in_list or end_node_in_list):
      print(f"Both Node {start_node.coord}, {end_node.coord} are new, create new path")
      return self.path_finding(start_node.coord, end_node.coord)

    if start_node_in_list and not end_node_in_list:      
      print(f"Node {start_node.coord} is end for other tubing, create junction")
      return self.create_junction_path(end_node.coord, start_node.coord)

    if end_node_in_list and not start_node_in_list:      
      print(f"Node {end_node.coord} is end for other tubing, create junction")
      return self.create_junction_path(start_node.coord, end_node.coord)

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



  # start node is free, end node is past_end
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
    for key, value in self.saved_path.items():
      if end_node in key:
        original_path_start_node, original_path_end_node = key
        path_to_join = value
    if len(path_to_join) < 3:
      print(f"Error: Path {list(map(lambda a: a.coord, path_to_join))} is too short to be joined")

    distance = float("inf")
    junction_node = None
    for node in path_to_join[1:-1]:
      dest_x, dest_y, dest_z = node.coord
      this_x, this_y, this_z = start_node.coord
      dis = math.sqrt((dest_x - this_x)**2 + (dest_y - this_y)**2 + (dest_z - this_z)**2)
      if dis < distance:
        distance = dis
        junction_node = node
    print(f"Node {junction_node.coord} has the shortest distance")

    junction_node.visited = False
    new_juction_path = self.path_finding(start_node.coord, junction_node.coord)

    # this is not going to happen because we create new path every junction
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
    return new_juction_path

  

  def create_bridge_path(self, start_coord, end_coord):
    print(f"Looking for bridging between path: {start_coord}(one path) to {end_coord}(another path)")
    start_node = self.node_grid[start_coord[0]][start_coord[1]][start_coord[2]]
    end_node = self.node_grid[end_coord[0]][end_coord[1]][end_coord[2]]

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

    distance = float("inf")
    start_bridge_node = None
    end_bridge_node = None
    for from_node in start_bridge_path[1:-1]:
      for dest_node in end_bridge_path[1:-1]:
        f_x,f_y,f_z = from_node.coord
        d_x,d_y,d_z = dest_node.coord
        dis = math.sqrt((f_x - d_x)**2 + (f_y - d_y)**2 + (f_z - d_z)**2)
        if dis < distance:
          distance = dis
          start_bridge_node = from_node
          end_bridge_node = dest_node
    print(f"Node {start_bridge_node.coord} to Node {end_bridge_node.coord} has the shortest distance")

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
    return new_bridge_path




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
    self.delete_path(start_node.coord, end_node.coord)
    start_connection_node = path_to_split[index-1]
    end_connection_node = path_to_split[index+1]
    return [start_connection_node, end_connection_node]

  









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
  grid = Grid((10,10,5))
  # print(node)
  # print(node.coord)
  # print(node.neighbors)

  path1 = grid.add_path((0,0,0),(0,10,0))
  path2 = grid.add_path((10,10,0),(10,0,0))
  # path3 = grid.add_path((10,0,0),(3,10,0))
  # path4 = grid.add_path((1,0,1),(4,10,0))
  # path5 = grid.add_path((6,0,0),(1,10,5))
  # path6 = grid.add_path((6,0,0),(10,10,0))
  # path7 = grid.add_path((6,8,2),(10,10,0))
  # path8 = grid.add_path((7,7,0),(10,10,0))
  # path9 = grid.add_path((0,10,0),(10,10,0))
  # path10 = grid.add_path((10,0,0),(10,10,0))
  path11 = grid.add_path((0,0,0), (10,0,0))
  grid.delete_path((0,1,0), (10,1,0))

  # do bottom -> top


  # enablePrint()

  # print(grid.node_grid[6][4][0].coord)
  # print(grid.node_grid[6][4][0].neighbors)
  # print(grid.node_grid[5][5][1].neighbors)

  # print(grid.saved_path)

  print("\n")
  path = grid.saved_path
  for key, value in path.items():
    path_coord = []
    key_coord = []
    for node in value:
      path_coord.append(node.coord)
    for node in key:
      key_coord.append(node.coord)
    print("Saved Path:")
    print(key_coord,":", path_coord)
  
  for key,value in grid.saved_junction.items():
    end_connection_list = value
    print("\n")
    print(f"Junction: {key.coord}")
    # print(f"End Nodes: {list(map(lambda a: a.coord, end_node_list))}")
    print(f"Connection points: {list(map(lambda a: a.coord, end_connection_list))}")
  
  # print(grid.saved_path)


    
