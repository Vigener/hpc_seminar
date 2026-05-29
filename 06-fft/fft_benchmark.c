#define _POSIX_C_SOURCE 200809L

#include <complex.h>
#include <errno.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static const double PI = 3.141592653589793238462643383279502884;

static void die(const char *message) {
    fprintf(stderr, "%s\n", message);
    exit(EXIT_FAILURE);
}

static double now_sec(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        die("clock_gettime failed");
    }
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

static size_t parse_size(const char *text) {
    char *end = NULL;
    errno = 0;
    unsigned long long value = strtoull(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0') {
        die("--size expects a positive integer");
    }
    return (size_t)value;
}

static int is_power_of_two(size_t value) {
    return value != 0 && (value & (value - 1)) == 0;
}

static unsigned int log2_size(size_t value) {
    unsigned int log_value = 0;
    while (((size_t)1 << log_value) < value) {
        ++log_value;
    }
    return log_value;
}

static size_t reverse_bits(size_t value, unsigned int bit_count) {
    size_t reversed = 0;
    for (unsigned int i = 0; i < bit_count; ++i) {
        reversed = (reversed << 1U) | (value & 1U);
        value >>= 1U;
    }
    return reversed;
}

static void fill_input(double complex *input, size_t n) {
    for (size_t i = 0; i < n; ++i) {
        double phase = 2.0 * PI * (double)i / (double)n;
        double real_part = 0.75 * cos(phase) + 0.25 * sin(7.0 * phase);
        double imag_part = 0.50 * sin(3.0 * phase) - 0.20 * cos(5.0 * phase);
        input[i] = real_part + imag_part * I;
    }
}

static void compute_dft(const double complex *input, double complex *output, size_t n) {
    for (size_t k = 0; k < n; ++k) {
        double complex sum = 0.0 + 0.0 * I;
        double angle_step = -2.0 * PI * (double)k / (double)n;
        double complex twiddle_step = cos(angle_step) + sin(angle_step) * I;
        double complex twiddle = 1.0 + 0.0 * I;

        for (size_t t = 0; t < n; ++t) {
            sum += input[t] * twiddle;
            twiddle *= twiddle_step;
        }

        output[k] = sum;
    }
}

static void compute_fft_in_place(double complex *data, size_t n) {
    unsigned int bit_count = log2_size(n);

    for (size_t i = 0; i < n; ++i) {
        size_t j = reverse_bits(i, bit_count);
        if (j > i) {
            double complex tmp = data[i];
            data[i] = data[j];
            data[j] = tmp;
        }
    }

    for (size_t len = 2; len <= n; len <<= 1U) {
        double angle = -2.0 * PI / (double)len;
        double complex wlen = cos(angle) + sin(angle) * I;

        for (size_t start = 0; start < n; start += len) {
            double complex w = 1.0 + 0.0 * I;
            size_t half = len / 2U;
            for (size_t offset = 0; offset < half; ++offset) {
                double complex u = data[start + offset];
                double complex v = data[start + offset + half] * w;
                data[start + offset] = u + v;
                data[start + offset + half] = u - v;
                w *= wlen;
            }
        }
    }
}

static double max_abs_diff(const double complex *lhs, const double complex *rhs, size_t n) {
    double max_error = 0.0;
    for (size_t i = 0; i < n; ++i) {
        double error = cabs(lhs[i] - rhs[i]);
        if (error > max_error) {
            max_error = error;
        }
    }
    return max_error;
}

static void print_usage(const char *program_name) {
    fprintf(stderr, "Usage: %s [--size N]\n", program_name);
}

int main(int argc, char **argv) {
    size_t n = 65536;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--size") == 0) {
            if (i + 1 >= argc) {
                print_usage(argv[0]);
                return EXIT_FAILURE;
            }
            n = parse_size(argv[++i]);
        } else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            print_usage(argv[0]);
            return EXIT_SUCCESS;
        } else {
            print_usage(argv[0]);
            return EXIT_FAILURE;
        }
    }

    if (!is_power_of_two(n)) {
        die("--size must be a power of two");
    }

    double complex *input = malloc(sizeof(*input) * n);
    double complex *dft_output = malloc(sizeof(*dft_output) * n);
    double complex *fft_output = malloc(sizeof(*fft_output) * n);
    if (input == NULL || dft_output == NULL || fft_output == NULL) {
        free(input);
        free(dft_output);
        free(fft_output);
        die("failed to allocate memory");
    }

    fill_input(input, n);

    double dft_start = now_sec();
    compute_dft(input, dft_output, n);
    double dft_elapsed = now_sec() - dft_start;

    memcpy(fft_output, input, sizeof(*fft_output) * n);
    double fft_start = now_sec();
    compute_fft_in_place(fft_output, n);
    double fft_elapsed = now_sec() - fft_start;

    double fft_error = max_abs_diff(dft_output, fft_output, n);

    printf("algorithm,n,elapsed_sec,max_abs_error\n");
    printf("dft,%zu,%.9f,%.12e\n", n, dft_elapsed, 0.0);
    printf("fft,%zu,%.9f,%.12e\n", n, fft_elapsed, fft_error);

    free(input);
    free(dft_output);
    free(fft_output);
    return EXIT_SUCCESS;
}