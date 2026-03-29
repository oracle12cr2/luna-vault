#!/usr/bin/env python3
"""Gemini TTS - 구글 AI 스튜디오 텍스트 음성 변환"""

import argparse
import contextlib
import os
import sys
import wave

from google import genai
from google.genai import types


MODEL_ID = "gemini-2.5-flash-preview-tts"

# 사용 가능한 보이스 목록
VOICES = {
    "zephyr": "Zephyr (밝고 활기찬)",
    "puck": "Puck (발랄하고 명랑한)",
    "charon": "Charon (깊고 차분한)",
    "kore": "Kore (따뜻하고 부드러운)",
    "fenrir": "Fenrir (낮고 힘있는)",
    "aoede": "Aoede (자연스럽고 중성적)",
    "leda": "Leda (성숙하고 안정적)",
    "orus": "Orus (크고 또렷한)",
    "perseus": "Perseus (부드럽고 편안한)",
}


@contextlib.contextmanager
def wave_file(filename, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        yield wf


def generate_tts(text: str, voice: str = "kore", output: str = "output.wav"):
    """텍스트를 음성으로 변환"""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경변수를 설정해주세요")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # 보이스 설정 포함한 프롬프트
    prompt = f"Say the following text in a natural, warm tone:\n\n{text}"

    print(f"🎙️  보이스: {voice}")
    print(f"📝 텍스트: {text[:80]}{'...' if len(text) > 80 else ''}")
    print(f"⏳ 음성 생성 중...")

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice.lower()
                    )
                )
            ),
        ),
    )

    # 오디오 데이터 추출
    blob = response.candidates[0].content.parts[0].inline_data

    # WAV 파일로 저장
    with wave_file(output) as wav:
        wav.writeframes(blob.data)

    # 파일 크기 확인
    size_kb = os.path.getsize(output) / 1024
    print(f"✅ 저장 완료: {output} ({size_kb:.1f} KB)")
    return output


def main():
    parser = argparse.ArgumentParser(description="Gemini TTS - 텍스트 음성 변환")
    parser.add_argument("text", nargs="?", help="변환할 텍스트")
    parser.add_argument("-f", "--file", help="텍스트 파일 경로")
    parser.add_argument(
        "-v", "--voice", default="kore", choices=list(VOICES.keys()),
        help="보이스 선택 (기본: kore)"
    )
    parser.add_argument("-o", "--output", default="output.wav", help="출력 파일명")
    parser.add_argument("--voices", action="store_true", help="사용 가능한 보이스 목록")

    args = parser.parse_args()

    if args.voices:
        print("🎤 사용 가능한 보이스:")
        for name, desc in VOICES.items():
            print(f"  {name:12s} — {desc}")
        return

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read().strip()
    elif args.text:
        text = args.text
    else:
        parser.print_help()
        return

    generate_tts(text, voice=args.voice, output=args.output)


if __name__ == "__main__":
    main()
