#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#   Region Fixer.
#   Fix your region files with a backup copy of your Minecraft world.
#   Copyright (C) 2011  Alejandro Aguilera (Fenixin)
#   https://github.com/Fenixin/Minecraft-Region-Fixer
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import nbt.region as region
import nbt.nbt as nbt
from glob import glob
from os.path import join, split, exists, getsize

class World(object):
    """ Stores all the info needed of a world, and once scanned, stores
    all the problems found """
    
    def __init__(self, world_path):
        self.world_path = world_path
        self.normal_mcr_files = glob(join(self.world_path, "region/r.*.*.mcr"))
        self.nether_mcr_files = glob(join(self.world_path,"DIM-1/region/r.*.*.mcr"))
        self.all_mcr_files = self.normal_mcr_files + self.nether_mcr_files
        
        self.level_file = join(self.world_path, "level.dat")
        self.level_status = {}
        
        self.player_files = glob(join(join(self.world_path, "players"), "*.dat"))
        self.players_status = {}
        self.player_problems = []
        
        self.mcr_problems = {}
        
        # Constants
        self.OK = 0
        self.CORRUPTED = 1
        self.WRONG_LOCATED = 2
        self.TOO_MUCH_ENTITIES = 3
    
    def count_problems(self, problem):
        counter = 0
        for region in self.mcr_problems:
            for chunk in self.mcr_problems[region]:
                for prob in self.mcr_problems[region][chunk]:
                    if prob == problem:
                        counter += 1
        return counter

def get_global_chunk_coords(region_filename, chunkX, chunkZ):
    """ Takes the region filename and the chunk local 
    coords and returns the global chunkcoords as integerss """
    
    regionX, regionZ = get_region_coords(region_filename)
    chunkX += regionX*32
    chunkZ += regionZ*32
    
    return chunkX, chunkZ

def get_chunk_region(chunkX, chunkZ):
    """ Returns the name of the region file given global chunk coords """
    
    regionX = chunkX / 32
    regionZ = chunkZ / 32
    
    region_name = 'r.' + str(regionX) + '.' + str(regionZ) + '.mcr'
    
    return region_name
    

def get_region_coords(region_filename):
    """ Splits the region filename (full pathname or just filename)
        and returns his region coordinates.
        Return X and Z coords as integers. """
    
    splited = split(region_filename)
    filename = splited[1]
    list = filename.split('.')
    coordX = list[1]
    coordZ = list[2]
    
    return int(coordX), int(coordZ)
    
def get_chunk_data_coords(nbt_file):
    """ Gets the coords stored in the NBT structure of the chunk.
        Takes an nbt obj and returns the coords as integers.
        Don't confuse with get_global_chunk_coords! """
    
    level = nbt_file.__getitem__('Level')
            
    coordX = level.__getitem__('xPos').value
    coordZ = level.__getitem__('zPos').value
    
    return coordX, coordZ

def delete_chunk_list(list):
    """ Takes a list generated by check_region_file and deletes
    all the chunks on it and returns the number of deleted chunks"""
    
    region_file = region_path = None # variable inizializations
    
    counter = 0
    for chunk in list:
        x = chunk[1]
        z = chunk[2]
        
        region_path = chunk[0]
        region_file = region.RegionFile(region_path)
        region_file.unlink_chunk(x, z)
        counter += 1
        region_file.__del__
    
    return counter

def replace_chunk_list(list, backup_list):

    unfixed_list = []
    unfixed_list.extend(list)

    counter = 0

    for corrupted_chunk in list:
        x = corrupted_chunk[1]
        z = corrupted_chunk[2]

        print "\n{0:-^60}".format(' New chunk to fix! ')

        for backup in backup_list:
            Fixed = False
            region_file = split(corrupted_chunk[0])[1]

            # search for the region file
            backup_region_path = glob(join(backup, region_file))[0]
            region_file = corrupted_chunk[0]
            if backup_region_path:
                print "Backup region file found in: {0} \nfixing...".format(backup_region_path)

                # get the chunk
                backup_region_file = region.RegionFile(backup_region_path)
                working_chunk = check_chunk(backup_region_file, x, z)
                backup_region_file.__del__()
                
                if isinstance(working_chunk, nbt.TAG_Compound):
                    # the chunk exists and is non-corrupted, fix it!
                    tofix_region_file = region.RegionFile(region_file)
                    #~ print corrupted_chunk[1],corrupted_chunk[2],working_chunk
                    #~ print type(corrupted_chunk[1]),type(corrupted_chunk[2]),type(working_chunk)
                    tofix_region_file.write_chunk(corrupted_chunk[1], corrupted_chunk[2],working_chunk)
                    tofix_region_file.__del__
                    Fixed = True
                    counter += 1
                    unfixed_list.remove(corrupted_chunk)
                    print "Chunk fixed using backup dir: {0}".format(backup)
                    break
                    
                elif working_chunk == None:
                    print "The chunk doesn't exists in this backup directory: {0}".format(backup)
                    # The chunk doesn't exists in the region file
                    continue
                    
                elif working_chunk == -1:
                    # The chunk is corrupted
                    print "The chunk is corrupted in this backup directory: {0}".format(backup)
                    continue
                    
                elif working_chunk == -2:
                    # The chunk is corrupted
                    print "The chunk is wrong located in this backup directory: {0}".format(backup)
                    continue
    
    return unfixed_list, counter
