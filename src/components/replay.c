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

		// in replay.so we open /tmp/replay.rep instead of /dev/urandom
		if (unlikely(needs_rand_below_fd) && strcmp(buf_copy, "/dev/urandom") == 0) {
			char* tmp = "/tmp/replay.rep";
			*result = syscall_no_intercept(SYS_openat, arg0, tmp, arg2, arg3, arg4);
			urandom_fd = *result;
			printf("\n### replay.c openat() /dev/urandom (/tmp/replay.rep) | fd: %d ###\n", urandom_fd);

			needs_rand_below_fd = 0;
			// rand_below_fd = open(tmp, O_WRONLY | O_CREAT | O_APPEND, S_IRWXU);
			return 0;
		}

	}
	return 1;
}

// gettimeofday essentially just does:
// 		tv->tv_sec = (long int) time ((time_t *) NULL);
// 		tv->tv_usec = 0L;
// which then modifies the rand_seed because AFL++ does this in afl-fuzz.c:
// 		gettimeofday(&tv, &tz);
//   	rand_set_seed(afl, tv.tv_sec ^ tv.tv_usec ^ getpid());
int gettimeofday(struct timeval *tp, void *tzp)
{
    if (unlikely(needs_time_fd)) {
        needs_time_fd = 0;

        char* tmp = "/tmp/time.rep";
        time_fd = open(tmp, O_RDONLY);
    }
    read(time_fd, tp, sizeof(*tp));
    
    return 1;
}

// atoi
int fsrv_save_flag = 0;
int needs_fault_fd = 1;
int32_t fault_fd;
int atoi(const char *string) {
  if (strcmp(string, "replay_indicator_fsrv") == 0) {
    fsrv_save_flag = (1 + fsrv_save_flag) % 2;
    return 0;
  }
  
  if (fsrv_save_flag) {
    if (unlikely(needs_fault_fd)) {
      char* tmp = "/tmp/fault.rep";
      fault_fd = open(tmp, O_RDONLY);
      needs_fault_fd = 0;
    }
    int val;
    ssize_t bytesRead = read(fault_fd, &val, sizeof(int));
    //if (bytesRead != -1) return val;
    (void)bytesRead;
    return val;
  }

  int (*original_atoi)(const char *);
  original_atoi = dlsym(RTLD_NEXT, "atoi");
  int res = (*original_atoi)(string);
  return res;
}

unsigned long strtoul(const char *nptr, char **endptr, int base) {
  if (strcmp(nptr, "replay_indicator_fsrv") == 0) {
    fsrv_save_flag = (1 + fsrv_save_flag) % 2;
    return 0;
  }
  
  if (fsrv_save_flag) {
    if (unlikely(needs_fault_fd)) {
      char* tmp = "/tmp/fault.rep";
      fault_fd = open(tmp, O_RDONLY);
      needs_fault_fd = 0;
    }
    unsigned long val;
    ssize_t bytesRead = read(fault_fd, &val, sizeof(unsigned long));
    //if (bytesRead != -1) return val;
    (void)bytesRead;
    return val;
  }

  unsigned long  (*original_strtoul)(const char*, char **, int);
  original_strtoul = dlsym(RTLD_NEXT, "strtoul");
  unsigned long res = (*original_strtoul)(nptr, endptr, base);
  return res;
}

int next_strtoull_is_important = 0;
int needs_hash_fd = 1;
int32_t hash_fd;
unsigned long long strtoull(const char *nptr, char **endptr, int base) {
  if (strcmp(nptr, "replay_indicator_hash64") == 0) {
    next_strtoull_is_important = 1;
    return 0;
  }
  
  if (next_strtoull_is_important) {
    next_strtoull_is_important = 0;
    if (unlikely(needs_hash_fd)) {
      char* tmp = "/tmp/hash.rep";
      hash_fd = open(tmp, O_RDONLY);
      needs_hash_fd = 0;
    }
    unsigned long long val;
    ssize_t bytesRead = read(hash_fd, &val, sizeof(unsigned long long));
    //if (bytesRead != -1) return val;
    (void)bytesRead;
    return val;
  }

  unsigned long long  (*original_strtoull)(const char*, char **, int);
  original_strtoull = dlsym(RTLD_NEXT, "strtoull");
  unsigned long long res = (*original_strtoull)(nptr, endptr, base);
  return res;
}


static __attribute__((constructor)) void
start(void)
{
	intercept_hook_point = &hook;
}
