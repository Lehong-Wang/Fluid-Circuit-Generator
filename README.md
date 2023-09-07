

# Fluid Circuit Generator

This prject is a Blender addon tool to automatically generate tubing network for fludic circuits.

## Requirements

* [Blender version 3.2](https://www.blender.org/download/)


## Installation

* Download this repository. 
  * What you need is the fluid_circuit_generator.zip file. You can discard the rest.
  * DO NOT unzip the file. Blender will automatically extract the contents when it installs addons.
* In Blender, go to Edit -> Preferences -> Add-ons
  * This window manages the addons installed in your Blender
* Click the install button on the top of this popup window, navigate to the fluid_circuit_generator.zip file and click Install Add-on.
* The installed addon should be shown, enable the addon by checking the check box. By this point, you should be able to start using the Fluid Circuit Generator.

![](pictures/enable_addon.png)
* At this point, there should be a new tab showing up on the side bar. If you don't see a side bar, press "N".

![](pictures/side_bar.png)


## Instructions

1. In the Main Panel, "Reset Addon" button should be pressed after each finalized assembly is generated and before you make a new one. It deletes everything.
2. In the Add Component Panel, you can choose to add a component for your circuit. Choose what you want to add and press the "Add Object" Button.
    * Currently, we have Logic Gate and Free End (outlets to air).
    * Logic Gates needs to have a stl file and a json file with the same name. There is a sample Logic Gate Library provided within the addon.
    * You can move, rotate and scale the selected object with this panel. You can also use default Blender operations to manuver the objects. There is a simple cheat sheet of basic Blender operations below.
3. In the Add Connection Panel, you can add connections between components.
    * Choose the component object with the eyedrop or drop down. Choose the port if applicable. Click again to deselect port.
    * Every row is a connection. To delete a connection, cross out both selections on that row.
4. In the Tubing Properties Panel, you can costumize your tubing.
    * First column is the basic properties. Unit length means the resolution / density of tubing routing. 
      * Usually you don't need to adjust this. Larger unit length gives you faster performance and premits larger tubing diameter. However, it could also cause the system to not be able to route dense tubing.
    * Second column if enabled adds a staging block under each logic gate conponent.
    * Third column adds a costum tip to each tip of the tubing. 
      * Costum tip is appended to the very top of the tubing, and offset moves the costum tip down
      * To make your own costum tip, refer to the sample costum tip in the Gate_Library folder in the zip file.
    * After you adjust the properties, press the Make Preview Tubing button to make a preview.
5. In the Generate Assembly Panel, you check your connections and make the final module
    * Press the Preview Conneciton button to visualize the connections you made. You can still edit your connection in this step. Preview is refreshed after you hide the preview.
    * If everything looks correct, click Confirm Changes
    * WARNING: The Generate Assembly operation is NOT reversible! Please make sure everything looks correct before you generate the final module.
    * NOTE: Ctrl+Z won't redo the changes correctly, and will cause wield errors.
    * If the final module is not what you want, you NEED to start over by pressing the Reset Addon Button at the top.
    * If you press the Generate Assembly button and an error message pop up, please read the error message and make changes accordingly. 
6. In the Calculate Propergation Delay Panel, you can calculate theoretical propergation delay in the system.
    * This panel is only functional once you generate the final module.
    * Select the port in the same way you choose the connections.
7. In the Set Group Visibility Panel, you can hide part of the final module.
    * It's mostly for convinience when you want to export the final module.
    * To export the final module, use this panel to hide thing you don't want to export.
      * Press "A" to select all visible objects.
      * Go to File -> Export -> Stl
      * Remember to check the Selection Only on the right of the popup window.
      * Choose your export location and export.


## Blender Operation Cheat Sheet

| Key | Description |
|---|---|
| A | Select all visible objects |
| X | Delete selected object |
| N | Show/Hide side bar |
| G | Grab/Move selected object |
| R | Rotate selected object |
| S | Scale selected object |
| Tab | Object/Edit mode |

For more detailed information on Blender Hotkeys, visit this 
[website](https://www.dummies.com/article/technology/software/animation-software/blender/blender-for-dummies-cheat-sheet-208646/).




