import ctypes
from pathlib import Path
import platform
import os
from cookie_store_pb2 import Cookie, CookieJar

# build library path
def get_library_path():
    # determine project root
    project_root = Path(__file__).parent.parent.parent

    # determine target platform
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

    # determine build type
    build_type = os.getenv("BUILD_TYPE", "release").lower()
    if build_type == "debug":
        lib_suffix = "debugShared"
    else:
        lib_suffix = "releaseShared"

    # build library path
    base_lib_dir = project_root / "build" / "bin" / kn_target
    cookie_lib_dir = base_lib_dir / lib_suffix

    if system == "Windows":
        lib_name = "kcookie_store.dll"
    elif system == "Darwin":
        lib_name = "libkcookie_store.dylib"
    else:  # Linux
        lib_name = "libkcookie_store.so"

    lib_path = cookie_lib_dir / lib_name

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
        # Define function prototypes
        lib.cookie_store_new.restype = ctypes.c_void_p
        lib.cookie_store_new.argtypes = []

        lib.cookie_store_free.restype = None
        lib.cookie_store_free.argtypes = [ctypes.c_void_p]

        lib.cookie_store_set.restype = ctypes.c_int
        lib.cookie_store_set.argtypes = [
            ctypes.c_void_p,  # store
            ctypes.POINTER(ctypes.c_ubyte),  # cookieData
            ctypes.c_int,  # cookieLen
            ctypes.POINTER(ctypes.c_char_p)  # errMsg
        ]

        lib.cookie_store_get_by_domain.restype = ctypes.c_int
        lib.cookie_store_get_by_domain.argtypes = [
            ctypes.c_void_p,  # store
            ctypes.c_char_p,  # domain
            ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte)),  # outData
            ctypes.POINTER(ctypes.c_int),  # outLen
            ctypes.POINTER(ctypes.c_char_p)  # errMsg
        ]

        lib.cookie_store_remove.restype = ctypes.c_int
        lib.cookie_store_remove.argtypes = [
            ctypes.c_void_p,  # store
            ctypes.c_char_p,  # name
            ctypes.c_char_p,  # domain
            ctypes.POINTER(ctypes.c_char_p)  # errMsg
        ]

        lib.cookie_store_get_all.restype = ctypes.c_int
        lib.cookie_store_get_all.argtypes = [
            ctypes.c_void_p,  # store
            ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte)),  # outData
            ctypes.POINTER(ctypes.c_int),  # outLen
            ctypes.POINTER(ctypes.c_char_p)  # errMsg
        ]

        lib.cookie_store_clear_all.restype = ctypes.c_int
        lib.cookie_store_clear_all.argtypes = [
            ctypes.c_void_p,  # store
            ctypes.POINTER(ctypes.c_char_p)  # errMsg
        ]

        lib.free_knative_pointer.restype = None
        lib.free_knative_pointer.argtypes = [ctypes.c_void_p]

        # Create a new store instance
        self._store = lib.cookie_store_new()
        if not self._store:
            raise RuntimeError("Failed to create cookie store")

    def __del__(self):
        if hasattr(self, '_store') and self._store:
            lib.cookie_store_free(self._store)
            self._store = None

    def set(self, cookie):
        """Add or update a cookie in the store"""
        # Serialize the cookie to protobuf
        cookie_data = cookie.SerializeToString()

        # Prepare parameters
        data_ptr = (ctypes.c_ubyte * len(cookie_data)).from_buffer_copy(cookie_data)
        err_msg = ctypes.c_char_p()

        # Call the C function
        result = lib.cookie_store_set(
            self._store,
            data_ptr,
            len(cookie_data),
            ctypes.byref(err_msg)
        )

        # Handle error if any
        if result != COOKIE_SUCCESS:
            error = err_msg.value.decode('utf-8') if err_msg.value else "Unknown error"
            if err_msg:
                lib.free_knative_pointer(err_msg)
            raise RuntimeError(f"Failed to set cookie: {error}")

        return True

    def get_by_domain(self, domain):
        """Get cookies by domain"""
        # Prepare parameters
        out_data = ctypes.POINTER(ctypes.c_ubyte)()
        out_len = ctypes.c_int()
        err_msg = ctypes.c_char_p()

        # Call the C function
        result = lib.cookie_store_get_by_domain(
            self._store,
            domain.encode('utf-8'),
            ctypes.byref(out_data),
            ctypes.byref(out_len),
            ctypes.byref(err_msg)
        )

        # Handle results
        if result == COOKIE_NOT_FOUND:
            if err_msg:
                lib.free_knative_pointer(err_msg)
            return []
        elif result != COOKIE_SUCCESS:
            error = err_msg.value.decode('utf-8') if err_msg.value else "Unknown error"
            if err_msg:
                lib.free_knative_pointer(err_msg)
            raise RuntimeError(f"Failed to get cookies by domain: {error}")

        # Deserialize the protobuf data
        data = bytes(ctypes.cast(out_data, ctypes.POINTER(ctypes.c_ubyte * out_len.value)).contents)
        cookie_jar = CookieJar()
        cookie_jar.ParseFromString(data)

        # Free allocated memory
        lib.free_knative_pointer(out_data)
        if err_msg:
            lib.free_knative_pointer(err_msg)

        return list(cookie_jar.cookies)

    def remove(self, name, domain):
        """Remove a cookie by name and domain"""
        # Prepare parameters
        err_msg = ctypes.c_char_p()

        # Call the C function
        result = lib.cookie_store_remove(
            self._store,
            name.encode('utf-8'),
            domain.encode('utf-8'),
            ctypes.byref(err_msg)
        )

        # Handle error if any
        if result != COOKIE_SUCCESS:
            error = err_msg.value.decode('utf-8') if err_msg.value else "Unknown error"
            if err_msg:
                lib.free_knative_pointer(err_msg)
            raise RuntimeError(f"Failed to remove cookie: {error}")

        return True

    def get_all(self):
        """Get all cookies in the store"""
        # Prepare parameters
        out_data = ctypes.POINTER(ctypes.c_ubyte)()
        out_len = ctypes.c_int()
        err_msg = ctypes.c_char_p()

        # Call the C function
        result = lib.cookie_store_get_all(
            self._store,
            ctypes.byref(out_data),
            ctypes.byref(out_len),
            ctypes.byref(err_msg)
        )

        # Handle results
        if result == COOKIE_NOT_FOUND:
            if err_msg:
                lib.free_knative_pointer(err_msg)
            return []
        elif result != COOKIE_SUCCESS:
            error = err_msg.value.decode('utf-8') if err_msg.value else "Unknown error"
            if err_msg:
                lib.free_knative_pointer(err_msg)
            raise RuntimeError(f"Failed to get all cookies: {error}")

        # Deserialize the protobuf data
        data = bytes(ctypes.cast(out_data, ctypes.POINTER(ctypes.c_ubyte * out_len.value)).contents)
        cookie_jar = CookieJar()
        cookie_jar.ParseFromString(data)

        # Free allocated memory
        lib.free_knative_pointer(out_data)
        if err_msg:
            lib.free_knative_pointer(err_msg)

        return list(cookie_jar.cookies)

    def clear_all(self):
        """Clear all cookies in the store"""
        # Prepare parameters
        err_msg = ctypes.c_char_p()

        # Call the C function
        result = lib.cookie_store_clear_all(
            self._store,
            ctypes.byref(err_msg)
        )

        # Handle error if any
        if result != COOKIE_SUCCESS:
            error = err_msg.value.decode('utf-8') if err_msg.value else "Unknown error"
            if err_msg:
                lib.free_knative_pointer(err_msg)
            raise RuntimeError(f"Failed to clear all cookies: {error}")

        return True