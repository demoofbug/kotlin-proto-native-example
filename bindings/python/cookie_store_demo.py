import random
import string
import time
from cookie_store_bridge import CookieStore  # Assuming the bridge is in this module
from cookie_store_pb2 import Cookie, CookieJar

# Fixed domains
DOMAINS = ["example.com", "test.com", "demo.org"]

def random_string(length):
    """Generate a random string of given length"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def print_menu():
    """Print the test menu options"""
    print("\n=== CookieStore Test Menu ===")
    print("1. Add random cookie")
    print("2. Get cookies by domain")
    print("3. Remove cookie by name and domain")
    print("4. Get all cookies")
    print("5. Clear all cookies")
    print("0. Exit")

def test_add_cookie(store):
    """Test adding a random cookie"""
    cookie = Cookie()
    cookie.name = random_string(15)
    cookie.value = random_string(31)
    cookie.domain = random.choice(DOMAINS)
    cookie.path = "/"
    cookie.secure = random.choice([True, False])
    cookie.httpOnly = random.choice([True, False])
    cookie.expirationTime = 0

    try:
        store.set(cookie)
        print(f"Random cookie added: name={cookie.name}, value={cookie.value}, domain={cookie.domain}")
    except Exception as e:
        print(f"Set cookie failed: {e}")

def test_get_by_domain(store):
    """Test getting cookies by domain"""
    domain = input("Enter domain to get cookies: ").strip()

    try:
        cookies = store.get_by_domain(domain)
        if not cookies:
            print(f"No cookies found for domain {domain}")
        else:
            print(f"Cookies for domain {domain}:")
            for c in cookies:
                print(f"  name={c.name}, value={c.value}, path={c.path}")
    except Exception as e:
        print(f"Get by domain failed: {e}")

def test_remove_cookie(store):
    """Test removing a cookie by name and domain"""
    name = input("Enter cookie name to remove: ").strip()
    domain = input("Enter domain: ").strip()

    try:
        store.remove(name, domain)
        print(f"Cookie removed: name={name}, domain={domain}")
    except Exception as e:
        print(f"Remove cookie failed: {e}")

def test_get_all(store):
    """Test getting all cookies"""
    try:
        cookies = store.get_all()
        if not cookies:
            print("No cookies in store.")
        else:
            print("All cookies:")
            for c in cookies:
                print(f"  name={c.name}, value={c.value}, domain={c.domain}, path={c.path}")
    except Exception as e:
        print(f"Get all cookies failed: {e}")

def test_clear_all(store):
    """Test clearing all cookies"""
    try:
        store.clear_all()
        print("All cookies cleared.")
    except Exception as e:
        print(f"Clear all cookies failed: {e}")

def main():
    """Main test program"""
    random.seed(time.time())

    try:
        store = CookieStore()
    except Exception as e:
        print(f"Failed to create CookieStore: {e}")
        return

    while True:
        print_menu()
        choice = input("Enter choice: ").strip()

        try:
            choice = int(choice)
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        if choice == 0:
            break
        elif choice == 1:
            test_add_cookie(store)
        elif choice == 2:
            test_get_by_domain(store)
        elif choice == 3:
            test_remove_cookie(store)
        elif choice == 4:
            test_get_all(store)
        elif choice == 5:
            test_clear_all(store)
        else:
            print("Invalid choice. Please try again.")

    print("Exiting program.")

if __name__ == "__main__":
    main()