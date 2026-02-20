#!/usr/bin/env python3
"""
NAS 자동 업로드 스크립트 (Windows용)
- Data 폴더 하위에 금일자(YYYY-MM-DD) 폴더 생성
- 지정한 로컬 폴더의 파일을 FTP로 업로드
- 진행률 표시
"""

import ftplib
import os
import sys
from datetime import datetime

# ===== 설정 =====
NAS_HOST = "oracle23cr2.myasustor.com"
NAS_PORT = 3000
NAS_USER = "admin"
NAS_PASS = "rlaxodhks8520!@#"
NAS_BASE = "/Data"
# ================


def format_size(size):
    """바이트를 읽기 쉬운 단위로 변환"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def scan_folder(path):
    """폴더 내 전체 파일 수와 총 크기 계산"""
    total_files = 0
    total_size = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            total_files += 1
            total_size += os.path.getsize(os.path.join(root, f))
    return total_files, total_size


def progress_bar(current, total, width=30):
    """진행률 바 생성"""
    pct = current / total * 100 if total > 0 else 0
    filled = int(width * current // total) if total > 0 else 0
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {pct:.1f}%"


def upload_file_with_progress(ftp, local_path, remote_path, file_num, total_files, uploaded_bytes, total_bytes):
    """단일 파일 업로드 (진행률 표시)"""
    file_size = os.path.getsize(local_path)
    file_name = os.path.basename(local_path)
    sent = [0]

    def callback(block):
        sent[0] += len(block)
        current_total = uploaded_bytes + sent[0]
        file_pct = sent[0] / file_size * 100 if file_size > 0 else 100
        total_pct = current_total / total_bytes * 100 if total_bytes > 0 else 100

        sys.stdout.write(
            f"\r  📤 [{file_num}/{total_files}] {file_name} "
            f"({format_size(sent[0])}/{format_size(file_size)}) {file_pct:.0f}% "
            f"| 전체: {progress_bar(current_total, total_bytes)} "
            f"({format_size(current_total)}/{format_size(total_bytes)})"
        )
        sys.stdout.flush()

    with open(local_path, "rb") as f:
        ftp.storbinary(f"STOR {remote_path}", f, 8192, callback)

    sys.stdout.write(" ✓\n")
    sys.stdout.flush()
    return file_size


def upload_folder(ftp, local_path, remote_path, file_num, total_files, uploaded_bytes, total_bytes):
    """로컬 폴더를 재귀적으로 FTP 업로드"""
    for item in sorted(os.listdir(local_path)):
        local_item = os.path.join(local_path, item)
        remote_item = f"{remote_path}/{item}"

        if os.path.isdir(local_item):
            try:
                ftp.mkd(remote_item)
            except ftplib.error_perm:
                pass
            file_num, uploaded_bytes = upload_folder(
                ftp, local_item, remote_item, file_num, total_files, uploaded_bytes, total_bytes
            )
        else:
            file_num += 1
            size = upload_file_with_progress(
                ftp, local_item, remote_item, file_num, total_files, uploaded_bytes, total_bytes
            )
            uploaded_bytes += size

    return file_num, uploaded_bytes


def main():
    if len(sys.argv) > 1:
        local_folder = sys.argv[1]
    else:
        local_folder = input("업로드할 폴더 경로 (예: D:\\Photos\\여행): ").strip()

    # 따옴표 제거
    local_folder = local_folder.strip('"').strip("'")

    if not os.path.isdir(local_folder):
        print(f"[✗] 폴더를 찾을 수 없음: {local_folder}")
        sys.exit(1)

    # 스캔
    print(f"\n[*] 폴더 스캔 중: {local_folder}")
    total_files, total_size = scan_folder(local_folder)
    print(f"[*] 파일 {total_files}개, 총 {format_size(total_size)}")

    if total_files == 0:
        print("[!] 업로드할 파일이 없음")
        sys.exit(0)

    # 금일자 폴더명
    today = datetime.now().strftime("%Y-%m-%d")
    remote_dir = f"{NAS_BASE}/{today}"

    # NAS 접속
    print(f"\n[*] NAS 접속: {NAS_HOST}:{NAS_PORT}")
    ftp = ftplib.FTP()
    ftp.connect(NAS_HOST, NAS_PORT, timeout=30)
    ftp.login(NAS_USER, NAS_PASS)
    print(f"[✓] 로그인 성공")

    # 금일자 폴더 생성
    try:
        ftp.mkd(remote_dir)
        print(f"[✓] 폴더 생성: {remote_dir}")
    except ftplib.error_perm:
        print(f"[*] 폴더 이미 존재: {remote_dir}")

    # 하위 폴더 생성
    folder_name = os.path.basename(local_folder.rstrip("\\/"))
    target_dir = f"{remote_dir}/{folder_name}"
    try:
        ftp.mkd(target_dir)
        print(f"[✓] 하위 폴더 생성: {target_dir}")
    except ftplib.error_perm:
        print(f"[*] 하위 폴더 이미 존재: {target_dir}")

    # 업로드 시작
    start = datetime.now()
    print(f"\n[*] 업로드 시작!\n")
    file_num, uploaded_bytes = upload_folder(ftp, local_folder, target_dir, 0, total_files, 0, total_size)

    elapsed = (datetime.now() - start).total_seconds()
    speed = total_size / elapsed if elapsed > 0 else 0

    ftp.quit()
    print(f"\n{'='*50}")
    print(f"[✓] 업로드 완료!")
    print(f"    파일: {total_files}개")
    print(f"    크기: {format_size(total_size)}")
    print(f"    시간: {elapsed:.1f}초")
    print(f"    속도: {format_size(speed)}/s")
    print(f"    위치: {target_dir}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
