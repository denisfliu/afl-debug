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
#include <stdlib.h>

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


int needs_rand_below_fd = 1;
int32_t urandom_fd;

int needs_time_fd = 1;
int32_t time_fd;

int needs_read_pipe_fd = 1;
int needs_write_pipe_fd = 1;
int32_t read_pipe_fd;
int32_t write_pipe_fd;

// experiment
int needs_file_out_fd = 1;
int32_t next_file_out_fd = 13;
int32_t file_out_fd;

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

    if (unlikely(needs_rand_below_fd) && strcmp(buf_copy, "/dev/urandom") == 0) {
        char* tmp = "/tmp/replay.rep";
        *result = syscall_no_intercept(SYS_openat, arg0, tmp, arg2, arg3, arg4);
        urandom_fd = *result;
        printf("### replay.c openat() /dev/urandom | fd: %d ###", urandom_fd);

        needs_rand_below_fd = 0;
        // rand_below_fd = open(tmp, O_WRONLY | O_CREAT | O_APPEND, S_IRWXU);
	return 0;
    }
	}
	return 1;
}

/*
ssize_t read(int fildes, void *buf, size_t nbyte)
{
    ssize_t (*original_read)(int, void *, size_t);
    original_read = dlsym(RTLD_NEXT, "read");
    ssize_t res = (*original_read)(fildes, buf, nbyte);

    if (unlikely(fildes == 198)) {
      if (unlikely(needs_read_pipe_fd)) {
        needs_read_pipe_fd = 0;
        char* tmp = "/tmp/read_pipe.rep";
        read_pipe_fd = open(tmp, O_RDONLY);
      }
      return (*original_read)(read_pipe_fd, buf, nbyte);
    }
    else if (fildes == urandom_fd) {
        printf("### READING FROM FAKE DEV URANDOM read() /dev/urandom ###");
    }
    else if (unlikely(fildes == 47)) {
      next_file_out_fd = res;
    }
    return res;
}
*/

/*
ssize_t write(int fildes, const void *buf, size_t nbyte) 
{
    ssize_t (*original_write)(int, const void *, size_t);
    original_write = dlsym(RTLD_NEXT, "write");
    ssize_t res;
    if (0) {

    }
    else if (unlikely(fildes == 199)) {
      void *buf1 = (void*) malloc(nbyte);
      if (unlikely(needs_write_pipe_fd)) {
        needs_write_pipe_fd = 0;
        char* tmp = "/tmp/write_pipe.rep";
        write_pipe_fd = open(tmp, O_RDONLY);
      }
      read(write_pipe_fd, buf1, nbyte);
      res = (*original_write)(fildes, buf1, nbyte);
      free(buf1);
    }
    else if (unlikely(fildes == 47)) {
      void *buf1 = (void*) malloc(nbyte);
      if (unlikely(needs_file_out_fd)) {
        needs_file_out_fd = 0;
        char* tmp = "/tmp/file_out.rep";
        file_out_fd = open(tmp, O_RDONLY);
      }
      read(file_out_fd, buf1, nbyte);
      res = (*original_write)(fildes, buf1, nbyte);
      free(buf1);
    } 
    else {
      res = (*original_write)(fildes, buf, nbyte);
    }

    return res;
}
*/

int gettimeofday(struct timeval *tp, void *tzp)
{
    if (unlikely(needs_time_fd)) {
        needs_time_fd = 0;

        char* tmp = "/tmp/time.rep";
        time_fd = open(tmp, O_RDONLY);
    }
    read(time_fd, tp, sizeof(*tp));
    read(time_fd, tzp, sizeof(*tzp));
    return 1;
}

static __attribute__((constructor)) void
start(void)
{
	intercept_hook_point = &hook;
}
