#include <algorithm>
#include <chrono>
#include <cmath>
#include <complex>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr double kPi = 3.141592653589793238462643383279502884;

[[noreturn]] void die(const std::string &message) {
    std::cerr << message << '\n';
    std::exit(EXIT_FAILURE);
}

double now_sec() {
    using clock = std::chrono::steady_clock;
    return std::chrono::duration<double>(clock::now().time_since_epoch()).count();
}

std::size_t parse_size(const char *text) {
    try {
        std::size_t position = 0;
        unsigned long long value = std::stoull(text, &position, 10);
        if (position != std::strlen(text)) {
            die("--size expects a positive integer");
        }
        return static_cast<std::size_t>(value);
    } catch (const std::exception &) {
        die("--size expects a positive integer");
    }
}

bool is_power_of_two(std::size_t value) {
    return value != 0 && (value & (value - 1)) == 0;
}

unsigned int log2_size(std::size_t value) {
    unsigned int log_value = 0;
    while ((std::size_t{1} << log_value) < value) {
        ++log_value;
    }
    return log_value;
}

std::size_t reverse_bits(std::size_t value, unsigned int bit_count) {
    std::size_t reversed = 0;
    for (unsigned int i = 0; i < bit_count; ++i) {
        reversed = (reversed << 1U) | (value & 1U);
        value >>= 1U;
    }
    return reversed;
}

void fill_input(std::vector<std::complex<double>> &input) {
    const std::size_t n = input.size();
    for (std::size_t i = 0; i < n; ++i) {
        const double phase = 2.0 * kPi * static_cast<double>(i) / static_cast<double>(n);
        const double real_part = 0.75 * std::cos(phase) + 0.25 * std::sin(7.0 * phase);
        const double imag_part = 0.50 * std::sin(3.0 * phase) - 0.20 * std::cos(5.0 * phase);
        input[i] = {real_part, imag_part};
    }
}

void compute_dft(const std::vector<std::complex<double>> &input, std::vector<std::complex<double>> &output) {
    const std::size_t n = input.size();
    for (std::size_t k = 0; k < n; ++k) {
        std::complex<double> sum{0.0, 0.0};
        const double angle_step = -2.0 * kPi * static_cast<double>(k) / static_cast<double>(n);
        const std::complex<double> twiddle_step{std::cos(angle_step), std::sin(angle_step)};
        std::complex<double> twiddle{1.0, 0.0};

        for (std::size_t t = 0; t < n; ++t) {
            sum += input[t] * twiddle;
            twiddle *= twiddle_step;
        }

        output[k] = sum;
    }
}

void compute_fft_in_place(std::vector<std::complex<double>> &data) {
    const std::size_t n = data.size();
    const unsigned int bit_count = log2_size(n);

    for (std::size_t i = 0; i < n; ++i) {
        const std::size_t j = reverse_bits(i, bit_count);
        if (j > i) {
            std::swap(data[i], data[j]);
        }
    }

    for (std::size_t len = 2; len <= n; len <<= 1U) {
        const double angle = -2.0 * kPi / static_cast<double>(len);
        const std::complex<double> wlen{std::cos(angle), std::sin(angle)};

        for (std::size_t start = 0; start < n; start += len) {
            std::complex<double> w{1.0, 0.0};
            const std::size_t half = len / 2U;
            for (std::size_t offset = 0; offset < half; ++offset) {
                const std::complex<double> u = data[start + offset];
                const std::complex<double> v = data[start + offset + half] * w;
                data[start + offset] = u + v;
                data[start + offset + half] = u - v;
                w *= wlen;
            }
        }
    }
}

double max_abs_diff(const std::vector<std::complex<double>> &lhs, const std::vector<std::complex<double>> &rhs) {
    double max_error = 0.0;
    for (std::size_t i = 0; i < lhs.size(); ++i) {
        const double error = std::abs(lhs[i] - rhs[i]);
        max_error = std::max(max_error, error);
    }
    return max_error;
}

void print_usage(const char *program_name) {
    std::cerr << "Usage: " << program_name << " [--size N]\n";
}

}  // namespace

int main(int argc, char **argv) {
    std::size_t n = 65536;

    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--size") == 0) {
            if (i + 1 >= argc) {
                print_usage(argv[0]);
                return EXIT_FAILURE;
            }
            n = parse_size(argv[++i]);
        } else if (std::strcmp(argv[i], "--help") == 0 || std::strcmp(argv[i], "-h") == 0) {
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

    std::vector<std::complex<double>> input(n);
    std::vector<std::complex<double>> dft_output(n);
    std::vector<std::complex<double>> fft_output(n);

    fill_input(input);

    const double dft_start = now_sec();
    compute_dft(input, dft_output);
    const double dft_elapsed = now_sec() - dft_start;

    fft_output = input;
    const double fft_start = now_sec();
    compute_fft_in_place(fft_output);
    const double fft_elapsed = now_sec() - fft_start;

    const double fft_error = max_abs_diff(dft_output, fft_output);

    std::cout << "algorithm,n,elapsed_sec,max_abs_error\n";
    std::cout << "dft," << n << ',' << dft_elapsed << ",0.000000000000e+00\n";
    std::cout << "fft," << n << ',' << fft_elapsed << ',' << fft_error << '\n';

    return EXIT_SUCCESS;
}