import mmap
import math
import codecs

def prev_newline(mm, line_buffer_size=100):
    """
    Return the pointer position immediately after the closest left hand
    newline, or to the beginning of the file if no such newlines exist.
    """
    # mm.seek(mm.tell - line_buffer_size)
    # TODO this fails on a line greater than line_buffer_size in length
    return mm.rfind(b'\n', mm.tell() - line_buffer_size, mm.tell()) + 1


def current_entry(mm):
    start = mm.tell()
    rawline = mm.readline()
    mm.seek(start)
    return rawline.decode(u'utf-8').strip()

def mmap_bin_search(ustr, dictionary_path):

    with codecs.open(dictionary_path, 'r+b') as f:
        # memory-map the file, size 0 means whole file
        mm = mmap.mmap(f.fileno(), 0)
        imin = 0
        imax = mm.size()
        count = 0
        # ustr = ustr.encode(u'utf-8')
        while True:
            mid = imin + int(math.floor((imax - imin) / 2))
            mm.seek(mid)
            mm.seek(prev_newline(mm))
            key = current_entry(mm)

            if key == ustr:
                return True
            elif key < ustr:
                imin = mid + 1
            else:
                imax = mid - 1

            count += 1
            if imin >= imax:
                break
        return None