# Python Script, API Version = V20 Beta
# Copyright (C) 2020 ANSYS, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

# Python Script, API Version = V20 Beta

import csv
import clr
from SPEOS_scripts.SpaceClaimCore.base import BaseSCDM


class MaterialsFromCSV(BaseSCDM):
    def __init__(self, SpeosSim, SpaceClaim):
        super(MaterialsFromCSV, self).__init__(SpaceClaim, ["V19", "V20"])
        self.speos_sim = SpeosSim

    def __get_real_original(self, item):
        """
        get the real original selection in order to get the material info
        para item: input SCDM part
        """
        result = item
        while self.GetOriginal(result):
            result = self.GetOriginal(result)
        return result

    def __create_material_dictionary(self):
        """
        create a dictionary from the whole project
        return: a dictionary according to material info
        """
        dict = {}
        root_part = self.GetRootPart()
        all_body = self.PartExtensions.GetAllBodies(root_part)
        for ibody in all_body:
            body = self.__get_real_original(ibody)
            try:
                if body.Material.Name not in dict:
                    dict[body.Material.Name] = self.List[self.IDesignBody]()
                dict[body.Material.Name].Add(ibody)
            except:
                print("Do nothing")
        return dict

    def apply_geo_to_material(self):
        """
        according to the material info, geometries are then applied to OP
        """
        op_list = {}
        all_op = self.GetRootPart().CustomObjects
        for item in all_op:
            op_list[item.Name] = self.List[self.IDesignBody]()

        material_dict = self.__create_material_dictionary()
        for item in material_dict:
            if item in op_list:
                op = self.Selection.CreateByNames(item).Items[0]
                try:
                    op = clr.Convert(op, self.speos_sim.Material)
                    my_selection = self.Selection.Create(material_dict[item])
                    op.VolumeGeometries.Set(my_selection)
                except:
                    print("Not an Optical property")
            else:
                op_created = self.speos_sim.Material.Create()
                op_created.Name = item
                sel = self.Selection.Create(material_dict[item])
                op_created.VolumeGeometries.Set(sel)

    def get_total_layers(self):
        """
        get the total layers as a list from the whole project
        return a list of layers' name
        """
        layer_list = []
        active_doc = self.GetActiveDocument()
        total_layers = active_doc.Layers
        for layer in total_layers:
            layer_list.append(layer.Name)
        return layer_list

    def apply_geo_to_layer(self):
        """
        according to material info, geometries are then applied to corresponding layers
        """
        layer_list = self.get_total_layers()
        geo_dic = self.__create_material_dictionary()

        for item in geo_dic:
            sel = self.Selection.Create(geo_dic[item])
            if item in layer_list:
                self.Layers.MoveTo(sel, item)
            else:
                self.__create_layer(item)
                layer_list.append(item)
                self.Layers.MoveTo(sel, item)

    def __create_layer(self, op_name):
        """
        create a new layer with a given name
        para op_name: string given to create a layer
        """
        active_doc = self.GetActiveDocument()
        nb_layer = active_doc.Layers.Count
        try:
            active_doc.Layers[nb_layer - 1].Create(active_doc, op_name, self.Color.Empty)
        except:
            print("there is a layer with same name")

    def __create_op(self, fop_name, op_name, sop_name, vop_name, work_directory):
        """
        create a OP according to the given parameters
        para fop_name: name of FOP from CSV
        para sop_name: name of SOP from CSV
        para vop_name: name of VOP from CSV
        para work_directory: file directory from CSV
        """
        if self.speos_sim.Material.Find(op_name) is None:
            material = self.speos_sim.Material.Create()
            material.Name = op_name
            if fop_name == "True":
                material.OpticalPropertiesType = self.speos_sim.Material.EnumOpticalPropertiesType.Surfacic
            else:
                material.OpticalPropertiesType = self.speos_sim.Material.EnumOpticalPropertiesType.Volumic
                if "Opaque" in vop_name:
                    material.VOPType = self.speos_sim.Material.EnumVOPType.Opaque
                elif "Optic" in vop_name:
                    material.VOPType = self.speos_sim.Material.EnumVOPType.Optic
                else:
                    material.VOPType = self.speos_sim.Material.EnumVOPType.Library
                    material.VOPLibrary = work_directory + "SPEOS input files\\" + vop_name

            if "Mirror" in sop_name:
                material.SOPType = self.speos_sim.Material.EnumSOPType.Mirror
                start = sop_name.find("Mirror") + 6
                value = int(sop_name[start:])
                material.SOPReflectance = value
            elif "Optical Polished" in sop_name:
                material.SOPType = self.speos_sim.Material.EnumSOPType.OpticalPolished
            else:
                material.SOPType = self.speos_sim.Material.EnumSOPType.Library
                material.SOPLibrary = work_directory + "SPEOS input files\\" + sop_name

    def create_speos_material(self, csv_path, work_directory):
        """
        to read a given CSV, and create OP according
        """
        # work_directory  = "D:\#ANSYS SPEOS_Concept Proof\API Scripts\ASP_MaterialFromCsv"
        with open(csv_path) as myfile:
            reader = csv.reader(myfile)
            for line in reader:
                print(line)
                if ("End" not in line) and ("Materialname " not in line):
                    op_name = line[0].rstrip()
                    fop_name = line[1]
                    vop_name = line[2]
                    sop_name = line[3]
                    self.__create_layer(op_name)
                    self.__create_op(fop_name, op_name, sop_name, vop_name, work_directory)

