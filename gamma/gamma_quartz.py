from ctypes import byref, sizeof, c_float, c_uint32, cdll
from ctypes.util import find_library


__all__ = ['Context']

kCGErrorSuccess = 0

CGDirectDisplayID = c_uint32

lib = cdll.LoadLibrary(find_library('ApplicationServices'))

CGGetOnlineDisplayList = lib.CGGetOnlineDisplayList
CGDisplayGammaTableCapacity = lib.CGDisplayGammaTableCapacity
CGSetDisplayTransferByTable = lib.CGSetDisplayTransferByTable
CGDisplayRestoreColorSyncSettings = lib.CGDisplayRestoreColorSyncSettings

CGDisplayGammaTableCapacity.restype = c_uint32


class Display:
    def __init__(self, id):
        self.id = id
        self.ramp_size = c_uint32(CGDisplayGammaTableCapacity(id))

        if self.ramp_size == 0:
            raise RuntimeError('Gamma ramp size is zero')

        self.saved_ramps = []


class Context:
    def __init__(self):
        display_count = c_uint32()

        error = CGGetOnlineDisplayList(c_uint32(0), None, byref(display_count))

        if error != kCGErrorSuccess:
            raise RuntimeError(
                '[CGError {}] Unable to get display count'.format(error))

        display_ids = (CGDirectDisplayID * display_count.value)()

        error = CGGetOnlineDisplayList(display_count, byref(display_ids),
                                       byref(display_count))

        if error != kCGErrorSuccess:
            raise RuntimeError(
                '[CGError {}] Unable to get display list'.format(error))

        self._displays = []

        for i in range(display_count.value):
            self._displays.append(Display(CGDirectDisplayID(display_ids[i])))

    def set(self, func):
        for display in self._displays:
            ramp_size = display.ramp_size.value
            ramp = (c_float * ramp_size * 3)()

            for i in range(ramp_size):
                ramp[0][i] = ramp[1][i] = ramp[2][i] = func(i / ramp_size)

            gamma_r = byref(ramp, 0 * ramp_size * sizeof(c_float))
            gamma_g = byref(ramp, 1 * ramp_size * sizeof(c_float))
            gamma_b = byref(ramp, 2 * ramp_size * sizeof(c_float))

            error = CGSetDisplayTransferByTable(display.id, display.ramp_size,
                                                gamma_r, gamma_g, gamma_b)

            if error != kCGErrorSuccess:
                raise RuntimeError(
                    '[CGError {}] Unable to set gamma ramp'.format(error))

    def close(self):
        CGDisplayRestoreColorSyncSettings()
