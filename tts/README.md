# Gemini TTS — 구글 AI 스튜디오 텍스트 음성 변환

Google Gemini API를 활용한 무료 TTS(Text-to-Speech) 도구.

## 특징
- **무료** — Google AI Studio 무료 티어 (일일 10회, 분당 3회)
- **고품질** — ElevenLabs급 음성 품질
- **30종 보이스** — 다양한 톤/성별/스타일
- **한국어 지원** — 자연스러운 한국어 음성 생성

## 설치

```bash
pip install "google-genai>=1.16.0"
export GEMINI_API_KEY="your-api-key"
```

## 사용법

```bash
# 기본 사용 (kore 보이스)
python3 gemini_tts.py "안녕하세요, TTS 테스트입니다"

# 보이스 변경
python3 gemini_tts.py "텍스트" -v algenib -o result.wav

# 파일에서 읽기
python3 gemini_tts.py -f script.txt -v charon -o narration.wav

# 보이스 목록 보기
python3 gemini_tts.py --voices
```

## 보이스 목록 (30종)

```
achernar, achird, algenib, algieba, alnilam,
aoede, autonoe, callirrhoe, charon, despina,
enceladus, erinome, fenrir, gacrux, iapetus,
kore, laomedeia, leda, orus, puck,
pulcherrima, rasalgethi, sadachbia, sadaltager, schedar,
sulafat, umbriel, vindemiatrix, zephyr, zubenelgenubi
```

### 추천 보이스 (한국어 테스트 기준)
| 보이스 | 특징 |
|---|---|
| **algenib** | 차분하고 지적인 톤 (자비스 느낌) |
| **kore** | 따뜻하고 부드러운 |
| **charon** | 깊고 차분한 |
| **puck** | 발랄하고 명랑한 |
| **zephyr** | 밝고 활기찬 |

## Rate Limit (무료 티어)
- 분당 3회
- **일일 10회**
- 긴 텍스트는 2분 분량씩 분할 변환 권장

## 파일 구조
```
tts/
├── README.md           # 이 파일
├── gemini_tts.py       # 메인 TTS 스크립트
└── test_all_voices.py  # 전체 보이스 비교 테스트
```

## 참고
- [Google AI Studio](https://aistudio.google.com)
- [Gemini TTS 공식 문서](https://ai.google.dev/gemini-api/docs/speech-generation)
- 모델: `gemini-2.5-flash-preview-tts`
