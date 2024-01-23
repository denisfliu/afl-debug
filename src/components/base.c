#define _GNU_SOURCE

#include <stdarg.h>
#include <stdio.h>
#include <dlfcn.h>
#include <string.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/time.h>
#include <stddef.h>
#include <string.h>
#include <syscall.h>
#include <stdio.h>

#include "libsyscall_intercept_hook_point.h"

#if __GNUC__ < 6
  #ifndef likely
    #define likely(_x) (_x)
  #endif
  #ifndef unlikely
    #define unlikely(_x) (_x)
  #endif
#else
  #ifndef likely
    #define likely(_x) __builtin_expect(!!(_x), 1)
  #endif
  #ifndef unlikely
    #define unlikely(_x) __builtin_expect(!!(_x), 0)
  #endif
#endif

#ifdef WORD_SIZE_64
  #define AFL_RAND_RETURN unsigned long long
#else
  #define AFL_RAND_RETURN uint32_t
#endif


int needs_read_fd = 1;
int needs_time_fd = 1;
int32_t rand_below_fd;
int32_t urandom_fd;
int32_t time_fd;

static int hook(long syscall_number,
		long arg0, long arg1,
		long arg2, long arg3,
		long arg4, long arg5,
		long *result)
{
	(void) arg3;
	(void) arg4;
	(void) arg5;

	if (syscall_number == SYS_openat) {
		char buf_copy[256] = "";
    strcat(buf_copy, (char *) arg1);

		*result = syscall_no_intercept(SYS_openat, arg0, arg1, arg2, arg3, arg4);

    if (unlikely(needs_read_fd) && strcmp(buf_copy, "/dev/urandom") == 0) {
        urandom_fd = *result;
        printf("### DETECTED /dev/urandom | fd: %d ###", urandom_fd);

        needs_read_fd = 0;
        char* tmp = "/tmp/replay.rep";
        rand_below_fd = open(tmp, O_WRONLY | O_CREAT | O_APPEND, S_IRWXU);
        printf("### TEMP FD CREATED: %d", rand_below_fd);
    }


		return 0;
	}
	return 1;
}

/*
int open(const char *pathname, int flags, ...)
{
    int res;
    int mode = 0;
    int (*original_open)(const char *, int, ...);
    original_open = dlsym(RTLD_NEXT, "open");

    if (__OPEN_NEEDS_MODE (flags)) {
      va_list arg;
      va_start (arg, flags);
      mode = va_arg (arg, int);
      va_end (arg);
    }

    res = (*original_open)(pathname, flags, mode);

    if (unlikely(needs_read_fd) && strcmp(pathname, "/dev/urandom") == 0) {
        printf("### DETECTED /dev/urandom ### ");
        urandom_fd = res;
        needs_read_fd = 0;

        char* tmp = "/tmp/replay.rep";
        rand_below_fd = original_open(tmp, O_WRONLY | O_CREAT | O_APPEND, S_IRWXU);
    }
    return res;
}
*/

ssize_t read(int fildes, void *buf, size_t nbyte)
{
    ssize_t (*original_read)(int, void *, size_t);
    original_read = dlsym(RTLD_NEXT, "read");
    ssize_t res = (*original_read)(fildes, buf, nbyte);
    if (fildes == urandom_fd) {
        printf("### DETECTED /dev/urandom ### ");
        char *msg = "read from /dev/urandom\n";
        write(rand_below_fd, msg, 24);
        write(open("/tmp/aaa", O_WRONLY), msg, 24);
        // my_ck_write(rand_below_fd, &res, sizeof(AFL_RAND_RETURN), "rand_below_thing");
    }
    return res;
}

int gettimeofday(struct timeval *tp, void *tzp)
{
    int (*original_gettimeofday)(struct timeval *, void *);
    original_gettimeofday = dlsym(RTLD_NEXT, "gettimeofday");
    if (unlikely(needs_time_fd)) {
        needs_time_fd = 0;

        char* tmp = "/tmp/time.rep";
        time_fd = open(tmp, O_WRONLY | O_CREAT | O_APPEND, S_IRWXU);
    }

    int res = (*original_gettimeofday)(tp, tzp);
    write(time_fd, &tp, sizeof(tp));
    // my_ck_write(time_fd, &tp, sizeof(tp), "gettimeofday");
    return res;
}

static __attribute__((constructor)) void
start(void)
{
	intercept_hook_point = &hook;
}