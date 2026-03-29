#!/usr/bin/env python3
"""모든 보이스 비교 테스트 (rate limit 대응)"""

import contextlib
import os
import time
import wave
from google import genai
from google.genai import types

MODEL_ID = "gemini-2.5-flash-preview-tts"

# 공식 지원 보이스 전체 (30종)
ALL_VOICES = [
    "achernar", "achird", "algenib", "algieba", "alnilam",
    "aoede", "autonoe", "callirrhoe", "charon", "despina",
    "enceladus", "erinome", "fenrir", "gacrux", "iapetus",
    "kore", "laomedeia", "leda", "orus", "puck",
    "pulcherrima", "rasalgethi", "sadachbia", "sadaltager", "schedar",
    "sulafat", "umbriel", "vindemiatrix", "zephyr", "zubenelgenubi",
]

# 이미 생성된 파일은 건너뛰기
TEXT = "안녕하세요. 저는 구글 AI 스튜디오의 TTS 보이스입니다. 이 목소리가 마음에 드시나요?"

@contextlib.contextmanager
def wave_file(filename, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        yield wf

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # 이미 생성된 파일 확인
    existing = set()
    for f in os.listdir("."):
        if f.startswith("voice_") and f.endswith(".wav"):
            name = f.replace("voice_", "").replace(".wav", "")
            existing.add(name)

    remaining = [v for v in ALL_VOICES if v not in existing]
    print(f"📊 전체 {len(ALL_VOICES)}종 | 완료 {len(existing)}종 | 남은 {len(remaining)}종")

    count = 0
    for voice in remaining:
        if count > 0 and count % 3 == 0:
            print("⏳ Rate limit 대기 (20초)...")
            time.sleep(20)

        print(f"🎙️  {voice} 생성 중...", end=" ", flush=True)
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=f"Say the following text naturally:\n\n{TEXT}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice
                            )
                        )
                    ),
                ),
            )
            blob = response.candidates[0].content.parts[0].inline_data
            fname = f"voice_{voice}.wav"
            with wave_file(fname) as wav:
                wav.writeframes(blob.data)
            size_kb = os.path.getsize(fname) / 1024
            print(f"✅ {fname} ({size_kb:.1f} KB)")
            count += 1
        except Exception as e:
            err = str(e)
            if "429" in err:
                print(f"⏳ Rate limit! 25초 대기 후 재시도...")
                time.sleep(25)
                try:
                    response = client.models.generate_content(
                        model=MODEL_ID,
                        contents=f"Say the following text naturally:\n\n{TEXT}",
                        config=types.GenerateContentConfig(
                            response_modalities=["AUDIO"],
                            speech_config=types.SpeechConfig(
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name=voice
                                    )
                                )
                            ),
                        ),
                    )
                    blob = response.candidates[0].content.parts[0].inline_data
                    fname = f"voice_{voice}.wav"
                    with wave_file(fname) as wav:
                        wav.writeframes(blob.data)
                    size_kb = os.path.getsize(fname) / 1024
                    print(f"✅ {fname} ({size_kb:.1f} KB)")
                    count += 1
                except Exception as e2:
                    print(f"❌ 재시도 실패: {e2}")
            else:
                print(f"❌ 실패: {e}")

    print(f"\n🎤 전체 생성 완료! ({len(existing) + count}/{len(ALL_VOICES)})")

if __name__ == "__main__":
    main()
