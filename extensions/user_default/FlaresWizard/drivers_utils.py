# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy

# Add property variable for the driver
def add_prop_var(driver, name, id_type, id, path):
    var = driver.driver.variables.new()
    var.name = name
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = id_type
    var.targets[0].id = id
    var.targets[0].data_path = path
    
# Flare property path
def flare_prop_path(flare, prop):
    flare_path = 'fw_group.coll["' + flare.name + '"].'
    return  flare_path + prop

# Element property path
def element_prop_path(element, flare, prop):
    flare_path = 'fw_group.coll["' + flare.name + '"].'
    element_path = flare_path + 'elements["' + element.name + '"].'
    return element_path + prop

# add a driver with a single property
def add_driver(src, prop_path, var_name, id_type, id, path, expression, idx = -1, length = 0):
    n = 1 if length == 0 else length
    for i in range(n):
        idx = idx if length == 0 else i
        p = path if length == 0 else path + '['+str(i)+']'
        src.driver_remove(prop_path, idx)
        driver = src.driver_add(prop_path, idx)
        add_prop_var(driver, var_name, id_type, id, p)
        driver.driver.expression = expression