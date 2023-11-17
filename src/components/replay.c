#define _GNU_SOURCE

#include <stdio.h>
#include <dlfcn.h>
#include <string.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>

// Some copied macros from AFL++
#define my_ck_write(fd, buf, len, fn)                                                   \
    do                                                                                  \
    {                                                                                   \
                                                                                        \
        if (len <= 0)                                                                   \
            break;                                                                      \
        int _fd = (fd);                                                                 \
        int32_t _written = 0, _off = 0, _len = (int32_t)(len);                          \
                                                                                        \
        do                                                                              \
        {                                                                               \
                                                                                        \
            int32_t _res = write(_fd, (buf) + _off, _len);                              \
            if (_res != _len && (_res > 0 && _written + _res != _len))                  \
            {                                                                           \
                                                                                        \
                if (_res > 0)                                                           \
                {                                                                       \
                                                                                        \
                    _written += _res;                                                   \
                    _len -= _res;                                                       \
                    _off += _res;                                                       \
                }                                                                       \
                else                                                                    \
                {                                                                       \
                                                                                        \
                    RPFATAL(_res, "Short write to %s, fd %d (%d of %d bytes)", fn, _fd, \
                            _res, _len);                                                \
                }                                                                       \
            }                                                                           \
            else                                                                        \
            {                                                                           \
                                                                                        \
                break;                                                                  \
            }                                                                           \
                                                                                        \
        } while (1);                                                                    \
                                                                                        \
    } while (0)

#define my_ck_read(fd, buf, len, fn)                 \
    do                                               \
    {                                                \
                                                     \
        int32_t _len = (int32_t)(len);               \
        int32_t _res = read(fd, buf, _len);          \
        if (_res != _len)                            \
            RPFATAL(_res, "Short read from %s", fn); \
                                                     \
    } while (0)

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
int32_t time_fd;

int open(const char *pathname, int flags, ...)
{
    int (*original_open)(const char *, int, ...);
    original_open = dlsym(RTLD_NEXT, "open");
    int res = (*original_open)(pathname, flags);
    if (unlikely(needs_read_fd) && strcmp(pathname, "/dev/urandom") == 0)
    {
        printf("### DETECTED /dev/urandom ### ");
        rand_below_fd = res;
        needs_read_fd = 0;

        char* tmp = "/tmp/replay.rep";
        rand_below_fd = original_open(tmp, O_RDONLY);
    }
    return res;
}

ssize_t read(int fildes, void *buf, size_t nbyte)
{
    ssize_t (*original_read)(int, void *, size_t);
    ssize_t res;

    if (unlikely(fildes == urandom_fd)) {
        my_ck_read(rand_below_fd, &res, sizeof(AFL_RAND_RETURN), "urandom");
    } else {
      original_read = dlsym(RTLD_NEXT, "read");
      res = (*original_read)(fildes, buf, nbyte);
    }
    return res;
}

int gettimeofday(struct timeval *tp, void *tzp)
{
    if (unlikely(needs_time_fd)) {
        needs_time_fd = 0;

        char* tmp = "/tmp/time.rep";
        time_fd = open(tmp, O_RDONLY);
    }
    my_ck_read(time_fd, &tp, sizeof(tp), "gettimeofday")
    return 1;
}