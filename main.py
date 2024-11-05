from myfs_4B import format, save, load, copy, remove, hard_link, NoFile
import sys

if len(sys.argv) < 2:
    # Missing filesystem name. Assuming default myfilesystem.fs
    backingfile = 'myfilesystem.fs'
else:
    backingfile = sys.argv[1]
    # one could actually use a usb stick raw at "/dev/something"
    # Data loss, and it'll need reformatting afterwards!


# create backingfile if needed
try: 
    with open(backingfile, 'x'): pass 
except FileExistsError: pass

##########################################
##########################################

alice_sample = """Alice was beginning to get very tired of sitting by her sister on the
bank, and of having nothing to do: once or twice she had peeped into the
book her sister was reading, but it had no pictures or conversations in
it, 'and what is the use of a book,' thought Alice 'without pictures or
conversations?'
"""

test_sample = "Did you know that the moon is made of cheese?"

def test_1():
    with open("test1.fs", 'r+b') as f:
        format(f) # clear the file system
        try:
            for i in range(7):
                # Add 7 files (is max with the original capacity)
                save(f, f"alice{i}.txt", f"content{i}")
                # Remove 1 file, there should be more space now
                remove(f, f"alice{i}.txt")
                # try adding another file
                save(f, f"hello.txt", f"Hello World!")
                # Check that the new file is there
                #assert load(f, "hello.txt") == "Hello World!"
        except Exception as e:
            print(f"Test 1 failed: {e}")


def test_2():
    # Test that content is loaded correctly
    with open("test_save_with_file_size.fs", 'w+b') as f:
        format(f)
        save(f, "test.txt", test_sample)
        content = load(f, "test.txt")
        content = content.decode('utf-8')
        assert content == test_sample

        hard_link(f, "test.txt", "link.txt")
        content = load(f, "link.txt")
        content = content.decode('utf-8')
        assert content == test_sample

        hard_link(f, "link.txt", "link2.txt")
        content = load(f, "link2.txt")
        content = content.decode('utf-8')
        assert content == test_sample


def test_3():
    # test that block was not zeroed out when deleted
    with open("test_remove_not_zeroed_out.fs", 'w+b') as f:
        format(f)
        save(f, "test.txt", test_sample)
        remove(f, "test.txt")
        
        # Check that the file system is not fully zeroed out
        f.seek(0)
        content = f.read()
        assert any(byte != 0 for byte in content), "File system is fully zeroed out after removal"


def test_4():
    with open("test_hard_link.fs", 'w+b') as f:
        format(f)
        save(f, "test.txt", test_sample)
        # Test that you can save a hard link
        hard_link(f, "test.txt", "link.txt")
        
        # Test that the content is the same
        content = load(f, "link.txt")
        content = content.decode('utf-8')
        assert content == test_sample
        
        # Test that removing the original file does not affect the hard link
        remove(f, "test.txt")
        content = load(f, "link.txt")
        content = content.decode('utf-8')
        assert content == test_sample
        
        # test that the file can be removed
        remove(f, "link.txt")
        try:
            load(f, "link.txt")
        except NoFile:
            pass
        else:
            raise AssertionError("Test 4 failed: File was not removed")

print()
print("*" * 60)
print(f"* Use xxd {backingfile} to inspect contents")
print("*" * 60)
print()

test_1()
test_2()
test_3()
test_4()
