"""
*
* The foo application.
*
* Copyright (C) 2025 Yarrawonga VIC woodvisualizations@gmail.com
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program.  If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.
*
"""

from . import editorPaths

import os
import re
from pathlib import Path


class FilePathHelper:
    """Helper class for file path operations, including versioning."""

    def __init__(self, filePath):
        self.filePath = filePath
        self.exists = os.path.exists(self.filePath)

    def versionUp(self):
        """
        Increments the version number in the filename.
        """
        return self._updateVersion(1)

    def versionDown(self):
        """
        Decrements the version number in the filename.
        """
        return self._updateVersion(-1)

    def setVersion(self, newVersion):
        """
        Sets a specific version number in the filename.
        """
        return self._updateVersion(newVersion)
    
    def extractVersion(self) -> str:
        match = re.search(r"[\\/](v\d{3})[\\/]", self.filePath, re.IGNORECASE)
        return match.group(1) if match else None

    def _updateVersion(self, step):
        """
        Updates the version number by incrementing, decrementing, or setting it.
        """
        version = self.extractVersion()
        versionNumber = int(version.replace("v",""))
        newVersion = "v"+str(versionNumber+step).zfill(3)
        file = self.filePath.replace(version, newVersion)
        
        return file

    def isLatestVersionOnDisk(self):
        """
        Checks if the file has the highest version available in the directory.
        """
        if not self.hasVersion():
            return False

        dirname, filename = os.path.split(self.filePath)
        versionPrefix = re.sub(r"\d+", "", self.getVersion())  # Extract 'v' part only
        baseName = re.sub(r"(v\d+)", "", filename)  # Remove version from filename

        existingVersions = []
        for file in Path(dirname).glob(f"{baseName}{versionPrefix}*."):
            match = re.search(r"(v)(\d+)", file.name, re.IGNORECASE)
            if match:
                existingVersions.append(int(match.group(2)))

        return max(existingVersions, default=-1) == int(self.getVersion()[1:])

    def getHighestVersion(self, versions):
        """
        Returns the highest version from a list like ['v001', 'v002', 'v007'].
        """
        if not versions:
            return None
        
        return max(versions, key=lambda v: int(re.search(r"\d+", v).group()))

    def getLatestVersion(self):
        """
        Sets the filename to the next available version based on existing files.
        """
        if not self.exists:
            return self.filePath
        
        version = self.extractVersion()
        
        if not version:
            return None
        
        splittedPath = self.filePath.split("/")
        parentPath = splittedPath[0]

        for component in splittedPath[1:]:
            if component == version:
                break
            else:
                parentPath = parentPath+"/"+component
    
        files = os.listdir(parentPath)
        
        highestVersion = self.getHighestVersion(files)
        latestVersion = parentPath+"/"+highestVersion+"/"+splittedPath[-1]
        
        return latestVersion