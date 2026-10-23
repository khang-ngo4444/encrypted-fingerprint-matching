#!/usr/bin/env python3
"""
Server Backend cho Live Demo & Dashboard He thong bao mat du lieu van tay (FHE CKKS).
Ho tro ca REST API, mo phong luong tu dong (Automation Flow), va phuc vu Web UI.
Tac gia: Ngo Hoang Nhat Khang & Ho Anh Tuan (VNUK)
"""

import os
import sys
import json
import csv
import struct
import math
import random
import time

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
BENCH_DIR = os.path.join(PROJECT_ROOT, "bench")

print(f"[INIT] Server Base Dir: {BASE_DIR}")
print(f"[INIT] Project Root: {PROJECT_ROOT}")

# 1. Load Du lieu Benchmark & Fidelity
fidelity_cache = {}
summary_metrics = {}
pipeline_timings = {}

def load_benchmarks():
    global fidelity_cache, summary_metrics, pipeline_timings
    
    # Fidelity cache: (anh_a, anh_b) -> dict
    fid_path = os.path.join(BENCH_DIR, "fidelity.csv")
    if os.path.exists(fid_path):
        with open(fid_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                a, b = r["anh_a"], r["anh_b"]
                fidelity_cache[(a, b)] = r
                fidelity_cache[(b, a)] = r
        print(f"[BENCH] Loaded {len(fidelity_cache)//2} unique fidelity pairs from fidelity.csv")

    # Pipeline timings
    pipe_path = os.path.join(BENCH_DIR, "pipeline_benchmark.csv")
    if os.path.exists(pipe_path):
        with open(pipe_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            for line in lines:
                if "," in line and not line.startswith("chang") and not line.startswith("#"):
                    parts = line.split(",")
                    if len(parts) >= 2:
                        try:
                            pipeline_timings[parts[0]] = float(parts[1])
                        except ValueError:
                            pass
        print(f"[BENCH] Loaded pipeline timings: {pipeline_timings}")

    # Summary metrics
    sum_path = os.path.join(BENCH_DIR, "tong_hop.csv")
    if os.path.exists(sum_path):
        with open(sum_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                k = f"{r.get('nhom')}_{r.get('hang_muc')}"
                summary_metrics[k] = r
        print(f"[BENCH] Loaded summary metrics: {len(summary_metrics)} items")

load_benchmarks()

# 2. Danh sach cac mau van tay FVC2002 (10 ngon x 8 lan quet = 80 ban ghi)
def get_sample_list():
    samples = []
    if os.path.exists(DATA_DIR):
        files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".bin"))
        for f in files:
            name = f.replace(".bin", "")
            parts = name.split("_")
            finger_id = parts[0]
            scan_id = parts[1] if len(parts) > 1 else "1"
            samples.append({
                "id": name,
                "finger": finger_id,
                "scan": scan_id,
                "file": f
            })
    return samples

# 3. Doc vector 512 chieu tu file .bin
def load_vector(name):
    path = os.path.join(DATA_DIR, f"{name}.bin")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        data = f.read()
    if len(data) != 4096: # 512 * 8 bytes
        return None
    return list(struct.unpack("<512d", data))

# 4. Tinh toan so khop (Simulation + Real Data Lookup)
def run_matching_flow(query_name, threshold=150.0):
    samples = get_sample_list()
    query_vec = load_vector(query_name)
    if not query_vec:
        return {"error": f"Không tìm thấy mẫu vân tay {query_name}"}

    query_finger = query_name.split("_")[0]
    results = []

    # So khop voi 79 ban ghi con lai
    for s in samples:
        target_name = s["id"]
        if target_name == query_name:
            continue
        
        target_finger = s["finger"]
        same_finger = (query_finger == target_finger)

        # Tim trong cache fidelity truoc
        fid = fidelity_cache.get((query_name, target_name))
        if fid:
            d_plain = float(fid["ban_ro"])
            d_fhe = float(fid["ban_ma"])
            abs_err = float(fid["sai_so_tuyet_doi"])
            rel_err = (abs_err / d_plain * 100.0) if d_plain > 0 else 0.0
        else:
            # Fallback tinh toan Euclidean thuc te
            target_vec = load_vector(target_name)
            if not target_vec:
                continue
            sq_diff = sum((q - t) ** 2 for q, t in zip(query_vec, target_vec))
            d_plain = round(sq_diff, 4)
            # Mo phong CKKS noise nho (mean ~0.0096%)
            noise = (random.random() - 0.5) * 0.04
            d_fhe = round(max(0.0, d_plain + noise), 4)
            abs_err = round(abs(d_fhe - d_plain), 5)
            rel_err = round(abs_err / d_plain * 100.0, 4) if d_plain > 0 else 0.0

        results.append({
            "target_id": target_name,
            "target_finger": target_finger,
            "same_finger": same_finger,
            "d_plain": d_plain,
            "d_fhe": d_fhe,
            "abs_err": abs_err,
            "rel_err_pct": rel_err
        })

    # Xep hang theo ban ro va ban ma
    results_by_plain = sorted(results, key=lambda x: x["d_plain"])
    for rank, r in enumerate(results_by_plain, 1):
        r["rank_plain"] = rank

    results_by_fhe = sorted(results, key=lambda x: x["d_fhe"])
    for rank, r in enumerate(results_by_fhe, 1):
        r["rank_fhe"] = rank
        # Gan quyet dinh nhan dang (khoang cach gan nhat vuot nguong hoac top 1)
        if rank == 1:
            r["decision"] = "KHỚP (MATCH)" if r["d_fhe"] <= threshold else "TỪ CHỐI (NO MATCH)"
            r["is_top1"] = True
        else:
            r["decision"] = "KHÁC NGÓN"
            r["is_top1"] = False

    top_match = results_by_fhe[0]
    rank_order_kept = all(r["rank_plain"] == r["rank_fhe"] for r in results_by_fhe[:5])

    # Chi tiet thoi gian luong xu ly theo khao sat Raspberry Pi 5
    telemetry = {
        "step1_sensor_capture": {
            "name": "Quét quang học cảm biến AS608",
            "device": "Cảm biến quang AS608 (500 DPI)",
            "duration_ms": 0.10,
            "status": "THÀNH CÔNG",
            "detail": "Thu thập ảnh mẫu vân tay 256x256, độ tương phản cục bộ chuẩn hóa"
        },
        "step2_feature_extract": {
            "name": "Trích xuất đặc trưng FingerCode",
            "device": "ESP32 (Cortex-M4 / Xtensa dual-core)",
            "duration_ms": 1.25,
            "status": "THÀNH CÔNG",
            "detail": "8 hướng Gabor × lưới 8×8 = 512 chiều, chuẩn hóa L2 (Scale K=32.0)"
        },
        "step3_client_encrypt": {
            "name": "Mã hóa CKKS trên thiết bị nhúng",
            "device": "SEAL-Embedded 1.1.0 (ESP32)",
            "duration_ms": pipeline_timings.get("thiet_bi_ma_hoa", 3.15),
            "status": "BẢO MẬT 128-BIT",
            "detail": "Mã hóa bằng Public Key (pk). Đa thức bậc 4096, 3 prime 27-bit, sinh bản mã 96 KB. Không giữ sk!"
        },
        "step4_network_transfer": {
            "name": "Truyền bản mã qua mạng",
            "channel": "Kênh TLS an toàn (ESP32 -> Raspberry Pi 5)",
            "duration_ms": pipeline_timings.get("nap_ban_ma", 0.13),
            "status": "HOÀN TẤT",
            "detail": "Truyền 96 KB Ciphertext lên Server. Kẻ nghe lén chỉ nhận được đa thức giả ngẫu nhiên."
        },
        "step5_server_matching": {
            "name": "So khớp đồng cấu trên Server",
            "device": "Raspberry Pi 5 (Microsoft SEAL 4.4.4, CKKS)",
            "duration_ms": pipeline_timings.get("server_tinh_toan", 22.51),
            "status": "KHÔNG GIẢI MÃ",
            "detail": "Tính d = q - e, bình phương d^2, relinearize, rescale, cộng dồn 9 vòng xoay Galois. MÁY CHỦ KHÔNG CÓ KHOÁ!"
        },
        "step6_keyholder_decrypt": {
            "name": "Giải mã kết quả tại trạm giữ khoá",
            "device": "Secure Element / Nơi giữ Secret Key (sk)",
            "duration_ms": pipeline_timings.get("giai_ma", 0.72),
            "status": "XÁC MINH DANH TÍNH",
            "detail": "Chỉ giải mã giá trị vô hướng khoảng cách Euclidean cuối cùng. Bản thân vân tay không bao giờ bị giải!"
        },
        "total_latency_ms": pipeline_timings.get("tong_pipeline", 26.51),
        "throughput_qps": 37.72
    }

    return {
        "query": query_name,
        "query_finger": query_finger,
        "database_size": len(results_by_fhe),
        "telemetry": telemetry,
        "top_match": top_match,
        "rank_order_kept_top5": rank_order_kept,
        "candidates": results_by_fhe[:15], # top 15 de hien thi bang
        "all_candidates_summary": {
            "avg_rel_error_pct": round(sum(r["rel_err_pct"] for r in results_by_fhe) / len(results_by_fhe), 4),
            "max_rel_error_pct": round(max(r["rel_err_pct"] for r in results_by_fhe), 4),
            "same_finger_top1": top_match["same_finger"]
        }
    }

# 5. Du lieu Khoi nghiep & Business Model Canvas (BMC)
def get_startup_bmc():
    return {
        "project_name": "BioCipher — Hệ thống xác thực vân tay bảo mật bằng mã hoá đồng cấu (FHE)",
        "authors": "Ngô Hoàng Nhật Khang & Hồ Anh Tuấn",
        "institution": "Viện Nghiên cứu & Đào tạo Việt - Anh (VNUK), Đại học Đà Nẵng",
        "competition": "VNUK Innovation Challenge 2026 — Bảng SV.Start-up",
        "legal_basis": "Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 (Hiệu lực từ 01/01/2026)",
        "core_message": "Quyền riêng tư không nên là cái giá của sự tiện lợi. Dữ liệu sinh trắc học không bao giờ tồn tại ở dạng đọc được trên máy chủ.",
        "bmc_grid": {
            "value_propositions": [
                {
                    "title": "Bảo mật tuyệt đối (Zero Plaintext)",
                    "desc": "Máy chủ xác định được khoảng cách giữa hai mẫu vân tay mà không giải mã ở bất kỳ bước nào. Quản trị viên hay hacker chiếm quyền máy chủ cũng không lấy được vân tay."
                },
                {
                    "title": "Tuân thủ pháp lý tức thì (Law 91/2025)",
                    "desc": "Giúp doanh nghiệp miễn trừ hoàn toàn rủi ro lộ lọt dữ liệu sinh trắc học nhạy cảm theo Luật 91/2025 có hiệu lực từ 01/01/2026."
                },
                {
                    "title": "Cắm vào hệ thống sẵn có (Plug-and-Play)",
                    "desc": "Khách hàng không cần thay cảm biến vân tay, không cần đổi bộ trích đặc trưng, không đổi CSDL. Chỉ thay duy nhất khâu so khớp."
                },
                {
                    "title": "Tốc độ phản hồi thời gian thực",
                    "desc": "Tổng thời gian toàn luồng chỉ 26,51 ms trên phần cứng phổ thông (Raspberry Pi 5 / Edge IoT), người dùng hoàn toàn không cảm nhận độ trễ."
                }
            ],
            "customer_segments": [
                {
                    "segment": "Doanh nghiệp chấm công & Kiểm soát ra vào",
                    "priority": "Ưu tiên số 1 (Giai đoạn thâm nhập)",
                    "rationale": "Đã có sẵn thiết bị, đang nắm giữ dữ liệu vân tay của hàng nghìn nhân sự, chịu áp lực thanh kiểm tra pháp lý đầu tiên."
                },
                {
                    "segment": "Ngân hàng số, Fintech & Cổng thanh toán eKYC",
                    "priority": "Ưu tiên số 2 (Mở rộng)",
                    "rationale": "Yêu cầu an toàn thông tin khắt khe cấp độ ngân hàng, sẵn sàng trả phí bản quyền cao để loại trừ rủi ro bồi thường rò rỉ dữ liệu."
                },
                {
                    "segment": "Nhà sản xuất thiết bị sinh trắc & Khóa thông minh (OEM)",
                    "priority": "Ưu tiên số 3 (Hợp tác B2B2C)",
                    "rationale": "Tích hợp sẵn SDK SEAL-Embedded trực tiếp vào firmware vi điều khiển bán ra thị trường quốc tế."
                }
            ],
            "channels": [
                "Bán trực tiếp B2B cho khối Doanh nghiệp và Tòa nhà thông minh",
                "Đối tác tích hợp hệ thống (System Integrators - SI) và nhà phân phối thiết bị máy chấm công",
                "Cổng Sandbox Kỹ thuật (Developer API & Testbed) cho phép kỹ sư khách hàng tự test độ trễ và độ an toàn trực tuyến"
            ],
            "customer_relationships": [
                "Hỗ trợ tích hợp kỹ thuật Dedicated 1:1 trong 48 giờ",
                "Cam kết mức độ dịch vụ (SLA) 99.9% uptime và bảo hiểm trách nhiệm an toàn thông tin",
                "Báo cáo định kỳ kiểm toán mã hóa và cập nhật bản vá lỗ hổng"
            ],
            "revenue_streams": [
                {
                    "stream": "License theo quy mô nhân sự (SaaS / On-Prem)",
                    "price": "45.000 VNĐ / nhân sự / năm (gói doanh nghiệp)",
                    "note": "Thu phí định kỳ hàng năm theo số lượng bản ghi vân tay quản lý"
                },
                {
                    "stream": "Phí tích hợp ban đầu (Setup & Integration)",
                    "price": "15.000.000 - 35.000.000 VNĐ / triển khai",
                    "note": "Cấu hình firmware cho thiết bị nhúng và đồng bộ CSDL bản mã"
                },
                {
                    "stream": "Bản quyền OEM SDK cho hãng sản xuất",
                    "price": "2,50 USD / thiết bị xuất xưởng",
                    "note": "Tích hợp firmware SEAL-Embedded vào chip khóa vân tay / thiết bị IoT"
                }
            ],
            "key_activities": [
                "Nghiên cứu & tối ưu hóa giải thuật CKKS trên phần cứng nhúng hạn chế (ESP32, ARM Cortex-M/A)",
                "Đóng gói SDK chuẩn C/C++, Python và RESTful Microservices",
                "Kiểm định an toàn mật mã đạt chuẩn FIPS 140-3 / ISO 27001",
                "Bảo vệ sở hữu trí tuệ (Bằng độc quyền giải pháp hữu ích)"
            ],
            "key_resources": [
                "Đội ngũ kỹ sư sáng lập VNUK chuyên sâu mật mã học lý thuyết & hệ thống nhúng",
                "Mã nguồn tối ưu độc quyền (Vá lỗi strict-aliasing của Microsoft SEAL-Embedded)",
                "Bộ dữ liệu kiểm nghiệm FVC2002 với 3.160 cặp đo đạc thực nghiệm đã chứng minh",
                "Hệ thống phòng lab nghiên cứu bảo mật tại VNUK"
            ],
            "key_partnerships": [
                "Viện Nghiên cứu & Đào tạo Việt - Anh (Bảo trợ khoa học và ươm tạo)",
                "Các nhà cung cấp thiết bị sinh trắc học tại Việt Nam (Ronald Jack, ZKTeco, Suprema)",
                "Cục An toàn thông tin & Hiệp hội An toàn thông tin Việt Nam (VNISA)",
                "Các công ty công nghệ nhân sự (HR Tech: Base.vn, 1Office)"
            ],
            "cost_structure": [
                "Chi phí R&D phần mềm nhúng và mật mã ứng dụng (40%)",
                "Chi phí kiểm định an toàn và chứng nhận bảo mật (20%)",
                "Chi phí hạ tầng máy chủ đo kiểm và cloud sandbox (15%)",
                "Chi phí bán hàng B2B, marketing hội thảo chuyên ngành (25%)"
            ]
        },
        "financial_projections": {
            "year1_2026": {
                "customers": "40 Doanh nghiệp (khoảng 15.000 nhân sự) + 1 đối tác OEM thử nghiệm",
                "revenue_vnd": 950000000,
                "cost_vnd": 820000000,
                "profit_vnd": 130000000,
                "margin_pct": 13.7,
                "milestone": "Đạt điểm hòa vốn cuối Q3/2026, hoàn thiện bộ SDK v1.0"
            },
            "year2_2027": {
                "customers": "180 Doanh nghiệp + 2 Ngân hàng/Fintech eKYC + 3 đối tác OEM",
                "revenue_vnd": 3450000000,
                "cost_vnd": 2150000000,
                "profit_vnd": 1300000000,
                "margin_pct": 37.6,
                "milestone": "Chiếm 15% thị phần bảo mật chấm công tại Đà Nẵng & TP.HCM, mở rộng Face FHE"
            },
            "year3_2028": {
                "customers": "520 Doanh nghiệp + 6 Ngân hàng + 8 đối tác OEM thiết bị",
                "revenue_vnd": 9200000000,
                "cost_vnd": 5100000000,
                "profit_vnd": 4100000000,
                "margin_pct": 44.5,
                "milestone": "Dẫn đầu thị trường xác thực sinh trắc học bảo mật tại Việt Nam, bắt đầu vươn ra Đông Nam Á"
            }
        },
        "risk_mitigation": [
            {
                "risk": "Rủi ro kỹ thuật: Tính toán FHE chậm hơn so với tính bản rõ (26.51ms vs 0.0004ms)",
                "mitigation": "Chế độ 1:1 (chấm công, xác thực cửa) chỉ mất 26.51ms (dưới ngưỡng nhận biết của mắt người ~50ms). Khi cần 1:N quy mô lớn, áp dụng phân cụm vector (LSH/Clustering) và tăng tốc AVX-512 / GPU."
            },
            {
                "risk": "Rủi ro thị trường: Khách hàng ngại thay đổi thói quen quản lý vân tay truyền thống",
                "mitigation": "Định vị sản phẩm theo mô hình 'Add-on Bảo Mật' không làm thay đổi quy trình vận hành. Tận dụng áp lực chế tài của Luật 91/2025 làm động lực chuyển dịch bắt buộc."
            },
            {
                "risk": "Rủi ro an toàn khóa: Nơi nắm giữ khoá bí mật (sk) bị tấn công",
                "mitigation": "Khoá bí mật không bao giờ lưu trên máy chủ đám mây. Khóa được phân mảnh (Threshold FHE) hoặc lưu trong chip phần cứng chuyên dụng (HSM / TPM / Secure Element) đặt tại trụ sở khách hàng."
            }
        ]
    }

# 6. Request Handler phuc vu Dashboard & REST API
class RequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Tranh cache khi demo video
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path

        if path == "/api/samples":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            samples = get_sample_list()
            self.wfile.write(json.dumps({"samples": samples}, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/benchmark":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            data = {
                "summary": summary_metrics,
                "pipeline": pipeline_timings,
                "verified_pairs_count": len(fidelity_cache) // 2,
                "avg_error_pct": 0.0096,
                "top1_fidelity_pct": 100.0,
                "rank_retention_pct": 99.71,
                "total_time_ms": 26.51,
                "security_bits": 128
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/bmc":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            bmc = get_startup_bmc()
            self.wfile.write(json.dumps(bmc, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/script":
            # Doc kich ban video demo 3 phut tu doc/cuoc-thi/kich-ban-video.md
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            script_path = os.path.join(PROJECT_ROOT, "doc", "cuoc-thi", "kich-ban-video.md")
            content = ""
            if os.path.exists(script_path):
                with open(script_path, "r", encoding="utf-8") as f:
                    content = f.read()
            self.wfile.write(json.dumps({"markdown": content}, ensure_ascii=False).encode("utf-8"))
            return

        # Phuc vu cac bieu do tu bench/charts/ neu duong dan la /charts/...
        elif path.startswith("/charts/"):
            chart_file = path.replace("/charts/", "")
            chart_path = os.path.join(BENCH_DIR, "charts", chart_file)
            if os.path.exists(chart_path):
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.end_headers()
                with open(chart_path, "rb") as f:
                    self.wfile.write(f.read())
                return

        # Mac dinh phuc vu file tinh tu thu muc demo_dashboard/
        if path == "/" or path == "":
            self.path = "/index.html"
            
        return super().do_GET()

    def do_POST(self):
        url = urlparse(self.path)
        path = url.path

        if path == "/api/run-flow":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                body = json.loads(post_data.decode("utf-8")) if post_data else {}
            except Exception:
                body = {}

            query_name = body.get("query_id")
            if not query_name:
                # Chon ngau nhien neu khong truyen
                samples = get_sample_list()
                if samples:
                    query_name = random.choice(samples)["id"]
                else:
                    query_name = "101_1"

            threshold = float(body.get("threshold", 150.0))
            res = run_matching_flow(query_name, threshold)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def run(port=8080):
    os.chdir(BASE_DIR)
    server_address = ("", port)
    try:
        httpd = HTTPServer(server_address, RequestHandler)
        print("=" * 70)
        print(f"🚀 SERVER LIVE DEMO & DASHBOARD ĐANG CHẠY TẠI:")
        print(f"👉 http://localhost:{port}")
        print(f"👉 http://127.0.0.1:{port}")
        print("=" * 70)
        print("💡 Tính năng đã sẵn sàng:")
        print("   1. Mô phỏng cảm biến AS608 -> ESP32 -> Raspberry Pi 5 hoàn chỉnh")
        print("   2. Chế độ Automation tự động nhận dạng liên tục cho quay video demo")
        print("   3. Bảng Business Model Canvas (BMC) & Kịch bản thuyết trình khởi nghiệp")
        print("=" * 70)
        httpd.serve_forever()
    except OSError as e:
        if port < 8090:
            print(f"[WARN] Cổng {port} đang bận, thử cổng {port+1}...")
            run(port + 1)
        else:
            raise e

if __name__ == "__main__":
    p = 8080
    if len(sys.argv) > 1:
        try:
            p = int(sys.argv[1])
        except ValueError:
            pass
    run(p)
