#!/usr/bin/env python3
"""
ETF 매매 신호 디스코드 알림 시스템
웹훅을 통한 실시간 매매 신호 전송
"""

import requests
import json
from datetime import datetime
from typing import Dict, List
import logging

class ETFDiscordNotifier:
    def __init__(self, webhook_url: str):
        """디스코드 알림기 초기화"""
        self.webhook_url = webhook_url
        self.setup_logging()
        
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def send_trading_signal(self, signal_data: Dict):
        """매매 신호를 디스코드로 전송"""
        
        try:
            # 신호 타입별 색상 및 이모지
            signal_config = {
                'BUY': {
                    'color': 0x00ff00,  # 초록색
                    'emoji': '🟢',
                    'title': '매수 신호'
                },
                'SELL': {
                    'color': 0xff0000,  # 빨간색  
                    'emoji': '🔴',
                    'title': '매도 신호'
                },
                'HOLD': {
                    'color': 0xffff00,  # 노란색
                    'emoji': '⚪',
                    'title': '보유 신호'
                }
            }
            
            signal_type = signal_data['signal_type']
            config = signal_config.get(signal_type, signal_config['HOLD'])
            
            # ETF 정보 매핑
            etf_names = {
                '069500': 'KODEX 200',
                '229200': 'KODEX KOSDAQ150', 
                '102110': 'TIGER 200IT',
                '133690': 'TIGER NASDAQ100',
                '449180': 'KODEX US SP500',
                '161510': 'KODEX 고배당',
                '091230': 'KODEX 2차전지',
                '160580': 'KODEX 삼성우선주',
                '091170': 'TIGER 건설',
                '130680': 'TIGER 원유선물'
            }
            
            etf_code = signal_data['etf_code']
            etf_name = etf_names.get(etf_code, f'ETF {etf_code}')
            
            # 강도별 아이콘
            strength_icons = {
                'STRONG': '🔥🔥🔥',
                'MEDIUM': '🔥🔥',
                'WEAK': '🔥'
            }
            
            strength = signal_data.get('signal_strength', 'WEAK')
            strength_icon = strength_icons.get(strength, '🔥')
            
            # 디스코드 임베드 메시지 생성
            embed = {
                'title': f"{config['emoji']} {config['title']} {strength_icon}",
                'description': f"**{etf_name}** ({etf_code})",
                'color': config['color'],
                'timestamp': datetime.now().isoformat(),
                'fields': [
                    {
                        'name': '💰 현재가',
                        'value': f"{signal_data['price']:,}원",
                        'inline': True
                    },
                    {
                        'name': '📊 신호 강도', 
                        'value': f"{strength} {strength_icon}",
                        'inline': True
                    },
                    {
                        'name': '🕐 시간',
                        'value': datetime.now().strftime('%H:%M:%S'),
                        'inline': True
                    },
                    {
                        'name': '📋 신호 근거',
                        'value': signal_data.get('signal_reason', '분석 중...'),
                        'inline': False
                    }
                ],
                'footer': {
                    'text': '🤖 루나 ETF 자동매매 시스템',
                    'icon_url': 'https://cdn.discordapp.com/emojis/123456789.png'  # 루나 아이콘 URL
                }
            }
            
            # 기술적 지표가 있으면 추가
            if 'rsi_14' in signal_data and signal_data['rsi_14']:
                rsi_value = signal_data['rsi_14']
                rsi_status = self.get_rsi_status(rsi_value)
                
                embed['fields'].append({
                    'name': '📈 RSI(14)',
                    'value': f"{rsi_value:.1f} {rsi_status}",
                    'inline': True
                })
                
            if 'sma_5' in signal_data and signal_data['sma_5']:
                embed['fields'].append({
                    'name': '📊 SMA5/20',
                    'value': f"{signal_data['sma_5']:.0f}/{signal_data.get('sma_20', 0):.0f}",
                    'inline': True
                })
            
            # 웹훅 페이로드
            payload = {
                'username': '루나 ETF Bot 🌙',
                'avatar_url': 'https://cdn.discordapp.com/emojis/123456789.png',
                'embeds': [embed]
            }
            
            # 디스코드 웹훅 전송
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 204:
                self.logger.info(f"✅ 디스코드 알림 전송 성공: {etf_code} {signal_type}")
                return True
            else:
                self.logger.error(f"❌ 디스코드 알림 전송 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 디스코드 알림 오류: {e}")
            return False

    def send_daily_summary(self, summary_data: List[Dict]):
        """일일 매매 신호 요약을 디스코드로 전송"""
        
        try:
            # 신호별 개수 계산
            buy_signals = [s for s in summary_data if s['signal_type'] == 'BUY']
            sell_signals = [s for s in summary_data if s['signal_type'] == 'SELL'] 
            hold_signals = [s for s in summary_data if s['signal_type'] == 'HOLD']
            
            # 강한 신호들 필터링
            strong_signals = [s for s in summary_data if s['signal_strength'] == 'STRONG']
            
            # 요약 임베드 생성
            embed = {
                'title': '📊 ETF 매매 신호 일일 요약',
                'description': f"**{datetime.now().strftime('%Y-%m-%d')} 장 마감 결과**",
                'color': 0x3498db,  # 파란색
                'timestamp': datetime.now().isoformat(),
                'fields': [
                    {
                        'name': '📈 총 신호 현황',
                        'value': f"🟢 매수: {len(buy_signals)}개\n🔴 매도: {len(sell_signals)}개\n⚪ 보유: {len(hold_signals)}개",
                        'inline': True
                    },
                    {
                        'name': '🔥 강한 신호',
                        'value': f"{len(strong_signals)}개",
                        'inline': True
                    },
                    {
                        'name': '⏰ 업데이트 시간',
                        'value': datetime.now().strftime('%H:%M:%S'),
                        'inline': True
                    }
                ]
            }
            
            # 강한 신호가 있으면 상세 정보 추가
            if strong_signals:
                strong_list = []
                for signal in strong_signals[:5]:  # 최대 5개만
                    etf_names = {
                        '069500': 'KODEX 200',
                        '229200': 'KOSDAQ150',
                        '102110': 'TIGER IT',
                        '133690': 'NASDAQ100',
                        '449180': 'S&P500'
                    }
                    
                    etf_name = etf_names.get(signal['etf_code'], signal['etf_code'])
                    signal_emoji = '🟢' if signal['signal_type'] == 'BUY' else '🔴'
                    
                    strong_list.append(
                        f"{signal_emoji} **{etf_name}** {signal['signal_type']} - {signal['price']:,}원"
                    )
                
                embed['fields'].append({
                    'name': '🔥 주요 강한 신호',
                    'value': '\n'.join(strong_list),
                    'inline': False
                })
            
            # 오늘 최고 수익률 ETF (임시 데이터)
            embed['fields'].append({
                'name': '🏆 오늘의 베스트',
                'value': "📊 분석 중... 실시간 API 연동 후 표시",
                'inline': False
            })
            
            embed['footer'] = {
                'text': '🤖 루나 ETF 자동매매 시스템 - 일일 리포트',
            }
            
            payload = {
                'username': '루나 ETF 요약 Bot 📊',
                'embeds': [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                self.logger.info("✅ 디스코드 일일 요약 전송 성공")
                return True
            else:
                self.logger.error(f"❌ 디스코드 요약 전송 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 디스코드 요약 오류: {e}")
            return False

    def send_market_status(self, market_open: bool):
        """장 시작/종료 알림"""
        
        try:
            if market_open:
                embed = {
                    'title': '🔔 한국 주식 시장 개장!',
                    'description': '**ETF 실시간 모니터링을 시작합니다**',
                    'color': 0x00ff00,
                    'timestamp': datetime.now().isoformat(),
                    'fields': [
                        {
                            'name': '⏰ 개장 시간',
                            'value': '09:00 ~ 15:30 (KST)',
                            'inline': True
                        },
                        {
                            'name': '📊 모니터링 ETF',
                            'value': '10개 ETF 실시간 추적',
                            'inline': True
                        }
                    ]
                }
            else:
                embed = {
                    'title': '🔔 한국 주식 시장 마감!',
                    'description': '**오늘 거래가 종료되었습니다**',
                    'color': 0xff6600,
                    'timestamp': datetime.now().isoformat(),
                    'fields': [
                        {
                            'name': '📊 다음 단계',
                            'value': 'Redis → Oracle 배치 처리 시작',
                            'inline': False
                        }
                    ]
                }
            
            payload = {
                'username': '루나 Market Bot 🏛️',
                'embeds': [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                status = "개장" if market_open else "마감"
                self.logger.info(f"✅ 디스코드 시장 {status} 알림 전송 성공")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 디스코드 시장 상태 알림 오류: {e}")
            return False

    def send_system_alert(self, alert_type: str, message: str):
        """시스템 알럿 전송 (에러, 경고 등)"""
        
        try:
            alert_config = {
                'error': {
                    'color': 0xff0000,
                    'emoji': '🚨',
                    'title': '시스템 오류'
                },
                'warning': {
                    'color': 0xffaa00,
                    'emoji': '⚠️',
                    'title': '시스템 경고'
                },
                'info': {
                    'color': 0x3498db,
                    'emoji': 'ℹ️',
                    'title': '시스템 정보'
                }
            }
            
            config = alert_config.get(alert_type, alert_config['info'])
            
            embed = {
                'title': f"{config['emoji']} {config['title']}",
                'description': message,
                'color': config['color'],
                'timestamp': datetime.now().isoformat(),
                'footer': {
                    'text': '🤖 루나 ETF 시스템 모니터링'
                }
            }
            
            payload = {
                'username': '루나 System Bot ⚙️',
                'embeds': [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 204
            
        except Exception as e:
            self.logger.error(f"❌ 시스템 알럿 전송 오류: {e}")
            return False

    def get_rsi_status(self, rsi_value: float) -> str:
        """RSI 값에 따른 상태 이모지"""
        if rsi_value < 20:
            return "📉 극과매도"
        elif rsi_value < 30:
            return "📉 과매도"
        elif rsi_value > 80:
            return "📈 극과매수"  
        elif rsi_value > 70:
            return "📈 과매수"
        else:
            return "😐 중립"

    def test_webhook(self):
        """웹훅 연결 테스트"""
        
        try:
            test_embed = {
                'title': '🧪 디스코드 웹훅 테스트',
                'description': '**루나 ETF 시스템 연결 테스트**',
                'color': 0x00ff00,
                'timestamp': datetime.now().isoformat(),
                'fields': [
                    {
                        'name': '상태',
                        'value': '✅ 연결 성공',
                        'inline': True
                    },
                    {
                        'name': '시간',
                        'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'inline': True
                    }
                ],
                'footer': {
                    'text': '🤖 루나 ETF 자동매매 시스템'
                }
            }
            
            payload = {
                'username': '루나 Test Bot 🧪',
                'embeds': [test_embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                print("✅ 디스코드 웹훅 테스트 성공!")
                return True
            else:
                print(f"❌ 디스코드 웹훅 테스트 실패: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 웹훅 테스트 오류: {e}")
            return False

def main():
    """디스코드 알림기 테스트"""
    print("🎨 ETF 디스코드 알림 시스템 테스트")
    print("=" * 40)
    
    # 테스트용 웹훅 URL (실제 사용시 교체 필요)
    webhook_url = input("디스코드 웹훅 URL을 입력하세요: ").strip()
    
    if not webhook_url:
        print("❌ 웹훅 URL이 필요합니다.")
        return
    
    notifier = ETFDiscordNotifier(webhook_url)
    
    print("\n🧪 웹훅 연결 테스트...")
    if not notifier.test_webhook():
        print("❌ 웹훅 테스트 실패")
        return
    
    print("\n📊 매매 신호 테스트...")
    test_signal = {
        'etf_code': '069500',
        'signal_type': 'BUY', 
        'signal_strength': 'STRONG',
        'price': 27500,
        'signal_reason': 'RSI 극과매도 (18.3) + 골든크로스',
        'rsi_14': 18.3,
        'sma_5': 27450,
        'sma_20': 27200
    }
    
    notifier.send_trading_signal(test_signal)
    
    print("\n🏛️ 시장 상태 테스트...")
    notifier.send_market_status(True)  # 개장 알림
    
    print("\n✅ 디스코드 알림 시스템 테스트 완료!")

if __name__ == "__main__":
    main()