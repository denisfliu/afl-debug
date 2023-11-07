#define _GNU_SOURCE

#include <stdio.h>
#include <dlfcn.h>

int urandom_fd = -1;
int open(const char *pathname, int flags)
{
    int *(*original_open)(const char *, int);
    int res;

    original_open = dlsym(RTLD_NEXT, "open");
    res = (*original_read)(pathname, flags);
    if (strcmp(pathname, "/dev/urandom") == 0)
    {
        urandom_fd = res
    }
    return res;
}

ssize_t read(int fildes, void *buf, size_t nbyte)
{
    ssize_t *(*original_read)(int, void *, size_t);
    original_read = dlsym(RTLD_NEXT, "read");
    return (*original_read)(fildes, buf, nbyte);
}

// exec time stuff needed