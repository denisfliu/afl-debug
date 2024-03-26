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

// for backtrace
#include <execinfo.h>
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

    return res;
}

/*/////////////////////////////
//////////     atoi    ////////
/////////////////////////////*/
// atoi
int fsrv_save_flag = 0;
int needs_fault_fd = 1;
int32_t fault_fd;

int atoi(const char *string) {
  int (*original_atoi)(const char *);
  original_atoi = dlsym(RTLD_NEXT, "atoi");
  int res = (*original_atoi)(string);
  if (strcmp(string, "replay_indicator_fsrv") == 0) {
    fsrv_save_flag = (1 + fsrv_save_flag) % 2;
    return 0;
  }
  
  if (fsrv_save_flag) {
    if (unlikely(needs_fault_fd)) {
      char* tmp = "/tmp/fault.rep";
      fault_fd = open(tmp, O_WRONLY | O_CREAT | O_APPEND, S_IRWXU);
      needs_fault_fd = 0;
    }
    write(fault_fd, &res, sizeof(int));
    return res;
  }
  return res;
}

/*/////////////////////////////
//////////   strtoul  ////////
/////////////////////////////*/
unsigned long strtoul(const char *nptr, char **endptr, int base) {
  unsigned long (*original_strtoul)(const char *, char **, int);
  original_strtoul = dlsym(RTLD_NEXT, "strtoul");
  unsigned long res = (*original_strtoul)(nptr, endptr, base);
  if (strcmp(nptr, "replay_indicator_fsrv") == 0) {
    fsrv_save_flag = (1 + fsrv_save_flag) % 2;
    return 0;
  }

  if (fsrv_save_flag) {
    if (unlikely(needs_fault_fd)) {
      char* tmp = "/tmp/fault.rep";
      fault_fd = open(tmp, O_WRONLY | O_CREAT | O_APPEND, S_IRWXU);
      needs_fault_fd = 0;
    }
    write(fault_fd, &res, sizeof(unsigned long));
    return res;
  }
  return res;
}

/*/////////////////////////////
//////////   strtoull  ////////
/////////////////////////////*/
int next_strtoull_is_important = 0;
int needs_hash_fd = 1;
int32_t hash_fd;

unsigned long long strtoull(const char *nptr, char **endptr, int base) {
  unsigned long long  (*original_strtoull)(const char*, char **, int);
  original_strtoull = dlsym(RTLD_NEXT, "strtoull");
  unsigned long long res = (*original_strtoull)(nptr, endptr, base);
  if (strcmp(nptr, "replay_indicator_hash64") == 0) {
    next_strtoull_is_important = 1;
    return 0;
  } else if (strcmp(nptr, "replay_indicator_fsrv") == 0) {
    fsrv_save_flag = (1 + fsrv_save_flag) % 2;
    return 0;
  }
  
  if (next_strtoull_is_important) {
    next_strtoull_is_important = 0;
    if (unlikely(needs_hash_fd)) {
      char* tmp = "/tmp/hash.rep";
      hash_fd = open(tmp, O_WRONLY | O_CREAT | O_APPEND, S_IRWXU);
      needs_hash_fd = 0;
    }
    write(hash_fd, &res, sizeof(unsigned long long));
    return res;
  } else if (fsrv_save_flag) {
    if (unlikely(needs_fault_fd)) {
      char* tmp = "/tmp/fault.rep";
      fault_fd = open(tmp, O_WRONLY | O_CREAT | O_APPEND, S_IRWXU);
      needs_fault_fd = 0;
    }
    write(hash_fd, &res, sizeof(unsigned long long));
    return res;
  }

  return res;
}


/*
int select(int nfds, fd_set *readfds, fd_set *writefds, fd_set *exceptfds, struct timeval *timeout) {
    int (*original_select)(int nfds, fd_set *readfds, fd_set *writefds, fd_set *exceptfds, struct timeval *timeout);
    original_select = dlsym(RTLD_NEXT, "select");
    int res = original_select(nfds, readfds, writefds, exceptfds, timeout);

    FILE *fptr;
    fptr = fopen("/tmp/select_output.txt", "a");
    fprintf(fptr, "\nINTERCEPTING SELECT(%d, %p, %p, %p, %p)\n", nfds, readfds, writefds, exceptfds, timeout);
    fclose(fptr);

    return res;
}
*/

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

// trying to check if forkserver has anything to do with it; I don't think it does
// pid_t fork(void) {
// 	pid_t (*original_fork)(void);
// 	original_fork = dlsym(RTLD_NEXT, "fork");
// 	pid_t res = (*original_fork)();

// 	printf("\nCALLED FORK: %d\n", res);

// 	return res;
// }

static __attribute__((constructor)) void
start(void)
{
	intercept_hook_point = &hook;
}
