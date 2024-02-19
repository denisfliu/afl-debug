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


// openat rand below
int needs_rand_below_fd = 1;
int32_t urandom_fd;
int32_t rand_below_fd;

// gettimeofday
int needs_time_fd = 1;
int32_t time_fd;

// experiment
int needs_read_pipe_fd = 1;
int needs_write_pipe_fd = 1;
int32_t read_pipe_fd;
int32_t write_pipe_fd;

// experiment
int needs_file_out_fd = 1;
int32_t next_file_out_fd = 13;
int32_t file_out_fd = 13;

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

        if (unlikely(needs_rand_below_fd) && strcmp(buf_copy, "/dev/urandom") == 0) {
            urandom_fd = *result;
            printf("### base.c openat() /dev/urandom | fd: %d ###", urandom_fd);

            needs_rand_below_fd = 0;
            char* tmp = "/tmp/replay.rep";
            rand_below_fd = open(tmp, O_WRONLY | O_CREAT | O_APPEND, S_IRWXU);
        }


		return 0;
	}
	return 1;
}

ssize_t read(int fildes, void *buf, size_t nbyte)
{
    ssize_t (*original_read)(int, void *, size_t);
    original_read = dlsym(RTLD_NEXT, "read");
    ssize_t res = (*original_read)(fildes, buf, nbyte);
    if (fildes == urandom_fd) {
        write(rand_below_fd, buf, nbyte);
    }
    /*
    else if (fildes == 198) {
      if (unlikely(needs_read_pipe_fd)) {
        needs_read_pipe_fd = 0;
        char* tmp = "/tmp/read_pipe.rep";
        read_pipe_fd = open(tmp, O_WRONLY | O_CREAT | O_APPEND, S_IRWXU);

      }
      write(read_pipe_fd, buf, nbyte);
    }
    else if (fildes == 47) {
      next_file_out_fd = res;
    }
    */

    return res;
}

/*
ssize_t write(int fildes, const void *buf, size_t nbyte) 
{
    ssize_t (*original_write)(int, const void *, size_t);
    original_write = dlsym(RTLD_NEXT, "write");
    ssize_t res = (*original_write)(fildes, buf, nbyte);

    if (fildes == 1000) {

    }
    else if (fildes == 199) {
      if (unlikely(needs_write_pipe_fd)) {
        needs_write_pipe_fd = 0;
        char* tmp = "/tmp/write_pipe.rep";
        write_pipe_fd = open(tmp, O_WRONLY | O_CREAT | O_APPEND, S_IRWXU);

      }
      write(write_pipe_fd, buf, nbyte);
    }
    else if (fildes == next_file_out_fd) {
      if (unlikely(needs_write_pipe_fd)) {
        needs_file_out_fd = 0;
        char* tmp = "/tmp/file_out.rep";
        file_out_fd = open(tmp, O_WRONLY | O_CREAT | O_APPEND, S_IRWXU);

      }
      write(file_out_fd, buf, nbyte);
    }

    return res;
}
*/


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
    write(time_fd, tp, sizeof(*tp));
    write(time_fd, tzp, sizeof(*tzp));
    // my_ck_write(time_fd, &tp, sizeof(tp), "gettimeofday");
    return res;
}

static __attribute__((constructor)) void
start(void)
{
	intercept_hook_point = &hook;
}
