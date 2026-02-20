#!/usr/bin/env python3
"""ASUSTOR NAS FTP 접속 확인 스크립트"""

import ftplib
import sys

HOST = "oracle23cr2.myasustor.com"
PORT = 3000
USERNAME = input("FTP 사용자명: ")
PASSWORD = input("FTP 비밀번호: ")

try:
    print(f"\n[*] {HOST}:{PORT} 접속 시도...")
    ftp = ftplib.FTP()
    ftp.connect(HOST, PORT, timeout=10)
    print(f"[✓] 연결 성공! 서버 응답: {ftp.getwelcome()}")

    ftp.login(USERNAME, PASSWORD)
    print(f"[✓] 로그인 성공!")

    # 디렉토리 목록 출력
    print(f"\n[*] 루트 디렉토리 목록:")
    files = ftp.nlst()
    for f in files:
        print(f"  📁 {f}")

    ftp.quit()
    print(f"\n[✓] 정상 종료")

except ftplib.error_perm as e:
    print(f"[✗] 인증 실패: {e}")
except ConnectionRefusedError:
    print(f"[✗] 연결 거부 — 포트 {PORT} 확인 필요")
except TimeoutError:
    print(f"[✗] 타임아웃 — 호스트 또는 포트 확인 필요")
except Exception as e:
    print(f"[✗] 오류: {e}")
