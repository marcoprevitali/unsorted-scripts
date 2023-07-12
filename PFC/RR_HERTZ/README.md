12/07/2023
Marco Previtali

Coverted the old Hertzian model with rolling resistance to PFC7. The debug example seems to work (4 spheres with linear and hertizan model, 2 with rolling resistance and 2 without, are pushed on a plane)

If you have never used a PFC dll plug-in, have a look at the Debug folder (PluginFiles\contactmodel\example\x64\Debug), where the project debug_rr_hertz.prj shows how to use it:

1. Copy the dll file in the problem folder (technically you can copy it in some specific Itasca installation folder to make it available for every project but I prefer having it only in a folder if I need to make changes).

2. In the code, type: "program load contactmodelmechanical 'the name of the dll.dll'"
In this case: "program load contactmodelmechanical 'contactmodelmechanical3d_rr_hertz_07.dll'". You can for example see this in the 4th line of the "comparison_rolling_resistance.dat" file.

3. assign the contact properties, etc.. as you would with any project

Note that the dll is loaded in the project the first time the "program load contactmodelmechanical" command is issued. If the project is saved, it will consider the dll as "already loaded" the next time the script is called. This means that if you're debugging the dll as shown in the video, it might not try to reload it and you need to close PFC and create a new project to actually load the dll.

https://youtu.be/TZUDU_Ggcxg

The source code and project setup are in
"PluginFiles\contactmodel\example"

The debug dll and project are located in:
"PluginFiles\contactmodel\example\x64\Debug", while the Release version of the dll in:  "PluginFiles\contactmodel\example\x64\Release".
The two dlls have the same code, but the debug version is not optimized by the compiler and therefore it is possible to look at the variable from the visual studio debug screen. If you don't want to modify the model, just use the Release version as it should be slightly more efficient.

I don't think the rest of the PluginFiles folder is needed but I kept it just in case it contains dependencies for the contact model code.
