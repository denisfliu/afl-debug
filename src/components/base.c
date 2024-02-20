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
int counting_get_time_of_day = 0;

static int hook(long syscall_number,
		long arg0, long arg1,
		long arg2, long arg3,
		long arg4, long arg5,
		long *result)
{
	(void) arg3;
	(void) arg4;
	(void) arg5;

  	// use syscall_intercept library to detect openat() call
	if (syscall_number == SYS_openat) {
		char buf_copy[256] = {};
        strcpy(buf_copy, (char *) arg1);

		// in base.so we let the normal /dev/urandom be opened and read from, and just make a copy of its contents
		*result = syscall_no_intercept(SYS_openat, arg0, arg1, arg2, arg3, arg4);

		// check if the file being openat()'d is /dev/urandom
        if (unlikely(needs_rand_below_fd) && strcmp(buf_copy, "/dev/urandom") == 0) {
            urandom_fd = *result;
            printf("\n### base.c openat() /dev/urandom | fd: %d ###\n", urandom_fd);

			// if yes, then open /tmp/replay.rep as append so we can save /dev/urandom contents whenever read() is called
            needs_rand_below_fd = 0;
            char* tmp = "/tmp/replay.rep";
            rand_below_fd = open(tmp, O_WRONLY | O_CREAT | O_APPEND, S_IRWXU);
            printf("### base.c openat() /tmp/replay.rep | fd: %d ###\n", rand_below_fd);
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

	// if the file descriptor being read() is /dev/urandom, add the contents of that read() to our replay.rep
    if (fildes == urandom_fd) {
		printf("\nreading from /dev/urandom %ld bytes, writing copy of contents to /tmp/replay.rep\n", nbyte);
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

// gettimeofday essentially just does:
// 		tv->tv_sec = (long int) time ((time_t *) NULL);
// 		tv->tv_usec = 0L;
// which then modifies the rand_seed because AFL++ does this in afl-fuzz.c:
// 		gettimeofday(&tv, &tz);
//   	rand_set_seed(afl, tv.tv_sec ^ tv.tv_usec ^ getpid());
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

    FILE *fptr;
    fptr = fopen("/tmp/time.txt", "a");
    fprintf(fptr, "Index: %d | Timeofday: %llu\n", counting_get_time_of_day++, (tp->tv_sec * 1000000ULL) + tp->tv_usec);
    fclose(fptr);
    
    return res;
}

// these are irrelevant
// size_t fread(void *ptr, size_t size, size_t n, FILE *stream) {
// 	ssize_t (*original_fread)(void*, size_t, size_t, FILE*);
//     original_fread = dlsym(RTLD_NEXT, "fread");
//     ssize_t res = (*original_fread)(ptr, size, n, stream);

// 	printf("CALLING FREAD(%p, %ld, %ld, %p)\n", ptr, size, n, stream);

// 	return res;
// }
// size_t fwrite(const void *ptr, size_t size, size_t n, FILE *s) {
// 	ssize_t (*original_fwrite)(const void*, size_t, size_t, FILE*);
//     original_fwrite = dlsym(RTLD_NEXT, "fwrite");
//     ssize_t res = (*original_fwrite)(ptr, size, n, s);

// 	printf("CALLING FWRITE(%p, %ld, %ld, %p)\n", ptr, size, n, s);

// 	return res;
// }

static __attribute__((constructor)) void
start(void)
{
	intercept_hook_point = &hook;
}
