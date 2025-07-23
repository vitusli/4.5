const FileSortMode = Object.freeze({
  NAME_DESC: Symbol("Az↓"),
  NAME_ASC: Symbol("Az↑"),
  SIZE_DESC: Symbol("Estimated Size↓"),
  SIZE_ASC: Symbol("Estimated Size↑"),
})

const DatablockSortMode = Object.freeze({
  NAME_DESC: Symbol("Name↓"),
  NAME_ASC: Symbol("Name↑"),
  TYPE_DESC: Symbol("Type↓"),
  TYPE_ASC: Symbol("Type↑"),
  SIZE_DESC: Symbol("Estimated Size↓"),
  SIZE_ASC: Symbol("Estimated Size↑"),
  PERCENTAGE_DESC: Symbol("Percentage↓"),
  PERCENTAGE_ASC: Symbol("Percentage↑"),
})

const ViewMode = Object.freeze({
  FILES: Symbol("Files"),
  DATABLOCKS: Symbol("Datablocks"),
})

var queryCache = {};
var currentFileSortMode = FileSortMode.SIZE_DESC;
// Stores mapping of fileId to sort mode for each datablock table.
// Display of all datablocks is stored with the key "/".
var currentDatablockTablesSortModes = {};
var currentViewMode = ViewMode.FILES;
// Whether to show 0 sized datablocks in the views.
var currentShowZeroSizeDatablocks = false;

// We only need to build the tree structure once.
var folderHierarchy = getTreeStructure();
var currentNode = folderHierarchy;

function getSortFunction(viewMode, sortMode) {
  function compareSize(a, b) {
    let sizeA = a.size_bytes;
    let sizeB = b.size_bytes;
    return sizeA - sizeB;
  }

  function comparePercentage(a, b) {
    let percentageA = a.size_factor;
    let percentageB = b.size_factor;
    return percentageA - percentageB;
  }

  if (viewMode === ViewMode.FILES) {
    switch (sortMode) {
      case FileSortMode.NAME_ASC:
        return function(a, b) {
          return a.name.localeCompare(b.name);
        }
      case FileSortMode.NAME_DESC:
        return function(a, b) {
          return b.name.localeCompare(a.name);
        }
      case FileSortMode.SIZE_ASC:
        return function(a, b) {
          return compareSize(a, b);
        }
      case FileSortMode.SIZE_DESC:
        return function(a, b) {
          return compareSize(b, a);
        }
      default:
        console.error("Invalid sort mode: " + sortMode);
        return function(a, b) {
          return compareSize(b, a);
        }
    }
  } else {
    switch (sortMode) {
      case DatablockSortMode.NAME_ASC:
        return function(a, b) {
          return a.name.localeCompare(b.name);
        }
      case DatablockSortMode.NAME_DESC:
        return function(a, b) {
          return b.name.localeCompare(a.name);
        }
      case DatablockSortMode.TYPE_ASC:
        return function(a, b) {
          return a.type.localeCompare(b.type);
        }
      case DatablockSortMode.TYPE_DESC:
        return function(a, b) {
          return b.type.localeCompare(a.type);
        }
      case DatablockSortMode.SIZE_ASC:
        return function(a, b) {
          return compareSize(a, b);
        }
      case DatablockSortMode.SIZE_DESC:
        return function(a, b) {
          return compareSize(b, a);
        }
      case DatablockSortMode.PERCENTAGE_ASC:
        return function(a, b) {
          return comparePercentage(a, b);
        }
      case DatablockSortMode.PERCENTAGE_DESC:
        return function(a, b) {
          return comparePercentage(b, a);
        }
      default:
        console.error("Invalid sort mode: " + sortMode);
        return function(a, b) {
          return comparePercentage(b, a);
        }
    }
  }
}

function getInverseSortMode(sortMode) {
  // TODO: How to achieve this in a more elegant way without rewriting the frozen objects and
  // using a "reverse" bool?
  switch (sortMode) {
    case FileSortMode.NAME_ASC:
      return FileSortMode.NAME_DESC;
    case FileSortMode.NAME_DESC:
      return FileSortMode.NAME_ASC;
    case FileSortMode.SIZE_ASC:
      return FileSortMode.SIZE_DESC;
    case FileSortMode.SIZE_DESC:
      return FileSortMode.SIZE_ASC;
    case DatablockSortMode.NAME_ASC:
      return DatablockSortMode.NAME_DESC;
    case DatablockSortMode.NAME_DESC:
      return DatablockSortMode.NAME_ASC;
    case DatablockSortMode.TYPE_ASC:
      return DatablockSortMode.TYPE_DESC;
    case DatablockSortMode.TYPE_DESC:
      return DatablockSortMode.TYPE_ASC;
    case DatablockSortMode.SIZE_ASC:
      return DatablockSortMode.SIZE_DESC;
    case DatablockSortMode.SIZE_DESC:
      return DatablockSortMode.SIZE_ASC;
    case DatablockSortMode.PERCENTAGE_ASC:
      return DatablockSortMode.PERCENTAGE_DESC;
    case DatablockSortMode.PERCENTAGE_DESC:
      return DatablockSortMode.PERCENTAGE_ASC;
    default:
      console.error("Invalid sort mode: " + sortMode);
      return sortMode;
  }
}

function getFieldNameToSortModes(fieldName) {
  let headerNameToSortModes = {
    "Name": [DatablockSortMode.NAME_DESC, DatablockSortMode.NAME_ASC],
    "Type": [DatablockSortMode.TYPE_DESC, DatablockSortMode.TYPE_ASC],
    "Estimated Size": [DatablockSortMode.SIZE_DESC, DatablockSortMode.SIZE_ASC],
    "Percentage": [DatablockSortMode.PERCENTAGE_DESC, DatablockSortMode.PERCENTAGE_ASC],
  };
  return headerNameToSortModes[fieldName];
}

function isSortModeForField(sortMode, fieldName) {
  let selectedMode = getFieldNameToSortModes(fieldName).find(function(mode) {
    return mode === sortMode;
  });

  return selectedMode !== undefined;
}

function formatByteSize(value) {
  const units = ["B", "KiB", "MiB", "GiB", "TiB"];
  let size = value;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return size.toFixed(2) + " " + units[unitIndex];
}

function getCommonPath(paths) {
  if (paths.length === 0) {
    return "";
  }
  const splitPaths = paths.map(path => path.split(/[\/\\]+/));
  // Initialize the common parts with the first path's segments
  let commonParts = splitPaths[0];

  // Compare with each subsequent path
  for (let i = 1; i < splitPaths.length; i++) {
    let currentParts = splitPaths[i];
    let j = 0;
    // Find the matching parts at the beginning
    while (j < commonParts.length && j < currentParts.length && commonParts[j] === currentParts[j]) {
      j++;
    }
    commonParts = commonParts.slice(0, j);
    if (commonParts.length === 0) {
      return "";
    }
  }

  return commonParts.join("/");
}

function getTimeStamp() {
  let jsonDiv = document.getElementById('jsonData');
  let jsonData = JSON.parse(jsonDiv.textContent);
  let timestamp = jsonData.timestamp;
  let date = new Date(timestamp);
  return date.toLocaleString();
}

function getTreeStructure() {
  // Get the JSON data from the hidden div and parse it.
  let jsonDiv = document.getElementById('jsonData');
  let jsonData = JSON.parse(jsonDiv.textContent);
  let fileMemoryUsageList = jsonData.memory_usage
  let commonPath = getCommonPath(fileMemoryUsageList.map(file => file.id));
  let rootFolderDict = {
    name: commonPath,
    id: commonPath,
    folders: [],
    files: [],
  };
  fileMemoryUsageList.forEach(function(fileMemoryUsage) {
    let relativePath = fileMemoryUsage.id.replace(commonPath, "").replace(/^\/+|\/+$/g, "");
    let folderParts = relativePath.split(/[\/\\]+/);
    folderParts = folderParts.slice(0, folderParts.length - 1);
    let currentFolderDict = rootFolderDict;
    let currentSubFolderDict = currentFolderDict.folders;
    folderParts.forEach(function(folderName) {
      let folderNode = currentSubFolderDict.find(function(folder) {
        return folder.name === folderName;
      });
      if (!folderNode) {
        folderNode = {
          name: folderName,
          id: currentFolderDict.id + "/" + folderName,
          folders: [],
          files: [],
        };
        currentSubFolderDict.push(folderNode);
      }
      currentFolderDict = folderNode;
      currentSubFolderDict = folderNode.folders;
    });
    currentFolderDict.files.push(fileMemoryUsage);
  });
  return rootFolderDict;
}

function getAllFilesAndDatablocks(treeNode) {
  function recordDatablocks(fileNode, filesAndDatablocks) {
    filesAndDatablocks.files.push(fileNode);
    filesAndDatablocks.datablocks = filesAndDatablocks.datablocks.concat(fileNode.datablocks);
  }

  // Without this the script doesn't work properly, even though this should be just a cache.
  let filesAndDatablocks = queryCache[treeNode.id];
  if (filesAndDatablocks) {
    return filesAndDatablocks;
  }
  filesAndDatablocks = { files: [], datablocks: [] };
  if ("files" in treeNode) {
    // Tree node is folder
    treeNode.files.forEach(function(fileNode) {
      recordDatablocks(fileNode, filesAndDatablocks);
    });
    treeNode.folders.forEach(function(subFolderNode) {
      let subFilesAndDatablocks = getAllFilesAndDatablocks(subFolderNode);
      filesAndDatablocks.files = filesAndDatablocks.files.concat(subFilesAndDatablocks.files);
      filesAndDatablocks.datablocks = filesAndDatablocks.datablocks.concat(subFilesAndDatablocks.datablocks);
    });
  } else {
    // Tree node is file
    recordDatablocks(treeNode, filesAndDatablocks);
  }
  queryCache[treeNode.id] = filesAndDatablocks;
  return filesAndDatablocks;
}

function filterData(searchInput) {
  let filesAndDatablocks = getAllFilesAndDatablocks(currentNode);
  searchInput = searchInput.toLowerCase();

  function isZeroSize(datablock) {
    return datablock.size_bytes === 0;
  }

  if (currentViewMode === ViewMode.FILES) {
    let filteredFiles = filesAndDatablocks.files
      .map(file => {
        let fileNameMatch = file.name.toLowerCase().includes(searchInput);

        let matchingDatablocks = file.datablocks.filter(datablock =>
          datablock.name.toLowerCase().includes(searchInput) ||
          datablock.type.toLowerCase().includes(searchInput)
        );

        if (fileNameMatch || matchingDatablocks.length > 0) {
          return {
            ...file,
            datablocks: fileNameMatch && matchingDatablocks.length === 0
              ? file.datablocks
              : matchingDatablocks
          };
        }
        return null;
      })
      .map(file => {
        if (file === null) {
          return null;
        }
        if (!currentShowZeroSizeDatablocks) {
          let allZero = file.datablocks.every(db => isZeroSize(db));
          if (allZero) {
            return null;
          }
          return {
            ...file,
            datablocks: file.datablocks.filter(db => !isZeroSize(db))
          }
        };
        return file;
      })
      .filter(file => file !== null)
      return filteredFiles;
  } else {
    let filteredDatablocks = filesAndDatablocks.datablocks.filter(datablock => {
      if (!currentShowZeroSizeDatablocks && isZeroSize(datablock)) {
        return false;
      }
      return (
        datablock.name.toLowerCase().includes(searchInput) ||
        datablock.type.toLowerCase().includes(searchInput)
      );
    });

    return filteredDatablocks;
  }
}

// Creates HTML elements and interactivity of the elements based on the provided dataList.
function showData(dataList) {
  function onTableSortModeChange(fileId, fieldName, tableElem) {
    let thisFieldSortModes = getFieldNameToSortModes(fieldName);
    let currentSortMode = currentDatablockTablesSortModes[fileId];

    let newMode = null;
    if (isSortModeForField(currentSortMode, fieldName)) {
      newMode = getInverseSortMode(currentSortMode);
    } else {
      newMode = thisFieldSortModes[0];
    }

    // Set the new sort mode for the table to global state
    currentDatablockTablesSortModes[fileId] = newMode;

    // Rerender the table with the new sort mode
    let nodeData = getCurrentNodeFilteredData();
    let datablockNodes = nodeData.find(function(fileNode) {
      return fileNode.id === fileId;
    });

    if (currentViewMode === ViewMode.FILES) {
      datablockNodes = datablockNodes.datablocks;
    } else {
      datablockNodes = nodeData;
    }
    // sort the datablocks based on the sort mode and replace the original table
    datablockNodes.sort(getSortFunction(ViewMode.DATABLOCKS, newMode));
    tableElem.replaceWith(createDatablockTable(fileId, datablockNodes));
  }

  // Creates a clickable button for sorting individual datablock tables based on 'fieldName' and 'fileId'
  // replacing content of 'tableElem' when clicked.
  function createTableSortButton(fieldName, fileId, tableElem) {
    let headerCell = document.createElement('th');

    let currentSortMode = currentDatablockTablesSortModes[fileId];
    if (isSortModeForField(currentSortMode, fieldName)){
      headerCell.textContent = currentSortMode.description;
    } else {
      headerCell.textContent = fieldName;
    }
    headerCell.classList.add('fileTableSortButton');
    headerCell.addEventListener('click', function() {
      onTableSortModeChange(fileId, fieldName, tableElem);
    });

    return headerCell;
  }

  function createTableWithHeader(fileId) {
    let table = document.createElement('table');
    table.classList.add('fileTable');
    let colGroup = document.createElement('colgroup');
    const colWidths = ["15%", "40%", "15%", "30%"];
    colWidths.forEach(function(width) {
      let col = document.createElement('col');
      col.style.width = width;
      colGroup.appendChild(col);
    });
    table.appendChild(colGroup);
    let header = document.createElement('tr');
    const headerNames = ["Type", "Name", "Estimated Size", "Percentage"];
    headerNames.forEach(function(headerName) {
      header.appendChild(createTableSortButton(headerName, fileId, table));
    });
    table.appendChild(header);
    return table;
  }

  function formatDatablockValue(value, fieldName) {
    switch (fieldName) {
      case "size_bytes":
        return formatByteSize(value);
      case "size_factor":
        return (value * 100).toFixed(2) + "%";
      default:
        return value;
    }
  }

  function colorFromPercentage(percentage)
  {
    let redChannel = (percentage * 255) / 10;
    let greenChannel = 255 - redChannel;
    return"rgb(" + redChannel + ", " + greenChannel + ", 0)";
  }

  function createPercentageBar(percentage) {
    let percentageBar = document.createElement('div');
    percentageBar.classList.add('percentageBar');
    percentageBar.style.width = percentage + "%";
    let percentageText = document.createElement('span');
    percentageText.textContent = percentage.toFixed(2) + "%";
    percentageText.classList.add('percentageText');
    percentageText.classList.add('outlineText');
    percentageBar.style.backgroundColor = colorFromPercentage(percentage);
    percentageBar.appendChild(percentageText);
    let percentageBarWrapper = document.createElement('div');
    percentageBarWrapper.classList.add('filePercentageBarWrapper');
    percentageBarWrapper.appendChild(percentageBar);
    percentageBarWrapper.appendChild(percentageText);
    percentageBarWrapper.appendChild(percentageBar);
    return percentageBarWrapper;
  }

  function createDatablockRow(datablockNode) {
    let datablockRow = document.createElement('tr');
    datablockRow.classList.add('datablockRow');
    const headerNames = ["type", "name", "size_bytes"];
    headerNames.forEach(function(fieldName) {
      let cell = document.createElement('td');
      cell.textContent = formatDatablockValue(datablockNode[fieldName], fieldName);
      datablockRow.appendChild(cell);
    });
    let barCell = document.createElement('td');
    barCell.appendChild(createPercentageBar(datablockNode.size_factor * 100.0));
    datablockRow.appendChild(barCell);
    return datablockRow;
  }

  function createDatablockTable(fileId, datablockNodes) {
    let datablockTable = createTableWithHeader(fileId);
    datablockNodes.forEach(function(datablockNode) {
      let datablockRow = createDatablockRow(datablockNode);
      datablockTable.appendChild(datablockRow);
    });
    return datablockTable;
  }

  let content = document.getElementById('content');
  content.innerHTML = "";
  if (currentViewMode === ViewMode.FILES) {
    let totalFilesSize = dataList.reduce((total, fileNode) => total + fileNode.size_bytes, 0);
    if (dataList.length > 1) {
      let totalSizeHeader = document.createElement('h2');
      totalSizeHeader.textContent = "Total Estimated Size: " + formatByteSize(totalFilesSize);
      content.appendChild(totalSizeHeader);
    }
    dataList.forEach(function(fileNode) {
      let fileBlock = document.createElement('div');
      fileBlock.classList.add('fileBlock');

      let headerWrapper = document.createElement('div');
      headerWrapper.classList.add('fileHeader');

      let toggle = document.createElement('span');
      toggle.textContent = dataList.length > 1 ? "[+]" : "[-]";
      toggle.classList.add('toggle');
      toggle.addEventListener('click', function() {
        let datablockTable = fileBlock.querySelector('.fileTable');
        if (datablockTable.style.display === 'none') {
          datablockTable.style.display = 'table';
          this.textContent = "[-]";
        } else {
          datablockTable.style.display = 'none';
          this.textContent = "[+]";
        }
      });
      headerWrapper.appendChild(toggle);

      let header = document.createElement('h3');
      header.textContent = fileNode.name + " (" + formatByteSize(fileNode.size_bytes) + ")";
      headerWrapper.appendChild(header);
      if (dataList.length > 1) {
        headerWrapper.appendChild(createPercentageBar((fileNode.size_bytes / totalFilesSize) * 100.0));
      }

      fileBlock.appendChild(headerWrapper);
      // Collapse datablock tables for file view by default
      let datablockTable = createDatablockTable(fileNode.id, fileNode.datablocks);
      if (dataList.length > 1) {
        datablockTable.style.display = 'none';
      }
      fileBlock.appendChild(datablockTable);
      content.appendChild(fileBlock);
    });
  } else {
    let header = document.createElement('h2');
    header.textContent = "All Datablocks: " + dataList.length;
    content.appendChild(header);
    content.appendChild(createDatablockTable("/", dataList));
  }
}

// Returns the currently filtered data based on the search input and current view mode.
// Populates sort modes for datablock tables if they are not set yet.
function getCurrentNodeFilteredData() {
  let query = document.getElementById('searchInput').value;
  let filteredData = filterData(query);
  if (currentViewMode === ViewMode.FILES) {
    filteredData = filteredData.sort(getSortFunction(ViewMode.FILES, currentFileSortMode))
    .map(function(fileNode) {
      if (!(fileNode.id in currentDatablockTablesSortModes)) {
        currentDatablockTablesSortModes[fileNode.id] = DatablockSortMode.PERCENTAGE_DESC;
      }
      return {
        ...fileNode,
        datablocks: fileNode.datablocks.sort(getSortFunction(ViewMode.DATABLOCKS, currentDatablockTablesSortModes[fileNode.id]))
      }
    });
  }
  else if (currentViewMode == ViewMode.DATABLOCKS)
  {
    if (!("/" in currentDatablockTablesSortModes)) {
      currentDatablockTablesSortModes["/"] = DatablockSortMode.PERCENTAGE_DESC;
    }
    filteredData = filteredData.sort(getSortFunction(ViewMode.DATABLOCKS, currentDatablockTablesSortModes["/"]));
  }
  return filteredData;
}

function showCurrentNodeFilteredData()
{
  showData(getCurrentNodeFilteredData());
}

function reRenderViewSortButtons() {
  let buttonsDiv = document.getElementById('sortModeButtons');
  let buttonsLabel = document.getElementById('sortModeLabel');
  buttonsDiv.innerHTML = "";
  if (currentViewMode !== ViewMode.FILES) {
    buttonsLabel.style.display = 'none';
    return;
  }
  buttonsLabel.style.display = 'block';
  for (let modeKey in FileSortMode) {
    let sortMode = FileSortMode[modeKey];
    let button = document.createElement('button');
    button.textContent = sortMode.description;
    button.classList.add('button');
    if (sortMode === currentFileSortMode) {
      button.classList.add('active');
    }
    button.addEventListener('click', function() {
      currentFileSortMode = sortMode;
      reRenderViewSortButtons();
      showCurrentNodeFilteredData();
    });
    buttonsDiv.appendChild(button);
  }
}

function reRenderViewButtons() {
  let buttonsDiv = document.getElementById('viewModeButtons');
  buttonsDiv.innerHTML = "";
  for (let modeKey in ViewMode) {
    let viewMode = ViewMode[modeKey];
    let button = document.createElement('button');
    button.textContent = viewMode.description;
    button.classList.add('button');
    if (viewMode === currentViewMode) {
      button.classList.add('active');
    }
    button.addEventListener('click', function() {
      currentViewMode = viewMode;
      reRenderViewSortButtons();
      showCurrentNodeFilteredData();
      reRenderViewButtons();
    });
    buttonsDiv.appendChild(button);
  }
  // Add toggle button for showing/hiding 0-sized datablocks
  let zeroToggleBtn = document.createElement('button');
  zeroToggleBtn.classList.add(...['button', 'button-ml-16']);
  zeroToggleBtn.textContent = "Show 0B";
  zeroToggleBtn.classList.toggle('active', currentShowZeroSizeDatablocks);
  zeroToggleBtn.addEventListener('click', function() {
    currentShowZeroSizeDatablocks = !currentShowZeroSizeDatablocks;
    zeroToggleBtn.classList.toggle('active');
    showCurrentNodeFilteredData();
  });
  buttonsDiv.appendChild(zeroToggleBtn);
}

function setTreeElementSelected(treeElement) {
  let selectedElements = document.querySelectorAll('.treeLabel.selected');
  selectedElements.forEach(function(selectedElement) {
    selectedElement.classList.remove('selected');
  });
  treeElement.classList.add('selected');
}

function generateTreeHTML(folderNode) {
  let li = document.createElement('li');

  // Create and attach the toggle button
  let toggle = document.createElement('span');
  toggle.textContent = "[+]";
  toggle.classList.add('toggle');
  toggle.addEventListener('click', function(e) {
    e.stopPropagation();
    let subUl = li.querySelector('ul');
    if (subUl) {
      if (subUl.style.display === 'none') {
        subUl.style.display = 'block';
        this.textContent = "[-]";
      } else {
        subUl.style.display = 'none';
        this.textContent = "[+]";
      }
    }
  });
  li.appendChild(toggle);

  let folderLabel = document.createElement('span');
  folderLabel.textContent = folderNode.name;
  folderLabel.classList.add('treeLabel');
  folderLabel.addEventListener('click', function() {
    currentNode = folderNode;
    setTreeElementSelected(folderLabel);
    showCurrentNodeFilteredData();
  });
  li.appendChild(folderLabel);
  hr = document.createElement('hr');
  li.appendChild(hr);

  let nestedUl = document.createElement('ul');
  nestedUl.style.display = 'none'; // Hide sub-folders by default

  // Recursively add sub-folder items
  folderNode.folders.forEach(function(subFolder) {
    nestedUl.appendChild(generateTreeHTML(subFolder));
  });

  // Add file items
  folderNode.files.forEach(function(fileNode) {
    let fileLi = document.createElement('li');
    let fileLabel = document.createElement('span');
    fileLabel.textContent = fileNode.name;
    fileLabel.classList.add('treeLabel');
    fileLabel.addEventListener('click', function(e) {
      e.stopPropagation();
      currentNode = fileNode;
      setTreeElementSelected(fileLabel);
      showCurrentNodeFilteredData();
    });
    fileLi.appendChild(fileLabel);
    nestedUl.appendChild(fileLi);
  });

  li.appendChild(nestedUl);
  return li;
}

// Initialize the tree view on page load
document.addEventListener('DOMContentLoaded', function() {
  let treeContainer = document.getElementById('treeview');
  let fileCount = getAllFilesAndDatablocks(folderHierarchy).files.length;
  // Hide tree view if there is only one file
  if (fileCount < 2) {
    treeContainer.remove();
  } else {
    let treeRoot = document.createElement('ul');
    treeRoot.appendChild(generateTreeHTML(folderHierarchy));
    treeContainer.appendChild(treeRoot);

    // Show the first level of folders by default
    treeRoot.querySelector('span.toggle').textContent = "[-]";
    treeRoot.querySelector('ul').style.display = 'block';
  }
  reRenderViewButtons();
  reRenderViewSortButtons();

  // Select the root folder by default, its the first treeLabel
  let rootLabel = document.querySelector('.treeLabel');
  if (rootLabel) {
    rootLabel.classList.add('selected');
  }

  // Add search input callback
  let searchInput = document.getElementById('searchInput');
  searchInput.addEventListener('input', function() {
      showCurrentNodeFilteredData();
  });

  // Show timestamp
  let timestamp = getTimeStamp();
  let timestampSpan = document.getElementById('timestamp');
  timestampSpan.textContent = "Created at: " + timestamp;

  // Show the root folder data by default, currentNode is set to folderHierarchy on initialization.
  showCurrentNodeFilteredData();
});