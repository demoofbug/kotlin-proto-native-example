#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "cookie_store.h"
#include "cookie_store.pb-c.h"

// Fixed domains
const char* domains[] = {"example.com", "test.com", "demo.org"};
const size_t num_domains = sizeof(domains) / sizeof(domains[0]);

// Helper function to generate random string of given length
void random_string(char* str, size_t length) {
    static const char charset[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    for (size_t i = 0; i < length; i++) {
        int key = rand() % (int)(sizeof(charset) - 1);
        str[i] = charset[key];
    }
    str[length] = '\0';
}

// Print error and free message
void print_error(const char* action, char* errMsg) {
    if (errMsg) {
        printf("%s failed: %s\n", action, errMsg);
        free_knative_pointer(errMsg);
    } else {
        printf("%s failed\n", action);
    }
}

// Test 1: Add random cookie
void test_add_cookie(cookie_store_t store) {
    Cs__Cookie cookie = CS__COOKIE__INIT;

    char name[16];
    char value[32];
    random_string(name, sizeof(name)-1);
    random_string(value, sizeof(value)-1);

    cookie.name = name;
    cookie.value = value;
    cookie.domain = (char*)domains[rand() % num_domains];
    cookie.path = "/";
    cookie.secure = rand() % 2;
    cookie.httponly = rand() % 2;
    cookie.expirationtime = 0;

    size_t len = cs__cookie__get_packed_size(&cookie);
    unsigned char* buf = (unsigned char*)malloc(len);
    if (!buf) {
        printf("Memory allocation failed.\n");
        return;
    }
    cs__cookie__pack(&cookie, buf);

    char* errMsg = NULL;
    int ret = cookie_store_set(store, buf, (int)len, &errMsg);
    free(buf);

    if (ret != COOKIE_SUCCESS) {
        print_error("Set cookie", errMsg);
    } else {
        printf("Random cookie added: name=%s, value=%s, domain=%s\n", name, value, cookie.domain);
    }
}

// Test 2: Get cookies by domain
void test_get_by_domain(cookie_store_t store) {
    char domain[64];
    printf("Enter domain to get cookies: ");
    scanf("%63s", domain);

    unsigned char* outData = NULL;
    int outLen = 0;
    char* errMsg = NULL;

    int ret = cookie_store_get_by_domain(store, domain, &outData, &outLen, &errMsg);
    if (ret != COOKIE_SUCCESS) {
        print_error("Get by domain", errMsg);
    } else if (outLen == 0) {
        printf("No cookies found for domain %s\n", domain);
    } else {
        Cs__CookieJar* jar = cs__cookie_jar__unpack(NULL, outLen, outData);
        free_knative_pointer(outData);
        if (!jar) {
            printf("Failed to unpack cookies.\n");
            return;
        }
        printf("Cookies for domain %s:\n", domain);
        for (size_t i = 0; i < jar->n_cookies; i++) {
            Cs__Cookie* c = jar->cookies[i];
            printf("  name=%s, value=%s, path=%s\n", c->name, c->value, c->path);
        }
        cs__cookie_jar__free_unpacked(jar, NULL);
    }
}

// Test 3: Remove cookie by name and domain
void test_remove_cookie(cookie_store_t store) {
    char name[64], domain[64];
    printf("Enter cookie name to remove: ");
    scanf("%63s", name);
    printf("Enter domain: ");
    scanf("%63s", domain);

    char* errMsg = NULL;
    int ret = cookie_store_remove(store, name, domain, &errMsg);
    if (ret != COOKIE_SUCCESS) {
        print_error("Remove cookie", errMsg);
    } else {
        printf("Cookie removed: name=%s, domain=%s\n", name, domain);
    }
}

// Test 4: Get all cookies
void test_get_all(cookie_store_t store) {
    unsigned char* outData = NULL;
    int outLen = 0;
    char* errMsg = NULL;

    int ret = cookie_store_get_all(store, &outData, &outLen, &errMsg);
    if (ret != COOKIE_SUCCESS) {
        print_error("Get all cookies", errMsg);
    } else if (outLen == 0) {
        printf("No cookies in store.\n");
    } else {
        Cs__CookieJar* jar = cs__cookie_jar__unpack(NULL, outLen, outData);
        free_knative_pointer(outData);
        if (!jar) {
            printf("Failed to unpack cookies.\n");
            return;
        }
        printf("All cookies:\n");
        for (size_t i = 0; i < jar->n_cookies; i++) {
            Cs__Cookie* c = jar->cookies[i];
            printf("  name=%s, value=%s, domain=%s, path=%s\n", c->name, c->value, c->domain, c->path);
        }
        cs__cookie_jar__free_unpacked(jar, NULL);
    }
}

// Test 5: Clear all cookies
void test_clear_all(cookie_store_t store) {
    char* errMsg = NULL;
    int ret = cookie_store_clear_all(store, &errMsg);
    if (ret != COOKIE_SUCCESS) {
        print_error("Clear all cookies", errMsg);
    } else {
        printf("All cookies cleared.\n");
    }
}

// Main menu
int main() {
    srand((unsigned int)time(NULL));

    cookie_store_t store = cookie_store_new();
    if (!store) {
        printf("Failed to create CookieStore.\n");
        return 1;
    }

    int choice = -1;
    while (choice != 0) {
        printf("\n=== CookieStore Test Menu ===\n");
        printf("1. Add random cookie\n");
        printf("2. Get cookies by domain\n");
        printf("3. Remove cookie by name and domain\n");
        printf("4. Get all cookies\n");
        printf("5. Clear all cookies\n");
        printf("0. Exit\n");
        printf("Enter choice: ");
        if (scanf("%d", &choice) != 1) {
            while (getchar() != '\n'); // clear input buffer
            choice = -1;
            continue;
        }

        switch(choice) {
            case 1: test_add_cookie(store); break;
            case 2: test_get_by_domain(store); break;
            case 3: test_remove_cookie(store); break;
            case 4: test_get_all(store); break;
            case 5: test_clear_all(store); break;
            case 0: break;
            default: printf("Invalid choice.\n"); break;
        }
    }

    cookie_store_free(store);
    printf("Exiting program.\n");
    return 0;
}