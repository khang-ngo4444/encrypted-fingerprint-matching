cmake_minimum_required(VERSION 3.13)
project(fingerprint_he LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Thư mục gốc dự án, truyền vào mã nguồn để không phải viết đường dẫn tuyệt đối.
set(ROOT ${CMAKE_CURRENT_LIST_DIR})

# --- Microsoft SEAL 4.4.4 -----------------------------------------------------
# setup.sh clone và build vào SEAL/build. Không dùng find_package vì SEAL chưa
# được `make install` nên không có SEALConfig.cmake ở chỗ hệ thống tìm được.
set(SEAL_LIB ${ROOT}/SEAL/build/lib/libseal-4.4.a)
if(NOT EXISTS ${SEAL_LIB})
    message(FATAL_ERROR "Khong thay ${SEAL_LIB}. Chay `bash setup.sh` truoc.")
endif()

set(SEAL_INCLUDES
    ${ROOT}/SEAL/native/src
    ${ROOT}/SEAL/build/native/src
    ${ROOT}/SEAL/build/thirdparty/msgsl-src/include)

# zlib/zstd do SEAL tự build, phải link kèm vì SEAL bật nén serialization.
set(SEAL_DEPS ${ROOT}/SEAL/build/lib/libz.a ${ROOT}/SEAL/build/lib/libzstd.a)

# --- SEAL-Embedded, thư viện phía thiết bị ------------------------------------
set(SE_LIB ${ROOT}/device/build/bin/libseal_embedded.a)
set(SE_INCLUDES ${ROOT}/device/lib ${ROOT}/device/lib/shake256)

find_package(Threads REQUIRED)

# Chương trình chỉ dùng Microsoft SEAL
foreach(prog 11_fingerprint_match 12_benchmark 14_fidelity)
    add_executable(${prog} src/${prog}.cpp)
    target_include_directories(${prog} PRIVATE ${SEAL_INCLUDES})
    target_compile_definitions(${prog} PRIVATE CME_ROOT="${ROOT}")
    target_link_libraries(${prog} PRIVATE ${SEAL_LIB} ${SEAL_DEPS} Threads::Threads)
endforeach()

if(EXISTS ${SE_LIB})
    # Ứng dụng phía thiết bị, chỉ dùng SEAL-Embedded
    foreach(prog 10_fingerprint_encrypt 13_bench_device)
        add_executable(${prog} src/${prog}.c)
        target_include_directories(${prog} PRIVATE ${SE_INCLUDES})
        target_compile_definitions(${prog} PRIVATE
            SE_DATA_PATH="adapter_output_data" CME_ROOT="${ROOT}")
        target_link_libraries(${prog} PRIVATE ${SE_LIB} m)
    endforeach()

    # Nối cả hai đầu trong một tiến trình. 15_device_shim.c là lớp vỏ C: header
    # của SEAL-Embedded dùng cú pháp chỉ hợp lệ trong C nên không biên dịch được
    # bằng trình biên dịch C++.
    foreach(prog 15_bench_pipeline 16_match_report 17_workflow)
        add_executable(${prog} src/${prog}.cpp src/15_device_shim.c)
        target_include_directories(${prog} PRIVATE ${SEAL_INCLUDES} ${SE_INCLUDES})
        target_compile_definitions(${prog} PRIVATE
            SE_DATA_PATH="adapter_output_data" CME_ROOT="${ROOT}")
        target_link_libraries(${prog} PRIVATE
            ${SE_LIB} ${SEAL_LIB} ${SEAL_DEPS} Threads::Threads m)
    endforeach()
else()
    message(WARNING "Khong thay ${SE_LIB} - bo qua cac chuong trinh phia thiet bi")
endif()
