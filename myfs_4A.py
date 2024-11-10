import sys

# file system parameters
TOTAL_SIZE = 0xf00

# Metainfo block
HEADER_START = 0x0

# 1 byte counter for the number of files
COUNTER_BYTES = 0x1
# 1 byte counter for the number of hard linked files
COUNTER_HARD_LINK_BYTES = 0x1

# pos for counter bytes
COUNTER_POS = 0x0 # just for clarity
# pos for hard link counter bytes
COUNTER_HARD_LINK_POS = 0x1

# size of file info entry (filename, ...)
FILE_ENTRY_SIZE = 0x11 # this can and prob should be made bigger, but i will keep it for now
# size of a file block (content of a file)
FILE_BLOCK_SIZE = 0x180
# max number of files (first block is reserved for metainfo, rest are files)
MAX_FILES = (TOTAL_SIZE - FILE_BLOCK_SIZE) // FILE_BLOCK_SIZE

# max entries in the file table
MAX_ENTRIES = (FILE_BLOCK_SIZE // FILE_ENTRY_SIZE) - 1

# max number of hard linked files
MAX_HARD_LINK_FILES = MAX_ENTRIES - MAX_FILES
# hard linked mask (1 bit)
HARD_LINK_MASK = 0x1
print(MAX_FILES)
print(MAX_ENTRIES)
print(MAX_HARD_LINK_FILES)
# this can represent 65536 bytes, which should be plenty
# this will be halfed as the first bit is reserved as a bit flag
FILESIZE_BYTES = 0x2

# so that they dont overwrite eachother
FILENAME_SIZE = FILE_ENTRY_SIZE - FILESIZE_BYTES


###### EXCEPTIONS ######
class NoFile(Exception):
    def __init__(self, message="No such file found"):
        self.message = message
        super().__init__(self.message)

class NoFreeSpace(Exception):
    def __init__(self, message="No free space available"):
        self.message = message
        super().__init__(self.message)
        
class EmptyFile(Exception):
    def __init__(self, message="Not allowed to store an empty file"):
        self.message = message
        super().__init__(self.message)

# for clarity
class EmptyFilename(Exception):
    def __init__(self, message="Filename cannot be empty"):
        self.message = message
        super().__init__(self.message)


###### FILE SYSTEM OPERATIONS ######

def format(f):
    """
    Formats the file system by writing the initial metadata.
    """
    f.write(b'\0' * TOTAL_SIZE)

def _get_num_files(f):
    f.seek(HEADER_START + COUNTER_POS)
    bytes = f.read(COUNTER_BYTES)
    num = int.from_bytes(bytes, "little", signed=False)
    return num

def _set_num_files(f, n):
    f.seek(HEADER_START + COUNTER_POS)
    bytes = n.to_bytes(COUNTER_BYTES, "little", signed=False)
    f.write(bytes)

def _get_num_linked_files(f):
    f.seek(HEADER_START + COUNTER_HARD_LINK_POS)
    bytes = f.read(COUNTER_HARD_LINK_BYTES)
    num = int.from_bytes(bytes, "little", signed=False)
    return num

def _set_num_linked_files(f, n):
    f.seek(HEADER_START + COUNTER_HARD_LINK_POS)
    bytes = n.to_bytes(COUNTER_HARD_LINK_BYTES, "little", signed=False)
    f.write(bytes)



def _find_empty_slot(f):
    """
    Finds the first empty slot in the file table.
    """
    for pos in range(MAX_ENTRIES):
        f.seek(HEADER_START + (pos + 1) * FILE_ENTRY_SIZE)
        entry = f.read(FILE_ENTRY_SIZE)
        if entry == b'\0' * FILE_ENTRY_SIZE:
            return pos + 1
    raise NoFreeSpace("No free space available in entries")


def save(f, filename, content):
    """
    Saves a file with the given content to the file system.
    
    Args:
        f (file object): The file object representing the file system.
        filename (str): The name of the file to be saved.
        content (str): The file content to be saved.
    """

    if not content:
        raise EmptyFile("Content cannot be empty>:(")

    # felt this was also needed
    if not filename:
        raise EmptyFilename("Filename cannot be empty>:(")
    
    #get num files
    num_existing = _get_num_files(f)
    num_existing_linked = _get_num_linked_files(f)

    if num_existing + num_existing_linked >= MAX_ENTRIES:
        raise NoFreeSpace(f"No free space available, max entries: {MAX_ENTRIES}")
    elif num_existing >= MAX_FILES:
        raise NoFreeSpace(f"No free space available, max files: {MAX_FILES}")


    new_fileno = _find_empty_slot(f) 

    # update num files
    _set_num_files(f, num_existing + 1)

    # im setting the first bit of to to 0, showing that this is not an hardlink
    file_size = (len(content) << 1).to_bytes(FILESIZE_BYTES, "little", signed=False)

    # write filename in ftable next free entry, truncate if needed
    f.seek(HEADER_START + FILE_ENTRY_SIZE * new_fileno)
    f.write(filename.encode('ascii')[:FILE_ENTRY_SIZE].ljust(FILENAME_SIZE, b'\0'))
    f.write(file_size)

    # write content to file block, truncate if needed
    f.seek(HEADER_START + FILE_BLOCK_SIZE * new_fileno)
    f.write(content.encode('ascii')[:FILE_BLOCK_SIZE])


# i could change this to a 1-indexed one (or wherever the datablocks begin),
# but i find it more readable this way
def find_fileno(f, filename):
    """
    
    Finds the line of the filename in the header.
    Uses 0-indexing.

    Args:
        f (file object): File system
        filename (str): Name of file

    Returns:
        int: 0-indexed position number
    """
    N = _get_num_files(f) + _get_num_linked_files(f)
    for pos in range(0, N):
        f.seek(HEADER_START + FILE_ENTRY_SIZE * (pos+1))
        name = f.read(FILENAME_SIZE)
        name = name.decode("ascii").strip('\0')
        if name == filename:
            return pos
    else:
        raise NoFile(f"File {filename} not found")
    

def find_filesize(f, fileno):
    """
    Return the file size of the file associated with
    the given file number. Resolves hard links if needed.

    Args:
        f (file object): The file system
        fileno (int): The file number
    """

    # Read size info and check for hard link bit
    f.seek(HEADER_START + FILE_ENTRY_SIZE * (fileno+1) + FILENAME_SIZE)
    size_info = int.from_bytes(f.read(FILESIZE_BYTES), "little", signed=False)
    is_hard_link = size_info & HARD_LINK_MASK

    if is_hard_link:
        fileno = (size_info >> 1) - 1
        f.seek(HEADER_START + FILE_ENTRY_SIZE * (fileno+1) + FILENAME_SIZE)
        size_info = int.from_bytes(f.read(FILESIZE_BYTES), "little", signed=False)
    
    return size_info >> 1, fileno


def load(f, filename):
    """
    Load the content of a file from a custom filesystem.
    Args:
        f (file object): The file object representing the file system.
        filename (str): The name of the file to load.
    Returns:
        str: The content of the file as a string.
    """
    
    # gets file num
    fileno = find_fileno(f, filename)
    content_size, fileno = find_filesize(f, fileno)
    
    f.seek(HEADER_START + FILE_BLOCK_SIZE * (fileno+1))
    content = f.read(content_size)
    # i see that in test1 it is expected an string, while in test2 it is expected bytes.
    # Therfore I deliberately chose to return bytes   
    return content


def copy(f, infile, outfile):
    """
    Copy the contents of a file from the filesystem 
    to another file in the filesystem.
    
    Args:
        f (file object): The file object representing the file system.
        infile (str): The name of the file to copy from.
        outfile (str): The name of the new file to copy to.
    """
    content = load(f, infile)
    save(f, outfile, content)


def remove(f, filename):
    """
    Remove a file from the filesystem.
    
    Args:
        f (file object): The file object representing the file system.
        filename (str): The name of the file to remove.
    """
    link_existing = _get_num_linked_files(f)
    num_existing = _get_num_files(f)

    fileno = find_fileno(f, filename)
    f.seek(HEADER_START + FILE_ENTRY_SIZE * (fileno+1) + FILENAME_SIZE)
    size_info = int.from_bytes(f.read(FILESIZE_BYTES), "little", signed=False)

    if size_info & HARD_LINK_MASK:
        _set_num_linked_files(f, link_existing - 1)
    else:
        _set_num_files(f, num_existing - 1)
    
    f.seek(HEADER_START + FILE_ENTRY_SIZE * (fileno+1))
    f.write(b'\0' * FILE_ENTRY_SIZE)


def hard_link(f, existing_file, link_name):
    """
    Create a hard link to an existing file.

    Args:
        f (file object): The file object representing the file system.
        existing_file (str): The name of the existing file.
        link_name (str): The name of the new hard link.
    """
    
    if not link_name:
        raise EmptyFilename("Filename cannot be empty>:(")

    # gets file num
    num_existing_linked = _get_num_linked_files(f)
    num_existing_files = _get_num_files(f)
    if num_existing_linked + num_existing_files >= MAX_ENTRIES:
        raise NoFreeSpace(f"No free space available, max entries: {MAX_ENTRIES}")
    elif num_existing_linked >= MAX_HARD_LINK_FILES:
        raise NoFreeSpace(f"No free space available, max hard links: {MAX_HARD_LINK_FILES}")
    
    fileno = find_fileno(f, existing_file)
    new_fileno = _find_empty_slot(f)

    f.seek(HEADER_START + FILE_ENTRY_SIZE * (fileno+1) + FILENAME_SIZE)
    size_info = int.from_bytes(f.read(FILESIZE_BYTES), "little", signed=False)
    
    if size_info & HARD_LINK_MASK:
        fileno = (size_info >> 1) - 1

    # updating the number of hard linked files 
    _set_num_linked_files(f, num_existing_linked + 1)

    # setting the first bit in file size to 1 to show that this is a hard link
    pointer = ((fileno + 1) << 1 | 1).to_bytes(FILESIZE_BYTES, "little", signed=False)

    # write filename in ftable next free entry, truncate if needed
    f.seek(HEADER_START + FILE_ENTRY_SIZE * new_fileno)
    f.write(link_name.encode('ascii')[:FILE_ENTRY_SIZE].ljust(FILENAME_SIZE, b'\0'))
    f.write(pointer)