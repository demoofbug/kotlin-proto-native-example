import ctypes
from pathlib import Path
import platform
import os
from cookie_store_pb2 import Cookie, CookieJar

# build library path
def get_library_path():
    project_root = Path(__file__).parent.parent.parent
    system = platform.system()
    machine = platform.machine()

    if system == "Linux":
        if machine == "x86_64":
            kn_target = "linuxX64"
        elif machine == "aarch64":
            kn_target = "linuxArm64"
        else:
            raise RuntimeError(f"Unsupported Linux architecture: {machine}")
    elif system == "Darwin":
        if machine == "x86_64":
            kn_target = "macosX64"
        elif machine == "arm64":
            kn_target = "macosArm64"
        else:
            raise RuntimeError(f"Unsupported macOS architecture: {machine}")
    elif system == "Windows":
        kn_target = "mingwX64"
    else:
        raise RuntimeError(f"Unsupported system: {system}")

    build_type = os.getenv("BUILD_TYPE", "release").lower()
    lib_suffix = "debugShared" if build_type == "debug" else "releaseShared"

    base_lib_dir = project_root / "build" / "bin" / kn_target / lib_suffix

    if system == "Windows":
        lib_name = "kcookie_store.dll"
    elif system == "Darwin":
        lib_name = "libkcookie_store.dylib"
    else:
        lib_name = "libkcookie_store.so"

    lib_path = base_lib_dir / lib_name
    if not lib_path.exists():
        raise FileNotFoundError(f"Library not found at: {lib_path}")

    return str(lib_path)

# load library
try:
    lib_path = get_library_path()
    lib = ctypes.CDLL(lib_path)
except Exception as e:
    raise RuntimeError(f"Failed to load cookie manager library: {e}")

# Define error codes
COOKIE_SUCCESS = 0
COOKIE_NOT_FOUND = 1
COOKIE_ALLOCATION_FAILED = 2
COOKIE_EXCEPTION = -1

class CookieStore:
    def __init__(self):
        lib.cookie_store_new.restype = ctypes.c_void_p
        lib.cookie_store_new.argtypes = []

        lib.cookie_store_free.restype = None
        lib.cookie_store_free.argtypes = [ctypes.c_void_p]

        lib.cookie_store_set.restype = ctypes.c_int
        lib.cookie_store_set.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_char_p)
        ]

        lib.cookie_store_get_by_domain.restype = ctypes.c_int
        lib.cookie_store_get_by_domain.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte)),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_char_p)
        ]

        lib.cookie_store_remove.restype = ctypes.c_int
        lib.cookie_store_remove.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_char_p)
        ]

        lib.cookie_store_get_all.restype = ctypes.c_int
        lib.cookie_store_get_all.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte)),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_char_p)
        ]

        lib.cookie_store_clear_all.restype = ctypes.c_int
        lib.cookie_store_clear_all.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_char_p)
        ]

        lib.free_knative_pointer.restype = None
        lib.free_knative_pointer.argtypes = [ctypes.c_void_p]

        self._store = lib.cookie_store_new()
        if not self._store:
            raise RuntimeError("Failed to create cookie store")

    def __del__(self):
        try:
            if hasattr(self, '_store') and self._store:
                lib.cookie_store_free(self._store)
        except Exception:
            pass
        finally:
            self._store = None

    def set(self, cookie):
        cookie_data = cookie.SerializeToString()
        data_ptr = (ctypes.c_ubyte * len(cookie_data)).from_buffer_copy(cookie_data)
        err_msg = ctypes.c_char_p()

        try:
            result = lib.cookie_store_set(
                self._store,
                data_ptr,
                len(cookie_data),
                ctypes.byref(err_msg)
            )
            if result != COOKIE_SUCCESS:
                error = err_msg.value.decode('utf-8') if err_msg.value else "Unknown error"
                raise RuntimeError(f"Failed to set cookie: {error}")
            return True
        finally:
            if err_msg.value:
                lib.free_knative_pointer(err_msg)

    def get_by_domain(self, domain):
        out_data = ctypes.POINTER(ctypes.c_ubyte)()
        out_len = ctypes.c_int()
        err_msg = ctypes.c_char_p()

        try:
            result = lib.cookie_store_get_by_domain(
                self._store,
                domain.encode('utf-8'),
                ctypes.byref(out_data),
                ctypes.byref(out_len),
                ctypes.byref(err_msg)
            )

            if result == COOKIE_NOT_FOUND:
                return []
            elif result != COOKIE_SUCCESS:
                error = err_msg.value.decode('utf-8') if err_msg.value else "Unknown error"
                raise RuntimeError(f"Failed to get cookies by domain: {error}")

            data = bytes(ctypes.cast(out_data, ctypes.POINTER(ctypes.c_ubyte * out_len.value)).contents)
            cookie_jar = CookieJar()
            cookie_jar.ParseFromString(data)
            return list(cookie_jar.cookies)
        finally:
            if out_data:
                lib.free_knative_pointer(out_data)
            if err_msg.value:
                lib.free_knative_pointer(err_msg)

    def remove(self, name, domain):
        err_msg = ctypes.c_char_p()

        try:
            result = lib.cookie_store_remove(
                self._store,
                name.encode('utf-8'),
                domain.encode('utf-8'),
                ctypes.byref(err_msg)
            )
            if result != COOKIE_SUCCESS:
                error = err_msg.value.decode('utf-8') if err_msg.value else "Unknown error"
                raise RuntimeError(f"Failed to remove cookie: {error}")
            return True
        finally:
            if err_msg.value:
                lib.free_knative_pointer(err_msg)

    def get_all(self):
        out_data = ctypes.POINTER(ctypes.c_ubyte)()
        out_len = ctypes.c_int()
        err_msg = ctypes.c_char_p()

        try:
            result = lib.cookie_store_get_all(
                self._store,
                ctypes.byref(out_data),
                ctypes.byref(out_len),
                ctypes.byref(err_msg)
            )

            if result == COOKIE_NOT_FOUND:
                return []
            elif result != COOKIE_SUCCESS:
                error = err_msg.value.decode('utf-8') if err_msg.value else "Unknown error"
                raise RuntimeError(f"Failed to get all cookies: {error}")

            data = bytes(ctypes.cast(out_data, ctypes.POINTER(ctypes.c_ubyte * out_len.value)).contents)
            cookie_jar = CookieJar()
            cookie_jar.ParseFromString(data)
            return list(cookie_jar.cookies)
        finally:
            if out_data:
                lib.free_knative_pointer(out_data)
            if err_msg.value:
                lib.free_knative_pointer(err_msg)

    def clear_all(self):
        err_msg = ctypes.c_char_p()

        try:
            result = lib.cookie_store_clear_all(
                self._store,
                ctypes.byref(err_msg)
            )
            if result != COOKIE_SUCCESS:
                error = err_msg.value.decode('utf-8') if err_msg.value else "Unknown error"
                raise RuntimeError(f"Failed to clear all cookies: {error}")
            return True
        finally:
            if err_msg.value:
                lib.free_knative_pointer(err_msg)
